'''
    Cumination
    Copyright (C) 2015 Whitecream

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
import json
from six.moves import urllib_parse
from resources.lib import utils
from resources.lib.adultsite import AdultSite

addon = utils.addon
site = AdultSite("beeg", "[COLOR hotpink]Beeg[/COLOR]", "https://beeg.com/api/v6/", "bg.png", "beeg")


def BGVersion():
    page = utils.getHtml(site.url[:-7], '')
    bgurl = site.url[:-8] + re.compile(r'<script\ssrc="?([^>"]+)"?></script></body>', re.DOTALL | re.IGNORECASE).findall(page)[0]
    bgpage = utils.getHtml(bgurl, site.url[:-7])
    bgversion = re.compile(r'version="\)\.concat\("([^"]+)', re.DOTALL | re.IGNORECASE).findall(bgpage)[0]
    bgsavedversion = addon.getSetting('bgversion')
    if bgversion != bgsavedversion:
        addon.setSetting('bgversion', bgversion)


@site.register(default_mode=True)
def BGMain():
    BGVersion()
    bgversion = addon.getSetting('bgversion')
    site.add_dir('[COLOR hotpink]Categories[/COLOR]', site.url + bgversion + '/tags', 'BGCat', site.img_cat)
    site.add_dir('[COLOR hotpink]Channels[/COLOR]', site.url + bgversion + '/channels', 'BGChnl', site.img_cat)
    site.add_dir('[COLOR hotpink]Porn Stars[/COLOR]', site.url + bgversion + '/people', 'BGPpl', site.img_cat)
    # site.add_dir('[COLOR hotpink]Search[/COLOR]', site.url + bgversion + '/index/main/0/pc?query=', 'BGSearch', site.img_search)
    BGList(site.url + bgversion + '/index/main/0/pc')
    utils.eod()


@site.register()
def BGList(url):
    bgversion = addon.getSetting('bgversion')
    listjson = utils.getHtml(url, site.url[:-7])
    jdata = json.loads(listjson)

    for video in jdata['videos']:
        if video["duration"]:
            m, s = divmod(video["duration"], 60)
            duration = ' [COLOR deeppink]{:d}:{:02d}[/COLOR]'.format(m, s)
        else:
            duration = ''
        quality = ' [COLOR orange]{}[/COLOR]'.format(video["quality"]) if video["quality"] else ''

        name = video['title']
        if not name:
            name = video['ps_name']
        name = name + quality + duration
        name = name if utils.PY3 else name.encode('utf8')

        img = 'https://img.beeg.com/400x225/' + video['thumbs'][0]['image']
        videopage = '{0}{1}/video/{2}?v=2'.format(site.url, bgversion, video['svid'])

        if video["full"] == 0:
            for i, thumb in enumerate(sorted(video["thumbs"], key=lambda x: x["start"])):
                pid = thumb['pid']
                img = "https://img.beeg.com/400x225/" + thumb['image']
                start = thumb['start']
                end = thumb['end']
                m, s = divmod(start, 60)
                stxt = '{:d}:{:02d}'.format(m, s)
                m, s = divmod(end, 60)
                etxt = '{:d}:{:02d}'.format(m, s)
                videopage = '{0}&s={1}&e={2}&p={3}'.format(videopage, start, end, pid)
                name_thumb = '{}[COLOR blue] part {} ({} - {})[/COLOR]'.format(name, str(i + 1), stxt, etxt)
                site.add_download_link(name_thumb, videopage, 'BGPlayvid', img, '')
        else:
            site.add_download_link(name, videopage, 'BGPlayvid', img, name)

    page = re.compile(r'/index/[^/]+/(\d+)/', re.DOTALL | re.IGNORECASE).findall(url)[0]
    page = int(page)
    pages = jdata['pages']
    npage = page + 1
    if npage < pages:
        nextp = url.replace('/%s/' % page, '/%s/' % npage)
        site.add_dir('Next Page... (Curently in %s of %s)' % (npage, pages), nextp, 'BGList', site.img_next)

    utils.eod()


@site.register()
def BGPlayvid(url, name, download=None):
    bgversion = addon.getSetting('bgversion')
    vp = utils.VideoPlayer(name, download)
    vp.progress.update(25, "[CR]Loading video page[CR]")
    videopage = utils.getHtml(url, site.url)
    videopage = json.loads(videopage)
    videourls = {}

    if videopage["240p"]:
        videourls.update({"240p": videopage["240p"]})
    if videopage["480p"]:
        videourls.update({"480p": videopage["480p"]})
    if videopage["720p"]:
        videourls.update({"720p": videopage["720p"]})
    if videopage["1080p"]:
        videourls.update({"1080p": videopage["1080p"]})
    if videopage["2160p"]:
        videourls.update({"2160p": videopage["2160p"]})
    videourl = utils.prefquality(videourls, sort_by=lambda x: int(''.join([y for y in x if y.isdigit()])), reverse=True)

    if not videourl:
        return

    DATA_MARKERS = 'data=pc_XX__{}_'.format(bgversion)
    videourl = videourl.format(DATA_MARKERS=DATA_MARKERS)
    if videourl.startswith("//"):
        videourl = "https:" + videourl

    vp.play_from_direct_link(videourl)


@site.register()
def BGCat(url):
    bgversion = addon.getSetting('bgversion')
    caturl = utils.getHtml2(url)
    cats = json.loads(caturl)['tags']
    for cat in cats:
        videolist = '{0}{1}/index/tag/0/pc?tag={2}'.format(site.url, bgversion, urllib_parse.quote(cat['tag']))
        title = cat['tag'].title() if utils.PY3 else cat['tag'].title().encode('utf8')
        name = title + ' [COLOR hotpink](%s videos)[/COLOR]' % cat['videos']
        site.add_dir(name, videolist, 'BGList', '')
    utils.eod()


@site.register()
def BGChnl(url):
    bgversion = addon.getSetting('bgversion')
    caturl = utils.getHtml2(url)
    cats = json.loads(caturl)['channels']
    for cat in cats:
        videolist = '{0}{1}/index/channel/0/pc?channel={2}'.format(site.url, bgversion, urllib_parse.quote(cat['channel']))
        title = cat['channel'].title() if utils.PY3 else cat['channel'].title().encode('utf8')
        name = title + ' [COLOR hotpink]({0} videos)[/COLOR]'.format(cat['videos'])
        if cat['image']:
            image = 'https://thumbs.beeg.com/channels/{0}.png'.format(cat['id'])
        else:
            image = 'https://beeg.com/img/channel-placeholder.bab27720.png'
        site.add_dir(name, videolist, 'BGList', image)

    if len(cats) == 100:
        if '?' in url:
            url, offset = url.split('?')
            offset = int(offset.split('=')[-1])
        else:
            offset = 0
        url = url.split('?')[0] + '?offset={0}'.format(offset + 100)
        site.add_dir('Next Page...', url, 'BGChnl', site.img_next)

    utils.eod()


@site.register()
def BGPpl(url):
    bgversion = addon.getSetting('bgversion')
    caturl = utils.getHtml2(url)
    cats = json.loads(caturl)['people']
    for cat in cats:
        videolist = '{0}{1}/index/people/0/pc?search_mode=code&people={2}'.format(site.url, bgversion, urllib_parse.quote(cat['code']))
        title = cat['name'] if utils.PY3 else cat['name'].encode('utf8')
        name = title + ' [COLOR hotpink]({0} videos)[/COLOR]'.format(cat['videos'])
        if cat['image']:
            image = 'https://thumbs.beeg.com/img/cast/{0}.png'.format(cat['id'])
        else:
            image = 'https://beeg.com/img/user-placeholder.39f16436.jpg'
        site.add_dir(name, videolist, 'BGList', image)

    if len(cats) == 100:
        if '?' in url:
            url, offset = url.split('?')
            offset = int(offset.split('=')[-1])
        else:
            offset = 0
        url = url.split('?')[0] + '?offset={0}'.format(offset + 100)
        site.add_dir('Next Page...', url, 'BGPpl', site.img_next)

    utils.eod()


@site.register()
def BGSearch(url, keyword=None):
    searchUrl = url
    if not keyword:
        site.search_dir(url, 'BGSearch')
    else:
        title = urllib_parse.quote_plus(keyword)
        searchUrl = searchUrl + title
        BGList(searchUrl)
