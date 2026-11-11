'''
    Cumination
    Copyright (C) 2021 Team Cumination

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

import re
from six.moves import urllib_parse
from resources.lib import utils
from resources.lib.adultsite import AdultSite

site = AdultSite('perverzija', '[COLOR hotpink]Perverzija[/COLOR]', 'https://tube.perverzija.com/', 'https://tube.perverzija.com/wp-content/uploads/2018/12/favico2.ico', 'perverzija')
site1 = AdultSite('pervtube', '[COLOR hotpink]PervTube[/COLOR]', 'https://pervtube.net/', 'https://pervtube.net/wp-content/uploads/2018/12/cropped-perverzija-usne-192x192.jpg', 'pervtube')


def getBaselink(url):
    if 'perverzija' in url:
        siteurl = site.url
    elif 'pervtube' in url:
        siteurl = site1.url
    else:
        return ''
    return siteurl


@site.register(default_mode=True)
@site1.register(default_mode=True)
def Main(url):
    siteurl = getBaselink(url)
    site.add_dir('[COLOR hotpink]Tags[/COLOR]', siteurl + 'tags/', 'Tag', site.img_tags)
    site.add_dir('[COLOR hotpink]Studios[/COLOR]', siteurl + 'studios/', 'Studios', site.img_cat)
    site.add_dir('[COLOR hotpink]Stars[/COLOR]', siteurl + 'stars/', 'Stars', site.img_star)
    site.add_dir('[COLOR hotpink]Full Movies[/COLOR]', siteurl + 'full-movie/', 'List', site.img_movies)
    site.add_dir('[COLOR hotpink]Search[/COLOR]', siteurl + '?s=', 'Search', site.img_search)
    List(siteurl + 'page/1/')


@site.register()
def List(url):
    listhtml = utils.getHtml(url)
    videos = listhtml.split('class="video-listing-filter"')[-1].split('<div class="item-thumbnail">')
    videos.pop(0)
    for video in videos:
        videourl = re.compile(r'<a href="([^"]+)"', re.DOTALL | re.IGNORECASE).findall(video)[0]
        name = re.compile(r'title="([^"]+)"', re.DOTALL | re.IGNORECASE).findall(video)[0]
        img = re.compile(r'src="([^"]+)"', re.DOTALL | re.IGNORECASE).findall(video)[0]
        name = utils.cleantext(name)
        duration = re.compile(r'time_dur">([^<]+)<', re.DOTALL | re.IGNORECASE).findall(video)
        duration = duration[0] if duration else ''

        contextmenu = []
        contexturl = (utils.addon_sys
                      + "?mode=" + str('perverzija.Lookupinfo')
                      + "&url=" + urllib_parse.quote_plus(videourl))
        contextmenu.append(('[COLOR deeppink]Lookup info[/COLOR]', 'RunPlugin(' + contexturl + ')'))

        site.add_download_link(name, videourl, 'Play', img, name, noDownload=True, contextm=contextmenu, duration=duration)

    nextp = re.compile(r'label="Next\s*Page"\s*href="([^"]+)', re.DOTALL | re.IGNORECASE).search(listhtml)
    if nextp:
        pgtxt = re.compile("""class=["']pages["']>([^<]+)""", re.DOTALL | re.IGNORECASE).findall(listhtml)[0]
        site.add_dir('Next Page... (Currently in {0})'.format(pgtxt), nextp.group(1), 'List', site.img_next)
    utils.eod()


@site.register()
def Tag(url):
    siteurl = getBaselink(url)
    cathtml = utils.getHtml(url)
    match = re.compile(r'(tag/[^"]+)">\s+([^\)]+\))', re.IGNORECASE | re.DOTALL).findall(cathtml)
    for caturl, name in match:
        name = utils.cleantext(name)
        site.add_dir(name, siteurl + caturl, 'List', '')
    utils.eod()


@site.register()
def Studios(url):
    siteurl = getBaselink(url)
    cathtml = utils.getHtml(url)
    match = re.compile(r'(studio/[^"]+)">\s+([^\)]+\))', re.IGNORECASE | re.DOTALL).findall(cathtml)
    for caturl, name in match:
        name = utils.cleantext(name)
        site.add_dir(name, siteurl + caturl, 'List', '')
    utils.eod()


@site.register()
def Stars(url):
    siteurl = getBaselink(url)
    cathtml = utils.getHtml(url)
    match = re.compile(r'(stars/[^"]+)">\s+([^\)]+\))', re.IGNORECASE | re.DOTALL).findall(cathtml)
    for caturl, name in match:
        name = utils.cleantext(name)
        site.add_dir(name, siteurl + caturl, 'List', '')
    utils.eod()


@site.register()
def Lookupinfo(url):
    class PerverzijaLookup(utils.LookupInfo):
        def url_constructor(self, url):
            if 'studio/' in url:
                return url
            if any(x in url for x in ['stars/', 'tag/']):
                return site.url + url

    lookup_list = [
        ("Studio", 'href="([^"]+)" rel="category tag">([^<]+)', ''),
        ("Tag", '(tag/[^"]+)" rel="tag">([^<]+)', ''),
        ("Actor", '(stars/[^"]+)" rel="tag">([^<]+)', ''),
    ]

    lookupinfo = PerverzijaLookup(site.url, url, 'perverzija.List', lookup_list)
    lookupinfo.getinfo()


@site.register()
def Search(url, keyword=None):
    if not keyword:
        site.search_dir(url, 'Search')
    else:
        url = "{0}{1}".format(url, keyword.replace(' ', '%20'))
        List(url)


@site.register()
def Play(url, name, download=None):
    vp = utils.VideoPlayer(name, download=download, IA_check='skip')
    try:
        videohtml = utils.getHtml(url)
        match = re.search(r'''["']player-embed["'][^>]*>\s*<iframe\b[^>]*?\ssrc\s*=\s*["']([^"']+)''', videohtml, re.IGNORECASE | re.DOTALL)
        if not match:
            utils.notify('Perverzija', 'No video player found')
            return
        iframeurl = urllib_parse.urljoin(url, match.group(1).replace('&amp;', '&'))
        host = (urllib_parse.urlsplit(iframeurl).hostname or '').lower()
        if 'xtremestream' in host:
            vp.progress.update(25, "[CR]Loading video page[CR]")
            iframehtml = _fresh_player_text(iframeurl, url)
            vp.progress.update(50, "[CR]Looking for qualities[CR]")
            videourl = _xtremestream_hls(iframeurl, iframehtml)
            if not videourl or vp.progress.iscanceled():
                return
            vp.progress.update(75, "[CR]Loading selected quality[CR]")
            # These are standard AES-128 HLS playlists supplied by the site's
            # Chromecast API. InputStream Adaptive handles PHP segment/key URLs,
            # decryption, audio and the complete VOD seek timeline directly.
            # A native enabled-state check preserves clear prerequisite errors;
            # Cumination performs the full InputStream Helper setup once below.
            if not utils.xbmc.getCondVisibility('System.AddonIsEnabled(inputstream.adaptive)'):
                raise _PlaybackError('Install and enable InputStream Adaptive for XtremeStream playback')
            vp.IA_check = 'IA'
            vp.play_from_direct_link(_hls_play_url(videourl, iframeurl))
        elif vp.resolveurl.HostedMediaFile(iframeurl).valid_url():
            vp.play_from_link_to_resolve(iframeurl)
        else:
            utils.notify('Perverzija', 'This video host is not supported')
    except _PlaybackError as exc:
        utils.kodilog('Perverzija: ' + str(exc))
        utils.notify('Perverzija', str(exc))
    except Exception as exc:
        # Do not include live player/signing tokens in the log or notification.
        utils.kodilog('Perverzija playback failed ({})'.format(type(exc).__name__))
        utils.notify('Perverzija', 'Could not load the video stream. Please retry.')
    finally:
        vp.progress.close()


class _PlaybackError(Exception):
    pass


def _fresh_player_text(url, referer, api=False):
    headers = {'User-Agent': utils.USER_AGENT, 'Accept-Encoding': 'identity',
               'Cache-Control': 'no-cache'}
    if api:
        headers['X-XS-P'] = '1'
    # getHtml caches responses; player and cast tokens must be fetched afresh.
    result = utils._getHtml(url, referer, headers=headers)
    return result.decode('utf-8') if isinstance(result, bytes) else result


def _xtremestream_hls(iframeurl, iframehtml):
    boot = re.search(r'''\bXSFTK\s*\.\s*boot\s*\(\s*['"]([^'"]+)['"]\s*,\s*['"]([^'"]+)['"]''', iframehtml)
    if boot:
        video_id, video_token = boot.groups()
        api_url = urllib_parse.urljoin(iframeurl, '/player/proto_api.php')
        query = {'data': video_id, 'vt': video_token, 'op': 'castsign'}
        cast_token = _fresh_player_text(api_url + '?' + urllib_parse.urlencode(query), iframeurl, api=True).strip()
        if not re.fullmatch(r'[A-Za-z0-9_+./=-]{16,512}', cast_token):
            raise _PlaybackError('Unable to create the XtremeStream playback session')
        query.update(op='castmaster', ct=cast_token)
        playlist_url = api_url + '?' + urllib_parse.urlencode(query)
    else:
        # Keep older XtremeStream player pages working without indexing an
        # unchecked regex result (the cause of the original IndexError).
        video_id = re.search(r'''\bvar\s+video_id\s*=\s*[`'"]([^`'"]+)''', iframehtml, re.IGNORECASE)
        loader = re.search(r'''\bvar\s+m3u8_loader_url\s*=\s*[`'"]([^`'"]+)''', iframehtml, re.IGNORECASE)
        if not video_id or not loader:
            raise _PlaybackError('Unsupported XtremeStream player layout')
        playlist_url = urllib_parse.urljoin(iframeurl, loader.group(1)) + video_id.group(1)

    playlist = _fresh_player_text(playlist_url, iframeurl)
    if not playlist.lstrip('\ufeff\r\n ').startswith('#EXTM3U'):
        raise _PlaybackError('XtremeStream did not return a playable HLS playlist')

    # Retain the complete master when it declares separate audio renditions.
    # Selecting only a video child in that case would discard its audio group.
    if re.search(r'^#EXT-X-MEDIA:.*TYPE=AUDIO', playlist, re.IGNORECASE | re.MULTILINE):
        return playlist_url

    links = {}
    stream_info = None
    for line in playlist.splitlines():
        line = line.strip()
        if line.upper().startswith('#EXT-X-STREAM-INF:'):
            stream_info = line
        elif line and not line.startswith('#') and stream_info:
            resolution = re.search(r'RESOLUTION=\d+x(\d+)', stream_info, re.IGNORECASE)
            if resolution:
                links[resolution.group(1)] = urllib_parse.urljoin(playlist_url, line)
            stream_info = None
    if links:
        return utils.prefquality(links, sort_by=lambda x: int(x), reverse=True)
    if '#EXTINF:' in playlist:
        return playlist_url
    raise _PlaybackError('No playable XtremeStream qualities found')


def _hls_play_url(url, referer):
    if urllib_parse.urlsplit(url).scheme not in ('http', 'https') or any(c in url for c in '|\r\n'):
        raise _PlaybackError('Invalid XtremeStream stream URL')
    # The PHP API accepts this filename hint. Cumination uses the .m3u8 marker
    # to configure InputStream Adaptive with the HLS MIME type and headers.
    if '.m3u8' not in url.lower():
        url += ('&' if '?' in url else '?') + 'filename=stream.m3u8'
    headers = {'User-Agent': utils.USER_AGENT, 'Referer': referer}
    return url + '|' + urllib_parse.urlencode(headers)


# @site.register()
# def Play(url, name, download=None):
#     vp = utils.VideoPlayer(name, download=download, IA_check='skip')
#     videohtml = utils.getHtml(url)
#     match = re.compile(r'"player-embed"\s*>\s*?<iframe.*?src="([^"]+)"', re.IGNORECASE | re.DOTALL).search(videohtml)
#     if match:
#         iframeurl = match.group(1)
#         if 'xtremestream' in iframeurl:
#             vp.progress.update(25, "[CR]Loading video page[CR]")
#             iframehtml = utils.getHtml(iframeurl, url)
#             videoid = re.compile(r'''var\s*video_id\s*=\s*[`'"]([^`'"]+).+?var\s*m3u8_loader_url\s=\s[`'"]([^`'"]+)''', re.IGNORECASE | re.DOTALL).findall(iframehtml)[0]
#             vp.progress.update(50, "[CR]Looking for qualities[CR]")
#             m3u8html = utils.getHtml(videoid[1] + videoid[0], iframeurl)
#             links = re.compile(r"resolution=\d+x(\d+)[^\n]*\n([^\s]+)", re.IGNORECASE | re.DOTALL).findall(m3u8html)
#             links = {key: value for key, value in links}
#             videourl = utils.prefquality(links, sort_by=lambda x: int(x), reverse=True)
#             vp.progress.update(75, "[CR]Loading selected quality[CR]")
#             m3u8html = utils.getHtml(videourl, iframeurl)
#             myplaylist = utils.TRANSLATEPATH("special://temp/myPlaylist.m3u8")
#             with open(myplaylist, 'w') as f:
#                 f.write(m3u8html)
#             myparent = "#EXTM3U\n#EXT-X-VERSION:3\n#EXT-X-STREAM-INF:PROGRAM-ID=1\n{0}".format(myplaylist)
#             videourl = utils.TRANSLATEPATH("special://temp/myParent.mp4")
#             with open(videourl, 'w') as f:
#                 f.write(myparent)
#             vp.play_from_direct_link(videourl)
#         elif vp.resolveurl.HostedMediaFile(iframeurl).valid_url():
#             vp.play_from_link_to_resolve(iframeurl)
#         else:
#             utils.notify('Oh oh', 'No other video hosts supported yet')
#     else:
#         utils.notify('Oh oh', 'No video found')
