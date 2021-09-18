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

from resources.lib import utils
from resources.lib.adultsite import AdultSite

site = AdultSite('javhoho', '[COLOR hotpink]JavHoHo[/COLOR]', 'https://www1.javhoho.com/', 'https://www1.javhoho.com/wp-content/uploads/2019/11/JAVHOHO-logo-x.png', 'javhoho')


@site.register(default_mode=True)
def Main():
    site.add_dir('[COLOR hotpink]Categories[/COLOR]', site.url, 'Cat', site.img_cat)
    site.add_dir('[COLOR hotpink]Search[/COLOR]', site.url + 'search/', 'Search', site.img_search)
    List(site.url + 'all-porn-videos/')


@site.register()
def List(url):
    try:
        listhtml = utils.getHtml(url)
    except:
        return None
    match = re.compile('class="item-thumbnail".+?href="([^"]+)".+?data-lazy-src="([^"]+)".+?title="([^"]+)"', re.DOTALL | re.IGNORECASE).findall(listhtml)
    for videopage, img, name in match:
        name = utils.cleantext(name)
        site.add_download_link(name, videopage, 'Playvid', img, name)
    try:
        next_page = re.compile('href="([^"]+)">&raquo;<').findall(listhtml)[0]
        last_page = re.compile('class="last" href="([^"]+)"').findall(listhtml)
        if last_page:
            last = last_page[0].split('/')[-2]
        page_nr = re.findall(r'\d+', next_page)[-1]
        site.add_dir('Next Page (' + page_nr + ('/' + last if last_page else '') + ')', next_page, 'List', site.img_next)
    except:
        pass
    utils.eod()


@site.register()
def Search(url, keyword=None):
    searchUrl = url
    if not keyword:
        utils.searchDir(url, 314)
    else:
        title = keyword.replace(' ', '%20')
        searchUrl = searchUrl + title
        List(searchUrl)


@site.register()
def Cat(url):
    cathtml = utils.getHtml(url, '')
    cathtml = cathtml.split('id="categories-3"')[-1].split('</div>')[0]
    match = re.compile('href="([^"]+)".*?>([^<]+)<', re.DOTALL | re.IGNORECASE).findall(cathtml)
    for catpage, name in match:
        # name = name + " [COLOR deeppink]" + videos + "[/COLOR]"
        site.add_dir(name, catpage, 'List', '')
    utils.eod()


@site.register()
def Playvid(url, name, download=None):
    vp = utils.VideoPlayer(name, download)
    vp.progress.update(20, "[CR]Loading video page[CR]")

    listhtml = utils.getHtml(url, site.url)
    listhtml = listhtml.split('Free Player<')[1].split('>VIP Download')[0]
    match = re.compile('data-lazy-src="([^"]+)"',).findall(listhtml)
    videoArray = {}
    for item in match:
        vp.progress.update(30, "[CR]Loading video page[CR]")
        if 'javhoho.com' in item:
            item = utils.getVideoLink(item, site.url, get_method=None)
        # if 'hxdrive.xyz' in item:
        #     if '/embed/' not in item:
        #         item = item.replace('hxdrive.xyz/', 'hxdrive.xyz/embed/')
        #     try:
        #         listhtml = utils.getHtml(item)
        #         item = re.compile('<iframe src="([^"]+)"', re.DOTALL).findall(listhtml)[0]
        #         if item.startswith('//'):
        #             item = 'https:' + item
        #     except:
        #         pass
        if 'bitporno' in item:
            try:
                listhtml = utils.getHtml(item)
                videourl = re.compile('file: "(.+?)"', re.DOTALL).findall(listhtml)[0]
                if videourl.startswith('/'):
                    videourl = 'https://www.bitporno.com' + videourl
                videoArray['Bitporno'] = videourl
            except:
                pass
        if 'streamz.cc' in item:
            try:
                listhtml = utils.getHtml(item)
                packed = re.compile(r'(eval\(function\(p,a,c,k,e,d\).+?)\s*</script>', re.DOTALL | re.IGNORECASE).findall(listhtml)[0]
                unpacked = utils.unpack(packed)
                videourl = re.compile("'(http.+?)\\\\'", re.DOTALL | re.IGNORECASE).findall(unpacked)[0]
                videoArray['Streamz.cc'] = videourl
            except:
                pass
        # if 'gdriveplayer.to' in item:
        #     try:
        #         listhtml = utils.getHtml(item)
        #         packed = re.compile(r'(eval\(function\(p,a,c,k,e,d\).+?)\s*</script>', re.DOTALL | re.IGNORECASE).findall(listhtml)[0]
        #         unpacked = utils.unpack(packed)
        #         videourl = re.compile("'(http.+?)'", re.DOTALL | re.IGNORECASE).findall(unpacked)[0]
        #         videoArray['Gdriveplayer.to'] = videourl
        #     except:
        #         pass
        if 'youvideos.ru' in item:
            item = item.replace('youvideos.ru/f/', 'youvideos.ru/v/')
            videoArray['YouVideos.ru'] = item
    if not videoArray:
        utils.notify('Oh oh', 'Couldn\'t find a video')
        return
    choice = utils.selector('Select server', videoArray)
    if not choice:
        return
    videourl = choice
    if 'youvideos.ru' in videourl:
        videourl = videourl.replace('youvideos.ru/v', 'feurl.com/v')
        vp.play_from_link_to_resolve(videourl)
    else:
        vp.play_from_direct_link(videourl)
    return
