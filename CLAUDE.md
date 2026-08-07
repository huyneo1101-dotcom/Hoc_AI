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

## Tin ở tab "Tin mới" — nay có routine, ĐỪNG sửa tay khối đó nữa (07/08/2026)

Trước 07/08 tab này là điểm quét tin duy nhất trong hệ không routine nào đụng tới, trang tự
ghi là *"cập nhật thủ công"*. Nay:

| File | Vai |
|---|---|
| `nguon-tin-ai.json` | bảng 14 nguồn RSS/Atom. Đo lại: `quet-tin-ai.py --do-nguon` |
| `quet-tin-ai.py` | quét, lọc, chống trùng → ghi lô vào `.quet/lo-<ngày>.json` |
| `tin-ai.json` | **dữ liệu hiển thị**. Routine ghi vào đây, trang nạp bằng `fetch` |
| `dang-tin.py` | cổng kiểm khuôn + commit + push. Đường DUY NHẤT được chạm git |
| `test-quet-tin-ai.py` | 26 ca (18 PHẢI CHẶN) · `--tu-kiem` bắt 14/14 bản hỏng |

**Chạy khi nào:** bước 5 của task `tin-kinh-doanh` (LaunchAgent 06:30). Cố ý ghép vào phiên có
sẵn thay vì dựng mốc riêng — khoản đắt của routine là số PHIÊN Claude mở ra (~173k token nền
mỗi phiên), không phải việc tải trang.

- **Các mục viết tay trong `index.html` giữ nguyên.** Mục mới do routine chèn nằm TRÊN chúng,
  bằng khối script cuối file. Đừng gộp hai nguồn này lại.
- **Nhãn `cat` phải khớp bảng `NHAN`** trong khối script đó: `model · gia · agent · antoan ·
  luat · hatang · sangtao · vn`. Lệch một chữ thì mục vẫn lên trang nhưng rơi hết về "Model
  mới" và bộ lọc chủ đề không tìm ra nó — `dang-tin.py` chặn trước, đừng gỡ cổng ấy.
- ⚠️ **`el.find('title') or el.find(atom_title)` là bug, không phải cách viết gọn.** Element
  không có con là FALSY trong Python nên `or` nhảy sang vế sau và trả `None`. Đo thật lúc
  dựng: 12/14 nguồn ra 0 tin, mà bảng vẫn in "14/14 nguồn sống" vì fetch không hề lỗi. Ca [01]
  canh chỗ này.
- ⚠️ **Loại trùng phải so TẬP TỪ, không so chuỗi tiêu đề.** Feed Google News gom nhiều toà
  soạn, nên cùng một sự kiện về 04-05 bản với 04-05 tiêu đề khác nhau — lượt chạy đầu để lọt
  cả 05 vào lô 10 tin. Ngưỡng giống nhau 0,5 chọn theo số đo, hạ tới 0,35 là nuốt tin thật.
- **Nguồn tải được nhưng 0 mục cũng tính là TRƯỢT** (vào mã thoát). Fail-open ở đây là lối hỏng
  câm: bảng khai đủ nguồn sống trong khi không tin nào về.
- ⛔ **anthropic.com KHÔNG có RSS công khai** — đã dò và chết 04 đường (`/rss.xml`,
  `/news/rss.xml`, `/news.rss`, `/feed.xml` đều 404). Tin Anthropic lấy qua Google News.
  Đừng dò lại.

## Skills dùng chung
Repo có `.claude/skills/` (11 skill từ plugin vibe-pwa-kit) — chủ yếu dành cho app React một-file; trang này đơn giản nên phần lớn skill không áp dụng, nhưng `deploy-static` và `pwa-healthcheck` vẫn hữu ích.
