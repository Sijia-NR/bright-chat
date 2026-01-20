import httpx
import json
from typing import Dict, Any, Optional
from fastapi import HTTPException, status
from contextlib import asynccontextmanager
import asyncio
from io import StringIO

from ..core.config import settings
from ..models.ias import IASChatRequest, IASChatResponse, IASChoice


class IASProxyService:
    def __init__(self):
        self.base_url = settings.IAS_BASE_URL
        self.timeout = settings.IAS_TIMEOUT
        self.max_retries = settings.IAS_MAX_RETRIES
        self.client = httpx.AsyncClient(
            timeout=self.timeout,
            limits=httpx.Limits(max_connections=100, max_keepalive_connections=20)
        )

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()

    @asynccontextmanager
    async def get_client(self):
        """Get HTTP client with proper error handling."""
        try:
            yield self.client
        except Exception as e:
            await self.close()
            raise e

    async def _make_request(
        self,
        method: str,
        url: str,
        json_data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        stream: bool = False
    ) -> Any:
        """Make HTTP request with retry logic."""
        last_exception = None

        for attempt in range(self.max_retries):
            try:
                async with self.get_client() as client:
                    response = client.request(
                        method,
                        url,
                        json=json_data,
                        headers=headers,
                        stream=stream
                    )

                    if stream:
                        return response
                    else:
                        response.raise_for_status()
                        return response.json()

            except httpx.HTTPStatusError as e:
                last_exception = e
                if e.response.status_code in [401, 403]:
                    # Don't retry on auth errors
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Invalid authentication for IAS API"
                    )
                if attempt == self.max_retries - 1:
                    raise
                await asyncio.sleep(2 ** attempt)  # Exponential backoff

            except httpx.RequestError as e:
                last_exception = e
                if attempt == self.max_retries - 1:
                    raise
                await asyncio.sleep(2 ** attempt)  # Exponential backoff

        # If we get here, all retries failed
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Failed after {self.max_retries} attempts: {str(last_exception)}"
        )

    async def chat(
        self,
        request: IASChatRequest,
        authorization: str,
        stream: bool = True
    ) -> IASChatResponse:
        """Proxy chat request to IAS API."""
        headers = {
            "Authorization": authorization,
            "Content-Type": "application/json",
            "Accept": "text/event-stream" if stream else "application/json"
        }

        # Prepare URL
        url = f"{self.base_url}/lmp-cloud-ias-server/api/llm/chat/completions/V2"

        try:
            if stream:
                return await self._stream_chat(url, request, headers)
            else:
                return await self._regular_chat(url, request, headers)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"IAS API error: {str(e)}"
            )

    async def _regular_chat(
        self,
        url: str,
        request: IASChatRequest,
        headers: Dict[str, str]
    ) -> IASChatResponse:
        """Make non-streaming chat request."""
        json_data = request.dict()
        response_data = await self._make_request(
            "POST",
            url,
            json_data=json_data,
            headers=headers,
            stream=False
        )

        return IASChatResponse(**response_data)

    async def _stream_chat(
        self,
        url: str,
        request: IASChatRequest,
        headers: Dict[str, str]
    ):
        """Make streaming chat request and return generator for SSE."""
        json_data = request.dict()
        json_data["stream"] = True

        response = await self._make_request(
            "POST",
            url,
            json_data=json_data,
            headers=headers,
            stream=True
        )

        # Process SSE stream and yield chunks
        async for line in response.aiter_lines():
            line = line.strip()
            if not line:
                continue

            if line.startswith("data: "):
                data = line[6:]  # Remove "data: " prefix
                if data == "[DONE]":
                    # Send final signal
                    yield "data: [DONE]\n\n"
                    break

                try:
                    chunk = json.loads(data)
                    # Convert chunk to SSE format
                    yield f"data: {json.dumps(chunk)}\n\n"
                except json.JSONDecodeError:
                    continue

    async def _process_stream_chunk(
        self,
        chunk: Dict[str, Any],
        full_response: IASChatResponse,
        buffer: StringIO
    ):
        """Process a single streaming chunk."""
        chunk_id = chunk.get("id", "")
        if not full_response.id:
            full_response.id = chunk_id

        full_response.app_id = chunk.get("appId", "")
        full_response.global_trace_id = chunk.get("globalTraceId", "")
        full_response.object = chunk.get("object", "")
        full_response.created = chunk.get("created", 0)

        choices = chunk.get("choices", [])
        for chunk_choice in choices:
            # Find or create choice
            choice = None
            for existing_choice in full_response.choices:
                if existing_choice.index == chunk_choice.get("index"):
                    choice = existing_choice
                    break

            if not choice:
                choice = IASChoice(
                    index=chunk_choice.get("index", 0),
                    finish_reason=None,
                    delta=None,
                    message=None
                )
                full_response.choices.append(choice)

            # Update choice with chunk data
            if "finish_reason" in chunk_choice:
                choice.finish_reason = chunk_choice["finish_reason"]

            if "delta" in chunk_choice:
                delta = chunk_choice["delta"]
                if choice.delta is None:
                    choice.delta = delta
                else:
                    # Merge delta
                    if delta.get("role"):
                        choice.delta["role"] = delta["role"]
                    if delta.get("content"):
                        # Buffer partial content
                        buffer.write(delta["content"])
                        choice.delta["content"] = delta["content"]

            if "message" in chunk_choice:
                if choice.message is None:
                    choice.message = chunk_choice["message"]
                else:
                    # Merge message
                    if chunk_choice["message"].get("role"):
                        choice.message.role = chunk_choice["message"]["role"]
                    if chunk_choice["message"].get("content"):
                        choice.message.content += chunk_choice["message"]["content"]

        # Handle usage
        if "usage" in chunk:
            full_response.usage = chunk["usage"]

    async def _stream_generator(self, request: IASChatRequest, authorization: str):
        """Generator for streaming responses."""
        headers = {
            "Authorization": authorization,
            "Content-Type": "application/json",
            "Accept": "text/event-stream"
        }

        url = f"{self.base_url}/lmp-cloud-ias-server/api/llm/chat/completions/V2"

        async for chunk in self._stream_chat(url, request, headers):
            yield chunk


# Create service instance
ias_proxy_service = IASProxyService()