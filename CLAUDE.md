# Học AI — trang hướng dẫn tiếng Việt cách dùng AI (ChatGPT/Claude/Gemini) và Claude Code

Trang tĩnh 1 file: `index.html` (~4.070 dòng, đo 07/08/2026), HTML + CSS + vanilla JS thuần — **KHÔNG React, KHÔNG build step, KHÔNG backend**. Chỉ là trang nội dung hướng dẫn có tab switcher (`showTab()`). Deploy tĩnh (GitHub Pages qua Actions + Netlify qua `netlify.toml`).

## Quy tắc làm việc với file này
- File nhỏ, chủ yếu là NỘI DUNG (text hướng dẫn) + CSS. Sửa nội dung → sửa trực tiếp trong `index.html`.
- Có `manifest.json` (PWA-lite, installable) nhưng **không có service worker** → không offline. Nếu muốn offline, xem skill `pwa-healthcheck` / `scaffold-vibe-pwa`.
- Không có React/Babel → không lo lỗi transpile. Không có localStorage/dữ liệu người dùng → không cần migration.

## Cấu trúc
- **2 tab chính**: "Kiến thức chung" (`concepts`) và "Tin mới" (`news`), cộng menu xổ "Công cụ AI (25)". Chuyển bằng `showTab(name)`; tab mặc định đọc từ `location.hash`, hash lạ thì rơi về `concepts`.
  - Tab **"Phân tích"** (`analysis`) đã bị **gỡ ngày 07/08/2026** theo yêu cầu của Huy — gỡ trọn 03 chỗ: nút trong `.tabs`, khối `<div id="tab-analysis">`, và khoá `analysis` trong bảng `tabs` của `showTab()`. Thêm/gỡ tab thì phải sờ đủ 03 chỗ này, thiếu chỗ thứ ba thì `showTab` ném lỗi trên `.hidden` của `null`.
- **09 tab con** trong `concepts` (`showSubTab`), sắp theo trình tự học từ dễ tới khó, nhãn nút mang số thứ tự:
  `general` (1 · Bắt đầu dùng AI) · `overview` (2) · `toolsdeep` (3) · `multiai` (4 · Dùng nhiều AI) ·
  `claude` (5) · `skills` (6 · Agent Skills) · `agentic` (7) · `roadmap` (8) · `quiz` (9).
  - ⚠️ Thêm/gỡ tab con phải sờ đủ **03 chỗ**: nút trong `.subtabs`, khối `<div class="subwrap" id="sub-<tên>">`, và khoá trong bảng `subs` của `showSubTab()`. Thiếu chỗ thứ ba thì tab câm — bấm nút không có gì xảy ra, **không lỗi nào phát ra**.
  - **Sắp xếp lại toàn trang 14/08/2026**: tách `skills` khỏi tab `claude` thành tab riêng (Skills nay dùng được cả trên claude.ai và API, không còn là chuyện riêng của Claude Code); thêm tab `multiai`; gộp mục 7 "Mẹo nâng cao" của `general` vào mục 4 và 6 vì trùng với `overview`; đổi lưới 24 thẻ công cụ ở `general` mục 2 thành **một bảng gọn có link** sang trang chi tiết, vì phần mô tả sâu đã nằm ở `toolsdeep`.
- **Tham chiếu chéo giữa các tab viết bằng TÊN TAB, không viết "tab trước"** — thứ tự tab đã đổi một lần và sẽ còn đổi. Đổi tên hay đổi số mục thì `grep` cả file các chuỗi dạng `tab "<tên>", mục N` rồi sửa hết trong cùng lượt; các chuỗi này còn nằm trong `explain` của bộ câu hỏi quiz.
### Quy đổi giá đô la sang tiền Việt (thêm 20/08/2026)
Mọi giá trong trang niêm yết bằng đô la. Khối script cuối `index.html` tự chèn phần quy đổi ngay cạnh
từng con số, chạy trên `#tab-concepts` và `#tab-news`. **Đổi tỷ giá thì sửa đúng hằng `TY_GIA_USD`** —
hai chỗ hiển thị trong ghi chú đầu tab "Chi tiết từng AI" cũng lấy từ chính nó.

Ba cái bẫy đã vấp và đã vá, đừng dựng lại theo lối cũ:
- ⚠️ **Dò dấu vết bằng chuỗi `(~` để chống chạy hai lần là SAI** — bảng giá sẵn có viết `Pro (~$99)`,
  nên phép dò ấy bỏ qua đúng những ô cần quy đổi nhất: 48 trong 50 con số bị sót, trang vẫn hiện bình
  thường và không lỗi nào phát ra. Nay dùng `WeakSet` nhớ nút đã xử lý.
- ⚠️ **Cùng một dấu chấm mang hai nghĩa**: `$1.320` là phân cách nghìn, còn `$0.003` và `$64.99` là số
  lẻ; tin viết lối Việt thì `0,14 USD` cũng là số lẻ. Đọc nhầm chiều nào cũng lệch cả trăm lần. `docSo()`
  phân định bằng hình dạng chuỗi, chỉ coi là phân cách nghìn khi phần đầu khác 0 và mọi nhóm sau đủ 3 chữ số.
- ⚠️ **Nhánh khoảng giá phải đứng TRƯỚC nhánh một số** trong biểu thức: `$100–200` mà để nhánh một số
  khớp trước thì ra `$100 · ~2,6 triệu đ–200`, đúng số nhưng đọc ra nghĩa khác. Đã hiện ở 05 chỗ lúc dựng.

Tab "Tin mới" nạp thêm mục bằng `fetch` nên nội dung tới SAU khi trang tải xong — có `MutationObserver`
canh, chạy một lần rồi thôi là mục do routine bơm vào không bao giờ được quy đổi mà không dấu hiệu nào lộ ra.

Đo sau khi vá, trên Chrome thật ở khổ 375px: 50/50 con số ở tab Kiến thức chung và 6/6 ở tab Tin mới đã
có phần tiền Việt, 0 ngoặc lồng ngoặc, 0 chỗ tràn ngang trên cả 09 tab con.

### Bảng trong thẻ phải cuộn ngang được
`.card:has(> table){overflow-x:auto}` thêm 20/08/2026. Trước đó bảng bản đồ công cụ rộng 430px nằm trong
khung 318px ở khổ điện thoại, chữ bị đẩy ra ngoài mép phải và không có cách nào đọc tiếp. Ép bảng co lại
thì cột mô tả vỡ thành từng chữ một dòng, nên cho thẻ cuộn thay vì cho bảng co.

- **Quiz**: 40 câu, nhãn nhóm trong `QUIZ_TAG_LABEL` phải khớp `tag` của từng câu — thêm nhóm mới mà quên khai nhãn thì bảng điểm cuối bài thiếu dòng đó trong im lặng. Số câu ghi trong `<footer>` của `sub-quiz` là **viết tay**, sửa bộ câu hỏi thì sửa luôn số đó.

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
- **Dòng `news-impact` là bắt buộc** — đây là thứ phân biệt trang này với một trang tổng hợp tin thường. Không có nó thì tin chỉ là chuyện của hãng. Với tin do routine bơm vào, khoá tương ứng là `voi_ban` trong `tin-ai.json`; `dang-tin.py` liệt nó vào `BAT_BUOC` từ 07/08/2026, vì trước đó lời dặn chỉ nằm trong SKILL và phía render để nó có điều kiện — tin thiếu vẫn lên trang mà không lỗi nào phát ra.
- **Nguồn lấy từ trang thứ ba phải ghi chữ "tổng hợp qua"** trước tên nguồn; nguồn chính hãng thì dẫn thẳng. Trang tự khai quy ước này trong khối `.news-note`, nên bỏ chữ đó là làm trang nói sai về chính nó.
- **Mọi `<a>` phải có `target="_blank" rel="noopener"`** và phải đo trả HTTP 200 trước khi ghi vào. Đo song song nhiều luồng hay dính 403/429 giả — link nào hỏng thì **đo lại tuần tự có `sleep`** rồi mới kết luận là chết. Với tin routine, `dang-tin.py` tự đo (tuần tự, nghỉ 0,4 giây, thử lại một lần), và **chỉ 404/410 mới bị coi là chết**: 403/429/5xx là dấu hiệu chặn bot chứ không phải trang đã gỡ, coi chúng là chết thì routine kêu oan gần như mỗi sáng và bảng hết được đọc. Ca [33] canh chiều bắt hụt, ca [34] canh chiều chặn oan.
- Nếu có routine tự bơm tin vào tab này, phần sinh HTML phải theo đúng khuôn trên; cập nhật luôn ngày trong dòng "Cập nhật lần gần nhất" của khối `.news-note`.
- Ngoài danh sách tin, tab còn 02 mục cố định phải giữ đồng bộ khi thêm tin lớn: bảng **"Dòng thời gian model lớn năm 2026"** (`.news-tl`) và lưới **"Tự theo dõi tin AI ở đâu cho chắc"** (`.news-src`).
- **Thêm một công cụ vào menu phải sờ đủ 04 chỗ**: mảng `TOOLS` trong khối script cuối file, khối
  `<div class="tool-page" id="tool-...">` ở `sub-toolsdeep`, một hàng trong bảng bản đồ ở `sub-general`
  mục 2 (kèm sửa `rowspan` của ô nhóm), và **hai con số đếm viết tay**: nhãn nút `Công cụ AI (N)` và câu
  "bản đồ nhanh N công cụ". Thiếu chỗ thứ tư thì trang tự nói sai về chính nó mà không lỗi nào phát ra.
  NotebookLM thêm 20/08/2026 là công cụ thứ 25 — Google đã đổi tên nó thành Gemini Notebook từ 07/2026.
- **Hai mục nội dung thêm 20/08/2026**: `#lua-dao-ai` (tab "Bắt đầu dùng AI" mục 7 — lừa đảo bằng AI,
  bốn kiểu đang gặp, quy tắc gọi lại bằng số tự lưu) và `#luat-ai-vn` (tab "Khái niệm nền tảng" mục 10 —
  Luật Trí tuệ nhân tạo hiệu lực 01/3/2026, nghĩa vụ gắn nhãn nội dung AI, bảng phải/không phải gắn nhãn).
  Hai mục trỏ chéo sang nhau bằng TÊN TAB kèm số mục, nên đổi số mục thì `grep` cả hai chỗ.
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
| `test-quet-tin-ai.py` | 33 ca (22 PHẢI CHẶN) · `--tu-kiem` bắt 18/18 bản hỏng |

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
