#!/usr/bin/env python3
"""Quét tin AI từ bảng nguồn, lọc ra lô tin đáng đưa lên tab "Tin mới" của trang Học AI.

Huy chốt 07/08/2026 qua bảng chọn "gộp lịch và đường chạy": trước đó tab "Tin mới" của
`index.html` ghi thẳng trong trang là *"cập nhật thủ công khi có tin quan trọng"* — tức là
điểm quét tin DUY NHẤT trong 05 điểm của hệ mà không routine nào đụng tới. Bộ này lấp chỗ đó
mà KHÔNG mở thêm phiên Claude nào: bước quét là script thuần, bước viết mục tiếng Việt ghép
vào cuối phiên `tin-kinh-doanh` 06:30 đang chạy sẵn.

VÌ SAO GHÉP VÀO PHIÊN CÓ SẴN, KHÔNG DỰNG PHIÊN RIÊNG: khoản đắt của một routine không nằm ở
việc tải trang mà ở số PHIÊN Claude mở ra — mỗi phiên phải đọc lại ~173k token nền trước khi
làm việc gì (mục 27 CLAUDE.md). Thêm một mốc chạy riêng cho việc này là trả tiền nền lần thứ
hai để làm một việc chỉ tốn vài phút.

VÌ SAO BƯỚC AI ĐỨNG CUỐI SKILL `tin-kinh-doanh`: bước đứng cuối mà hỏng thì mọi bước trước
đã xong và đã gửi đi. Đặt nó chen giữa là lấy rủi ro của việc mới gán cho việc đang chạy ổn.

CHỐNG TRÙNG: sổ `.quet/so-da-doc.jsonl` ghi URL đã vào lô. Thiếu nó thì mỗi sáng tab tin lặp
lại tin hôm qua, mà một trang tin lặp thì vài hôm là hết được mở.

CHIỀU HỎNG CỐ Ý: nguồn trượt thì KÊU bằng mã thoát khác 0, không im lặng trả lô rỗng — lô rỗng
ngày ít tin và "mọi nguồn đều chặn" cho ra cùng một đầu ra, chỉ mã thoát phân biệt được
(mục 17 CLAUDE.md, luật lỗi phải trả về phía KÊU).

Dùng:
    quet-tin-ai.py                 # quét, ghi lô ra .quet/lo-<ngày>.json
    quet-tin-ai.py --do-nguon      # chỉ đo bảng nguồn, không ghi sổ
    quet-tin-ai.py --tran 12       # đổi trần số tin trong lô
"""
import argparse
import concurrent.futures
import html
import json
import os
import re
import sys
import unicodedata
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime

RA = os.path.dirname(os.path.abspath(__file__))
NGUON = os.path.join(RA, 'nguon-tin-ai.json')
THU_MUC_QUET = os.path.join(RA, '.quet')
SO = os.path.join(THU_MUC_QUET, 'so-da-doc.jsonl')
VN = timezone(timedelta(hours=7))

# Cửa sổ 40 giờ chứ không phải 24: lượt chạy 06:30 giờ Việt Nam rơi vào đêm hôm trước ở Mỹ,
# nơi phần lớn nguồn trong bảng đăng bài. Lấy đúng 24 giờ là cắt mất nửa ngày làm việc của
# họ. Trùng lặp đã có sổ chặn nên rộng tay ở đây không sinh tin lặp.
CUA_SO_GIO = 40
# Trần số tin đưa cho bước viết. Tab "Tin mới" là chỗ đọc lướt, 8 mục một ngày đã là nhiều.
TRAN_LO = 10
# Hạn ngạch theo loại nguồn, cắt TRƯỚC khi xếp hạng chung. Đo lượt đầu 07/08/2026: xếp chung
# một bảng điểm thì nguồn báo (TechCrunch, VentureBeat, Verge, Ars, MIT) chiếm 8/10 chỗ vì
# chúng đăng dày và tiêu đề nào cũng chạm từ khoá, đẩy thông báo gốc của chính hãng xuống
# dưới lằn cắt. Trang Học AI cần thông báo gốc trước, bình luận báo chí sau.
TRAN_LOAI = [('hang', 5), ('bao', 3), ('viet', 1), ('blog', 1)]
# Trần cho MỘT nguồn, chồng lên trần theo loại. Feed Google News gom hàng chục toà soạn nên
# một mình nó lấp kín hạn ngạch của cả loại `hang` — đo lượt đầu: 05/10 chỗ về cùng từ đó.
TRAN_MOI_NGUON = 2

# Tin bị loại thẳng: nhịp lặp, thương vụ tài chính, kiện tụng nhân sự. Trang này dạy CÁCH
# DÙNG AI, nên một vòng gọi vốn hay một vụ kiện bản quyền không đổi gì cho người đọc.
# Mẫu cố ý HẸP và buộc có ngữ cảnh tài chính: 'ai stocks' trần vẫn có thể là tin hạ giá API
# — mà chặn oan tin giá là mất đúng thứ người đọc cần.
MAU_LOAI = [
    r'\b(series [a-e]|funding round|raises \$?\d|valuation of|ipo filing)\b',
    r'\b(lawsuit|sues|court filing|antitrust probe) (against |over )',
    r'\b(stock|shares|earnings) (jump|slump|surge|fall|rise)',
    r'\b(hires|poaches|steps down as|named ceo)\b',
    r'\b(webinar|register now|sponsored)\b',
]
# Vế ĐÁNG ĐỌC: tin phải chạm ít nhất một dấu hiệu có thứ mới để dùng hoặc để biết. Cổng này
# CHỈ áp cho nguồn `bao` và `viet` — hai loại đăng dày nhất và lệch xa chủ đề nhất. Nguồn
# `hang` và `blog` được miễn: chính hãng chỉ đăng khi có thứ để công bố, còn hai blog trong
# bảng vốn đã viết đúng chủ đề, áp cổng vào đó là cắt oan bài hướng dẫn hay.
MAU_DANG = [
    r'\b(launch|release|announc|introduc|unveil|now available|rolls? out|ships?)\b',
    r'\b(model|gpt-\d|claude|gemini|llama|mistral|grok|deepseek|sora|copilot)\b',
    r'\b(free|pricing|price|cheaper|cost|per token|rate limit|context window)\b',
    r'\b(feature|update|version|agent|api|extension|plugin|skill)\b',
    r'(ra mắt|cập nhật|tính năng|miễn phí|phiên bản|công cụ|hướng dẫn|mẹo)',
]
# Từ khoá cộng điểm — thứ người đọc trang này quan tâm nhất, theo đúng nội dung 07 tab con
# hiện có (kiến thức chung · công cụ · Claude · agentic · lộ trình học).
DIEM = [
    (5, r'\b(claude|anthropic|claude code)\b'),
    (4, r'\b(gpt-\d|chatgpt|openai|gemini|copilot)\b'),
    (3, r'\b(free|miễn phí|pricing|giá|rate limit|context window)\b'),
    (3, r'\b(agent|agentic|skill|mcp|tool use)\b'),
    (2, r'\b(release|launch|ra mắt|cập nhật|announc)\b'),
    (2, r'\b(guide|tutorial|how to|hướng dẫn|mẹo|tips)\b'),
]


def chuan(s):
    """Chuẩn hoá NFC + gộp khoảng trắng lạ trước MỌI phép so khớp.

    Nội dung feed đi qua nhiều khâu (trình soạn của toà soạn, bộ sinh RSS, proxy) nên cùng
    một chữ có thể về ở dạng NFD hoặc mang U+00A0/U+202F. Hai chuỗi nhìn y hệt nhau mà khác
    byte thì mọi phép khớp từ khoá bên dưới im lặng trượt (mục 17 CLAUDE.md).
    """
    s = unicodedata.normalize('NFC', html.unescape(s or ''))
    s = re.sub(r'[  ⁠​]', ' ', s)
    return re.sub(r'\s+', ' ', s).strip()


def bo_dau(s):
    return ''.join(c for c in unicodedata.normalize('NFD', s.lower())
                   if unicodedata.category(c) != 'Mn')


# Từ dừng loại trước khi so trùng — giữ lại thì hai tin không liên quan vẫn chung 30% số từ.
TU_DUNG = set('''a an the of to in on for with and or is are was were its his her their this
that from at by as be been being will would can could may might new more most than then
about into over after before up down out off just also only very s t don co ltd inc
va la cua cho voi tu den ra vao mot cac nhung se da dang bi duoc theo khi nhu'''.split())
# Ngưỡng giống nhau. 0,5 chọn theo số đo lượt đầu: 05 bản của tin "Meta coding agent" đôi một
# giống 0,50-0,71, còn cặp gần nhất trong nhóm tin KHÁC nhau chỉ đạt 0,33 ("ChatGPT unlimited
# chats" với "OpenAI smart speaker"). Hạ xuống 0,35 là bắt đầu nuốt tin thật.
NGUONG_GIONG = 0.5


def tap_tu(tieu_de):
    """Tập từ đặc trưng của một tiêu đề, đã bỏ dấu, bỏ đuôi toà soạn và bỏ từ dừng.

    Feed Google News gắn đuôi ' - Tên toà soạn' vào mọi tiêu đề; giữ đuôi đó lại thì hai bản
    của cùng một tin luôn khác nhau đúng ở phần khác nhau nhất.
    """
    s = re.sub(r'\s+-\s+[^-]{1,40}$', '', chuan(tieu_de))
    tu = {x for x in re.findall(r'[a-z0-9]+', bo_dau(s)) if len(x) > 2 and x not in TU_DUNG}
    return tu


def giong(a, b):
    if not a or not b:
        return False
    return len(a & b) / len(a | b) >= NGUONG_GIONG


def lay(url, timeout=25):
    req = urllib.request.Request(url, headers={
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
                      'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36',
        'Accept': 'application/rss+xml, application/atom+xml, application/xml, text/xml, */*',
    })
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def _mo_ta(el):
    for tag in ('description', 'summary', '{http://www.w3.org/2005/Atom}summary',
                '{http://www.w3.org/2005/Atom}content', 'content'):
        n = el.find(tag)
        if n is not None and (n.text or ''):
            return chuan(re.sub(r'<[^>]+>', ' ', n.text))[:600]
    return ''


def _thoi_diem(el):
    for tag in ('pubDate', 'published', '{http://www.w3.org/2005/Atom}published',
                '{http://www.w3.org/2005/Atom}updated', 'updated',
                '{http://purl.org/dc/elements/1.1/}date'):
        n = el.find(tag)
        if n is None or not (n.text or '').strip():
            continue
        t = (n.text or '').strip()
        for phep in (parsedate_to_datetime,
                     lambda x: datetime.fromisoformat(x.replace('Z', '+00:00'))):
            try:
                d = phep(t)
                return d if d.tzinfo else d.replace(tzinfo=timezone.utc)
            except Exception:
                continue
    return None


def _link(el):
    n = el.find('link')
    if n is not None:
        if (n.text or '').strip():
            return chuan(n.text)
        if n.get('href'):
            return n.get('href')
    for n in el.findall('{http://www.w3.org/2005/Atom}link'):
        if n.get('rel') in (None, 'alternate') and n.get('href'):
            return n.get('href')
    return ''


def doc_feed(ten, url, loai):
    """Trả (danh sách tin, lỗi-hay-None). Lỗi trả về CHUỖI chứ không ném ra ngoài —
    một nguồn chết không được làm hỏng cả lượt quét, nhưng phải đếm được để mã thoát biết."""
    try:
        b = lay(url)
    except Exception as e:
        return [], '%s: %r' % (ten, e)
    try:
        goc = ET.fromstring(b)
    except Exception as e:
        return [], '%s: XML hỏng %r' % (ten, e)
    muc = goc.findall('.//item') + goc.findall('.//{http://www.w3.org/2005/Atom}entry')
    ra = []
    for el in muc:
        # ⚠ PHẢI so `is not None`, CẤM viết `el.find(a) or el.find(b)`. Một Element không có
        # con là FALSY trong Python, nên `or` nhảy sang vế sau và trả None — đo thật lúc dựng
        # 07/08/2026: 12/14 nguồn ra 0 tin trong im lặng, bảng vẫn in "14/14 nguồn sống" vì
        # fetch không hề lỗi. Đây là lối hỏng không có tiếng kêu nào.
        n = el.find('title')
        if n is None:
            n = el.find('{http://www.w3.org/2005/Atom}title')
        tieu_de = chuan(n.text if n is not None else '')
        link = _link(el)
        if not tieu_de or not link:
            continue
        ra.append({'ten_nguon': ten, 'loai': loai, 'tieu_de': tieu_de, 'url': link,
                   'mo_ta': _mo_ta(el), 'thoi_diem': _thoi_diem(el)})
    return ra, None


def doc_so():
    if not os.path.exists(SO):
        return set()
    ra = set()
    with open(SO, encoding='utf-8') as f:
        for d in f:
            d = d.strip()
            if not d:
                continue
            try:
                ra.add(json.loads(d).get('url', ''))
            except Exception:
                continue
    return ra


def ghi_so(tin):
    os.makedirs(THU_MUC_QUET, exist_ok=True)
    with open(SO, 'a', encoding='utf-8') as f:
        for t in tin:
            f.write(json.dumps({'url': t['url'], 'ngay': datetime.now(VN).strftime('%Y-%m-%d')},
                               ensure_ascii=False) + '\n')
    os.chmod(SO, 0o600)


def cham(t):
    van = bo_dau(t['tieu_de'] + ' ' + t['mo_ta'])
    d = 0
    for diem, mau in DIEM:
        if re.search(bo_dau(mau), van):
            d += diem
    # Tin có ngày mới hơn được cộng, để hai tin cùng điểm thì tin mới đứng trên.
    if t.get('thoi_diem'):
        gio = (datetime.now(timezone.utc) - t['thoi_diem']).total_seconds() / 3600
        d += 2 if gio <= 12 else (1 if gio <= 24 else 0)
    return d


def dang_doc(t):
    van = bo_dau(t['tieu_de'] + ' ' + t['mo_ta'])
    for mau in MAU_LOAI:
        if re.search(bo_dau(mau), van):
            return False
    if t['loai'] in ('bao', 'viet'):
        return any(re.search(bo_dau(m), van) for m in MAU_DANG)
    return True


def quet(tran_lo=TRAN_LO, ghi=True):
    if not os.path.exists(NGUON):
        print('KHÔNG có bảng nguồn %s' % NGUON, file=sys.stderr)
        return 2, None
    with open(NGUON, encoding='utf-8') as f:
        bang = json.load(f).get('nguon') or []
    if not bang:
        print('bảng nguồn RỖNG', file=sys.stderr)
        return 2, None

    tin, loi = [], []
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as ex:
        for n, (ra, e) in zip(bang, ex.map(
                lambda x: doc_feed(x['ten'], x['url'], x.get('loai') or 'bao'), bang)):
            tin.extend(ra)
            if e:
                loi.append(e)
            elif not ra:
                # Fetch 200 mà bóc ra 0 mục cũng là TRƯỢT, phải đếm vào mã thoát. Đúng lối
                # hỏng đã vấp lúc dựng: 12/14 nguồn về rỗng vì một phép so sai, mà không lỗi
                # mạng nào phát ra nên bảng vẫn khai đủ nguồn sống.
                loi.append('%s: tải được nhưng 0 mục' % n['ten'])

    moc = datetime.now(timezone.utc) - timedelta(hours=CUA_SO_GIO)
    # Tin KHÔNG khai thời điểm vẫn giữ: một số feed (GitHub releases, vài bản Atom rút gọn)
    # bỏ trống trường ngày, loại thẳng là mất nguồn chứ không phải lọc tin cũ. Sổ đã-đọc
    # chặn phần lặp lại giúp, nên giữ lại ở đây an toàn hơn cắt.
    trong_cua = [t for t in tin if t['thoi_diem'] is None or t['thoi_diem'] >= moc]
    da_doc = doc_so()
    con = [t for t in trong_cua if t['url'] not in da_doc and dang_doc(t)]

    # Loại trùng theo TẬP TỪ, không theo chuỗi tiêu đề.
    #
    # CƠ CHẾ GÂY VẤP, đo thật lượt chạy đầu 07/08/2026: so 70 ký tự đầu của tiêu đề để lại
    # nguyên 05 bản của cùng một sự kiện trong lô 10 tin — "Meta is launching its first AI
    # coding agent to rival Anthropic and OpenAI", "Meta Launches AI Coding Agent to
    # Challenge OpenAI and Anthropic", "Meta Releases Coding Agent to Compete With…". Cùng
    # một tin, ba toà soạn viết ba tiêu đề, không hai chuỗi nào giống nhau. Feed Google News
    # gom nhiều toà soạn trong một nguồn nên lối này là chắc chắn xảy ra, không phải rủi ro.
    thay, sach = [], []
    for t in sorted(con, key=cham, reverse=True):
        tu = tap_tu(t['tieu_de'])
        if any(giong(tu, cu) for cu in thay):
            continue
        thay.append(tu)
        sach.append(t)

    lo, dem, dem_nguon = [], {k: 0 for k, _ in TRAN_LOAI}, {}
    han = dict(TRAN_LOAI)
    tran_nguon = {n['ten']: n['tran'] for n in bang if isinstance(n.get('tran'), int)}
    for t in sach:
        if len(lo) >= tran_lo:
            break
        k = t['loai']
        if dem.get(k, 0) >= han.get(k, 0):
            continue
        # Trần theo TỪNG NGUỒN, chồng lên trần theo loại. Một feed gom nhiều toà soạn
        # (Google News) đẩy được rất nhiều tin cùng chủ đề vào một lượt, và phép loại trùng
        # chỉ chặn được bản viết giống nhau — 05 bài KHÁC nhau về cùng một hãng vẫn lọt.
        # Nguồn nào cần chặt hơn thì khai `"tran": n` trong bảng nguồn. Đang dùng cho feed
        # phát hành của Claude Code: nó ra bản vá gần như hằng ngày, và hai mục liền nhau
        # tên "v2.1.224" · "v2.1.223" trên một trang tin đọc như trang hỏng.
        if dem_nguon.get(t['ten_nguon'], 0) >= tran_nguon.get(t['ten_nguon'], TRAN_MOI_NGUON):
            continue
        dem[k] = dem.get(k, 0) + 1
        dem_nguon[t['ten_nguon']] = dem_nguon.get(t['ten_nguon'], 0) + 1
        lo.append(t)
    # Còn chỗ trống sau khi mọi hạn ngạch đã đầy thì lấp bằng tin điểm cao nhất còn lại —
    # hạn ngạch để chia đều, không phải để bỏ trống chỗ.
    # ⚠ Vòng lấp này nới hạn ngạch theo LOẠI, nhưng KHÔNG được nới trần theo NGUỒN — nới cả
    # hai là mở lại đúng cái lỗ vừa bịt, và lô lại đầy tin của một feed. Ca [07] canh chiều
    # này (mục 17: siết một ngưỡng thì thêm ngay ca canh chiều nới của chính ngưỡng ấy).
    if len(lo) < tran_lo:
        for t in sach:
            if len(lo) >= tran_lo:
                break
            if t in lo:
                continue
            if dem_nguon.get(t['ten_nguon'], 0) >= tran_nguon.get(t['ten_nguon'], TRAN_MOI_NGUON):
                continue
            dem_nguon[t['ten_nguon']] = dem_nguon.get(t['ten_nguon'], 0) + 1
            lo.append(t)

    for t in lo:
        t['thoi_diem'] = t['thoi_diem'].isoformat() if t['thoi_diem'] else None

    ma = 0
    if len(loi) * 2 > len(bang):
        ma = 1
    if ghi:
        os.makedirs(THU_MUC_QUET, exist_ok=True)
        ten = os.path.join(THU_MUC_QUET, 'lo-%s.json' % datetime.now(VN).strftime('%Y-%m-%d'))
        with open(ten, 'w', encoding='utf-8') as f:
            json.dump({'ngay': datetime.now(VN).strftime('%Y-%m-%d'),
                       'so_nguon': len(bang), 'so_nguon_truot': len(loi), 'loi': loi,
                       'tong_thay': len(tin), 'trong_cua_so': len(trong_cua),
                       'con_lai_sau_loc': len(sach), 'lo': lo}, f, ensure_ascii=False, indent=1)
        ghi_so(lo)
        print('%d/%d nguồn đọc được · %d tin thấy · %d trong cửa sổ · %d qua lọc · lô %d tin'
              % (len(bang) - len(loi), len(bang), len(tin), len(trong_cua), len(sach), len(lo)))
        for e in loi:
            print('  ✗ %s' % e)
        print('LÔ: %s' % ten)
    return ma, lo


def do_nguon():
    with open(NGUON, encoding='utf-8') as f:
        bang = json.load(f).get('nguon') or []
    chet = 0
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as ex:
        for n, (ra, e) in zip(bang, ex.map(
                lambda x: doc_feed(x['ten'], x['url'], x.get('loai') or 'bao'), bang)):
            xau = e or ('tải được nhưng 0 mục' if not ra else '')
            print('%-34s %-5s %4d item%s' % (n['ten'], n.get('loai'), len(ra),
                                             '  ✗ ' + xau if xau else ''))
            if xau:
                chet += 1
    print('— %d/%d nguồn sống' % (len(bang) - chet, len(bang)))
    return 1 if chet * 2 > len(bang) else 0


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--do-nguon', action='store_true')
    p.add_argument('--tran', type=int, default=TRAN_LO)
    p.add_argument('--khong-ghi', action='store_true')
    a = p.parse_args()
    if a.do_nguon:
        sys.exit(do_nguon())
    ma, _ = quet(tran_lo=a.tran, ghi=not a.khong_ghi)
    sys.exit(ma)
