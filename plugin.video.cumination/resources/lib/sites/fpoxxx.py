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

site = AdultSite('fpoxxx', '[COLOR hotpink]FPOXXX[/COLOR]', 'https://www.fpo.xxx/', 'fpoxxx.png', 'fpoxxx')

addon = utils.addon

@site.register(default_mode=True)
def Main():
    site.add_dir('[COLOR hotpink]Pornstars[/COLOR]', site.url + 'models-2/?sort_by=today_videos&from=1', 'Pornstars', site.img_cat)
    site.add_dir('[COLOR hotpink]Search[/COLOR]', site.url + 'search/', 'Search', site.img_search)
    List(site.url + '?&sort_by=post_date&from=1')


@site.register()
def List(url):
    listhtml = utils.getHtml(url)
    pattern = re.compile(
        r'class="item  ">.*?href="([^"]+)".*?'
        r'title="([^"]+)".*?'
        r'data-original="([^"]+)".*?duration">([^>]+)</span>'
        , re.DOTALL | re.IGNORECASE
    )
    matches = pattern.findall(listhtml)
    if not matches:
        utils.notify('FPOXXX', 'No videos found.')
        return
    for videopage, name, img, duration in matches:
        name = utils.cleantext(name) + ' [COLOR hotpink][{0}][/COLOR]'.format(duration)
        site.add_download_link(name, videopage, 'Playvid', img, name, duration=duration)

    if 'search/' in url:
        search_np = url.split('search/')[1].split('?')[0][:-1]
        next_np = str(int(url.split('from_albums=')[1]) + 1)
        np = re.compile(r'class="last">.*?data-parameters="q:([^:]+);.*?from_videos\+from_albums:([^:]+)">Last.*?from_videos\+from_albums:([^:]+)">Next.*?'
            , re.DOTALL | re.IGNORECASE).search(listhtml)
        if np:
            nplink =np.group(1).replace('%2F', '/')
            nplink = site.url + 'search/' + search_np + '/?q=' + search_np + '&from_videos=' + next_np + '&from_albums=' + next_np
            lastpage = np.group(2)
            nextpage = np.group(3)
            if int(next_np) < int(lastpage):
                site.add_dir('Next Page... ({0} of {1})'.format(next_np, lastpage), nplink, 'List', site.img_next)

    else:
        np = re.compile(r'class="last">.*?;from:([^:]+)">Last.*?href="([^"]+)".*?;from:([^:]+)">Next'
            , re.DOTALL | re.IGNORECASE).search(listhtml)
        if np:
            nplink = np.group(2) if np.group(2).startswith('http') else site.url[:-1] + np.group(2)
            lastpage = np.group(1)
            nextpage = np.group(3)
            site.add_dir('Next Page... ({0} of {1})'.format(nextpage, lastpage), nplink, 'List', site.img_next)
    utils.eod()

@site.register()
def ListStars(url):
    listhtml = utils.getHtml(url)
    pattern = re.compile(
        r'class="item  ">.*?href="([^"]+)".*?'
        r'title="([^"]+)".*?'
        r'data-original="([^"]+)".*?duration">([^>]+)</span>'
        , re.DOTALL | re.IGNORECASE
    )
    matches = pattern.findall(listhtml)
    if not matches:
        utils.notify('FPOXXX', 'No videos found.')
        return
    for videopage, name, img, duration in matches:
        name = utils.cleantext(name) + ' [COLOR hotpink][{0}][/COLOR]'.format(duration)
        site.add_download_link(name, videopage, 'Playvid', img, name, duration=duration)

    np = re.compile(r'class="last">.*?;from:([^:]+)">Last.*?href="([^"]+)".*?;from:([^:]+)">Next'
        , re.DOTALL | re.IGNORECASE).search(listhtml)
    if np:
        nplink = np.group(2) if np.group(2).startswith('http') else site.url[:-1] + np.group(2)
        next_np = url.split('from=')[1]
        next_np = str(int(next_np) + 1)
        nplink = url.split('?')[0] + '?sort_by=today_videos&from=' + next_np

        lastpage = np.group(1)
        if int(next_np) < int(lastpage):
            site.add_dir('Next Page... ({0} of {1})'.format(next_np, lastpage), nplink, 'ListStars', site.img_next)
    utils.eod()


@site.register()
def Pornstars(url):
    listhtml = utils.getHtml(url)
    pattern = re.compile(
        r'class="item" href="([^"]+)" title="([^"]+)".*?src="([^"]+)".*?videos">([^>]+)</div>'
        , re.DOTALL | re.IGNORECASE
    )
    matches = pattern.findall(listhtml)
    if not matches:
        utils.notify('FPOXXX', 'No videos found.')
        return
    for videopage, name, img, duration in matches:
        name = utils.cleantext(name) + ' [COLOR hotpink][{0}][/COLOR]'.format(duration)
        site.add_dir(name, videopage + '?sort_by=post_date&from=1', 'ListStars', img)

    np = re.compile(r'class="last">.*?;from:([^:]+)">Last.*?href="([^"]+)".*?;from:([^:]+)">Next'
        , re.DOTALL | re.IGNORECASE).search(listhtml)
    if np:
        nplink = np.group(2) if np.group(2).startswith('http') else site.url[:-1] + np.group(2)
        lastpage = np.group(1)
        nextpage = np.group(3)
        site.add_dir('Next Page... ({0} of {1})'.format(nextpage, lastpage), nplink, 'Pornstars', site.img_next)
    utils.eod()


@site.register()
def Search(url, keyword=None):
    if not keyword:
        site.search_dir(url, 'Search')
    else:
        url += keyword.replace(' ', '-') + '/?q=' + keyword.replace(' ', '+') + '&from_videos=1&from_albums=1'
        List(url)


@site.register()
def Playvid(url, name, download=None):
    vp = utils.VideoPlayer(name, download)
    html = utils.getHtml(url)
    
    license = re.search(r"license_code:\s*'(\$\d+)",html, flags=re.DOTALL | re.IGNORECASE)
    video_url = re.search(r"video_url:\s*'([^']+)",html, flags=re.DOTALL | re.IGNORECASE)
    
    if license and video_url:
        lc = license.group(1)
        vu = video_url.group(1)
        
        final_url = kvs_decode(vu, lc)
   
        final_url += '|User-Agent={0}&Referer={1}'.format(utils.USER_AGENT, url)
        vp.play_from_direct_link(final_url)
    else:
        vp.play_from_site_link(url + ('/' if not url.endswith('/') else ''))

