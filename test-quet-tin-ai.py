#!/usr/bin/env python3
"""Bộ test cho `quet-tin-ai.py` — bộ quét tin AI của trang Học AI.

Chạy:
    python3 /Users/Huy/Claude/App/Hoc_AI/test-quet-tin-ai.py
    python3 /Users/Huy/Claude/App/Hoc_AI/test-quet-tin-ai.py --tu-kiem

`--tu-kiem` dựng các bản mã HỎNG (gỡ đúng dòng vá) rồi chạy lại bộ ca; ca khai trong
`BAN_HONG` phải chuyển sang ĐỎ, không thì phép kiểm này không có răng (mục 17 CLAUDE.md).

⚠ MỌI CA GỌI THẲNG HÀM TRONG TIẾN TRÌNH, không `subprocess` — subprocess luôn nạp bản THẬT
trên đĩa nên ca xanh trên cả bản đúng lẫn bản hỏng, tức `--tu-kiem` không đụng tới được.

⚠ KHÔNG ca nào chạm mạng. Mọi dữ liệu là XML dựng tay, để kết quả tất định — một bộ test
đọc feed thật thì hôm nay xanh mai đỏ theo tin tức, và bảng kêu oan vài lần là hết được đọc.
"""
import argparse
import importlib.util
import io
import os
import sys
import tempfile
from contextlib import redirect_stdout
from datetime import datetime, timedelta, timezone

RA = os.path.dirname(os.path.abspath(__file__))
THAT = os.path.join(RA, 'quet-tin-ai.py')


def nap(duong_dan):
    spec = importlib.util.spec_from_file_location('qta_' + str(abs(hash(duong_dan))), duong_dan)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def _rss(muc):
    """Dựng một feed RSS 2.0 từ danh sách (tiêu đề, mô tả, giờ-trước)."""
    it = []
    for td, mt, gio in muc:
        d = (datetime.now(timezone.utc) - timedelta(hours=gio)).strftime(
            '%a, %d %b %Y %H:%M:%S +0000')
        it.append('<item><title>%s</title><link>https://vd.test/%s</link>'
                  '<description>%s</description><pubDate>%s</pubDate></item>'
                  % (td, abs(hash(td)), mt, d))
    return ('<?xml version="1.0"?><rss version="2.0"><channel><title>Feed</title>%s'
            '</channel></rss>' % ''.join(it)).encode('utf-8')


def _atom(muc):
    it = []
    for td, mt, gio in muc:
        d = (datetime.now(timezone.utc) - timedelta(hours=gio)).isoformat()
        it.append('<entry><title>%s</title><link rel="alternate" href="https://vd.test/a%s"/>'
                  '<summary>%s</summary><published>%s</published></entry>'
                  % (td, abs(hash(td)), mt, d))
    return ('<?xml version="1.0"?><feed xmlns="http://www.w3.org/2005/Atom">'
            '<title>Feed</title>%s</feed>' % ''.join(it)).encode('utf-8')


def chay_bo_ca(m, duong_dang=None):
    """Trả danh sách (mã ca, mô tả, đạt-hay-không).

    `duong_dang` cho phép `--tu-kiem` trỏ phần ca [20]-[30] vào một BẢN HỎNG của
    `dang-tin.py`; để trống thì dùng bản thật trên đĩa.
    """
    ra = []

    def ca(ma, mo_ta, dat):
        ra.append((ma, mo_ta, bool(dat)))

    # ── [01] PHẢI CHẶN — feed RSS phải bóc ra được tiêu đề.
    # Đây là ca canh lỗi đã vấp thật lúc dựng 07/08/2026: `el.find('title') or el.find(...)`
    # trả None vì Element không con là falsy, làm 12/14 nguồn ra 0 tin mà không lỗi nào phát.
    tin, loi = _doc(m, _rss([('Claude Code ra bản mới', 'anthropic release', 2)]))
    ca('01', 'RSS bóc được tiêu đề (lỗi Element-falsy)',
       loi is None and len(tin) == 1 and tin[0]['tieu_de'] == 'Claude Code ra bản mới')

    # ── [02] ĐỐI CHỨNG — Atom cũng phải bóc được, để [01] đỏ thì biết hỏng ở đâu.
    tin, loi = _doc(m, _atom([('OpenAI launches new model', 'gpt release', 1)]))
    ca('02', 'Atom bóc được tiêu đề', loi is None and len(tin) == 1)

    # ── [03] PHẢI CHẶN — nguồn tải được nhưng 0 mục vẫn phải tính là TRƯỢT.
    # Fail-open ở đây là lối hỏng câm: bảng khai đủ nguồn sống trong khi không tin nào về.
    ma, lo, thong = _quet(m, {'A': _rss([]), 'B': _rss([]), 'C': _rss([])})
    ca('03', '0 mục cũng đếm là nguồn trượt ⇒ mã thoát 1', ma == 1)

    # ── [04] ĐỐI CHỨNG — mọi nguồn có tin thì mã thoát 0.
    ma, lo, thong = _quet(m, {'A': _rss([('Claude adds new feature', 'launch', 1)]),
                              'B': _rss([('Gemini pricing drops', 'price cut', 2)]),
                              'C': _rss([('ChatGPT free tier expands', 'now available', 3)])})
    ca('04', 'nguồn đều sống ⇒ mã thoát 0', ma == 0)

    # ── [05] PHẢI CHẶN — 05 bản của cùng một sự kiện chỉ được lấy MỘT.
    # Lối hỏng đo thật lượt chạy đầu: so chuỗi tiêu đề để lọt cả 05 bản vào lô 10 tin.
    cung_tin = [
        ('Meta is launching its first AI coding agent to rival Anthropic and OpenAI - qz', 'x', 1),
        ('Meta Launches AI Coding Agent to Challenge OpenAI and Anthropic - devops', 'x', 2),
        ('Meta Releases Coding Agent to Compete With OpenAI and Anthropic - WSJ', 'x', 2),
        ('Meta debuts first AI coding agent to take on Anthropic and OpenAI - CNBC', 'x', 3),
    ]
    ma, lo, thong = _quet(m, {'A': _rss(cung_tin)})
    ca('05', '04 bản cùng một tin ⇒ lô giữ đúng 01', len(lo) == 1)

    # ── [06] ĐỐI CHỨNG chống NỚI TAY — hai tin KHÁC nhau không được gộp làm một.
    khac = [('ChatGPT brings unlimited text chats to free users', 'x', 1),
            ('Anthropic will design its own hardware to power Claude', 'x', 2)]
    ma, lo, thong = _quet(m, {'A': _rss(khac)})
    ca('06', '02 tin khác nhau ⇒ giữ đủ 02', len(lo) == 2)

    # ── [07] PHẢI CHẶN — một nguồn không được chiếm quá trần của nó.
    nhieu = [('Claude model A launches with new API', 'x', 1),
             ('Gemini feature B now available for free', 'x', 1),
             ('GPT tool C ships to developers today', 'x', 1),
             ('Llama update D introduces agent skills', 'x', 1)]
    ma, lo, thong = _quet(m, {'A': _rss(nhieu)})
    ca('07', 'trần mỗi nguồn = 2 ⇒ lô không quá 02 tin từ một feed', len(lo) <= 2)

    # ── [08] PHẢI CHẶN — sổ đã-đọc phải chặn tin đã đưa lượt trước.
    with tempfile.TemporaryDirectory() as tmp:
        m.THU_MUC_QUET = tmp
        m.SO = os.path.join(tmp, 'so.jsonl')
        m.ghi_so([{'url': 'https://vd.test/da-co'}])
        cu = m.doc_so()
    ca('08', 'sổ đã-đọc ghi rồi đọc lại được', 'https://vd.test/da-co' in cu)

    # ── [09] PHẢI CHẶN — tin ngoài cửa sổ thời gian phải bị loại.
    ma, lo, thong = _quet(m, {'A': _rss([('Old news about Claude launch', 'x', 500)])})
    ca('09', 'tin cũ hơn cửa sổ ⇒ không vào lô', len(lo) == 0)

    # ── [10] PHẢI CHẶN — tin gọi vốn/kiện tụng bị loại khỏi trang dạy dùng AI.
    rac = [('Startup raises $50M in Series B funding for AI', 'x', 1),
           ('Lawsuit against OpenAI over training data', 'x', 1)]
    ma, lo, thong = _quet(m, {'A': _rss(rac)})
    ca('10', 'tin gọi vốn và kiện tụng bị loại', len(lo) == 0)

    # ── [11] ĐỐI CHỨNG chống nới tay — tin giá/tính năng KHÔNG được loại nhầm.
    ma, lo, thong = _quet(m, {'A': _rss([('Anthropic cuts API pricing for Claude', 'x', 1)])})
    ca('11', 'tin hạ giá API vẫn qua được cổng loại', len(lo) == 1)

    # ── [12] PHẢI CHẶN — `chuan()` phải trả chuỗi NFC.
    # ⚠ Bản ca đầu đo `tap_tu(nfc) == tap_tu(nfd)` và VẪN XANH trên bản hỏng: `tap_tu` gọi
    # `bo_dau`, mà bỏ dấu thì NFD hay NFC ra như nhau — ca dựng ở nhánh phép thay không đi
    # qua (mục 17, nguyên nhân (b)). Phải đo thẳng chuỗi `chuan` trả về, vì đó mới là chỗ
    # NFC quyết định kết quả: tiêu đề NFD ghi vào tab tin sẽ hiển thị lệch dấu trên trình
    # duyệt và không khớp khi đối chiếu với bản đã đăng.
    import unicodedata
    nfc = 'Trí tuệ nhân tạo ra mắt tính năng mới'
    nfd = unicodedata.normalize('NFD', nfc)
    ca('12', 'chuan() trả chuỗi NFC dù nguồn về dạng NFD', m.chuan(nfd) == nfc)

    # ── [12b] PHẢI CHẶN — khoảng trắng lạ bị gộp. Nguồn Việt hay mang U+00A0/U+202F, hai
    # chuỗi nhìn y hệt nhau mà khác byte thì mọi phép so khớp im lặng trượt.
    ca('12b', 'gộp khoảng trắng lạ (U+00A0, U+202F, U+2060)',
       m.chuan('Claude ra mắt⁠ tính năng') == 'Claude ra mắt tính năng')

    # ── [13] PHẢI CHẶN — bảng nguồn mất thì KÊU bằng mã 2, không trả lô rỗng êm.
    cu_nguon = m.NGUON
    m.NGUON = os.path.join(RA, 'khong-he-ton-tai.json')
    with redirect_stdout(io.StringIO()):
        ma, lo = m.quet(ghi=False)
    m.NGUON = cu_nguon
    ca('13', 'mất bảng nguồn ⇒ mã thoát 2', ma == 2)

    # ── [14] ĐỐI CHỨNG — đuôi toà soạn của Google News bị bóc khỏi tiêu đề khi so.
    ca('14', 'bóc đuôi " - Toà soạn" trước khi so',
       m.tap_tu('Claude adds skills - TechCrunch') == m.tap_tu('Claude adds skills'))

    ra.extend(ca_dang_tin(duong_dang))
    return ra


def _muc(**doi):
    goc = {'ngay': '07/08/2026', 'cat': 'model', 'tieu_de': 'Có tin', 'noi_dung': 'Nội dung',
           'voi_ban': 'Bạn dùng được ngay hôm nay.',
           'nguon': [{'ten': 'X', 'url': 'https://vd.test/a'}]}
    goc.update(doi)
    return goc


def ca_dang_tin(duong_dan=None):
    """Bộ ca cho `dang-tin.py` — cổng đăng tin lên trang.

    Cổng này là chỗ DUY NHẤT routine được chạm vào git, nên mọi nhánh từ chối của nó phải có
    ca canh: khuôn sai, nhãn lạ, và quan trọng nhất là cây làm việc còn thay đổi của phiên khác.
    """
    d = nap(duong_dan or os.path.join(RA, 'dang-tin.py'))
    # Bước đo địa chỉ nguồn là bước DUY NHẤT của cổng này chạm mạng. Tiêm nó ngay từ đây để
    # mọi ca gọi `dang()` giữ được tính tất định; ca nào cần đo hành vi của chính bước đó thì
    # tự thay `d.ma_http` bằng bản giả riêng bên dưới.
    d.ma_http = lambda url, timeout=12: (200, '')
    d.NGHI_GIUA_LINK = 0
    ra = []

    def ca(ma, mo_ta, dat):
        ra.append((ma, mo_ta, bool(dat)))

    def dang_voi(ma_gia, muc=None, **kw):
        """Chạy `dang()` trên một `tin-ai.json` dựng tay, với `ma_http` và git giả.

        ⚠ Phải trỏ `d.TIN` sang file tạm, KHÔNG để ca đọc `tin-ai.json` thật trên đĩa: nội
        dung file đó đổi mỗi sáng theo tin tức, nên ca nào dựa vào nó thì hôm nay xanh mai đỏ
        mà chẳng ai sửa gì.

        Trả (mã thoát, danh sách lệnh git đã gọi, số lần đo link).
        """
        import json as _json
        dem = []

        def gia(url, timeout=12):
            dem.append(url)
            return ma_gia

        lenh = []

        def git_sach(*args):
            lenh.append(args)
            if args[:2] == ('status', '--porcelain'):
                return 0, ' M tin-ai.json\n'
            return 0, ''

        cu_ma, cu_git, cu_tin = d.ma_http, d.git, d.TIN
        tmp = tempfile.mkdtemp()
        duong = os.path.join(tmp, 'tin-ai.json')
        with open(duong, 'w', encoding='utf-8') as f:
            _json.dump({'muc': muc if muc is not None else [_muc()]}, f, ensure_ascii=False)
        d.ma_http, d.git, d.TIN = gia, git_sach, duong
        try:
            with redirect_stdout(io.StringIO()):
                ma = d.dang(**kw)
        finally:
            d.ma_http, d.git, d.TIN = cu_ma, cu_git, cu_tin
        return ma, [a[0] for a in lenh], len(dem)

    ca('20', 'khuôn đúng ⇒ không lỗi (đối chứng)', d.kiem({'muc': [_muc()]}) == [])
    ca('21', 'nhãn cat lạ bị chặn', d.kiem({'muc': [_muc(cat='linh-tinh')]}) != [])
    ca('22', 'ngày sai khuôn bị chặn', d.kiem({'muc': [_muc(ngay='7/8/26')]}) != [])
    ca('23', 'nguồn thiếu địa chỉ bị chặn',
       d.kiem({'muc': [_muc(nguon=[{'ten': 'X'}])]}) != [])
    ca('24', 'thiếu tiêu đề bị chặn', d.kiem({'muc': [_muc(tieu_de='')]}) != [])
    ca('25', 'thiếu mảng muc bị chặn', d.kiem({'cap_nhat': '2026-08-07'}) != [])

    goi = {'muc': [_muc(tieu_de='t%d' % i) for i in range(d.TRAN_MUC + 5)]}
    ca('26', 'quá trần thì cắt bớt', d.cat_bot(goi) and len(goi['muc']) == d.TRAN_MUC)
    ca('27', 'dưới trần thì giữ nguyên (đối chứng)', d.cat_bot({'muc': [_muc()]}) is False)

    # ── [28] PHẢI CHẶN — cây làm việc còn thay đổi của phiên khác ⇒ mã 3, KHÔNG commit.
    goi_git = []

    def git_gia_co_file_la(*args):
        goi_git.append(args)
        if args[:2] == ('status', '--porcelain'):
            return 0, ' M index.html\n M tin-ai.json\n'
        return 0, ''

    cu = d.git
    d.git = git_gia_co_file_la
    try:
        with redirect_stdout(io.StringIO()):
            ma = d.dang()
    finally:
        d.git = cu
    ca('28', 'có thay đổi lạ ⇒ mã 3 và KHÔNG commit',
       ma == 3 and not any(a and a[0] == 'commit' for a in goi_git))

    # ── [29] PHẢI CHẶN — `git status` lỗi thì KÊU, không coi đầu ra rỗng là "cây sạch".
    def git_gia_loi(*args):
        if args[:2] == ('status', '--porcelain'):
            return 128, ''
        return 0, ''

    d.git = git_gia_loi
    try:
        with redirect_stdout(io.StringIO()):
            ma = d.dang()
    finally:
        d.git = cu
    ca('29', 'git status lỗi ⇒ mã 2 (không fail-open)', ma == 2)

    # ── [30] ĐỐI CHỨNG — chỉ mình tin-ai.json đổi ⇒ commit rồi push, đúng pathspec.
    goi2 = []

    def git_gia_sach(*args):
        goi2.append(args)
        if args[:2] == ('status', '--porcelain'):
            return 0, ' M tin-ai.json\n'
        return 0, ''

    d.git = git_gia_sach
    try:
        with redirect_stdout(io.StringIO()):
            ma = d.dang()
    finally:
        d.git = cu
    lenh = [a[0] for a in goi2]
    ca('30', 'chỉ tin-ai.json đổi ⇒ commit + push, KHÔNG dùng git add',
       ma == 0 and 'commit' in lenh and 'push' in lenh and 'add' not in lenh
       and any(a[0] == 'commit' and 'tin-ai.json' in a for a in goi2))

    # ── [31] PHẢI CHẶN — mục thiếu dòng "👉 Với bạn" không được lên trang.
    # `CLAUDE.md` của repo khai dòng này là BẮT BUỘC, SKILL routine 06:30 cũng dặn viết nó,
    # nhưng cả hai đều là văn bản. Phía render để nó có điều kiện nên tin thiếu vẫn hiện đủ
    # tiêu đề và nguồn — không lỗi nào phát ra, chỉ mất đúng phần người đọc cần.
    ca('31', 'thiếu "voi_ban" bị chặn', d.kiem({'muc': [_muc(voi_ban='')]}) != [])

    # ── [32] ĐỐI CHỨNG chống nới tay — có "voi_ban" thì không được chặn nhầm.
    ca('32', 'có "voi_ban" vẫn qua khuôn', d.kiem({'muc': [_muc(voi_ban='Đổi X cho bạn.')]}) == [])

    # ── [33] PHẢI CHẶN — địa chỉ nguồn trả 404 ⇒ mã 2 và KHÔNG commit.
    ma, lenh, dem = dang_voi((404, 'Not Found'))
    ca('33', 'nguồn HTTP 404 ⇒ mã 2, không commit',
       ma == 2 and 'commit' not in lenh and dem >= 1)

    # ── [34] ĐỐI CHỨNG chống CHẶN OAN — 403 là bị chặn bot, KHÔNG phải trang đã gỡ.
    # Chiều hỏng ở đây đắt hơn chiều kia: coi 403 là chết thì routine kêu gần như mỗi sáng,
    # và một bảng kêu oan vài lần là hết được đọc (mục 17 CLAUDE.md).
    ma, lenh, dem = dang_voi((403, 'Forbidden'))
    ca('34', 'nguồn HTTP 403 vẫn đăng được (không chặn oan)', ma == 0 and 'commit' in lenh)

    # ── [35] ĐỐI CHỨNG — đo không kết luận được (mạng hỏng) cũng không được chặn.
    ma, lenh, dem = dang_voi((None, 'mạng hỏng'))
    ca('35', 'đo link không kết luận được ⇒ vẫn đăng', ma == 0 and 'commit' in lenh)

    # ── [36] PHẢI CHẶN — cờ --bo-do-link phải THẬT SỰ bỏ bước đo, không chỉ in ra là bỏ.
    # Cờ mở được quảng cáo mà không có thật còn tệ hơn không có cờ (mục 17 CLAUDE.md).
    ma, lenh, dem = dang_voi((404, 'Not Found'), bo_do_link=True)
    ca('36', '--bo-do-link ⇒ KHÔNG gọi phép đo nào', ma == 0 and dem == 0)

    # ── [37] PHẢI CHẶN — mọi nguồn của MỌI mục đều phải được đo, không chỉ mục đầu.
    ma, lenh, dem = dang_voi((200, ''), muc=[_muc(tieu_de='a'), _muc(tieu_de='b')])
    ca('37', 'đo đủ nguồn của mọi mục', ma == 0 and dem == 2)

    return ra


def _doc(m, xml):
    """Gọi `doc_feed` với XML dựng sẵn, không chạm mạng."""
    cu = m.lay
    m.lay = lambda url, timeout=25: xml
    try:
        return m.doc_feed('Nguồn thử', 'https://vd.test/feed', 'hang')
    finally:
        m.lay = cu


def _quet(m, bang_xml):
    """Chạy trọn `quet()` với bảng nguồn giả và sổ đã-đọc rỗng trong thư mục tạm."""
    import json
    cu_lay, cu_nguon, cu_so, cu_tm = m.lay, m.NGUON, m.SO, m.THU_MUC_QUET
    tmp = tempfile.mkdtemp()
    bang = {'nguon': [{'ten': t, 'url': 'https://vd.test/%s' % t, 'loai': 'hang'}
                      for t in bang_xml]}
    duong = os.path.join(tmp, 'nguon.json')
    with open(duong, 'w', encoding='utf-8') as f:
        json.dump(bang, f)
    m.NGUON, m.THU_MUC_QUET, m.SO = duong, tmp, os.path.join(tmp, 'so.jsonl')
    m.lay = lambda url, timeout=25: bang_xml[url.rsplit('/', 1)[1]]
    buf = io.StringIO()
    try:
        with redirect_stdout(buf):
            ma, lo = m.quet(ghi=False)
    finally:
        m.lay, m.NGUON, m.SO, m.THU_MUC_QUET = cu_lay, cu_nguon, cu_so, cu_tm
    return ma, lo or [], buf.getvalue()


def in_bang(ket_qua, tieu_de):
    print('\n%s' % tieu_de)
    do = []
    for ma, mo_ta, dat in ket_qua:
        print('  %s [%s] %s' % ('✓' if dat else '✗', ma, mo_ta))
        if not dat:
            do.append(ma)
    print('  → %d/%d đạt' % (len(ket_qua) - len(do), len(ket_qua)))
    return do


def tu_kiem():
    sys.path.insert(0, '/Users/Huy/Claude/HeThong')
    from khung_tu_kiem import don_mo_coi_mot_lan
    _don = don_mo_coi_mot_lan(os.path.dirname(os.path.abspath(__file__)))
    if _don:
        print('\u00b7 d\u1ecdn %d b\u1ea3n h\u1ecfng m\u1ed3 c\u00f4i c\u1ee7a l\u01b0\u1ee3t ki\u1ec3m ch\u1ebft gi\u1eefa ch\u1eebng' % _don)
    sys.path.insert(0, '/Users/Huy/Claude/HeThong')
    from khung_tu_kiem import LoiNeo, neo_hai_dong

    print('— chạy bộ ca trên BẢN ĐÚNG trước —')
    do_that = in_bang(chay_bo_ca(nap(THAT)), 'BẢN THẬT')
    if do_that:
        print('\n✗ Bản THẬT đã có ca đỏ (%s) — sửa mã trước, phép tự kiểm không nói được gì '
              'khi nền đã đỏ.' % ', '.join(do_that))
        return 1

    tong_hong = 0
    # Hai file được canh: bộ quét và cổng đăng. Cột cuối của mỗi dòng `BAN_HONG` nói bản hỏng
    # thuộc file nào — thiếu cột đó thì cổng đăng có mã mà không có bản hỏng nào chứng minh
    # các ca [20]-[30] có răng.
    for ten, tim, thay, phai_do, thuoc in BAN_HONG:
        muc_tieu = THAT if thuoc == 'quet' else os.path.join(RA, 'dang-tin.py')
        goc = open(muc_tieu, encoding='utf-8').read()
        try:
            tim2, thay2 = neo_hai_dong(goc, tim, thay)
        except LoiNeo as e:
            print('  ✗ %s — %s' % (ten, e))
            tong_hong += 1
            continue
        noi_dung = goc.replace(tim2, thay2)
        if noi_dung == goc:
            print('  ✗ %s — phép thay không đổi được gì' % ten)
            tong_hong += 1
            continue
        import hashlib
        # Tên mang PID + băm nội dung: PID để hai phiên cùng chạy `--tu-kiem` không xoá bản
        # hỏng của nhau, băm để lần nạp sau không đọc lại `.pyc` cũ của cùng tên file trong
        # cùng một giây (mục 17 CLAUDE.md).
        ten_file = os.path.join(RA, '_thu-hong-%d-%s-%s.py' % (
            os.getpid(), hashlib.sha1(noi_dung.encode()).hexdigest()[:8], thuoc))
        try:
            with open(ten_file, 'w', encoding='utf-8') as f:
                f.write(noi_dung)
            try:
                kq = (chay_bo_ca(nap(ten_file)) if thuoc == 'quet'
                      else chay_bo_ca(nap(THAT), duong_dang=ten_file))
            except Exception as e:
                print('  ✗ %s — bản hỏng không chạy được: %r' % (ten, e))
                tong_hong += 1
                continue
            do = [ma for ma, _, dat in kq if not dat]
            if len(do) == len(kq):
                print('  ✗ %s — ĐỎ TOÀN BỘ, phép thay làm hỏng cú pháp chứ không gỡ lớp vá'
                      % ten)
                tong_hong += 1
                continue
            thieu = [x for x in phai_do if x not in do]
            if thieu:
                print('  ✗ %s — ca %s VẪN XANH trên bản hỏng (đỏ: %s)'
                      % (ten, ', '.join(thieu), ', '.join(do) or 'không ca nào'))
                tong_hong += 1
            else:
                print('  ✓ %s — bắt được, ca đỏ: %s' % (ten, ', '.join(do)))
        finally:
            try:
                os.unlink(ten_file)
            except OSError:
                pass
    print('\n%s %d/%d bản hỏng bị bắt' % ('✓' if not tong_hong else '✗',
                                          len(BAN_HONG) - tong_hong, len(BAN_HONG)))
    return 1 if tong_hong else 0


# ⚠ QUY ƯỚC: bảng BAN_HONG đặt CUỐI file, sau mã — `neo_hai_dong` chọn vị trí khớp ĐẦU TIÊN
# làm chỗ mã thật.
BAN_HONG = [
    # Phép thay phải viết ĐÚNG dòng gốc gây bug (`or` giữa hai `find`), không phải một dòng
    # nghe-như-hỏng. Bản đầu khai `el.find('title') and None` không làm ca nào đỏ: Element
    # không con là FALSY nên `and` trả về chính Element, tức bản "hỏng" vẫn chạy đúng.
    ('mở lại lỗi Element-falsy',
     "        n = el.find('title')\n        if n is None:\n            n = el.find('{http://www.w3.org/2005/Atom}title')",
     "        n = el.find('title') or el.find('{http://www.w3.org/2005/Atom}title')\n        if n is None:\n            pass",
     ['01'], 'quet'),
    ('bỏ phép đếm nguồn 0 mục',
     "                loi.append('%s: tải được nhưng 0 mục' % n['ten'])",
     "                pass",
     ['03'], 'quet'),
    ('so trùng bằng chuỗi thay vì tập từ',
     "        if any(giong(tu, cu) for cu in thay):",
     "        if False:",
     ['05'], 'quet'),
    ('bỏ trần mỗi nguồn',
     "        if dem_nguon.get(t['ten_nguon'], 0) >= tran_nguon.get(t['ten_nguon'], TRAN_MOI_NGUON):",
     "        if False:",
     ['07'], 'quet'),
    ('bỏ cửa sổ thời gian',
     "    trong_cua = [t for t in tin if t['thoi_diem'] is None or t['thoi_diem'] >= moc]",
     "    trong_cua = list(tin)",
     ['09'], 'quet'),
    ('bỏ cổng loại tin gọi vốn/kiện tụng',
     "    for mau in MAU_LOAI:\n        if re.search(bo_dau(mau), van):\n            return False",
     "    for mau in []:\n        if re.search(bo_dau(mau), van):\n            return False",
     ['10'], 'quet'),
    ('bỏ chuẩn hoá NFC',
     "    s = unicodedata.normalize('NFC', html.unescape(s or ''))",
     "    s = html.unescape(s or '')",
     ['12'], 'quet'),
    ('mất bảng nguồn trả êm thay vì mã 2',
     "        print('KHÔNG có bảng nguồn %s' % NGUON, file=sys.stderr)\n        return 2, None",
     "        print('KHÔNG có bảng nguồn %s' % NGUON, file=sys.stderr)\n        return 0, []",
     ['13'], 'quet'),
    ('bỏ phép bóc đuôi toà soạn',
     "    s = re.sub(r'\\s+-\\s+[^-]{1,40}$', '', chuan(tieu_de))",
     "    s = chuan(tieu_de)",
     ['14'], 'quet'),
    # ── bản hỏng của CỔNG ĐĂNG ──────────────────────────────────────────────────────────
    ('bỏ kiểm nhãn cat',
     "        if m.get('cat') not in NHAN_HOP_LE:",
     "        if False:",
     ['21'], 'dang'),
    ('bỏ kiểm khuôn ngày',
     "        if not re.match(r'^\\d{2}/\\d{2}/\\d{4}$', str(m.get('ngay') or '')):",
     "        if False:",
     ['22'], 'dang'),
    ('bỏ trần số mục',
     "    if len(muc) <= TRAN_MUC:\n        return False",
     "    if True:\n        return False",
     ['26'], 'dang'),
    ('đăng bất chấp thay đổi của phiên khác',
     "    la = [d for d in ban if d[3:].strip().strip('\"') != TEN_FILE]",
     "    la = []",
     ['28'], 'dang'),
    ('fail-open khi git status lỗi',
     "    if ma != 0:\n        print('không đọc được trạng thái git: %s' % ra.strip(), file=sys.stderr)\n        return 2",
     "    if False:\n        print('không đọc được trạng thái git: %s' % ra.strip(), file=sys.stderr)\n        return 2",
     ['29'], 'dang'),
    ('bỏ "voi_ban" khỏi danh sách bắt buộc',
     "BAT_BUOC = ('ngay', 'cat', 'tieu_de', 'noi_dung', 'voi_ban')",
     "BAT_BUOC = ('ngay', 'cat', 'tieu_de', 'noi_dung')",
     ['31'], 'dang'),
    ('bỏ hẳn bước đo địa chỉ nguồn',
     "    if not bo_do_link:\n        chet = do_link(d)",
     "    if False:\n        chet = do_link(d)",
     ['33'], 'dang'),
    # Bản hỏng theo chiều NỚI đã có ở trên; đây là chiều SIẾT — coi mọi mã khác 200 là chết.
    # Không có bản hỏng này thì ca [34]/[35] chỉ là hai dòng xanh không ai chứng minh có răng,
    # mà đúng chiều này mới là chiều làm routine kêu oan mỗi sáng.
    ('coi mọi mã HTTP khác 200 là trang đã gỡ',
     "MA_CHET = (404, 410)",
     "MA_CHET = tuple(x for x in range(201, 600))",
     ['34'], 'dang'),
    ('chỉ đo nguồn của mục đầu tiên',
     "    for i, m in enumerate(d.get('muc') or []):",
     "    for i, m in enumerate((d.get('muc') or [])[:1]):",
     ['37'], 'dang'),
]

if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--tu-kiem', action='store_true')
    a = p.parse_args()
    if a.tu_kiem:
        sys.exit(tu_kiem())
    sys.exit(1 if in_bang(chay_bo_ca(nap(THAT)), 'BỘ CA quet-tin-ai.py') else 0)
