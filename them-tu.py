#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Thêm mục từ vào tab «Từ điển thuật ngữ» của app AI Guide (Hoc_AI).

Vì sao có file này: mỗi khi trong câu trả lời xuất hiện một khái niệm kỹ thuật mà Huy
có thể chưa gặp, khái niệm đó phải được ghi vào từ điển ngay lượt đó (quy tắc mục 33
của ~/.claude/CLAUDE.md). Sửa tay `index.html` cho việc lặp đi lặp lại này thì sai
lặng lẽ: thiếu `data-cat` là mục biến khỏi mọi bộ lọc, trùng `id` là liên kết
`#tu-...` nhảy sai chỗ, và không lỗi nào phát ra trên trang.

Dùng:
  python3 them-tu.py --nhom ai --tu "prompt caching" --nghia "nhớ đoạn đầu" \\
      --giai "Trả tiền một lần cho phần đầu câu hỏi rồi dùng lại nhiều lượt sau."

  python3 them-tu.py --co-chua "webhook"      # từ này đã có trong từ điển chưa
  python3 them-tu.py --json <file.json>       # thêm nhiều mục một lượt
  python3 them-tu.py --tu-kiem                # bộ ca test, gồm ca PHẢI CHẶN
"""

import argparse
import html
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unicodedata

GOC = os.path.dirname(os.path.abspath(__file__))
INDEX = os.path.join(GOC, 'index.html')

# Nhóm phải khớp data-gcat của nút lọc VÀ data-gsec của section. Nhóm 'doc' cố ý
# nằm ngoài: nó là một cái bảng dịch câu, không phải danh sách thẻ .term.
NHOM = {
    'git':    'Lưu & giữ mã',
    'mang':   'Đưa lên mạng',
    'auto':   'Chạy tự động',
    'web':    'Bên trong trang',
    'data':   'Dữ liệu',
    'ai':     'AI & chi phí',
    'antoan': 'Bí mật & an toàn',
    'loi':    'Lỗi & cách sửa',
}

# Thẻ được giữ nguyên trong phần giải nghĩa; mọi thứ khác bị vô hiệu hoá thành chữ.
THE_CHO_PHEP = ('b', 'em', 'code')

GIAI_TOI_THIEU = 25   # giải nghĩa ngắn hơn thế này là chưa giải nghĩa


class Chan(Exception):
    """Lỗi có địa chỉ, dừng trước khi ghi bất cứ thứ gì xuống đĩa."""


def nfc(s):
    return unicodedata.normalize('NFC', s or '')


def bo_dau(s):
    s = unicodedata.normalize('NFD', nfc(s))
    s = ''.join(c for c in s if not unicodedata.combining(c))
    return s.replace('đ', 'd').replace('Đ', 'D')


def lam_slug(ten):
    s = bo_dau(ten).lower()
    s = re.sub(r'[^a-z0-9]+', '-', s).strip('-')
    # Slug rỗng nghĩa là tên chỉ gồm ký tự lạ — chặn ở chỗ gọi.
    return s[:40].rstrip('-')


def lam_khoa(*phan):
    """Chuỗi data-k: không dấu, thường, các từ cách nhau một khoảng trắng, không trùng."""
    tho = ' '.join(p for p in phan if p)
    tho = bo_dau(tho).lower()
    tho = re.sub(r'[^a-z0-9]+', ' ', tho)
    da_co, ra = set(), []
    for t in tho.split():
        if t not in da_co:
            da_co.add(t)
            ra.append(t)
    return ' '.join(ra)


def loc_the(s):
    """Escape hết rồi mở lại đúng vài thẻ định dạng. Chuỗi người nhập không bao giờ
    được đi thẳng vào HTML: một dấu `"` lọt vào thuộc tính là vỡ cả thẻ."""
    s = html.escape(nfc(s), quote=False)
    for the in THE_CHO_PHEP:
        s = s.replace('&lt;%s&gt;' % the, '<%s>' % the)
        s = s.replace('&lt;/%s&gt;' % the, '</%s>' % the)
    return s


def gap_dong(s, cot=112, thut=10):
    """Bẻ dòng cho khớp phong cách file, không bẻ giữa một thẻ HTML."""
    tu = s.split()
    dong, hien = [], ''
    for t in tu:
        thu = (hien + ' ' + t).strip()
        if len(thu) > cot - (thut if dong else 8):
            dong.append(hien)
            hien = t
        else:
            hien = thu
    if hien:
        dong.append(hien)
    return ('\n' + ' ' * thut).join(dong)


def doc_index(duong=None):
    duong = duong or INDEX
    if not os.path.exists(duong):
        raise Chan('không thấy file %s' % duong)
    with open(duong, encoding='utf-8') as f:
        return f.read()


def da_co_gi(noi_dung):
    """Trả về (tập slug, tập khoá) đang có, để dò trùng."""
    slug = set(re.findall(r'id="(tu-[a-z0-9-]+)"', noi_dung))
    khoa = set()
    for k in re.findall(r'data-k="([^"]*)"', noi_dung):
        khoa.update(k.split())
    return slug, khoa


def tim_cho_chen(noi_dung, nhom):
    """Vị trí ký tự để chèn: ngay trước thẻ đóng .glosslist của đúng section."""
    mo = re.search(r'<section id="gloss-%s" data-gsec="%s">' % (nhom, nhom), noi_dung)
    if not mo:
        raise Chan('không thấy section gloss-%s trong index.html' % nhom)
    het = noi_dung.find('\n  </section>', mo.end())
    if het < 0:
        raise Chan('section gloss-%s không có thẻ đóng' % nhom)
    khoi = noi_dung[mo.end():het]
    if '<div class="glosslist">' not in khoi:
        raise Chan('section gloss-%s không có khối .glosslist' % nhom)
    # Thẻ đóng của .glosslist là dòng `    </div>` cuối cùng trong khối.
    dong = list(re.finditer(r'\n    </div>', khoi))
    if not dong:
        raise Chan('section gloss-%s không có thẻ đóng .glosslist' % nhom)
    return mo.end() + dong[-1].start()


def dung_khoi(tu, nghia, giai, nhom, slug, khoa):
    dau = '<b>%s</b>' % loc_the(tu)
    if nghia:
        dau += ' <span class="say">%s</span>' % loc_the(nghia)
    than = gap_dong(loc_the(giai))
    return ('\n\n      <div class="term" id="%s" data-cat="%s" data-k="%s">%s\n'
            '        <p>%s</p></div>' % (slug, nhom, khoa, dau, than))


def them_mot(noi_dung, tu, nghia, giai, nhom, khoa_them='', ep=False):
    tu, nghia, giai = nfc(tu).strip(), nfc(nghia).strip(), nfc(giai).strip()
    nhom = (nhom or '').strip().lower()

    if not tu:
        raise Chan('thiếu --tu')
    if nhom not in NHOM:
        raise Chan('nhóm "%s" không có thật; chọn một trong: %s'
                   % (nhom, ', '.join(sorted(NHOM))))
    if len(giai) < GIAI_TOI_THIEU:
        raise Chan('giải nghĩa dài %d ký tự, dưới ngưỡng %d — chưa đủ để người ngoài '
                   'nghề hiểu' % (len(giai), GIAI_TOI_THIEU))
    if '\n' in tu or '\n' in nghia:
        raise Chan('tên từ và nghĩa phải nằm gọn một dòng')

    goc = lam_slug(tu)
    if not goc:
        raise Chan('tên "%s" không sinh ra được slug (toàn ký tự lạ)' % tu)
    slug = 'tu-' + goc

    co_slug, co_khoa = da_co_gi(noi_dung)
    if slug in co_slug and not ep:                    # NEO-TRUNG-SLUG
        raise Chan('«%s» đã có trong từ điển (id=%s). Sửa mục cũ, đừng thêm mục hai.'
                   % (tu, slug))
    if slug in co_slug and ep:
        raise Chan('id %s đã tồn tại; --ep không dùng để tạo id trùng' % slug)

    khoa = lam_khoa(tu, nghia, khoa_them)
    if not khoa:
        raise Chan('không sinh được data-k cho «%s»' % tu)
    if '"' in khoa or '<' in khoa:
        raise Chan('data-k chứa ký tự làm vỡ thuộc tính')

    vi_tri = tim_cho_chen(noi_dung, nhom)
    khoi = dung_khoi(tu, nghia, giai, nhom, slug, khoa)
    moi = noi_dung[:vi_tri] + khoi + noi_dung[vi_tri:]

    # Nghiệm thu ngay trên chuỗi sắp ghi, không tin vào việc chèn đã đúng.
    if moi.count('<div class="term"') != noi_dung.count('<div class="term"') + 1:
        raise Chan('sau khi chèn, số mục từ không tăng đúng 1')
    if len(re.findall(r'id="%s"' % re.escape(slug), moi)) != 1:
        raise Chan('id %s xuất hiện %d lần sau khi chèn'
                   % (slug, len(re.findall(r'id="%s"' % re.escape(slug), moi))))
    if '<script' in khoi.lower():
        raise Chan('khối vừa dựng có thẻ script — nội dung nhập vào chưa được lọc')
    return moi, slug


def ghi(duong, noi_dung):
    tam = duong + '.dangghi'
    with open(tam, 'w', encoding='utf-8') as f:
        f.write(noi_dung)
    os.replace(tam, duong)


def lenh_them(args):
    duong = args.file or INDEX
    noi_dung = doc_index(duong)
    muc = []
    if args.json:
        with open(args.json, encoding='utf-8') as f:
            muc = json.load(f)
        if not isinstance(muc, list):
            raise Chan('file json phải là một danh sách các mục từ')
    else:
        muc = [{'tu': args.tu, 'nghia': args.nghia, 'giai': args.giai,
                'nhom': args.nhom, 'khoa': args.khoa}]

    them = []
    for m in muc:
        noi_dung, slug = them_mot(noi_dung, m.get('tu', ''), m.get('nghia', ''),
                                  m.get('giai', ''), m.get('nhom', ''),
                                  m.get('khoa', ''))
        them.append((m.get('tu'), m.get('nhom'), slug))

    if args.thu:
        print('Thử (chưa ghi):')
        for tu, nhom, slug in them:
            print('  + %-28s nhóm %-6s  #%s' % (tu, nhom, slug))
        return 0

    ghi(duong, noi_dung)
    tong = noi_dung.count('<div class="term"')
    for tu, nhom, slug in them:
        print('Đã thêm «%s» vào nhóm %s (%s) — %s#%s'
              % (tu, nhom, NHOM[nhom], os.path.basename(duong), slug))
    print('Từ điển nay có %d mục từ.' % tong)
    return 0


def lenh_co_chua(args):
    noi_dung = doc_index(args.file or INDEX)
    can = bo_dau(nfc(args.co_chua)).lower().strip()
    slug = 'tu-' + lam_slug(args.co_chua)
    co_slug, co_khoa = da_co_gi(noi_dung)
    if slug in co_slug:
        print('CÓ RỒI: «%s» → #%s' % (args.co_chua, slug))
        return 0
    dinh = [k for k in co_khoa if can and (can in k or k in can)]
    if dinh:
        print('CHƯA CÓ mục riêng, nhưng khoá gần giống đang dùng: %s'
              % ', '.join(sorted(dinh)[:8]))
    else:
        print('CHƯA CÓ: «%s» — nên thêm.' % args.co_chua)
    return 3


# ── Bộ tự kiểm ────────────────────────────────────────────────────────────────

CA = []


def ca(ten, phai_chan=False):
    def bao(f):
        CA.append((ten, phai_chan, f))
        return f
    return bao


@ca('01 thêm một mục hợp lệ')
def _c01(noi_dung):
    moi, slug = them_mot(noi_dung, 'prompt caching', 'nhớ đoạn đầu',
                         'Trả tiền một lần cho phần đầu câu hỏi rồi dùng lại nhiều lượt.',
                         'ai')
    assert slug == 'tu-prompt-caching', slug
    assert 'id="tu-prompt-caching"' in moi
    assert moi.count('<div class="term"') == noi_dung.count('<div class="term"') + 1
    return moi


@ca('02 mục mới nằm đúng trong section của nhóm')
def _c02(noi_dung):
    moi, _ = them_mot(noi_dung, 'zzz thử nhóm', '', 'Mục dựng ra chỉ để đo vị trí chèn.', 'antoan')
    dau = moi.find('<section id="gloss-antoan"')
    cuoi = moi.find('\n  </section>', dau)
    assert dau < moi.find('id="tu-zzz-thu-nhom"') < cuoi, 'chèn lạc section'
    return noi_dung


@ca('03 trùng slug', phai_chan=True)   # PHẢI CHẶN
def _c03(noi_dung):
    them_mot(noi_dung, 'commit', 'đóng dấu', 'Ghi một lần sửa vào sổ lịch sử của mã.', 'git')


@ca('04 nhóm không có thật', phai_chan=True)   # PHẢI CHẶN
def _c04(noi_dung):
    them_mot(noi_dung, 'zzz nhóm lạ', '', 'Giải nghĩa đủ dài để qua ngưỡng ký tự.', 'linhtinh')


@ca('05 nhóm doc là bảng, không nhận thẻ', phai_chan=True)   # PHẢI CHẶN
def _c05(noi_dung):
    them_mot(noi_dung, 'zzz vào bảng', '', 'Giải nghĩa đủ dài để qua ngưỡng ký tự.', 'doc')


@ca('06 giải nghĩa cụt', phai_chan=True)   # PHẢI CHẶN
def _c06(noi_dung):
    them_mot(noi_dung, 'zzz cụt', '', 'Ngắn quá.', 'ai')


@ca('07 thiếu tên từ', phai_chan=True)   # PHẢI CHẶN
def _c07(noi_dung):
    them_mot(noi_dung, '', '', 'Giải nghĩa đủ dài để qua ngưỡng ký tự.', 'ai')


@ca('08 tên toàn ký tự lạ', phai_chan=True)   # PHẢI CHẶN
def _c08(noi_dung):
    them_mot(noi_dung, '★ ☆ ★', '', 'Giải nghĩa đủ dài để qua ngưỡng ký tự.', 'ai')


@ca('09 nội dung nhập vào bị lọc thẻ')
def _c09(noi_dung):
    moi, slug = them_mot(noi_dung, 'zzz lọc thẻ', 'thử "dấu nháy"',
                         'Có <script>alert(1)</script> và <b>đậm</b> lẫn dấu " trong câu này.',
                         'loi')
    # Cắt từ chính chỗ id trở đi. Lùi lại vài chục ký tự để lấy cả thẻ mở thì đoạn cắt
    # ăn luôn thẻ đóng </div> của mục đứng trước, và mọi phép kiểm sau đó soi vào chỗ trống.
    khoi = moi[moi.find('id="%s"' % slug):]
    khoi = khoi[:khoi.find('</div>')]
    assert '<script' not in khoi.lower(), 'thẻ script lọt vào trang'
    assert '<b>đậm</b>' in khoi, 'thẻ định dạng cho phép bị nuốt mất'
    assert khoi.count('data-k="') == 1 and '&quot;' not in khoi.split('data-k="')[1].split('"')[0]
    return noi_dung


@ca('10 mục mới có đủ data-cat và data-k')
def _c10(noi_dung):
    moi, slug = them_mot(noi_dung, 'zzz đủ thuộc tính', 'kiểm lọc',
                         'Thiếu data-cat thì mục biến khỏi mọi bộ lọc mà không lỗi nào phát ra.',
                         'web')
    d = moi[moi.find('id="%s"' % slug):]
    d = d[:d.find('>')]
    assert 'data-cat="web"' in d, d
    assert re.search(r'data-k="[a-z0-9 ]+"', d), d
    return noi_dung


@ca('11 gõ không dấu vẫn tra được')
def _c11(noi_dung):
    moi, slug = them_mot(noi_dung, 'phiên bản thử', 'bản đánh số',
                         'Mỗi lần xuất bản lại thì đánh một số mới để phân biệt với bản cũ.', 'git')
    d = moi[moi.find('id="%s"' % slug):]
    khoa = d.split('data-k="')[1].split('"')[0]
    assert 'phien ban thu' in khoa, khoa
    assert khoa == khoa.lower() and '  ' not in khoa
    return noi_dung


@ca('12 file đích không tồn tại', phai_chan=True)   # PHẢI CHẶN
def _c12(noi_dung):
    doc_index(os.path.join(GOC, 'khong-he-co-file-nay.html'))


def chay_tu_kiem(im=False):
    goc = doc_index()
    dat = truot = 0
    for ten, phai_chan, f in CA:
        try:
            f(goc)
            if phai_chan:
                print('  ✗ %s — LỌT: đáng lẽ phải bị chặn' % ten)
                truot += 1
            else:
                if not im:
                    print('  ✓ %s' % ten)
                dat += 1
        except Chan as e:
            if phai_chan:
                if not im:
                    print('  ✓ %s — chặn đúng: %s' % (ten, e))
                dat += 1
            else:
                print('  ✗ %s — chặn oan: %s' % (ten, e))
                truot += 1
        except AssertionError as e:
            print('  ✗ %s — sai kết quả: %s' % (ten, e))
            truot += 1
    print('%d/%d ca đạt.' % (dat, dat + truot))
    return 0 if truot == 0 else 1


def chay_ban_hong():
    """Gỡ đúng dòng vá rồi chạy lại — ca PHẢI CHẶN tương ứng phải lọt.
    Ca test chỉ có ý nghĩa khi đã chứng minh nó bắt được lỗi thật."""
    with open(os.path.abspath(__file__), encoding='utf-8') as f:
        goc = f.read()
    hong = [
        ('trùng slug (gỡ NEO-TRUNG-SLUG)',
         re.sub(r'\n +if slug in co_slug and not ep:.*?\n(?: +.*\n)+?(?= +if slug in co_slug and ep:)',
                '\n', goc)),
        ('nhóm lạ (bỏ phép kiểm NHOM)',
         goc.replace('if nhom not in NHOM:', 'if False:')),
        ('giải nghĩa cụt (bỏ ngưỡng)',
         goc.replace('if len(giai) < GIAI_TOI_THIEU:', 'if False:')),
    ]
    thu = tempfile.mkdtemp(prefix='hocai-hong-')
    truot = 0
    try:
        for ten, ma in hong:
            if ma == goc:
                print('  ✗ bản hỏng «%s» không khác bản gốc — phép gỡ đã lệch' % ten)
                truot += 1
                continue
            duong = os.path.join(thu, 'hong.py')
            with open(duong, 'w', encoding='utf-8') as f:
                f.write(ma)
            r = subprocess.run([sys.executable, duong, '--tu-kiem', '--im'],
                               capture_output=True, text=True, cwd=GOC)
            if r.returncode == 0:
                print('  ✗ bản hỏng «%s» vẫn báo đạt — bộ ca không bắt được lỗi này' % ten)
                truot += 1
            else:
                print('  ✓ bản hỏng «%s» bị bắt' % ten)
    finally:
        shutil.rmtree(thu, ignore_errors=True)
    print('%d/%d bản hỏng đều bị bắt.' % (len(hong) - truot, len(hong)))
    return 0 if truot == 0 else 1


def main():
    p = argparse.ArgumentParser(description='Thêm mục từ vào từ điển app AI Guide')
    p.add_argument('--tu', help='chữ cần giải nghĩa, viết đúng như lúc nói')
    p.add_argument('--nghia', default='', help='nghĩa Việt ngắn, hiện mờ bên cạnh')
    p.add_argument('--giai', default='', help='giải nghĩa bằng chuyện đời thường')
    p.add_argument('--nhom', help='một trong: ' + ', '.join(sorted(NHOM)))
    p.add_argument('--khoa', default='', help='thêm từ khoá tra cứu, cách nhau khoảng trắng')
    p.add_argument('--json', help='file json chứa danh sách nhiều mục từ')
    p.add_argument('--co-chua', help='kiểm một chữ đã có trong từ điển chưa')
    p.add_argument('--thu', action='store_true', help='xem trước, không ghi')
    p.add_argument('--file', help='ghi vào file khác index.html (dùng khi test)')
    p.add_argument('--tu-kiem', action='store_true', help='chạy bộ ca test')
    p.add_argument('--ban-hong', action='store_true', help='dựng bản hỏng, chứng minh ca bắt được lỗi')
    p.add_argument('--im', action='store_true', help='chỉ in ca trượt')
    a = p.parse_args()

    try:
        if a.ban_hong:
            return chay_ban_hong()
        if a.tu_kiem:
            return chay_tu_kiem(im=a.im)
        if a.co_chua:
            return lenh_co_chua(a)
        if not (a.json or (a.tu and a.nhom)):
            p.print_help()
            return 2
        return lenh_them(a)
    except Chan as e:
        print('CHẶN: %s' % e, file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
