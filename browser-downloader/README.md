# 浏览器自动下载工具

基于 Playwright 的半自动文件下载脚本。账号密码可手动输入或从 `.env` 读取，验证码 / 二次验证由你在弹出的浏览器中手动完成，登录态自动保存供下次复用。

## 安装

```bash
cd browser-downloader
pip install -r requirements.txt
playwright install chromium
```

## 配置

```bash
cp config.example.json config.json
cp .env.example .env       # 可选
```

编辑 `config.json` 填入目标网站的 URL 和 CSS 选择器：

| 字段 | 含义 |
| --- | --- |
| `login_url` | 登录页 URL |
| `download_page_url` | 登录后跳转去查找下载链接的页面 |
| `selectors.username_input` | 账号输入框选择器 |
| `selectors.password_input` | 密码输入框选择器 |
| `selectors.submit_button` | 登录按钮（脚本会尝试自动点；留空则你手动点） |
| `selectors.login_success_indicator` | 登录成功后才出现的元素（用于确认登录完成） |
| `selectors.download_links` | 所有要下载的链接的选择器（支持多个，用逗号分隔） |
| `download_dir` | 下载目录 |
| `storage_state_file` | 保存登录态的文件路径 |
| `headless` | 是否无头运行（首次登录必须 false） |
| `wait_for_captcha_seconds` | >0 时改为定时等待模式（不需要按回车） |
| `max_files` | 限制最多下载几个，0 = 不限制 |

## 运行

```bash
python browser_downloader.py
# 或指定其他配置文件
python browser_downloader.py /path/to/other-config.json
```

**首次运行**：浏览器打开 → 脚本填账号密码 → 你输入验证码点登录 → 回终端按回车 → 自动下载 → `storage_state.json` 已保存。

**之后运行**：直接复用登录态，全自动下载。如果 session 过期，删掉 `storage_state.json` 重新登录即可。

## 安全

- `.env`、`config.json`、`storage_state.json`、`downloads/` 都已在 `.gitignore` 中，不会被提交。
- 密码通过 `getpass` 读取，输入时不显示在终端。
