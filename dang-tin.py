#!/usr/bin/env python3
"""Kiểm khuôn `tin-ai.json` rồi đưa lên trang — cổng duy nhất cho routine đăng tin AI.

VÌ SAO PHẢI LÀ SCRIPT, KHÔNG ĐỂ PHIÊN TỰ GÕ `git`: SKILL của routine 06:30 cấm thẳng
`git add/commit/push`, và rào nằm trong prompt là VĂN BẢN — một lượt viết lệch là phiên tự
đẩy thứ khác lên repo công khai. Chuyển việc đó vào script thì rào thành mã: script chỉ chạm
đúng MỘT file, và từ chối chạy khi cây làm việc có thay đổi nào khác.

⛔ KHÔNG dùng `git add`. Repo này có nhiều phiên cùng mở (mục 9b CLAUDE.md): index của git là
tài nguyên dùng chung, `add` của phiên A sẽ bị commit của phiên B cuốn theo. `git commit <path>`
không đụng index.

Mã thoát:
    0  đăng xong, hoặc không có gì mới để đăng (im lặng là hợp lệ ở đây)
    2  JSON sai khuôn / thiếu file / repo lạ  ⇒ KÊU, đừng đăng
    3  cây làm việc có thay đổi NGOÀI tin-ai.json ⇒ dừng, việc của phiên khác

Dùng:
    dang-tin.py              # kiểm rồi commit + push
    dang-tin.py --chi-kiem   # chỉ kiểm khuôn, không đụng git
"""
import argparse
import json
import os
import re
import subprocess
import sys

RA = os.path.dirname(os.path.abspath(__file__))
TIN = os.path.join(RA, 'tin-ai.json')
TEN_FILE = 'tin-ai.json'
# Nhãn phải khớp bảng `NHAN` trong khối script cuối `index.html`. Lệch một chữ thì mục vẫn
# lên trang nhưng rơi hết về nhãn "Model mới" và bộ lọc chủ đề không tìm ra nó.
NHAN_HOP_LE = {'model', 'gia', 'agent', 'antoan', 'luat', 'hatang', 'sangtao', 'vn'}
# Trần số mục giữ trong file. Tin AI cũ hơn chừng này thì phần viết tay bên dưới đã kể rồi.
TRAN_MUC = 12
BAT_BUOC = ('ngay', 'cat', 'tieu_de', 'noi_dung')


def kiem(d):
    """Trả danh sách lỗi. Rỗng nghĩa là khuôn đúng."""
    loi = []
    if not isinstance(d, dict):
        return ['tin-ai.json không phải object']
    muc = d.get('muc')
    if not isinstance(muc, list):
        return ['thiếu mảng "muc"']
    for i, m in enumerate(muc):
        ten = 'mục %d' % (i + 1)
        if not isinstance(m, dict):
            loi.append('%s không phải object' % ten)
            continue
        for k in BAT_BUOC:
            if not (m.get(k) or '').strip() if isinstance(m.get(k), str) else not m.get(k):
                loi.append('%s thiếu "%s"' % (ten, k))
        if m.get('cat') not in NHAN_HOP_LE:
            loi.append('%s có nhãn lạ %r (hợp lệ: %s)'
                       % (ten, m.get('cat'), ', '.join(sorted(NHAN_HOP_LE))))
        if not re.match(r'^\d{2}/\d{2}/\d{4}$', str(m.get('ngay') or '')):
            loi.append('%s có ngày sai khuôn dd/mm/yyyy: %r' % (ten, m.get('ngay')))
        for n in (m.get('nguon') or []):
            if not isinstance(n, dict) or not str(n.get('url') or '').startswith('http'):
                loi.append('%s có nguồn thiếu địa chỉ hợp lệ' % ten)
    return loi


def cat_bot(d):
    """Giữ TRAN_MUC mục đầu. Trả True nếu có cắt."""
    muc = d.get('muc') or []
    if len(muc) <= TRAN_MUC:
        return False
    d['muc'] = muc[:TRAN_MUC]
    return True


def git(*args):
    r = subprocess.run(['git', '-C', RA] + list(args), capture_output=True, text=True)
    return r.returncode, (r.stdout or '') + (r.stderr or '')


def dang(chi_kiem=False):
    if not os.path.exists(TIN):
        print('KHÔNG có %s' % TIN, file=sys.stderr)
        return 2
    try:
        with open(TIN, encoding='utf-8') as f:
            d = json.load(f)
    except Exception as e:
        print('tin-ai.json hỏng: %r' % e, file=sys.stderr)
        return 2
    loi = kiem(d)
    if loi:
        for x in loi:
            print('  ✗ %s' % x, file=sys.stderr)
        return 2
    if cat_bot(d):
        with open(TIN, 'w', encoding='utf-8') as f:
            json.dump(d, f, ensure_ascii=False, indent=1)
            f.write('\n')
        print('đã cắt còn %d mục' % TRAN_MUC)
    print('khuôn đạt · %d mục' % len(d.get('muc') or []))
    if chi_kiem:
        return 0

    ma, ra = git('status', '--porcelain')
    # ⚠ Phải đọc CẢ mã thoát. `git status` lỗi tạm cũng trả stdout rỗng, mà rỗng đúng là tín
    # hiệu "cây sạch" ⇒ fail-open, script sẽ commit trong khi không biết cây đang có gì
    # (mục 9b CLAUDE.md).
    if ma != 0:
        print('không đọc được trạng thái git: %s' % ra.strip(), file=sys.stderr)
        return 2
    ban = [d for d in ra.splitlines() if d.strip()]
    la = [d for d in ban if d[3:].strip().strip('"') != TEN_FILE]
    if la:
        print('cây làm việc còn thay đổi KHÁC — dừng, đó là việc của phiên khác:',
              file=sys.stderr)
        for d in la:
            print('  %s' % d, file=sys.stderr)
        return 3
    if not ban:
        print('tin-ai.json không đổi — không có gì để đăng')
        return 0

    ma, ra = git('commit', TEN_FILE, '-m', 'chore: cap nhat tin AI cho tab Tin moi')
    if ma != 0:
        print('commit trượt: %s' % ra.strip(), file=sys.stderr)
        return 2
    ma, ra = git('push')
    if ma != 0:
        print('push trượt: %s' % ra.strip(), file=sys.stderr)
        return 2
    print('đã đăng — trang sẽ tự dựng lại qua GitHub Pages')
    return 0


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--chi-kiem', action='store_true')
    a = p.parse_args()
    sys.exit(dang(chi_kiem=a.chi_kiem))
