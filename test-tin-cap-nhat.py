#!/usr/bin/env python3
"""Ca test cho dòng "Cập nhật lần gần nhất" ở khối .news-note trong index.html.

Trước 22/08/2026 dòng này là chữ viết tay, đứng im từ 07/08 dù routine vẫn thêm tin
mỗi sáng — trang tự nói sai về chính nó mà không lỗi nào phát ra. Nay dòng này đọc
`tin-ai.json.cap_nhat` bằng JS lúc trang tải. Ca dưới đây kiểm tra đúng 02 chỗ bắt
buộc phải còn nguyên: cái neo `id="tin-cap-nhat"` trong HTML, và đoạn JS gán lại
`textContent` của nó từ `d.cap_nhat`. Thiếu MỘT trong hai là dòng chữ lại đứng im.

Chạy: python3 test-tin-cap-nhat.py
Tự kiểm: python3 test-tin-cap-nhat.py --tu-kiem
"""
import re
import sys
from pathlib import Path

APP = Path(__file__).resolve().parent
INDEX = APP / "index.html"


def doc(duong=None):
    return (duong or INDEX).read_text(encoding="utf-8")


def ca_neo_html(noi_dung):
    """[01] Neo id="tin-cap-nhat" phải còn trong khối .news-note."""
    return bool(re.search(r'<b id="tin-cap-nhat">[^<]*</b>', noi_dung))


def ca_js_gan_lai(noi_dung):
    """[02] Script fetch phải gán lại textContent của neo đó từ d.cap_nhat."""
    m = re.search(r"getElementById\('tin-cap-nhat'\)", noi_dung)
    if not m:
        return False
    doan = noi_dung[m.start():m.start() + 400]
    return "capNhatEl.textContent" in doan and "d.cap_nhat" in doan


CA = [
    ("[01] neo html còn", ca_neo_html),
    ("[02] js gán lại ngày", ca_js_gan_lai),
]


def chay(duong=None):
    noi_dung = doc(duong)
    ket = []
    for ten, ham in CA:
        ok = ham(noi_dung)
        ket.append((ten, ok))
        print(("✓ " if ok else "✗ ") + ten)
    return ket


def tu_kiem():
    """Dựng bản HỎNG (gỡ đúng dòng vá) rồi chạy lại — ca PHẢI CHẶN phải báo ✗."""
    noi_dung = doc()
    hong = noi_dung.replace(
        'capNhatEl.textContent = p[2] + \'/\' + p[1] + \'/\' + p[0];',
        '/* hỏng: bỏ dòng gán lại ngày */',
    )
    if hong == noi_dung:
        print("KHÔNG dựng được bản hỏng — chuỗi cần thay đã đổi, sửa lại test này")
        return 1

    import tempfile
    with tempfile.NamedTemporaryFile("w", suffix=".html", delete=False, encoding="utf-8") as f:
        f.write(hong)
        duong_hong = Path(f.name)

    try:
        ket = chay(duong_hong)
        loi = dict(ket)
        if loi["[02] js gán lại ngày"]:
            print("TRƯỢT: bản hỏng vẫn báo ✓ ở ca [02] — ca không bắt được lỗi")
            return 1
        print("ĐẠT: bản hỏng bị ca [02] bắt đúng")
        return 0
    finally:
        duong_hong.unlink(missing_ok=True)


if __name__ == "__main__":
    if "--tu-kiem" in sys.argv:
        sys.exit(tu_kiem())
    ket = chay()
    sys.exit(0 if all(ok for _, ok in ket) else 1)
