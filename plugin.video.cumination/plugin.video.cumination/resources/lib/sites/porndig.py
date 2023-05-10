"""
    Cumination
    Copyright (C) 2016 Whitecream

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
"""

from six.moves import urllib_parse
import re
import json
from resources.lib import utils
from resources.lib.adultsite import AdultSite

site = AdultSite('porndig', '[COLOR hotpink]Porndig[/COLOR] [COLOR white]Professional[/COLOR]', 'https://www.porndig.com/',
                 'porndig.png', 'porndig')
site2 = AdultSite('porndig2', '[COLOR hotpink]Porndig[/COLOR] [COLOR white]Amateurs[/COLOR]', 'http://www.porndig.com/',
                  'porndig.png', 'porndig')

addon = utils.addon
headers = {'User-Agent': utils.USER_AGENT,
           'X-Requested-With': 'XMLHttpRequest'}


@site.register(default_mode=True)
@site2.register(default_mode=True)
def Main(name):
    if 'Amateurs' in name:
        addon.setSetting('pdsection', '1')
    else:
        addon.setSetting('pdsection', '0')
    site.add_dir('[COLOR hotpink]Categories[/COLOR]', site.url + 'videos/', 'Categories', site.img_cat)
    if addon.getSetting("pdsection") == '0':
        site.add_dir('[COLOR hotpink]Studios[/COLOR]', site.url + 'studios/load_more_studios', 'Studios', '', 0)
        site.add_dir('[COLOR hotpink]Pornstars[/COLOR]', site.url + 'pornstars/load_more_pornstars', 'Pornstars', '', 0)
    List(1, 0, 0)


@site.register()
def Categories(url):
    if addon.getSetting("pdsection") == '1':
        url = site.url + 'amateur/videos/'
    urldata = utils.getHtml(url, site.url)
    reobj = re.compile(r'category_slug.+?value="([^"]+).+?>([^<]+)', re.DOTALL | re.IGNORECASE).findall(urldata)
    for catchannel, catname in reobj:
        site.add_dir(utils.cleantext(catname), '', 'List', '', 0, catchannel, 3)
    utils.eod()


def VideoListData(page, channel):
    sort = 'date'
    offset = page * 36
    if addon.getSetting("pdsection") == '1':
        catid = 4
    else:
        catid = 1
    values = {'main_category_id': catid,
              'type': 'post',
              'name': 'category_videos',
              'filters[filter_type]': sort,
              'filters[filter_period]': '',
              'offset': offset}
    return urllib_parse.urlencode(values)


def CatListData(page, channel):
    sort = 'date'
    offset = page * 100
    if addon.getSetting("pdsection") == '1':
        catid = 4
    else:
        catid = 1
    values = {'main_category_id': catid,
              'type': 'post',
              'name': 'category_videos',
              'filters[filter_type]': sort,
              'filters[filter_period]': '',
              'offset': offset,
              'quantity': 100,
              'category_id[]': channel}
    return urllib_parse.urlencode(values)


def VideoListStudio(page, channel):
    sort = 'date'
    offset = page * 30
    values = {'main_category_id': '1',
              'type': 'post',
              'name': 'studio_related_videos',
              'filters[filter_type]': sort,
              'filters[filter_period]': '',
              'offset': offset,
              'content_id': channel}
    return urllib_parse.urlencode(values)


def VideoListPornstar(page, channel):
    sort = 'date'
    offset = page * 30
    values = {'main_category_id': '1',
              'type': 'post',
              'name': 'pornstar_related_videos',
              'filters[filter_type]': sort,
              'filters[filter_period]': '',
              'offset': offset,
              'content_id': channel}
    return urllib_parse.urlencode(values)


def StudioListData(page):
    offset = page * 30
    values = {'main_category_id': '1',
              'type': 'studio',
              'name': 'top_studios',
              'filters[filter_type]': 'likes',
              'starting_letter': '',
              'offset': offset}
    return urllib_parse.urlencode(values)


def PornstarListData(page):
    offset = page * 30
    values = {'main_category_id': '1',
              'type': 'pornstar',
              'name': 'top_pornstars',
              'filters[filter_type]': 'likes',
              'country_code': '',
              'starting_letter': '',
              'offset': offset}
    return urllib_parse.urlencode(values)


@site.register()
def Pornstars(url, page=1):
    data = PornstarListData(page)
    urldata = utils.getHtml(url, site.url, headers, data=data)
    urldata = ParseJson(urldata)
    i = 0
    match = re.compile(r'id="_([\d]+).+?src="([^"?]+).+?alt="([^"]+).+?videos".+?p>([^<]+)',
                       re.DOTALL | re.IGNORECASE).findall(urldata)
    for ID, img, studio, videos in match:
        title = "{0} [COLOR deeppink][I]{1} videos[/I][/COLOR]".format(studio, videos)
        site.add_dir(title, '', 'List', img, 0, ID, 2)
        i += 1
    if i >= 30:
        page += 1
        name = 'Next Page... ({0})'.format(page + 1)
        site.add_dir(name, url, 'Pornstars', site.img_next, page)
    utils.eod()


@site.register()
def Studios(url, page=1):
    data = StudioListData(page)
    urldata = utils.getHtml(url, site.url, headers, data=data)
    urldata = ParseJson(urldata)
    i = 0
    match = re.compile(r'id="_([\d]+).+?src="([^"?]+).+?alt="([^"]+).+?videos".+?p>([^<]+)',
                       re.DOTALL | re.IGNORECASE).findall(urldata)
    for ID, img, studio, videos in match:
        title = "{0} [COLOR deeppink][I]{1} videos[/I][/COLOR]".format(studio, videos)
        site.add_dir(title, '', 'List', img, 0, ID, 1)
        i += 1
    if i >= 30:
        page += 1
        name = 'Next Page... ({0})'.format(page + 1)
        site.add_dir(name, url, 'Studios', site.img_next, page)
    utils.eod()


@site.register()
def List(channel, section, page=0):
    if section == 0:
        data = VideoListData(page, channel)
        maxresult = 36
    elif section == 1:
        data = VideoListStudio(page, channel)
        maxresult = 30
    elif section == 2:
        data = VideoListPornstar(page, channel)
        maxresult = 30
    elif section == 3:
        data = CatListData(page, channel)
        maxresult = 100

    urldata = utils.getHtml(site.url + "posts/load_more_posts", site.url, headers, data=data)
    urldata = ParseJson(urldata)
    i = 0
    match = re.compile(r'<section.+?href="([^"]+)">([^<]+).+?class="([^"]+).+?<img.+?src="([^"]+).+?tion">(?:<span>)?([^<]+)',
                       re.DOTALL | re.IGNORECASE).findall(urldata)
    for url, name, hd, img, duration in match:
        if 'full' in hd:
            hd = "[COLOR yellow]FULLHD[/COLOR]"
        elif '4k' in hd:
            hd = "[COLOR red]4K[/COLOR]"
        elif 'hd' in hd:
            hd = "[COLOR orange]HD[/COLOR]"
        else:
            hd = ""
        url = site.url[:-1] + url
        name = name.replace(u'\u2019', "'")
        site.add_download_link(name, url, 'Playvid', img, name, duration=duration, quality=hd)
        i += 1
    if i >= maxresult and channel:
        page += 1
        name = 'Next Page... ({0})'.format(page + 1)
        site.add_dir(name, '', 'List', site.img_next, page=page, channel=channel, section=section)
    utils.eod()


@site.register()
def Playvid(url, name, download=None):
    vp = utils.VideoPlayer(name, download)
    vp.progress.update(25, "[CR]Loading video page[CR]")
    videopage = utils.getHtml(url, site.url)
    player = re.compile(r'<iframe.+?class=""\s*src="([^"]+)"', re.DOTALL | re.IGNORECASE).findall(videopage)
    if player:
        playerpage = utils.getHtml(player[0], url)
    else:
        vp.progress.close()
        return
    links = re.compile(r'"src":\s*"([^"]+)".+?"label":\s*"([^"]+)"', re.DOTALL | re.IGNORECASE).findall(playerpage)
    links = {x[1].replace('4K', '2160p').replace('UHD', '2160p'): x[0] for x in links}
    videourl = utils.selector('Choose your video', links, setting_valid='qualityask', sort_by=lambda x: int(x[:-1]), reverse=True)
    if not videourl:
        vp.progress.close()
        return
    videourl = videourl.replace("\\", "")
    videourl = utils.getVideoLink(videourl, url)
    vp.play_from_direct_link(videourl)


def ParseJson(urldata):
    urldata = json.loads(urldata)
    return urldata['data']['content']
