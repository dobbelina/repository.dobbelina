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
from resources.lib.decrypters.kvsplayer import kvs_decode

site = AdultSite('yourlesbians', '[COLOR hotpink]YourLesbians[/COLOR]', 'https://yourlesbians.com/', 'yourlesbians.png', 'yourlesbians')

addon = utils.addon

@site.register(default_mode=True)
def Main():
    site.add_dir('[COLOR hotpink]Search[/COLOR]', site.url + 'search/', 'Search', site.img_search)
    # site.add_dir('[COLOR hotpink]Categories[/COLOR]', site.url + 'categories/&sort_by=avg_videos_rating&from=1', 'Categories', site.img_cat)

    List(site.url + 'lesbian-videos/')


@site.register()
def List(url):
    listhtml = utils.getHtml(url)
    pattern = re.compile(
        r'class="thumb thumb_rel item.*?href="([^"]+)".*?title="([^"]+)".*?data-original="([^"]+)".*?time">([^>]+)<'
        , re.DOTALL | re.IGNORECASE
    )
    matches = pattern.findall(listhtml)
    if not matches:
        utils.notify('YourLesbians', 'No videos found.')
        return
    for videopage, name, img, duration in matches:
        name = utils.cleantext(name)    # + ' [COLOR hotpink][{0}][/COLOR]'.format(duration)
        site.add_download_link(name, videopage, 'Playvid', img, name, duration=duration)

    np = re.compile(r'>\.\.\.<.*?data-parameters="([^"]+):([^:]+)">.*?[from_albums|from]:(\d+)">.*Next'
        , re.DOTALL | re.IGNORECASE).search(listhtml)
    if np:
        # nplink = np.group(2) if np.group(2).startswith('http') else site.url[:-1] + np.group(2)
        nplink = np.group(1).replace(':', '=').replace(';', '&').replace('+from_albums', '')
        nplink = (url.split('?')[0] if '?' in url else url) + '?' + nplink + '=' + np.group(3)
        nextpage = np.group(3)
        lastpage = np.group(2)
        if int(nextpage) < int(lastpage):
            site.add_dir('Next Page... ({0} of {1})'.format(nextpage, lastpage), nplink, 'List', site.img_next)
        
    utils.eod()

""" 
<div class="thumb item">
        <a href="https://yourlesbians.com/categories/lesbian-hentai-porn/" title="Lesbian Hentai">
          <div class="img-holder">
                          <img class="lazy-load" src="https://yourlesbians.com/contents/categories/130/s1_hentai.jpg" alt="Lesbian Hentai" style="display: block;">
                        <div class="cat-title">
              <div class="title">Lesbian Hentai</div>
                              <div class="thumb-item">
                  <i><svg class="svg-icon icon-play"><use xlink:href="#icon-play"></use></svg></i>
                  3
                </div>

                <div class="thumb-item">
                  <i><svg class="svg-icon icon-like"><use xlink:href="#icon-like"></use></svg></i>
                                                      100%
                </div>
                          </div>
          </div>
        </a>
      </div>
"""
@site.register()
def Categories(url):
    listhtml = utils.getHtml(url)
    pattern = re.compile(
        r'<h1(.+?)</h1>'      #\s+title="([^"]+)"'
        # r'.*?data-original="([^"]+)"'
        # r'.*?</i>\s*([\d]+)'
        , re.DOTALL | re.IGNORECASE
    )
    matches = pattern.findall(listhtml)
    if not matches:
        utils.notify('YourLesbians', 'No videos found.')
        return
    for videopage, name, img, duration in matches:
        name = utils.cleantext(name)    # + ' [COLOR hotpink][{0}][/COLOR]'.format(duration)
        site.add_download_link(name, videopage, 'Playvid', img, name, duration=duration)

    np = re.compile(r'>\.\.\.<.*?data-parameters="([^"]+):([^:]+)">.*?[from_albums|from]:(\d+)">.*Next'
        , re.DOTALL | re.IGNORECASE).search(listhtml)
    if np:
        # nplink = np.group(2) if np.group(2).startswith('http') else site.url[:-1] + np.group(2)
        nplink = np.group(1).replace(':', '=').replace(';', '&').replace('+from_albums', '')
        nplink = (url.split('?')[0] if '?' in url else url) + '?' + nplink + '=' + np.group(3)
        nextpage = np.group(3)
        lastpage = np.group(2)
        if int(nextpage) < int(lastpage):
            site.add_dir('Next Page... ({0} of {1})'.format(nextpage, lastpage), nplink, 'List', site.img_next)
        
    utils.eod()


@site.register()
def Search(url, keyword=None):
    if not keyword:
        site.search_dir(url, 'Search')
    else:
        url += keyword.replace(' ', '-') + '/?q=' + keyword.replace(' ', '+') + '&category_ids=&sort_by=&from_videos=1&from_albums=1'
        List(url)


@site.register()
def Playvid(url, name, download=None):
    utils.kodilog('porntn Playvid: ' + url)
    vp = utils.VideoPlayer(name, download)
    vp.progress.update(25, "[CR]Loading video page[CR]")
    html = utils.getHtml(url, site.url)
    sources = {}
    license = re.compile(r"license_code:\s*'([^']+)", re.DOTALL | re.IGNORECASE).findall(html)[0]
    patterns = [
                r"video_url:\s*'([^']+)'.*?(?:video_url_text:\s*'([^']+)')?",
                r"video_alt_url:\s*'([^']+)[^;]+?video_alt_url_text:\s*'([^']+)",
                r"video_alt_url2:\s*'([^']+)[^;]+?video_alt_url2_text:\s*'([^']+)",
                r"video_url:\s*'([^']+)',\s*postfix:\s*'\.mp4',\s*(preview)"]
    for pattern in patterns:
        items = re.compile(pattern, re.DOTALL | re.IGNORECASE).findall(html)
        for surl, qual in items:
            qual = '00' if (qual or '480p') == 'preview' else (qual or '480p')
            qual = qual.replace(' HD', '')
            surl = kvs_decode(surl, license)
            sources[qual] = surl
    videourl = utils.selector('Select quality', sources, setting_valid='qualityask', sort_by=lambda x: 1081 if x == '4k' else int(x[:-1]), reverse=True)

    if not videourl:
        vp.progress.close()
        return
    vp.play_from_direct_link(videourl + '|referer=' + url)


