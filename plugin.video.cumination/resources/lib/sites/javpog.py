# -*- coding: utf-8 -*-
'''
    Cumination - adapté pour javpog.com
'''

import base64
import random
import re
import string
import time
import xbmc
import xbmcgui
from six.moves import urllib_parse
from resources.lib import utils
from resources.lib.adultsite import AdultSite

site = AdultSite(
    'javpog',
    '[COLOR hotpink]JavPOG[/COLOR]',
    'https://javpog.com/',
    'javpog.png',
    'javpog'
)

javpog_headers = utils.base_hdrs.copy()
javpog_headers.update({'Referer': site.url})

UA = utils.USER_AGENT
ORIGIN = 'https://javpog.com'

MEDIA_RE = re.compile(
    r'''["'\(]([^"'\(\)<>\s]+?\.(?:m3u8|mp4|webm|mkv|mov)(?:\?[^"'\(\)<>\s]*)?)["'\)]''',
    re.IGNORECASE)
SRC_RE = re.compile(
    r'''(?:src|file|source|url|video_url|hls|mp4|link)\s*[:=]\s*["']([^"']+?\.(?:m3u8|mp4|webm|mkv|mov)(?:\?[^"']*)?)''',
    re.IGNORECASE)
IFRAME_RE = re.compile(r'''<iframe[^>]+src=["']([^"']+)["']''', re.IGNORECASE)
META_RE = re.compile(r'''<meta[^>]+http-equiv=["']?refresh["']?[^>]+content=["'][^"']*?url=([^"';]+)''', re.IGNORECASE)
JS_REDIR_RE = re.compile(r'''(?:location\.href|location\.replace|window\.location)\s*[=(]\s*["']([^"']+)["']''', re.IGNORECASE)
B64FILE_RE = re.compile(r'''["'](?:file|source|src|url|video_url)["']\s*[:=]\s*["']([A-Za-z0-9+/=]{24,})["']''', re.IGNORECASE)
PASSMD5_RE = re.compile(r'''/pass_md5/([^'"\)\s]+)''', re.IGNORECASE)


def _get_html(url, referer, headers=None, tries=2):
    for i in range(tries):
        try:
            html = utils.getHtml(url, referer, headers=headers or javpog_headers)
            if html:
                return html
        except Exception as e:
            utils.kodilog('JAVPOG fetch retry {}/{} {} : {}'.format(i + 1, tries, url, e))
            xbmc.sleep(500)
    return ''


def _is_media(u):
    if not u:
        return False
    path = u.split('|')[0].split('?')[0].lower()
    return path.endswith(('.m3u8', '.mp4', '.webm', '.mkv', '.mov'))


def _absolute(u, base):
    if not u:
        return ''
    u = u.replace('&amp;', '&').strip().strip('"\'')
    if u.startswith('//'):
        u = 'https:' + u
    elif u.startswith('/') or u.startswith('?'):
        u = urllib_parse.urljoin(base, u)
    return u if u.startswith('http') else ''


def _hdr(u, referer):
    if not u or '|' in u:
        return u
    return '{0}|Referer={1}&User-Agent={2}'.format(u, referer, UA)


def _doodstream(embed, path):
    """Résout un embed DoodStream (vide0.net & clones) via /pass_md5/."""
    token = path.split('/')[-1]
    api = urllib_parse.urljoin(embed, '/pass_md5/' + path)
    base = _get_html(api, embed, headers={
        'Referer': embed,
        'X-Requested-With': 'XMLHttpRequest',
        'Accept': '*/*'
    })
    if not base:
        return None
    base = base.strip().replace('\n', '').replace('\r', '')
    rnd = ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(10))
    sep = '&' if '?' in base else '?'
    final = '{0}{1}{2}token={3}&expiry={4}'.format(base, rnd, sep, token, int(time.time() * 1000))
    utils.kodilog('JAVPOG doodstream -> {}'.format(final))
    return _hdr(final, embed)


def _extract_media(html, base):
    h = html.replace('\\/', '/').replace('\\u0026', '&').replace('\\u003d', '=')
    out = []
    for rx in (SRC_RE, MEDIA_RE):
        for m in rx.finditer(h):
            u = _absolute(m.group(1), base)
            if u and _is_media(u) and u not in out:
                out.append(u)
    for m in B64FILE_RE.finditer(h):
        val = m.group(1)
        try:
            dec = base64.b64decode(val + '=' * (-len(val) % 4)).decode('utf-8', 'ignore')
        except Exception:
            continue
        if _is_media(dec):
            u = _absolute(dec, base)
            if u and u not in out:
                out.append(u)
    return out


@site.register(default_mode=True)
def Main():
    site.add_dir('[COLOR hotpink]Categories[/COLOR]', site.url, 'Categories', site.img_cat)
    site.add_dir('[COLOR hotpink]Actress[/COLOR]', site.url + 'jav-actress-list/', 'Actresses', site.img_cat)
    site.add_dir('[COLOR hotpink]Tags[/COLOR]', site.url + 'tags/', 'Tags', site.img_tags)
    site.add_dir('[COLOR hotpink]Makers[/COLOR]', site.url + 'jav-makers-list/', 'Makers', site.img_cat)
    site.add_dir('[COLOR hotpink]Most viewed[/COLOR]', site.url + '?orderby=views&order=DESC', 'List', site.img_cat)
    site.add_dir('[COLOR hotpink]Release date[/COLOR]', site.url + '?orderby=rdate&order=DESC', 'List', site.img_cat)
    site.add_dir('[COLOR hotpink]Search[/COLOR]', site.url + '?s=', 'Search', site.img_search)
    List(site.url)
    utils.eod()


@site.register()
def List(url):
    listhtml = _get_html(url, site.url)
    if 'Nothing Found' in listhtml or 'No results' in listhtml:
        utils.notify(msg='Nothing found')
        utils.eod()
        return
    delimiter = '<div class="inside-article">'
    re_videopage = r'class="imgg"><a href="([^"]+)"'
    re_name = r'class="grid1">\s*<h2>\s*<a[^>]*>([^<]+)'
    re_img = r'class="imgg"><a[^>]*>\s*<img[^>]*src="([^"]+)"'
    re_date = r'class="date">([^<]+)<'
    utils.videos_list(site, 'javpog.Playvid', listhtml, delimiter, re_videopage,
                      re_name, re_img, re_duration=re_date, contextm='javpog.Related')
    np = re.search(r'class="next page-numbers"\s+href="([^"]+)"', listhtml, re.DOTALL | re.IGNORECASE)
    if np:
        npurl = np.group(1).replace('&amp;', '&')
        npnr = re.search(r'/page/(\d+)/', npurl)
        lp = re.search(r'class="last"[^>]*href="[^"]*/page/(\d+)/"', listhtml, re.DOTALL | re.IGNORECASE)
        cm_page = (utils.addon_sys + "?mode=javpog.GotoPage&list_mode=javpog.List&url="
                   + urllib_parse.quote_plus(npurl) + "&np=" + (npnr.group(1) if npnr else '')
                   + "&lp=" + (lp.group(1) if lp else '0'))
        cm = [('[COLOR violet]Goto Page #[/COLOR]', 'RunPlugin(' + cm_page + ')')]
        site.add_dir('[COLOR hotpink]Next Page...[/COLOR]', npurl, 'List', site.img_next, contextm=cm)
    utils.eod()


@site.register()
def GotoPage(list_mode, url, np, lp=0):
    dialog = xbmcgui.Dialog()
    pg = dialog.numeric(0, 'Enter Page number')
    if pg:
        if int(lp) > 0 and int(pg) > int(lp):
            utils.notify(msg='Out of range!')
            return
        url = re.sub(r'/page/\d+/', '/page/{0}/'.format(pg), url)
        xbmc.executebuiltin('Container.Update(' + utils.addon_sys + "?mode=" + str(list_mode)
                            + "&url=" + urllib_parse.quote_plus(url) + ')')


@site.register()
def Categories(url):
    cathtml = _get_html(url, site.url)
    match = re.compile(r'href="(https://javpog\.com/category/[^"]+)"[^>]*>([^<]+)</a>', re.DOTALL | re.IGNORECASE).findall(cathtml)
    seen = set()
    for caturl, name in match:
        if caturl in seen:
            continue
        seen.add(caturl)
        site.add_dir(utils.cleantext(name), caturl, 'List', site.img_cat)
    utils.eod()


def _index_links(url, pattern, mode):
    html = _get_html(url, site.url)
    seen = set()
    for link, name in re.compile(pattern, re.DOTALL | re.IGNORECASE).findall(html):
        if link in seen:
            continue
        seen.add(link)
        name = re.sub(r'\s*\(\d+\)\s*$', '', utils.cleantext(name)).strip()
        if name:
            site.add_dir(name, link, mode, site.img_cat)
    np = re.search(r'class="next page-numbers"\s+href="([^"]+)"', html, re.DOTALL | re.IGNORECASE)
    if np:
        site.add_dir('[COLOR hotpink]Next Page...[/COLOR]', np.group(1), mode, site.img_next)
    utils.eod()


@site.register()
def Actresses(url):
    _index_links(url, r'href="(https://javpog\.com/actress/[^"]+)"[^>]*>([^<]+)<', 'List')


@site.register()
def Tags(url):
    _index_links(url, r'href="(https://javpog\.com/tag/[^"]+)"[^>]*>([^<]+)<', 'List')


@site.register()
def Makers(url):
    _index_links(url, r'href="(https://javpog\.com/maker/[^"]+)"[^>]*>([^<]+)<', 'List')


@site.register()
def Search(url, keyword=None):
    if not keyword:
        site.search_dir(url, 'Search')
    else:
        List('{0}{1}'.format(url, urllib_parse.quote_plus(keyword)))


@site.register()
def Related(url):
    html = _get_html(url, site.url)
    block = html.split('<h3>Related videos</h3>')
    if len(block) > 1:
        html = block[1]
    for item in html.split('<li class="post-id-'):
        match = re.search(r'<a href="([^"]+)" class="thumbnail"><img[^>]*src="([^"]+)"', item, re.DOTALL | re.IGNORECASE)
        if not match:
            continue
        nm = re.search(r'title="([^"]+)"', item, re.DOTALL | re.IGNORECASE)
        name = utils.cleantext(nm.group(1)) if nm else ''
        if name:
            site.add_download_link(name, match.group(1), 'Playvid', match.group(2), name)
    utils.eod()


def _resolve_embed(embed, referer, depth=0):
    if depth > 4:
        return None
    if _is_media(embed):
        return _hdr(embed, referer)

    cands = [embed]
    if 'searcho' in embed:
        swap = embed.replace('?dd=', '?dr=').replace('?cd=', '?cr=')
        if swap != embed:
            cands.append(swap)
    if 'vide0' in embed and 'bg=' in embed:
        cands.append(re.sub(r'[?&]bg=[^&]*', '', embed))

    for cand in cands:
        html = _get_html(cand, referer, headers={'Referer': referer, 'Origin': ORIGIN})
        if not html:
            continue
        utils.kodilog('JAVPOG raw ({}) len={} : {}'.format(
            cand, len(html), html[:400].replace('\r', ' ').replace('\n', ' ')))

        # DoodStream (vide0.net & clones) : résolution dédiée
        pm = PASSMD5_RE.search(html)
        if pm:
            link = _doodstream(cand, pm.group(1))
            if link:
                return link

        unpacked = ''
        try:
            unpacked = utils.get_packed_data(html)
        except Exception:
            pass
        full = html + '\n' + unpacked if unpacked else html

        media = _extract_media(full, cand)
        if media:
            return _hdr(media[0], cand)

        for rx in (META_RE, JS_REDIR_RE):
            m = rx.search(full)
            if m:
                nxt = _absolute(m.group(1), cand)
                if nxt and nxt != cand:
                    res = _resolve_embed(nxt, cand, depth + 1)
                    if res:
                        return res

        for src in IFRAME_RE.findall(full):
            nxt = _absolute(src, cand)
            if nxt and nxt != cand:
                res = _resolve_embed(nxt, cand, depth + 1)
                if res:
                    return res

    return None


@site.register()
def Playvid(url, name, download=None):
    vp = utils.VideoPlayer(name, download)
    vp.progress.update(25, "[CR]Loading video page[CR]")
    videohtml = _get_html(url, site.url)
    if not videohtml:
        utils.notify('Oh oh', 'Video page timeout')
        return

    embeds = []
    for b64 in re.findall(r'"iframe_url"\s*:\s*"([^"]+)"', videohtml):
        try:
            embed = base64.b64decode(b64 + '=' * (-len(b64) % 4)).decode('utf-8', 'ignore')
        except Exception:
            continue
        if embed.startswith('http') and embed not in embeds:
            embeds.append(embed)

    # vide0/doodstream d'abord (fiable), searcho (HS) en dernier
    embeds.sort(key=lambda e: 1 if 'searcho' in e else 0)
    utils.kodilog('JAVPOG embeds : {}'.format(embeds))

    direct = None
    for embed in embeds:
        vp.progress.update(50, "[CR]Resolving stream[CR]")
        link = _resolve_embed(embed, url)
        utils.kodilog('JAVPOG embed {} -> {}'.format(embed, link))
        if link:
            direct = link
            break  # <-- on stoppe dès qu'un embed est résolu

    if not direct:
        for src in re.findall(r'<source[^>]+src=["\']([^"\']+)', videohtml, re.IGNORECASE):
            u = _absolute(src, url)
            if u:
                direct = _hdr(u, url)
                break

    if direct:
        vp.play_from_direct_link(direct)
    elif embeds:
        vp.play_from_link_list(embeds)
    else:
        utils.notify('Oh oh', 'No video found')