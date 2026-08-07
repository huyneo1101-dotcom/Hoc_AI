# Học AI — trang hướng dẫn tiếng Việt cách dùng AI (ChatGPT/Claude/Gemini) và Claude Code

Trang tĩnh 1 file: `index.html` (~4.070 dòng, đo 07/08/2026), HTML + CSS + vanilla JS thuần — **KHÔNG React, KHÔNG build step, KHÔNG backend**. Chỉ là trang nội dung hướng dẫn có tab switcher (`showTab()`). Deploy tĩnh (GitHub Pages qua Actions + Netlify qua `netlify.toml`).

## Quy tắc làm việc với file này
- File nhỏ, chủ yếu là NỘI DUNG (text hướng dẫn) + CSS. Sửa nội dung → sửa trực tiếp trong `index.html`.
- Có `manifest.json` (PWA-lite, installable) nhưng **không có service worker** → không offline. Nếu muốn offline, xem skill `pwa-healthcheck` / `scaffold-vibe-pwa`.
- Không có React/Babel → không lo lỗi transpile. Không có localStorage/dữ liệu người dùng → không cần migration.

## Cấu trúc
- **2 tab chính**: "Kiến thức chung" (`concepts`) và "Tin mới" (`news`), cộng menu xổ "Công cụ AI (24)". Chuyển bằng `showTab(name)`; tab mặc định đọc từ `location.hash`, hash lạ thì rơi về `concepts`.
  - Tab **"Phân tích"** (`analysis`) đã bị **gỡ ngày 07/08/2026** theo yêu cầu của Huy — gỡ trọn 03 chỗ: nút trong `.tabs`, khối `<div id="tab-analysis">`, và khoá `analysis` trong bảng `tabs` của `showTab()`. Thêm/gỡ tab thì phải sờ đủ 03 chỗ này, thiếu chỗ thứ ba thì `showTab` ném lỗi trên `.hidden` của `null`.
- 7 tab con trong `concepts` (`showSubTab`): `general` · `toolsdeep` · `overview` · `claude` · `agentic` · `roadmap` · `quiz`.

### Tab "Tin mới" — khuôn bắt buộc khi thêm tin (nâng cấp 07/08/2026)
Tab này nay có **bộ lọc theo chủ đề** (`filterNews(cat)`), nên **mỗi tin PHẢI mang `data-cat`** — thiếu thuộc tính đó thì tin biến mất khỏi mọi bộ lọc trừ "Tất cả", và **không có lỗi nào phát ra**: trang vẫn render, nút vẫn bấm được, chỉ là tin đó không bao giờ hiện khi lọc.

Khuôn một tin, dán nguyên vào đầu `<div class="news-list" id="news-list">` (mới nhất trên cùng):

```html
<div class="news-item" data-cat="model">
  <div class="news-item-head"><span class="news-date">07/08/2026</span><span class="news-cat">Model mới</span></div>
  <h3>Tiêu đề tiếng Việt, không thuật ngữ trần</h3>
  <p>2-4 câu diễn giải lại, đủ ngày · ai làm · làm gì · con số.</p>
  <div class="news-impact"><b>👉 Với bạn:</b> ảnh hưởng thực tế với người dùng thường.</div>
  <div class="source-note">Nguồn: <a href="URL" target="_blank" rel="noopener">Tên nguồn</a></div>
</div>
```

- **08 giá trị `data-cat` hợp lệ** (phải khớp `data-cat` của nút trong `#news-filter`, không được đặt giá trị mới nếu chưa thêm nút): `model` · `gia` · `agent` · `sangtao` · `vn` · `luat` · `antoan` · `hatang`.
- **Dòng `news-impact` là bắt buộc** — đây là thứ phân biệt trang này với một trang tổng hợp tin thường. Không có nó thì tin chỉ là chuyện của hãng.
- **Nguồn lấy từ trang thứ ba phải ghi chữ "tổng hợp qua"** trước tên nguồn; nguồn chính hãng thì dẫn thẳng. Trang tự khai quy ước này trong khối `.news-note`, nên bỏ chữ đó là làm trang nói sai về chính nó.
- **Mọi `<a>` phải có `target="_blank" rel="noopener"`** và phải đo trả HTTP 200 trước khi ghi vào. Đo song song nhiều luồng hay dính 403/429 giả — link nào hỏng thì **đo lại tuần tự có `sleep`** rồi mới kết luận là chết.
- Nếu có routine tự bơm tin vào tab này, phần sinh HTML phải theo đúng khuôn trên; cập nhật luôn ngày trong dòng "Cập nhật lần gần nhất" của khối `.news-note`.
- Ngoài danh sách tin, tab còn 02 mục cố định phải giữ đồng bộ khi thêm tin lớn: bảng **"Dòng thời gian model lớn năm 2026"** (`.news-tl`) và lưới **"Tự theo dõi tin AI ở đâu cho chắc"** (`.news-src`).
- Nội dung meta: trang này có phần dạy cách tạo Agent Skills (`.claude/skills`) — trớ trêu là repo trước đây tự nó chưa có, nay đã có `.claude/skills/` từ plugin vibe-pwa-kit.
- Asset: `icon.svg` (icon PWA), liên kết ra ngoài tới Anthropic Academy (`anthropic.skilljar.com`, `anthropic.com/learn`) và `nodejs.org`.

## Deploy
- **GitHub Pages** qua Actions: `.github/workflows/deploy-pages.yml`.
- **Netlify** qua `netlify.toml`: `publish = "."`, không có build command (`command = ""`), kèm security headers (X-Frame-Options, Referrer-Policy, X-Content-Type-Options).

## Skills dùng chung
Repo có `.claude/skills/` (11 skill từ plugin vibe-pwa-kit) — chủ yếu dành cho app React một-file; trang này đơn giản nên phần lớn skill không áp dụng, nhưng `deploy-static` và `pwa-healthcheck` vẫn hữu ích.
