import os
import sys
import time
import threading
import uvicorn
from playwright.sync_api import sync_playwright
from codesentinel.api.main import app

PORT = 8085
BASE_URL = f"http://127.0.0.1:{PORT}"

def start_server():
    server = uvicorn.Server(uvicorn.Config(app, host="127.0.0.1", port=PORT, log_level="error"))
    t = threading.Thread(target=server.run, daemon=True)
    t.start()
    
    start_time = time.time()
    while time.time() - start_time < 5:
        try:
            import urllib.request
            with urllib.request.urlopen(f"{BASE_URL}/api/health", timeout=1) as resp:
                if resp.status == 200:
                    break
        except Exception:
            time.sleep(0.1)
    print("Server ready on", BASE_URL)
    return server

def main():
    os.makedirs("docs/screenshots", exist_ok=True)
    server = start_server()
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1280, "height": 800})
        page = context.new_page()
        
        # 1. Login Page
        print("Navigating to /login...")
        page.goto(f"{BASE_URL}/login")
        page.wait_for_timeout(1000)
        page.screenshot(path="docs/screenshots/01_login.png")
        print("Saved docs/screenshots/01_login.png")
        
        # Perform Login
        page.fill("input#username", "admin")
        page.fill("input#password", "admin123")
        page.click("button[type='submit']")
        page.wait_for_timeout(1500)
        
        # 2. Overview / Dashboard
        print("Navigating to dashboard...")
        page.goto(f"{BASE_URL}/")
        page.wait_for_timeout(1500)
        page.screenshot(path="docs/screenshots/02_dashboard.png")
        print("Saved docs/screenshots/02_dashboard.png")
        
        # 3. Toggle Theme (Dark Mode)
        print("Toggling dark mode...")
        # Check if theme toggle button exists
        theme_btn = page.query_selector("button[aria-label*='theme' i], button[title*='theme' i], button:has(svg)")
        if theme_btn:
            theme_btn.click()
            page.wait_for_timeout(500)
        page.screenshot(path="docs/screenshots/03_dashboard_dark.png")
        print("Saved docs/screenshots/03_dashboard_dark.png")
        
        # 4. Pull Requests Page
        print("Navigating to /prs...")
        page.goto(f"{BASE_URL}/prs")
        page.wait_for_timeout(1500)
        page.screenshot(path="docs/screenshots/04_pull_requests.png")
        print("Saved docs/screenshots/04_pull_requests.png")
        
        # 5. Open PR Drawer
        print("Opening PR detail drawer...")
        pr_row = page.query_selector("table tbody tr")
        if pr_row:
            pr_row.click()
            page.wait_for_timeout(1000)
            page.screenshot(path="docs/screenshots/05_pr_drawer.png")
            print("Saved docs/screenshots/05_pr_drawer.png")
            
            # Close drawer if close button exists
            close_btn = page.query_selector("button[aria-label*='Close' i]")
            if close_btn:
                close_btn.click()
                page.wait_for_timeout(500)
                
        # 6. Issues Page
        print("Navigating to /issues...")
        page.goto(f"{BASE_URL}/issues")
        page.wait_for_timeout(1500)
        page.screenshot(path="docs/screenshots/06_issues.png")
        print("Saved docs/screenshots/06_issues.png")
        
        # 7. Mobile Viewport
        print("Testing mobile viewport...")
        mobile_context = browser.new_context(viewport={"width": 375, "height": 667})
        mobile_page = mobile_context.new_page()
        mobile_page.goto(f"{BASE_URL}/")
        mobile_page.wait_for_timeout(1500)
        mobile_page.screenshot(path="docs/screenshots/07_mobile_view.png")
        print("Saved docs/screenshots/07_mobile_view.png")
        
        browser.close()
    
    server.should_exit = True
    print("All Playwright E2E screenshots captured successfully!")

if __name__ == "__main__":
    main()
