#!/usr/bin/env python3
"""
浏览器自动下载工具（半自动登录 + Session 持久化）

工作流程：
  1. 如果存在 storage_state.json（已保存的登录态），直接复用，跳过登录步骤。
  2. 否则打开有头浏览器：
     - 自动填入账号密码（来自 .env 或终端交互输入）
     - 验证码 / 二次验证由你在弹出的浏览器窗口手动完成
     - 完成后回到终端按回车，脚本保存登录态供下次使用
  3. 进入下载页，按配置的选择器查找下载链接，依次下载到本地目录。

用法：
    pip install -r requirements.txt
    playwright install chromium
    cp config.example.json config.json   # 修改其中的 URL / 选择器
    cp .env.example .env                 # 可选：填入账号密码
    python browser_downloader.py
"""

from __future__ import annotations

import getpass
import json
import os
import sys
from pathlib import Path
from typing import Any

from playwright.sync_api import (
    Browser,
    BrowserContext,
    Page,
    Playwright,
    TimeoutError as PWTimeout,
    sync_playwright,
)

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_CONFIG_PATH = SCRIPT_DIR / "config.json"


def load_config(path: Path) -> dict[str, Any]:
    if not path.exists():
        sys.exit(
            f"找不到配置文件 {path}\n"
            f"请先运行：cp {path.parent / 'config.example.json'} {path}\n"
            f"然后编辑里面的 URL 和选择器。"
        )
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def get_credentials() -> tuple[str, str]:
    username = os.environ.get("LOGIN_USERNAME") or input("账号: ").strip()
    password = os.environ.get("LOGIN_PASSWORD") or getpass.getpass("密码（输入时隐藏）: ")
    if not username or not password:
        sys.exit("账号或密码为空，已退出。")
    return username, password


def has_saved_session(cfg: dict[str, Any]) -> bool:
    state_path = SCRIPT_DIR / cfg["storage_state_file"]
    return state_path.exists() and state_path.stat().st_size > 0


def new_context(browser: Browser, cfg: dict[str, Any]) -> BrowserContext:
    state_path = SCRIPT_DIR / cfg["storage_state_file"]
    download_dir = SCRIPT_DIR / cfg["download_dir"]
    download_dir.mkdir(parents=True, exist_ok=True)

    kwargs: dict[str, Any] = {"accept_downloads": True}
    if state_path.exists() and state_path.stat().st_size > 0:
        kwargs["storage_state"] = str(state_path)
    return browser.new_context(**kwargs)


def perform_login(page: Page, cfg: dict[str, Any]) -> None:
    sel = cfg["selectors"]
    username, password = get_credentials()

    print(f"打开登录页：{cfg['login_url']}")
    page.goto(cfg["login_url"], wait_until="domcontentloaded")

    page.fill(sel["username_input"], username)
    page.fill(sel["password_input"], password)
    print("已自动填入账号密码。")

    wait_seconds = int(cfg.get("wait_for_captcha_seconds", 0))
    if wait_seconds > 0:
        print(f"等待 {wait_seconds} 秒供你输入验证码...")
        page.wait_for_timeout(wait_seconds * 1000)
    else:
        print(
            "\n>>> 请在弹出的浏览器中手动完成：验证码 / 滑块 / 二次验证 / 点击登录按钮。\n"
            ">>> 完成后回到这里按回车继续（如果脚本应该自动点登录请直接按回车）..."
        )
        try:
            input()
        except EOFError:
            pass

    if sel.get("submit_button"):
        try:
            if page.locator(sel["submit_button"]).is_visible(timeout=2000):
                page.click(sel["submit_button"])
        except PWTimeout:
            pass

    success_sel = sel.get("login_success_indicator")
    if success_sel:
        print(f"等待登录成功标志：{success_sel}")
        try:
            page.wait_for_selector(success_sel, timeout=120_000)
            print("登录成功 ✓")
        except PWTimeout:
            sys.exit("等待登录成功标志超时。请检查 selectors.login_success_indicator 是否正确。")
    else:
        print("未配置 login_success_indicator，跳过登录校验（建议补上以提高可靠性）。")


def save_session(context: BrowserContext, cfg: dict[str, Any]) -> None:
    state_path = SCRIPT_DIR / cfg["storage_state_file"]
    context.storage_state(path=str(state_path))
    print(f"已保存登录态到 {state_path}（下次运行将自动复用）")


def download_files(page: Page, cfg: dict[str, Any]) -> int:
    sel = cfg["selectors"]
    download_dir = SCRIPT_DIR / cfg["download_dir"]
    max_files = int(cfg.get("max_files", 0))

    print(f"打开下载页：{cfg['download_page_url']}")
    page.goto(cfg["download_page_url"], wait_until="domcontentloaded")

    links = page.locator(sel["download_links"])
    count = links.count()
    if count == 0:
        print("未找到任何下载链接。请检查 selectors.download_links。")
        return 0

    if max_files > 0:
        count = min(count, max_files)
    print(f"找到 {count} 个待下载项，开始下载...")

    saved = 0
    for i in range(count):
        link = links.nth(i)
        try:
            label = (link.inner_text(timeout=2000) or "").strip().replace("\n", " ")[:60]
        except PWTimeout:
            label = f"item-{i}"
        try:
            with page.expect_download(timeout=60_000) as dl_info:
                link.click()
            download = dl_info.value
            target = download_dir / download.suggested_filename
            download.save_as(str(target))
            saved += 1
            print(f"  [{i + 1}/{count}] {label}  →  {target.name}")
        except PWTimeout:
            print(f"  [{i + 1}/{count}] {label}  →  超时未触发下载，跳过")
        except Exception as e:
            print(f"  [{i + 1}/{count}] {label}  →  失败：{e}")

    return saved


def run(playwright: Playwright, cfg: dict[str, Any]) -> None:
    browser = playwright.chromium.launch(headless=cfg.get("headless", False))
    context = new_context(browser, cfg)
    page = context.new_page()

    try:
        if has_saved_session(cfg):
            print("检测到已保存的登录态，跳过登录。")
        else:
            perform_login(page, cfg)
            save_session(context, cfg)

        saved = download_files(page, cfg)
        print(f"\n完成 ✓ 共保存 {saved} 个文件到 {SCRIPT_DIR / cfg['download_dir']}")
    finally:
        context.close()
        browser.close()


def main() -> None:
    config_path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_CONFIG_PATH
    cfg = load_config(config_path)
    with sync_playwright() as p:
        run(p, cfg)


if __name__ == "__main__":
    main()
