'''
    Cumination
    Copyright (C) 2023 Team Cumination

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
from resources.lib import utils
from resources.lib.adultsite import AdultSite

site = AdultSite('yespornvip', '[COLOR hotpink]YesPorn.vip[/COLOR]', 'https://yesporn.vip/', 'yespornvip.webp', 'yespornvip')
# https://yesporn.vip/?mode=async&function=get_block&block_id=list_videos_most_recent_videos&sort_by=post_date&from=1&_=1779432159664
addon = utils.addon


@site.register(default_mode=True)
def Main():
    site.add_dir('[COLOR hotpink]Team Skeet[/COLOR]', site.url + 'channels/team-skeet/', 'List', site.img_cat)
    site.add_dir('[COLOR hotpink]OnlyFans[/COLOR]', site.url + 'channels/onlyfans/', 'List', site.img_cat)
    site.add_dir('[COLOR hotpink]Vixen[/COLOR]', site.url + 'channels/vixen-g7g6z5/', 'List', site.img_cat)
    site.add_dir('[COLOR hotpink]Pure Taboo[/COLOR]', site.url + 'channels/puretaboo-g7g6z5/', 'List', site.img_cat)
    site.add_dir('[COLOR hotpink]Search[/COLOR]', site.url + 'search/', 'Search', site.img_search)
    List(site.url + '?from=1')


@site.register()
def List(url):
    listhtml = utils.getHtml(url)
    match = re.compile(
        r'<div class="thumb thumb_rel item(?![^"]*item--adv-thumb)[^"]*">.*?'
        r'<a\s+href="([^"]+)"\s+title="([^"]+)"[^>]*>.*?'
        r'(?:data-original|data-webp)="([^"]+)"[^>]*>.*?'
        r'<div class="qualtiy">\s*([^<]+)\s*</div>.*?'
        r'<div class="time">\s*([^<]+)\s*</div>.*?'
        r'data-fav-video-id="(\d+)"',
        re.DOTALL | re.IGNORECASE
    ).findall(listhtml)
    import xbmcgui
    # xbmcgui.Dialog().textviewer("Debug", f"Match: {str(match)}")
    for urlpage, name, img, quality, duration, embed in match:
        name = utils.cleantext(name)
        videopage = site.url + 'embed/' + embed
        site.add_download_link(name+ f' [COLOR yellow]({duration})[/COLOR][COLOR hotpink] [{quality}][/COLOR]', videopage, 'Playvid', img, name)

    np = re.compile(r'href="([^"]+)">Next<', re.DOTALL | re.IGNORECASE).search(listhtml)
    if np:
        np = np.group(1)
        nextpage = re.search(r'page/(\d+)', np).group(1)
        site.add_dir('Next Page... ({0})'.format(nextpage), np, 'List', site.img_next)
    utils.eod()


@site.register()
def Search(url, keyword=None):
    if not keyword:
        site.search_dir(url, 'Search')
    else:
        url += keyword.replace(' ', '+')
        List(url + '/')


@site.register()
def Playvid(url, name, download=None):
    vp = utils.VideoPlayer(name, download)
    # vp.play_from_site_link(url, url)
    play_from_kt_player(vp, utils.getHtml(url, site.url), url)


def play_from_kt_player(self, html, url=None):
    from resources.lib.decrypters.kvsplayer import kvs_decode
    license = re.search(r"license_code:\s*'(\$\d+)", html, re.DOTALL | re.IGNORECASE)
    if license:
        license = license.group(1)
    match = re.compile(r"video(?:_|_alt_)url\d?:\s*'([^']+)[^;]+?video(?:_|_alt_)url\d?_text:\s*'([^']+)", re.DOTALL | re.IGNORECASE).findall(html)
    if not match:
        match = re.compile(r"video(?:_|_alt_)url\d?: '([^']+)'.+?postfix\s*:\s*'([^']+)'", re.DOTALL | re.IGNORECASE).findall(html)

    sources = {qual: videourl for videourl, qual in match}
    import xbmcgui
    videourl = list(sources.values())[0]
    '''if len(sources.keys()) == 1:
        videourl = list(sources.values())[0]
    else:
        try:
            videourl = utils.prefquality(sources, sort_by=lambda x: 2160 if x == '4k' else int(x.split('p')[0]), reverse=True)
        except:
            videourl = utils.selector('Select quality', sources, reverse=True)
    xbmcgui.Dialog().textviewer("Debug", f"Sources: {str(sources)}\nSelected URL: {videourl}\nLicense: {license}")
    data = utils.getHtml(videourl, url)
    xbmcgui.Dialog().textviewer("Debug", f"Sources: {str(data)}\nSelected URL: {videourl}\nLicense: {license}")
    videourl_match = re.search(r'file\s*:\s*"([^"]+)"', data, re.DOTALL | re.IGNORECASE)
    xbmcgui.Dialog().textviewer("Debug", f"Sources: {str(videourl_match)}")
    

    if not videourl:
        self.progress.close()
        return
    if '?login' in videourl:
        utils.notify(i18n('oh_oh'), i18n('Login required for this quality.'))
        self.progress.close()
        return'''
    if videourl.startswith('function/0/'):
        if not license:
            utils.notify(i18n('oh_oh'), 'Unable to play video: License code not found')
            self.progress.close()
            return
        from resources.lib.decrypters.kvsplayer import kvs_decode
        videourl = kvs_decode(videourl, license)
    videourl += '|User-Agent={0}&Referer={1}'.format(utils.USER_AGENT, url)

    if not videourl:
        self.progress.close()
        return
    self.play_from_direct_link(videourl)

