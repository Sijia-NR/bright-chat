#!/usr/bin/env python3
"""
诊断网络请求
"""
from playwright.sync_api import sync_playwright
import time
import json

with sync_playwright() as p:
    browser = p.chromium.launch(
        headless=True,
        args=['--no-sandbox', '--disable-setuid-sandbox']
    )
    context = browser.new_context(viewport={'width': 1920, 'height': 1080})

    # 监听网络请求
    requests_log = []

    def log_request(request):
        requests_log.append({
            'url': request.url,
            'method': request.method,
            'headers': request.headers
        })
        print(f"[REQUEST] {request.method} {request.url}")

    def log_response(response):
        print(f"[RESPONSE] {response.status} {response.url}")
        if response.status >= 400:
            print(f"  Error: {response.status}")

    page = context.new_page()
    page.on("request", log_request)
    page.on("response", log_response)

    try:
        print("=" * 80)
        print("诊断网络请求")
        print("=" * 80)

        # 访问首页
        print("\n1. 访问首页")
        page.goto("http://localhost:8080", wait_until="networkidle")
        time.sleep(2)

        # 执行登录
        print("\n2. 执行登录")
        page.fill("input[type='text']", "admin")
        time.sleep(0.5)
        page.fill("input[type='password']", "pwd123")
        time.sleep(0.5)

        print("\n3. 点击登录按钮（监听网络请求）")
        page.click("button:has-text('登录')")

        # 等待响应
        time.sleep(5)

        print("\n4. 网络请求汇总:")
        print(f"   总请求数: {len(requests_log)}")

        # 查找登录请求
        login_requests = [r for r in requests_log if 'login' in r['url'].lower() or 'auth' in r['url'].lower()]
        print(f"   登录相关请求: {len(login_requests)}")
        for req in login_requests:
            print(f"     - {req['method']} {req['url']}")

        # 查找API请求
        api_requests = [r for r in requests_log if '18080' in r['url']]
        print(f"   后端API请求: {len(api_requests)}")
        for req in api_requests:
            print(f"     - {req['method']} {req['url']}")

        time.sleep(5)

        print("\n5. 检查页面状态")
        print(f"   URL: {page.url}")
        print(f"   Title: {page.title()}")

        body_text = page.evaluate("() => document.body.innerText")
        if "登录失败" in body_text:
            print("   状态: 登录失败")
        elif "新会话" in body_text:
            print("   状态: 登录成功")
        else:
            print("   状态: 未知")

    finally:
        browser.close()

print("\n" + "=" * 80)
print("诊断完成")
print("=" * 80)
