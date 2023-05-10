'''
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
'''

import re
import hashlib
import xbmcplugin
from resources.lib import utils
from resources.lib.adultsite import AdultSite

site = AdultSite('absoluporn', '[COLOR hotpink]AbsoluPorn[/COLOR]', "http://www.absoluporn.com/en", "absoluporn.gif", 'absoluporn')


@site.register(default_mode=True)
def Main():
    site.add_dir('[COLOR hotpink]Top Rated[/COLOR]', '{0}/wall-note-1.html'.format(site.url), 'List', '', '')
    site.add_dir('[COLOR hotpink]Most Viewed[/COLOR]', '{0}/wall-main-1.html'.format(site.url), 'List', '', '')
    site.add_dir('[COLOR hotpink]Longest[/COLOR]', '{0}/wall-time-1.html'.format(site.url), 'List', '', '')
    site.add_dir('[COLOR hotpink]Categories[/COLOR]', site.url, 'Cat', site.img_cat)
    site.add_dir('[COLOR hotpink]Search[/COLOR]', '{0}/search-'.format(site.url), 'Search', site.img_search)
    List('{0}/wall-date-1.html'.format(site.url))


@site.register()
def List(url):
    listhtml = utils.getHtml(url, '')
    match = re.compile('thumb-main-titre"><a href="..([^"]+)".*?title="([^"]+)".*?src="([^"]+)".*?<div class="thumb-info">(.*?)time">([^<]+)<', re.DOTALL | re.IGNORECASE).findall(listhtml)
    for videourl, name, img, hd, duration in match:
        name = utils.cleantext(name)
        if 'hd' in hd:
            hd = 'FULLHD' if 'full' in hd else 'HD'
        else:
            hd = ''
        videopage = site.url[:-3] + videourl
        videopage = videopage.replace(" ", "%20")
        site.add_download_link(name, videopage, 'Playvid', img, name, duration=duration, quality=hd)

    nextp = re.compile(r'<span class="text16">\d+</span> <a href="..([^"]+)"').search(listhtml)
    if nextp:
        nextp = nextp.group(1).replace(" ", "%20")
        site.add_dir('Next Page', site.url[:-3] + nextp, 'List', site.img_next)

    utils.eod()


@site.register()
def Playvid(url, name, download=None):
    vp = utils.VideoPlayer(name, download)
    vp.progress.update(25, "[CR]Loading video page[CR]")
    videopage = utils.getHtml(url, '')
    r = re.compile(r'<source\s*src="([^"]+)', re.DOTALL | re.IGNORECASE).search(videopage)
    if r:
        videourl = r.group(1)
    else:
        servervideo = re.compile("servervideo = '([^']+)'", re.DOTALL | re.IGNORECASE).findall(videopage)[0]
        vpath = re.compile("path = '([^']+)'", re.DOTALL | re.IGNORECASE).findall(videopage)[0]
        coda, repp = re.compile(r"repp = (codage\()*'([^']+)'", re.DOTALL | re.IGNORECASE).findall(videopage)[0]
        filee = re.compile("filee = '([^']+)'", re.DOTALL | re.IGNORECASE).findall(videopage)[0]
        if coda:
            repp = hashlib.md5(repp).hexdigest()
        videourl = servervideo + vpath + repp + filee
    vp.play_from_direct_link(videourl)


@site.register()
def Cat(url):
    cathtml = utils.getHtml(url, '')
    catsec = re.findall('categorie">(.+?)All', cathtml, re.DOTALL)[0]
    match = re.compile(r'li>.+?href="..([^"]+)[^>]+>([^<]+).+?">([^<]+)').findall(catsec)
    for caturl, name, items in match:
        catpage = site.url[:-3] + caturl
        name += " [COLOR deeppink]" + items + "[/COLOR]"
        site.add_dir(name, catpage, 'List', '', '')
    xbmcplugin.addSortMethod(utils.addon_handle, xbmcplugin.SORT_METHOD_TITLE)
    utils.eod()


@site.register()
def Search(url, keyword=None):
    searchUrl = url
    if not keyword:
        site.search_dir(url, 'Search')
    else:
        title = keyword.replace(' ', '%20')
        searchUrl = searchUrl + title + '-1.html'
        List(searchUrl)
