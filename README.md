# Hướng dẫn sử dụng AI

Trang tĩnh tiếng Việt (`index.html`, tự chứa — HTML/CSS/JS thuần, không cần build), gồm 2 tab:

- **Hướng dẫn chung**: cẩm nang cho người mới dùng ChatGPT/Claude/Gemini — khái niệm, cách viết prompt, ví dụ theo tình huống, lưu ý & mẹo.
- **Claude & Claude Code**: phân biệt Claude (chatbot) và Claude Code (CLI), cài đặt/dùng Claude Code, hướng dẫn Agent Skills từng bước cho người mới, và bảng tóm tắt các khóa học chính thức trên Anthropic Academy.

## Chạy thử trên máy

Mở trực tiếp `index.html` bằng trình duyệt, không cần server.

## Đăng lên mạng

Repo đã có sẵn:
- **GitHub Pages**: tự deploy khi push lên `main` (xem `.github/workflows/deploy-pages.yml`). Bật tại Settings → Pages → Source: GitHub Actions.
- **Netlify**: `netlify.toml` đã cấu hình publish thư mục gốc, không cần build command — chỉ cần Import repo này trên Netlify.
