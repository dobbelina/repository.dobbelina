'''
    Cumination
    Copyright (C) 2020 Team Cumination

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''


import glob
import json
import os
import re
import threading
import time
import xbmc
from six.moves import urllib_parse
from resources.lib import utils
from resources.lib.adultsite import AdultSite

site = AdultSite('xvideos', '[COLOR hotpink]xVideos[/COLOR]', 'https://www.xvideos.com/', 'xvideos.png', 'xvideos')


@site.register(default_mode=True)
def Main():
    categories = {'Straight': '', 'Gay': 'gay/', 'Trans': 'shemale/'}
    category = get_setting('category')
    country = get_setting('country')
    site.add_dir('[COLOR hotpink]Country: [/COLOR] [COLOR orange]{}[/COLOR]'.format(country), site.url, 'Country', site.img_cat)
    site.add_dir('[COLOR hotpink]Category: [/COLOR] [COLOR orange]{}[/COLOR]'.format(category), site.url, 'Category', site.img_cat)
    site.add_dir('[COLOR hotpink]Categories[/COLOR]', site.url + categories[category], 'Categories', site.img_cat)
    cat = 'trans/' if category == 'Trans' else categories[category]
    country = country.lower().replace(' ', '_').replace(',', '_') + '/'
    site.add_dir('[COLOR hotpink]Pornstars[/COLOR]', site.url + 'pornstars-index/{}{}from/worldwide'.format(cat, country), 'Pornstars', site.img_cat)
    site.add_dir('[COLOR hotpink]Tags[/COLOR]', site.url + 'tags', 'Tags', site.img_cat)
    cat = 'straight' if category == 'Straight' else categories[category][:-1]
    site.add_dir('[COLOR hotpink]Search[/COLOR]', site.url + '?typef={}&k='.format(cat), 'Search', site.img_search)
    List(site.url + categories[category])
    utils.eod()


@site.register()
def List(url):
    url = update_url(url)
    hdr = dict(utils.base_hdrs)
    hdr['User-Agent'] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:84.0) Gecko/20100101 Firefox/84.0'
    try:
        listhtml = utils.getHtml(url, headers=hdr)
    except:
        return None

    cm_sortby = (utils.addon_sys + "?mode=" + str('xvideos.ContextSortbyFilter'))
    cm_date = (utils.addon_sys + "?mode=" + str('xvideos.ContextDateFilter'))
    cm_length = (utils.addon_sys + "?mode=" + str('xvideos.ContextLengthFilter'))
    cm_quality = (utils.addon_sys + "?mode=" + str('xvideos.ContextQualityFilter'))
    cm_filter = [('[COLOR violet]SortBy[/COLOR] [COLOR orange]{}[/COLOR]'.format(get_setting('sortby')), 'RunPlugin(' + cm_sortby + ')'),
                 ('[COLOR violet]Date[/COLOR] [COLOR orange]{}[/COLOR]'.format(get_setting('date')), 'RunPlugin(' + cm_date + ')'),
                 ('[COLOR violet]Length[/COLOR] [COLOR orange]{}[/COLOR]'.format(get_setting('length')), 'RunPlugin(' + cm_length + ')'),
                 ('[COLOR violet]Quality[/COLOR] [COLOR orange]{}[/COLOR]'.format(get_setting('quality')), 'RunPlugin(' + cm_quality + ')')]

    match = re.compile(r'div id="video.+?href="([^"]+)".+?data-src="([^"]+)"(.+?)title="([^"]+)">.+?duration">([^<]+)<', re.DOTALL | re.IGNORECASE).findall(listhtml)
    for videopage, img, res, name, duration in match:
        match = re.search(r'mark">(.+?)<', res)
        res = match.group(1) if match else ''
        name = utils.cleantext(name)
        img = img.replace('THUMBNUM', '5')

        cm_related = (utils.addon_sys + "?mode=" + str('xvideos.ContextRelated') + "&url=" + urllib_parse.quote_plus(videopage))
        cm = [('[COLOR violet]Related videos[/COLOR]', 'RunPlugin(' + cm_related + ')')]
        if 'k=' in url or '/tags/' in url or '/c/' in url:
            cm += cm_filter

        site.add_download_link(name, site.url[:-1] + videopage, 'Playvid', img, name, contextm=cm, duration=duration, quality=res)
    npage = re.compile(r'href="([^"]+)" class="no-page next-page', re.DOTALL | re.IGNORECASE).findall(listhtml)
    if npage:
        npage = npage[0].replace('&amp;', '&')
        np = re.findall(r'\d+', npage)[-1]
        if url.split(site.url)[-1] in ('', 'gay/', 'shemale/'):
            npage = npage.replace('/2', '/1')
        else:
            np = str(int(np) + 1)
        if npage == '#1':
            npage = url + '/1'
        elif npage.startswith('#'):
            new = npage.split('#')[-1]
            old = str(int(new) - 1)
            npage = url.replace('/{}'.format(old), '/{}'.format(new))
        if not npage.startswith('http'):
            npage = site.url[:-1] + npage
        lp = re.compile(r'>(\d+)<', re.DOTALL | re.IGNORECASE).findall(listhtml.split('next-page')[0])
        if lp:
            lp = '/' + lp[-1]
        else:
            ''
        site.add_dir('Next Page ({}{})'.format(np, lp), npage, 'List', site.img_next)
    if 'No video match with this search.' in listhtml:
        site.add_dir('No videos found. [COLOR hotpink]Clear all filters.[/COLOR]', '', 'ResetFilters', Folder=False, contextm=cm_filter)
    utils.eod()


@site.register()
def ResetFilters():
    utils.addon.setSetting('xvideosdate', 'anytime')
    utils.addon.setSetting('xvideoslen', 'all')
    utils.addon.setSetting('xvideosqual', 'all')
    utils.refresh()
    return


@site.register()
def Category(url):
    categories = {'Straight': '', 'Gay': 'gay/', 'Trans': 'shemale/'}
    oldcat = get_setting('category')
    cat = utils.selector('Select category', categories.keys())
    if cat and cat != oldcat:
        utils.addon.setSetting('xvideoscategory', cat)
        cat = 'straight' if cat == 'Straight' else categories[cat][:-1]
        utils._getHtml(site.url + 'switch-sexual-orientation/' + cat)
        utils.refresh()


@site.register()
def Country(url):
    countries = {'Afghanistan': 'af', 'Argentina': 'ar', 'Australia': 'au', 'Austria': 'at', 'Azerbaijan': 'az', 'Bangladesh': 'bd', 'Belgium': 'be', 'Bolivia': 'bo', 'Brazil': 'br', 'Bulgaria': 'bg', 'Cambodia': 'kh', 'Cameroon': 'cm', 'Canada': 'ca', 'Chile': 'cl', 'China': 'cn', 'Colombia': 'co', 'Cyprus': 'cy', 'Czech Republic': 'cz', 'Denmark': 'dk', 'Dominican Republic': 'do', 'Ecuador': 'ec', 'Egypt': 'eg', 'Finland': 'fi', 'France': 'fr', 'Georgia': 'ge', 'Germany': 'de', 'Greece': 'gr', 'Guatemala': 'gt', 'Hong Kong': 'hk', 'Hungary': 'hu', 'Iceland': 'is', 'India': 'in', 'Indonesia': 'id', 'Iraq': 'iq', 'Ireland': 'ie', 'Israel': 'il', 'Italy': 'it', 'Japan': 'jp', 'Jordan': 'jo', 'Kenya': 'ke', 'Korea': 'kr', 'Lao People\'s Democratic Republic': 'la', 'Latvia': 'lv', 'Lebanon': 'lb', 'Malaysia': 'my', 'Malta': 'mt', 'Mexico': 'mx', 'Moldova, Republic of': 'md', 'Morocco': 'ma', 'Myanmar': 'mm', 'Netherlands': 'nl', 'New Zealand': 'nz', 'Nigeria': 'ng', 'Norway': 'no', 'Pakistan': 'pk', 'Peru': 'pe', 'Philippines': 'ph', 'Poland': 'pl', 'Portugal': 'pt', 'Qatar': 'qa', 'Romania': 'ro', 'Russia': 'ru', 'Senegal': 'sn', 'Serbia': 'rs', 'Singapore': 'sg', 'Slovakia': 'sk', 'South Africa': 'za', 'Spain': 'es', 'Sri Lanka': 'lk', 'Sweden': 'se', 'Switzerland': 'ch', 'Taiwan': 'tw', 'Tanzania, United Republic of': 'tz', 'Thailand': 'th', 'Tunisia': 'tn', 'USA': 'us', 'Ukraine': 'ua', 'United Kingdom': 'gb', 'Venezuela': 've', 'Vietnam': 'vn'}
    country = utils.selector('Select country', countries.keys())
    if country:
        utils.addon.setSetting('xvideoscountry', country)
        curl = '{}change-country/{}'.format(site.url, countries[country])
        utils._getHtml(curl, site.url)
        utils.clear_cache()
        utils.refresh()


@site.register()
def Categories(url):
    cathtml = utils.getHtml(url)
    match = re.compile(r'href="([^"]+)">([^<]+)<[^"]+class="dyn', re.DOTALL | re.IGNORECASE).findall(cathtml)
    for catpage, name in sorted(match, key=lambda x: x[1]):
        site.add_dir(name, site.url[:-1] + catpage, 'List', site.img_cat)
    utils.eod()


@site.register()
def PSList(url):
    hdr = dict(utils.base_hdrs)
    hdr['User-Agent'] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:84.0) Gecko/20100101 Firefox/84.0'
    try:
        listhtml = utils.getHtml(url, headers=hdr)
    except:
        return None
    jdata = json.loads(listhtml)
    for video in jdata["videos"]:
        videopage = video['u']
        name = utils.cleantext(video['t'] if utils.PY3 else video['t'].encode('utf-8'))
        namef = utils.cleantext(video['tf'] if utils.PY3 else video['tf'].encode('utf-8'))
        duration = video['d']
        img = video['i'].replace(r'\/', '/')
        quality = ''
        if video['td'] == 1:
            quality = '1440p'
        elif video['hp'] == 1:
            quality = '1080p'
        elif video['h'] == 1:
            quality = '720p'
        elif video['hm'] == 1:
            quality = '480p'
        else:
            quality = '360p'
        cm_related = (utils.addon_sys + "?mode=" + str('xvideos.ContextRelated') + "&url=" + urllib_parse.quote_plus(videopage))
        cm = [('[COLOR violet]Related videos[/COLOR]', 'RunPlugin(' + cm_related + ')')]
        site.add_download_link(name, site.url[:-1] + videopage, 'Playvid', img, namef, contextm=cm, duration=duration, quality=quality)

    videos = jdata["nb_videos"]
    videospp = jdata["nb_per_page"]
    cp = jdata["current_page"]
    # page = page if page else 0
    np = int(cp) + 1
    npage = url + '/1' if cp == 0 else url.replace('/' + str(cp), '/' + str(np))
    lp = int(int(videos) / float(videospp)) + 1
    np += 1
    if lp >= np:
        site.add_dir('Next Page ({}/{})'.format(np, lp), npage, 'PSList', site.img_next)
    utils.eod()


@site.register()
def Pornstars(url):
    try:
        cathtml = utils.getHtml(url)
    except:
        return None
    match = re.compile(r'div id="profile.+?src="([^"]+)".+?href="([^"]+)">([^<]+)<\/a><\/p>.+?(\d+ videos)', re.DOTALL | re.IGNORECASE).findall(cathtml)
    for img, catpage, name, videos in match:
        name = '{} [COLOR deeppink]{}[/COLOR]'.format(name, videos)
        catpage += '/videos/best'
        site.add_dir(name, site.url[:-1] + catpage, 'PSList', img)
    npage = re.compile(r'href="([^"]+)" class="no-page next-page', re.DOTALL | re.IGNORECASE).findall(cathtml)
    if npage:
        npage = npage[0].replace('&amp;', '&')
        np = re.findall(r'\d+', npage)[-1]
        np = int(np) + 1
        site.add_dir('Next Page ({})'.format(np), site.url[:-1] + npage, 'Pornstars', site.img_next)
    utils.eod()


@site.register()
def Tags(url):
    category = get_setting('category')
    try:
        cathtml = utils.getHtml(url)
    except:
        return None
    match = re.compile(r'href="([^"]+)"><b>([^<]+)</b>.+?>([^<]+)<', re.DOTALL | re.IGNORECASE).findall(cathtml)
    for catpage, name, count in match:
        name = utils.cleantext(name) + "[COLOR deeppink] " + count + "[/COLOR]"
        if '/t:' in catpage:
            catpage = re.sub(r'/t:\w+/', '/', catpage)
        if category == 'Gay':
            catpage = catpage.replace('/tags/', '/tags/t:gay/')
        elif category == 'Trans':
            catpage = catpage.replace('/tags/', '/tags/t:shemale/')
        site.add_dir(name, site.url[:-1] + catpage, 'List', site.img_next)
    utils.eod()


@site.register()
def Playvid(url, name, download=None):
    vp = utils.VideoPlayer(name, download, 'src=&quot;([^&]+)&quot;', direct_regex="html5player\.setVideoHLS\('([^']+)'")
    vp.progress.update(25, "[CR]{0}[CR]".format(utils.i18n('load_vpage')))
    html = utils.getHtml(url, site.url)
    if 'html5player.setVideoHLS' not in html:
        if not download:
            m3u8 = get_interactive_m3u8(html)
            if m3u8:
                stream = serve_interactive_m3u8(m3u8)
                if not stream:
                    stream = m3u8
                vp.progress.close()
                utils.playvid(stream, name, IA_check='IA')
                return
        vp.direct_regex = 'contentUrl": "([^"]+)'
    vp.play_from_html(html, url)


def serve_interactive_m3u8(m3u8):
    """Serve the stitched playlist over a local HTTP server so
    inputstream.adaptive can play it (native Kodi HLS cannot handle the
    fMP4 scenes these videos use)."""
    if not utils.PY3:
        return None
    try:
        from http.server import HTTPServer, SimpleHTTPRequestHandler
    except ImportError:
        return None
    directory = os.path.dirname(m3u8)

    class Handler(SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            SimpleHTTPRequestHandler.__init__(self, *args, directory=directory, **kwargs)

        def log_message(self, *args, **kwargs):
            pass

    try:
        server = HTTPServer(('127.0.0.1', 0), Handler)
    except OSError:
        return None
    threading.Thread(target=server.serve_forever).start()
    threading.Thread(target=lambda: time.sleep(300)).start()
    return 'http://127.0.0.1:{}/{}'.format(server.server_port, os.path.basename(m3u8))


def get_interactive_m3u8(html):
    """Interactive videos expose only a 360p linear mp4 plus scene-based HD
    streams (IVP player). Stitch every scene's best variant into a single local
    HLS so the whole video plays as one stream in HD."""
    try:
        embed = re.compile(r'<iframe src="(https://[^"]+embed\.html)"', re.DOTALL | re.IGNORECASE).findall(html)
        if not embed:
            return None
        embedhtml = utils.getHtml(embed[0], site.url)
        scenario = re.compile(r"""scenario:\s*['"]([^'"]+)['"]""", re.DOTALL | re.IGNORECASE).findall(embedhtml)
        if not scenario:
            return None
        scenariohtml = utils.getHtml(scenario[0], embed[0])
        data = json.loads(scenariohtml)
        assets = data.get('assetsUrl', '').rstrip('/')
        scene_ids = [s['id'] for s in data.get('scenes', []) if s.get('id') and s.get('kind') not in ('intro', 'external')]
        if not scene_ids:
            return None

        lines = ['#EXTM3U', '#EXT-X-VERSION:7', '#EXT-X-TARGETDURATION:120']
        found = 0
        for sid in scene_ids:
            master_url = '{}/{}/master.m3u8'.format(assets, sid)
            try:
                master = utils.getHtml(master_url, site.url)
            except Exception:
                master = None
            variant = best_variant(master)
            if not variant:
                continue
            master_base = master_url.rsplit('/', 1)[0]
            varurl = master_base + '/' + variant
            playlist = utils.getHtml(varurl, site.url)
            var_base = varurl.rsplit('/', 1)[0]
            segments = []
            init_url = None
            for line in playlist.splitlines():
                line = line.strip()
                if line.startswith('#EXT-X-MAP:'):
                    m = re.search(r'URI="([^"]+)"', line)
                    if m:
                        init_url = m.group(1)
                        if not init_url.startswith('http'):
                            init_url = var_base + '/' + init_url
                elif line and not line.startswith('#'):
                    segments.append(line if line.startswith('http') else var_base + '/' + line)
            extinf = re.findall(r'#EXTINF:([0-9.]+)', playlist)
            if not segments or not extinf:
                continue
            if found:
                lines.append('#EXT-X-DISCONTINUITY')
            if init_url:
                lines.append('#EXT-X-MAP:URI="{}"'.format(init_url))
            for j in range(min(len(segments), len(extinf))):
                lines.append('#EXTINF:{},'.format(extinf[j]))
                lines.append(segments[j])
            found += 1
        if not found:
            return None
        lines.append('#EXT-X-ENDLIST')
        tempdir = utils.TRANSLATEPATH('special://temp/')
        for stale in glob.glob(os.path.join(tempdir, 'xvideos_interactive_*.m3u8')):
            try:
                os.remove(stale)
            except OSError:
                pass
        path = os.path.join(tempdir, 'xvideos_interactive_{}.m3u8'.format(os.getpid()))
        with open(path, 'w') as f:
            f.write('\n'.join(lines))
        return path
    except Exception:
        return None


def best_variant(master):
    if not master:
        return None
    variants = []
    for i, line in enumerate(master.splitlines()):
        if line.startswith('#EXT-X-STREAM-INF'):
            uri = master.splitlines()[i + 1].strip() if i + 1 < len(master.splitlines()) else ''
            if uri and not uri.startswith('#'):
                mres = re.search(r'RESOLUTION=(\d+)x(\d+)', line)
                mband = re.search(r'BANDWIDTH=(\d+)', line)
                mcodec = re.search(r'CODECS="([^"]+)"', line)
                codecs = mcodec.group(1) if mcodec else ''
                variants.append({
                    'height': int(mres.group(2)) if mres else 0,
                    'bandwidth': int(mband.group(1)) if mband else 0,
                    'avc': 'avc1' in codecs,
                    'uri': uri,
                })
    if not variants:
        return None
    h264 = [v for v in variants if v['avc']]
    candidates = h264 if h264 else variants
    return max(candidates, key=lambda v: (v['height'], v['bandwidth']))['uri']


@site.register()
def Search(url, keyword=None):
    searchUrl = url
    if not keyword:
        site.search_dir(url, 'Search')
    else:
        title = keyword.replace(' ', '+')
        searchUrl = searchUrl + title
        List(searchUrl)


def get_setting(x):
    ret = ''
    if x == 'sortby':
        ret = utils.addon.getSetting('xvideossortby') if utils.addon.getSetting('xvideossortby') else 'relevance'
    if x == 'date':
        ret = utils.addon.getSetting('xvideosdate') if utils.addon.getSetting('xvideosdate') else 'anytime'
    if x == 'length':
        ret = utils.addon.getSetting('xvideoslen') if utils.addon.getSetting('xvideoslen') else 'all'
    if x == 'quality':
        ret = utils.addon.getSetting('xvideosqual') if utils.addon.getSetting('xvideosqual') else 'all'
    if x == 'country':
        ret = utils.addon.getSetting('xvideoscountry') if utils.addon.getSetting('xvideoscountry') else 'USA'
    if x == 'category':
        ret = utils.addon.getSetting('xvideoscategory') if utils.addon.getSetting('xvideoscategory') else 'Straight'
    return ret


@site.register()
def ContextSortbyFilter():
    filters = {'relevance': 1, 'uploaddate': 2, 'rating': 3, 'length': 4, 'views': 5, 'random': 6}
    cat = utils.selector('Select date', filters.keys(), sort_by=lambda x: filters[x])
    if cat:
        utils.addon.setSetting('xvideossortby', cat)
        utils.refresh()


@site.register()
def ContextDateFilter():
    filters = {'anytime': 1, 'today': 2, 'week': 3, 'month': 4, '3month': 5, '6month': 6}
    cat = utils.selector('Select date', filters.keys(), sort_by=lambda x: filters[x])
    if cat:
        cat = 'all' if cat == 'Anytime' else cat
        utils.addon.setSetting('xvideosdate', cat)
        utils.refresh()


@site.register()
def ContextLengthFilter():
    filters = {'all': 1, '1-3min': 2, '3-10min': 3, '10min_more': 4, '10-20min': 5, '20min_more': 6}
    cat = utils.selector('Select length', filters.keys(), sort_by=lambda x: filters[x])
    if cat:
        utils.addon.setSetting('xvideoslen', cat)
        utils.refresh()


@site.register()
def ContextQualityFilter():
    filters = {'all': 1, 'hd': 2}
    cat = utils.selector('Select quality', filters.keys(), sort_by=lambda x: filters[x])
    if cat:
        utils.addon.setSetting('xvideosqual', cat)
        utils.refresh()


@site.register()
def ContextRelated(url):
    contexturl = (utils.addon_sys
                  + "?mode=" + str('xvideos.ListRelated')
                  + "&url=" + urllib_parse.quote_plus(url))
    xbmc.executebuiltin('Container.Update(' + contexturl + ')')


@site.register()
def ListRelated(url):
    url = site.url[:-1] + url
    html = utils.getHtml(url, site.url)
    jhtml = html.split('video_related=[')[-1].split('];')[0]
    jdata = json.loads('[' + jhtml + ']')
    for video in jdata:
        videopage = video['u']
        name = utils.cleantext(video['t'] if utils.PY3 else video['t'].encode('utf-8'))
        namef = utils.cleantext(video['tf'] if utils.PY3 else video['tf'].encode('utf-8'))
        duration = video['d']
        img = video['i'].replace(r'\/', '/')
        quality = ''
        if video['td'] == 1:
            quality = '1440p'
        elif video['hp'] == 1:
            quality = '1080p'
        elif video['h'] == 1:
            quality = '720p'
        elif video['hm'] == 1:
            quality = '480p'
        else:
            quality = '360p'
        cm_related = (utils.addon_sys + "?mode=" + str('xvideos.ContextRelated') + "&url=" + urllib_parse.quote_plus(videopage))
        cm = [('[COLOR violet]Related videos[/COLOR]', 'RunPlugin(' + cm_related + ')')]
        site.add_download_link(name, site.url[:-1] + videopage, 'Playvid', img, namef, contextm=cm, duration=duration, quality=quality)
    utils.eod()


def update_url(url):
    sortby = get_setting('sortby')
    date = get_setting('date')
    length = get_setting('length')
    quality = get_setting('quality')
    if 'k=' in url:
        if (sortby == 'relevance' and 'sort=' in url) or (sortby != 'relevance' and 'sort=' + sortby not in url):
            url = re.sub(r'[\?&]sort=[^\?&]+', '', url)
            url = re.sub(r'[\?&]p=[^\?&]+', '', url)
            url += '&sort=' + sortby if sortby != 'relevance' else ''
        if (date == 'anytime' and 'datef=' in url) or (date != 'anytime' and 'datef=' + date not in url):
            url = re.sub(r'[\?&]datef=[^\?&]+', '', url)
            url = re.sub(r'[\?&]p=[^\?&]+', '', url)
            url += '&datef=' + date if date != 'anytime' else ''
        if (length == 'all' and 'durf=' in url) or (length != 'all' and 'durf=' + length not in url):
            url = re.sub(r'[\?&]durf=[^\?&]+', '', url)
            url = re.sub(r'[\?&]p=[^\?&]+', '', url)
            url += '&durf=' + length if length != 'all' else ''
        if (quality == 'all' and 'quality=' in url) or (quality != 'all' and 'quality=' + quality not in url):
            url = re.sub(r'[\?&]quality=[^\?&]+', '', url)
            url = re.sub(r'[\?&]p=[^\?&]+', '', url)
            url += '&quality=' + quality if quality != 'all' else ''

    if '/tags/' in url:
        type = 'tags'
    elif '/c/' in url:
        type = 'c'
    else:
        type = ''

    if type:
        if (quality == 'all' and '/q:' in url) or (quality != 'all' and '/q:' + quality not in url):
            url = re.sub(r'/q:[^/]+', '', url)
            url = re.sub(r'/\d+$', '', url)
            if quality != 'all':
                url = url.replace(site.url + type, site.url + type + '/q:' + quality)
        if (length == 'all' and '/d:' in url) or (length != 'all' and '/d:' + length not in url):
            url = re.sub(r'/d:[^/]+', '', url)
            url = re.sub(r'/\d+$', '', url)
            if length != 'all':
                url = url.replace(site.url + type, site.url + type + '/d:' + length)
        if (date == 'anytime' and '/m:' in url) or (date != 'anytime' and '/m:' + date not in url):
            url = re.sub(r'/m:[^/]+', '', url)
            if type != 'tags':
                url = re.sub(r'/\d+$', '', url)
            if date != 'anytime':
                url = url.replace(site.url + type, site.url + type + '/m:' + date)
        if (sortby == 'relevance' and '/s:' in url) or (sortby != 'relevance' and '/s:' + sortby not in url):
            url = re.sub(r'/s:[^/]+', '', url)
            url = re.sub(r'/\d+$', '', url)
            if sortby != 'relevance':
                url = url.replace(site.url + type, site.url + type + '/s:' + sortby)

    return url
