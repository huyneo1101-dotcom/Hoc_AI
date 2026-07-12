# Học AI — trang hướng dẫn tiếng Việt cách dùng AI (ChatGPT/Claude/Gemini) và Claude Code

Trang tĩnh 1 file: `index.html` (~566 dòng), HTML + CSS + vanilla JS thuần — **KHÔNG React, KHÔNG build step, KHÔNG backend**. Chỉ là trang nội dung hướng dẫn có tab switcher (`showTab()`). Deploy tĩnh (GitHub Pages qua Actions + Netlify qua `netlify.toml`).

## Quy tắc làm việc với file này
- File nhỏ, chủ yếu là NỘI DUNG (text hướng dẫn) + CSS. Sửa nội dung → sửa trực tiếp trong `index.html`.
- Có `manifest.json` (PWA-lite, installable) nhưng **không có service worker** → không offline. Nếu muốn offline, xem skill `pwa-healthcheck` / `scaffold-vibe-pwa`.
- Không có React/Babel → không lo lỗi transpile. Không có localStorage/dữ liệu người dùng → không cần migration.

## Cấu trúc
- 2 tab: **"Hướng dẫn chung"** (`general`) và **"Claude & Claude Code"** (`claude`). Chuyển tab bằng `showTab(name)` (dòng ~549); tab mặc định đọc từ `location.hash` (`#claude` → tab claude, còn lại → general).
- Nội dung meta: trang này có phần dạy cách tạo Agent Skills (`.claude/skills`) — trớ trêu là repo trước đây tự nó chưa có, nay đã có `.claude/skills/` từ plugin vibe-pwa-kit.
- Asset: `icon.svg` (icon PWA), liên kết ra ngoài tới Anthropic Academy (`anthropic.skilljar.com`, `anthropic.com/learn`) và `nodejs.org`.

## Deploy
- **GitHub Pages** qua Actions: `.github/workflows/deploy-pages.yml`.
- **Netlify** qua `netlify.toml`: `publish = "."`, không có build command (`command = ""`), kèm security headers (X-Frame-Options, Referrer-Policy, X-Content-Type-Options).

## Skills dùng chung
Repo có `.claude/skills/` (11 skill từ plugin vibe-pwa-kit) — chủ yếu dành cho app React một-file; trang này đơn giản nên phần lớn skill không áp dụng, nhưng `deploy-static` và `pwa-healthcheck` vẫn hữu ích.
