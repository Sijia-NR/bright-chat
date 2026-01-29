#!/usr/bin/env python3
"""
诊断前端页面结构
"""
from playwright.sync_api import sync_playwright
import time

with sync_playwright() as p:
    browser = p.chromium.launch(
        headless=True,
        args=['--no-sandbox', '--disable-setuid-sandbox']
    )
    context = browser.new_context(viewport={'width': 1920, 'height': 1080})
    page = context.new_page()

    try:
        print("=" * 80)
        print("诊断前端页面结构")
        print("=" * 80)

        # 访问首页
        print("\n1. 访问首页")
        page.goto("http://localhost:8080", wait_until="networkidle")
        print(f"   URL: {page.url}")
        print(f"   Title: {page.title()}")

        # 获取页面内容
        print("\n2. 获取页面HTML结构")
        html = page.content()
        print(f"   HTML长度: {len(html)}")

        # 查找所有input元素
        print("\n3. 查找input元素")
        inputs = page.query_selector_all("input")
        print(f"   找到 {len(inputs)} 个input元素")
        for i, inp in enumerate(inputs[:5]):
            input_type = inp.get_attribute("type") or "text"
            input_placeholder = inp.get_attribute("placeholder") or ""
            input_name = inp.get_attribute("name") or ""
            input_id = inp.get_attribute("id") or ""
            print(f"   Input {i+1}: type={input_type}, placeholder={input_placeholder}, name={input_name}, id={input_id}")

        # 查找所有button元素
        print("\n4. 查找button元素")
        buttons = page.query_selector_all("button")
        print(f"   找到 {len(buttons)} 个button元素")
        for i, btn in enumerate(buttons[:5]):
            btn_text = btn.text_content() or ""
            btn_type = btn.get_attribute("type") or ""
            print(f"   Button {i+1}: text={btn_text[:50]}, type={btn_type}")

        # 检查是否已登录
        print("\n5. 检查是否已登录")
        has_new_session = False
        try:
            page.wait_for_selector("text=新会话", timeout=2000)
            has_new_session = True
            print("   ✓ 已登录（检测到'新会话'按钮）")
        except:
            print("   ✗ 未登录")

        if not has_new_session:
            print("\n6. 执行登录")
            # 查找用户名输入框
            username_filled = False
            for selector in ["input[type='text']", "input[placeholder*='用户']", "[name='username']"]:
                try:
                    if page.query_selector(selector):
                        page.fill(selector, "admin")
                        username_filled = True
                        print(f"   ✓ 填写用户名: {selector}")
                        break
                except:
                    pass

            if not username_filled:
                print("   ✗ 未找到用户名输入框")

            time.sleep(0.5)

            # 查找密码输入框
            password_filled = False
            for selector in ["input[type='password']", "input[placeholder*='密码']", "[name='password']"]:
                try:
                    if page.query_selector(selector):
                        page.fill(selector, "pwd123")
                        password_filled = True
                        print(f"   ✓ 填写密码: {selector}")
                        break
                except:
                    pass

            if not password_filled:
                print("   ✗ 未找到密码输入框")

            time.sleep(0.5)

            # 查找登录按钮
            login_clicked = False
            for selector in ["button:has-text('登录')", "button[type='submit']"]:
                try:
                    if page.query_selector(selector):
                        page.click(selector)
                        login_clicked = True
                        print(f"   ✓ 点击登录按钮: {selector}")
                        break
                except:
                    pass

            if not login_clicked:
                print("   ✗ 未找到登录按钮")

            time.sleep(3)

            # 检查登录结果
            print("\n7. 检查登录结果")
            print(f"   URL: {page.url}")
            print(f"   Title: {page.title()}")

            # 查找主界面元素
            main_ui_indicators = [
                "text=新会话",
                "text=发送",
                ".chat-container",
                "textarea"
            ]

            for indicator in main_ui_indicators:
                try:
                    page.wait_for_selector(indicator, timeout=2000)
                    print(f"   ✓ 检测到主界面元素: {indicator}")
                    break
                except:
                    print(f"   ✗ 未检测到: {indicator}")

            # 获取登录后的页面内容
            print("\n8. 登录后页面内容")
            html_after = page.content()
            print(f"   HTML长度: {len(html_after)}")

            # 查找所有可见文本
            print("\n9. 查找页面主要文本内容")
            body_text = page.evaluate("() => document.body.innerText")
            lines = body_text.split('\n')[:20]
            for line in lines:
                if line.strip():
                    print(f"   {line[:80]}")

            # 保存截图
            screenshot_path = "/data1/allresearchProject/Bright-Chat/backend-python/diagnose_screenshot.png"
            page.screenshot(path=screenshot_path, full_page=True)
            print(f"\n10. 截图已保存: {screenshot_path}")

    finally:
        browser.close()

print("\n" + "=" * 80)
print("诊断完成")
print("=" * 80)
