from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from fastapi import Request

from ...models.ias import IASChatRequest, IASChatResponse
from ...services.ias_proxy import ias_proxy_service
from ..middleware import setup_middleware

router = APIRouter(tags=["IAS API Proxy"])


@router.post("/lmp-cloud-ias-server/api/llm/chat/completions/V2")
async def proxy_chat(
    request: Request,
    chat_request: IASChatRequest
):
    """Proxy chat request to IAS API with streaming support."""
    # Get authorization header
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )

    authorization = auth_header

    try:
        # Determine if we want streaming
        stream = chat_request.stream

        if stream:
            # Return streaming response
            return StreamingResponse(
                ias_proxy_service._stream_generator(chat_request, authorization),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "Access-Control-Allow-Origin": "*",
                }
            )
        else:
            # Return regular JSON response
            response = await ias_proxy_service.chat(
                chat_request,
                authorization,
                stream=False
            )
            return response

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"IAS API error: {str(e)}"
        )