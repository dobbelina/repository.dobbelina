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
from resources.lib.jsunpack import unpack
from resources.lib.adultsite import AdultSite

site = AdultSite('rlc', '[COLOR hotpink]Reallifecam.to[/COLOR]', 'https://reallifecam.to/', 'https://reallifecam.to/images/logo/logo.png', 'rlc')
site1 = AdultSite('vh', '[COLOR hotpink]Voyeur-house.to[/COLOR]', 'https://voyeur-house.to/', 'https://voyeur-house.to/images/logo/logo.png', 'vh')
site2 = AdultSite('vhlife', '[COLOR hotpink]Voyeur-house.life[/COLOR]', 'https://voyeur-house.life/', 'https://www.voyeur-house.life/images/logo/logo.png', 'vhlife')
site3 = AdultSite('vhlife1', '[COLOR hotpink]Voyeurhouse.life[/COLOR]', 'https://www.voyeurhouse.life/', 'https://www.voyeurhouse.life/images/logo/logo.png', 'vhlife1')
site4 = AdultSite('camcaps', '[COLOR hotpink]Camcaps.to[/COLOR]', 'https://camcaps.to/', 'https://camcaps.to/images/logo/logo.png', 'camcapsto')


def getBaselink(url):
    if 'reallifecam.to' in url:
        siteurl = site.url
    elif 'voyeur-house.to' in url:
        siteurl = site1.url
    elif 'voyeur-house.life' in url:
        siteurl = site2.url
    elif 'voyeurhouse.life' in url:
        siteurl = site3.url
    elif 'camcaps.to' in url:
        siteurl = site4.url
    return siteurl


@site.register(default_mode=True)
@site1.register(default_mode=True)
@site2.register(default_mode=True)
@site3.register(default_mode=True)
@site4.register(default_mode=True)
def Main(url):
    siteurl = getBaselink(url)
    site.add_dir('[COLOR hotpink]Categories[/COLOR]', siteurl + 'categories', 'Categories', site.img_cat)
    if 'camcaps.to' in url:
        site.add_dir('[COLOR hotpink]Search[/COLOR]', siteurl + 'search/videos/', 'Search', site.img_search)
    else:
        site.add_dir('[COLOR hotpink]Search[/COLOR]', siteurl + 'search/videos?search_query=', 'Search', site.img_search)
    List(siteurl + 'videos?o=mr')


@site.register()
def List(url):
    siteurl = getBaselink(url)
    listhtml = utils.getHtml(url, '')

    match = re.compile(r'col-sm-6.+?<a href="([^"]+)".+?img src="([^"]+)" title="([^"]+)"(.+?)class="duration">\s*([\d:]+)', re.DOTALL | re.IGNORECASE).findall(listhtml)

    for videopage, img, name, quality, duration in match:
        name = utils.cleantext(name)
        if videopage.startswith('/'):
            videopage = siteurl[:-1] + videopage
        hd = 'HD' if '>HD<' in quality else ''
        site.add_download_link(name, videopage, 'Playvid', img, name, duration=duration, quality=hd)
    try:
        next_page = re.compile('href="([^"]+)" class="prevnext"', re.DOTALL | re.IGNORECASE).findall(listhtml)[0]
        page_nr = re.findall(r'\d+', next_page)[-1]
        site.add_dir('Next Page ({})'.format(page_nr), next_page, 'List', site.img_next)
    except:
        pass
    utils.eod()


@site.register()
def Search(url, keyword=None):
    searchUrl = url
    if not keyword:
        site.search_dir(url, 'Search')
    else:
        title = keyword.replace(' ', '%20')
        searchUrl = searchUrl + title
        List(searchUrl)


@site.register()
def Categories(url):
    siteurl = getBaselink(url)
    cathtml = utils.getHtml(url, '')
    if 'reallifecam.to' in url or 'voyeur-house.to' in url:
        match = re.compile('div class="col-sm.+?a href="([^"]+)"(>).+?title-truncate">([^<]+)<.+?class="badge">([^<]+)<', re.DOTALL | re.IGNORECASE).findall(cathtml)
    else:
        match = re.compile(r'col-sm.+?a href="([^"]+)">.+?img src="([^"]+)"\s*title="([^"]+)".+?"float-right">\s*(\d+)\s*<', re.DOTALL | re.IGNORECASE).findall(cathtml)
    for catpage, img, name, videos in match:
        catpage = siteurl[:-1] + catpage if catpage.startswith('/') else catpage
        img = siteurl[:-1] + img if img.startswith('/') else site.img_cat
        name = utils.cleantext(name.strip()).title() + " [COLOR deeppink]" + videos + "[/COLOR]"
        site.add_dir(name, catpage, 'List', img)
    utils.eod()


@site.register()
def Playvid(url, name, download=None):
    vp = utils.VideoPlayer(name, download)
    vp.progress.update(25, "[CR]Loading video page[CR]")
    videopage = utils.getHtml(url)

    match = re.compile(r'class="video-embedded">\s*<iframe[^>]+src="(http[^"]+)"', re.DOTALL | re.IGNORECASE).findall(videopage)
    if match:
        refurl = match[0]
        if '/vtplayer.net/' in refurl:
            refurl = refurl.replace('embed-', '')
        if vp.resolveurl.HostedMediaFile(refurl):
            vp.play_from_link_to_resolve(refurl)
            return
        refpage = utils.getHtml(refurl)
        if '/playerz/' in refurl:
            videourl = re.compile(r'"src":"\.([^"]+)"', re.DOTALL | re.IGNORECASE).findall(refpage)[0]
            videourl = refurl.split('/ss.php')[0] + videourl
            videourlpage = utils.getHtml(videourl)
            vp.direct_regex = '{"file":"([^"]+)"'
            vp.play_from_html(videourlpage)
        else:
            videourl = re.compile(r'>(eval.+?)<\/script>', re.DOTALL | re.IGNORECASE).findall(refpage)[0]
            videourl = unpack(videourl)
            videolink = re.compile('(?:src|file):"([^"]+)"', re.DOTALL | re.IGNORECASE).findall(videourl)
            if match:
                videolink = videolink[0] + '|Referer=' + refurl
                if videolink.startswith('/') and 'vidello' in refurl:
                    videolink = 'https://oracle.vidello.net' + videolink
                vp.play_from_direct_link(videolink)
    else:
        vp.play_from_html(videopage)
