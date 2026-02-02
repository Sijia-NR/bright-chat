"""
浏览器工具（服务端 Playwright 无头模式）
Browser Tool using Server-Side Playwright Headless Mode

允许 Agent 执行网页浏览、数据抓取等任务
Allows Agent to perform web browsing, data scraping, etc.
"""
import asyncio
import logging
from typing import Dict, Any, Optional, List
from urllib.parse import unquote
from playwright.async_api import async_playwright, Browser, Page, BrowserContext

logger = logging.getLogger(__name__)

# 全局浏览器实例（复用以提高性能）
_browser: Optional[Browser] = None
_context: Optional[BrowserContext] = None
_playwright = None

# 并发保护锁
_browser_lock = asyncio.Lock()
_context_lock = asyncio.Lock()


async def _get_browser() -> Browser:
    """获取或创建浏览器实例（线程安全）"""
    global _browser, _playwright

    async with _browser_lock:
        if _browser is None or not _browser.is_connected():
            logger.info("🌐 [浏览器工具] 启动无头浏览器...")
            _playwright = await async_playwright().start()
            _browser = await _playwright.chromium.launch(headless=True)
            logger.info("✅ [浏览器工具] 浏览器启动成功")

        return _browser


async def _get_context() -> BrowserContext:
    """获取或创建浏览器上下文（线程安全）"""
    global _context

    browser = await _get_browser()

    async with _context_lock:
        if _context is None or not _browser.is_connected():
            logger.info("🌐 [浏览器工具] 创建浏览器上下文...")
            _context = await browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            )
            logger.info("✅ [浏览器工具] 浏览器上下文创建成功")

        return _context


async def browser_tool(
    action: str,
    url: Optional[str] = None,
    selector: Optional[str] = None,
    text: Optional[str] = None,
    wait_time: int = 3000
) -> Dict[str, Any]:
    """
    浏览器工具（服务端无头模式）

    支持的操作：
    - navigate: 导航到 URL
    - screenshot: 截图
    - click: 点击元素
    - fill: 填写表单
    - scrape: 抓取页面文本
    - search: 搜索引擎搜索

    Args:
        action: 操作类型 (navigate/screenshot/click/fill/scrape/search)
        url: 目标 URL
        selector: CSS 选择器
        text: 文本内容（用于填写或搜索）
        wait_time: 等待时间（毫秒）

    Returns:
        操作结果
    """
    import time
    start_time = time.time()

    logger.info(f"🌐 [浏览器工具] 开始执行操作: {action}")
    logger.info(f"🌐 [浏览器工具] URL: {url}")
    logger.info(f"🌐 [浏览器工具] 选择器: {selector}")

    try:
        browser = await _get_browser()
        context = await _get_context()
        page = await context.new_page()

        result = {"success": False, "data": None, "error": None}

        if action == "navigate":
            # 导航到指定 URL
            if not url:
                result["error"] = "缺少 URL 参数"
                return result

            logger.info(f"🌐 [浏览器工具] 导航到: {url}")
            await page.goto(url, wait_until="networkidle", timeout=30000)
            result["success"] = True
            result["data"] = {"url": page.url, "title": await page.title()}

        elif action == "screenshot":
            # 截图
            screenshot_bytes = await page.screenshot(full_page=False)
            import base64
            result["success"] = True
            result["data"] = {
                "screenshot": base64.b64encode(screenshot_bytes).decode('utf-8'),
                "format": "base64"
            }

        elif action == "click":
            # 点击元素
            if not selector:
                result["error"] = "缺少 selector 参数"
                return result

            logger.info(f"🌐 [浏览器工具] 点击元素: {selector}")
            await page.click(selector, timeout=10000)
            await page.wait_for_timeout(wait_time)
            result["success"] = True
            result["data"] = {"clicked": selector}

        elif action == "fill":
            # 填写表单
            if not selector or not text:
                result["error"] = "缺少 selector 或 text 参数"
                return result

            logger.info(f"🌐 [浏览器工具] 填写: {selector} = {text}")
            await page.fill(selector, text, timeout=10000)
            result["success"] = True
            result["data"] = {"filled": selector, "text": text}

        elif action == "scrape":
            # 抓取页面文本
            if url:
                await page.goto(url, wait_until="networkidle", timeout=30000)

            # 等待页面加载
            await page.wait_for_timeout(2000)

            # 获取页面文本
            text_content = await page.inner_text("body")

            # 获取页面元数据
            title = await page.title()
            url_final = page.url

            result["success"] = True
            result["data"] = {
                "title": title,
                "url": url_final,
                "content": text_content[:10000],  # 限制长度
                "content_length": len(text_content)
            }

        elif action == "search":
            # 搜索引擎搜索（使用百度）
            if not text:
                result["error"] = "缺少搜索关键词"
                return result

            # ✅ 改为百度搜索
            search_url = f"https://www.baidu.com/s?wd={text}"
            logger.info(f"🌐 [浏览器工具] 百度搜索: {text}")

            await page.goto(search_url, wait_until="networkidle", timeout=30000)
            await page.wait_for_timeout(2000)

            # 提取百度搜索结果
            # 百度结果选择器：div.c-container 或 div.result
            results = await page.query_selector_all("div.c-container")

            search_data = []
            for i, result_elem in enumerate(results[:10]):  # 最多 10 个结果
                try:
                    # 百度的标题选择器
                    title_elem = await result_elem.query_selector("h3 a")
                    if not title_elem:
                        continue

                    title = await title_elem.inner_text()
                    link = await title_elem.get_attribute("href")

                    # 百度的摘要选择器
                    snippet_elem = await result_elem.query_selector("div.c-abstract")
                    snippet = await snippet_elem.inner_text() if snippet_elem else ""

                    # 清理百度链接（去除百度跳转链接）
                    if link and link.startswith("/link?url="):
                        # 解码百度跳转链接
                        link = unquote(link.split("url=")[1].split("&")[0])

                    search_data.append({
                        "rank": i + 1,
                        "title": title.strip(),
                        "url": link,
                        "snippet": snippet[:200] if snippet else ""
                    })
                except Exception as e:
                    logger.warning(f"⚠️ [浏览器工具] 提取百度结果 {i+1} 失败: {e}")
                    continue

            result["success"] = True
            result["data"] = {
                "query": text,
                "results": search_data,
                "count": len(search_data),
                "engine": "baidu"  # 标记使用的搜索引擎
            }
            logger.info(f"✅ [浏览器工具] 百度搜索完成，找到 {len(search_data)} 个结果")

        else:
            result["error"] = f"不支持的操作: {action}"

        # 关闭页面
        await page.close()

        execution_time = time.time() - start_time
        logger.info(f"✅ [浏览器工具] 操作完成，耗时: {execution_time:.3f}秒")

        return result

    except Exception as e:
        error_msg = f"浏览器操作失败: {str(e)}"
        logger.error(f"❌ [浏览器工具] {error_msg}")
        return {"success": False, "error": error_msg, "data": None}


async def close_browser():
    """关闭浏览器（用于清理）"""
    global _browser, _context, _playwright

    async with _context_lock:
        if _context:
            await _context.close()
            _context = None

    async with _browser_lock:
        if _browser:
            await _browser.close()
            _browser = None

        if _playwright:
            await _playwright.stop()
            _playwright = None

    logger.info("🌐 [浏览器工具] 浏览器已关闭")
