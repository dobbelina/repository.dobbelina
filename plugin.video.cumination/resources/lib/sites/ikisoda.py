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
from resources.lib.decrypters.kvsplayer import kvs_decode
from resources.lib.adultsite import AdultSite
from urllib.parse import quote

site = AdultSite('ikisoda', '[COLOR hotpink]Ikisoda[/COLOR]', 'https://ikisoda.com/', 'ikisoda.png', 'ikisoda')

addon = utils.addon
perPage = 30

@site.register(default_mode=True)
def Main():
    global perPage
    perPage_setting = utils.addon.getSetting('ikisodaper_page')
    if perPage_setting and perPage_setting.strip() != "":
        perPage = int(perPage_setting)
    else:
        perPage = 30
        utils.addon.setSetting("ikisodaper_page", str(perPage))
    perPage = getPerPage()
    site.add_dir('[COLOR hotpink]Categories[/COLOR]', site.url + 'categories/?items_per_page=120', 'List1', site.img_cat)
    site.add_dir('[COLOR hotpink]Models[/COLOR]', site.url + f'jav-models/?&models_per_page={perPage}&sort_by=video_viewed_count&type=actress', 'List2', site.img_cat)
  
    site.add_dir('[COLOR hotpink]Search[/COLOR]', site.url + 'search/', 'Search', site.img_search)
    List(site.url)


@site.register()
def List(url):
    perPage = getPerPage()

    if '?' in url:
        url += '&videos_per_page={}&sort_by=post_date'.format(perPage)
    else:
        url += '?videos_per_page={}&sort_by=post_date'.format(perPage)    # sort_by=post_date for newers, sort_by=custom1 for popular

    site.add_download_link(
        'Current models per page: [COLOR fuchsia][B]{}[/B][/COLOR] - [COLOR red][B]Change[/B][/COLOR]'.format(perPage), 
        url, 
        'ChangePerPage', 
        '', 
        '', 
        noDownload=True
    )
    listhtml = utils.getHtml(url)
    pattern = re.compile(
        r'<a class="is-item-link is-item-link-video" href="([^"]+)".*?'          # href
        r'data-original="([^"]+)".*?'                                            # image
        r'<div class="is-item-duration[^"]*">([^<]+)</div>.*?'                   # duration
        r'<div class="is-item-title[^"]*">\s*(.*?)\s*</div>.*?'                  # title
        r'<div class="is-info-views">.*?<span>([^<]+)</span>.*?'                 # views
        r'<div class="is-info-rating[^"]*">.*?<span>([^<]+)</span>',             # rating
        re.DOTALL
    )
    matches = pattern.findall(listhtml)
    for videopage, img, duration, name, views, rating in matches:
        name = utils.cleantext(name)
        videopage = site.url[:-1] + videopage if videopage.startswith('/') else videopage
        site.add_download_link(f"{name} [COLOR yellow]({duration})[/COLOR][COLOR hotpink] [{views} views, {rating} rating][/COLOR]", videopage, 'Playvid', img, name)

    np = re.search(
        r'<li\s+class="next".*?<a\s+href="([^"]+)"',
        listhtml,
        re.DOTALL | re.IGNORECASE
    )

    if np:
        np = np.group(1)
        np = np.replace('\t', '').replace('\n', '').replace(' ', '')

        if np.startswith("/"):
            np = site.url[:-1] + np

        nextpage = re.search(r'/(\d+)/', np)
        if nextpage:
            nextpage = nextpage.group(1)
        else:
            nextpage = "?"

        site.add_dir(
            f"Next Page... ({nextpage})",
            np,
            "List",
            site.img_next
        )


    # np = re.compile(r'class="next"\s.*?href="([^"]+)"', re.DOTALL | re.IGNORECASE).search(listhtml)
    # if np:
    #     np = np.group(1)
    #     nextpage = re.search(r'page/(\d+)', np).group(1)
    #     site.add_dir('Next Page... ({0})'.format(nextpage), np, 'List', site.img_next)
    utils.eod()


@site.register()
def List1(url):
    perPage = getPerPage()
    html = utils.getHtml(url)

    pattern = re.compile(
        r'is-item item" href="([^"]+)".*?'                            # href
        r'<img[^>]+src="([^"]+)".*?'                                  # image
        r'<div class="is-item-title[^"]*">\s*(.*?)\s*</div>.*?'       # title
        r'<div class="is-count-videos[^"]*">\s*([^<]+)\s*</div>',     # count videos
        re.DOTALL
    )

    matches = pattern.findall(html)
    for href, img, title, count in matches:
        label = (
            f"[COLOR gold]{title}[/COLOR]  "
            f"[COLOR cyan]{count}[/COLOR]"
        )
        site.add_dir(f"{label}", href + f'?items_per_page={perPage}', 'List', site.img_cat)
    np = re.compile(r'href="([^"]+)">Next<', re.DOTALL | re.IGNORECASE).search(html)
    if np:
        np = np.group(1)
        nextpage = re.search(r'page/(\d+)', np).group(1)
        site.add_dir('Next Page... ({0})'.format(nextpage), np, 'List', site.img_next)
    utils.eod()


@site.register()
def List2(url):
    perPage = getPerPage()
    html = utils.getHtml(url)
    pattern = re.compile(
        r'<div class="is-item b6m-model">.*?'                             # container model
        r'<a[^>]+href="([^"]+)"[^>]*>.*?'                                 # href
        r'data-original="([^"]+)".*?'                                     # image
        r'<div class="is-item-title[^"]*">.*?(?:<span>#\d+</span>\s*)?([^<]+?)\s*</div>.*?'  # name
        r'is-info-count-videos">\s*([^<]+)\s*</div>.*?'                   # count videos
        r'is-info-views">.*?<span>([^<]+)</span>.*?'                      # views
        r'is-info-rating[^"]*">.*?<span>([^<]+)</span>'                   # rating
        , re.DOTALL
    )

    matches = pattern.findall(html)
    for href, img, title, count, views, rating in matches:
        label = (
            f"[COLOR gold]{title}[/COLOR]  "
            f"[COLOR cyan]{count}[/COLOR]"
            f"[COLOR yellow] ({views} views)[/COLOR]"
            f"[COLOR hotpink] [{rating} rating][/COLOR]"
        )

        site.add_dir(f"{label}", href + f'?items_per_page={perPage}', 'List', quote(img, safe=':/'))

    np = re.search(
        r'<li\s+class="next".*?<a\s+href="([^"]+)"',
        html,
        re.DOTALL | re.IGNORECASE
    )

    if np:
        np = np.group(1)
        np = np.replace('\t', '').replace('\n', '').replace(' ', '')

        if np.startswith("/"):
            np = site.url[:-1] + np

        nextpage = re.search(r'/(\d+)/', np)
        if nextpage:
            nextpage = nextpage.group(1)
        else:
            nextpage = "?"

        site.add_dir(
            f"Next Page... ({nextpage})",
            np,
            "List2",
            site.img_next
        )
    utils.eod()


@site.register()
def Search(url, keyword=None):
    if not keyword:
        site.search_dir(url, 'Search')
    else:
        url += keyword.replace(' ', '+')
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


@site.register()
def ChangePerPage(url=None, name=None):
    vq = utils._get_keyboard(heading=utils.i18n('srch_for'))
    if not vq or not vq.isdigit():
        return False
        
    utils.addon.setSetting("ikisodaper_page", str(vq))
    utils.refresh()
    return True

def getPerPage():
    perPage_setting = utils.addon.getSetting('ikisodaper_page')
    if perPage_setting and perPage_setting.strip() != "":
        return int(perPage_setting)
    return 30
