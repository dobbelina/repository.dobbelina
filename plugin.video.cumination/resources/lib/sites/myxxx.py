'''
    Cumination
    Copyright (C) 2022 Team Cumination

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
import xbmc
from six.moves import urllib_parse
from resources.lib import utils
from resources.lib.adultsite import AdultSite

site = AdultSite('myxxx', '[COLOR hotpink]MyXXX[/COLOR]', 'https://myxxx.video/', 'https://myxxx.video/wp-content/uploads/2022/01/logomywhite-1-e1641144567609.png', 'myxxx')
site1 = AdultSite('freexxx', '[COLOR hotpink]FreeXXX[/COLOR]', 'https://freexxx.video/', 'https://freexxx.video/wp-content/uploads/2022/03/freexxx-1-e1648221702248.png', 'freexxx')
site2 = AdultSite('javxxx', '[COLOR hotpink]JavXXX[/COLOR]', 'https://javxxx.video/', 'https://javxxx.video/wp-content/uploads/2021/12/javlogo-e1640874858194.png', 'javxxx')
site3 = AdultSite('xmilf', '[COLOR hotpink]xMILF[/COLOR]', 'https://xmilf.video/', 'https://xmilf.video/wp-content/uploads/2021/12/xmilflogo-e1640970068601.png', 'xmilf')


def getBaselink(url):
    if 'myxxx.video' in url:
        siteurl = site.url
    elif 'freexxx.video' in url:
        siteurl = site1.url
    elif 'javxxx.video' in url:
        siteurl = site2.url
    elif 'xmilf.video' in url:
        siteurl = site3.url
    return siteurl


@site.register(default_mode=True)
@site1.register(default_mode=True)
@site2.register(default_mode=True)
@site3.register(default_mode=True)
def myxxx_main(url):
    siteurl = getBaselink(url)
    site.add_dir('[COLOR hotpink]Categories[/COLOR]', siteurl + 'categories/', 'myxxx_cat', '', '')
    site.add_dir('[COLOR hotpink]Actors[/COLOR]', siteurl + 'actors/', 'myxxx_cat', '', '')
    site.add_dir('[COLOR hotpink]Search[/COLOR]', siteurl + '?s=', 'myxxx_search', site.img_search)
    myxxx_list(siteurl)


@site.register()
def myxxx_list(url):
    listhtml = utils.getHtml(url)
    match = re.compile('<article.*?href="([^"]+)" title="([^"]+)"(.*?)</div>', re.DOTALL | re.IGNORECASE).findall(listhtml)
    for videopage, name, img in match:
        contextmenu = []
        contexturl = (utils.addon_sys
                          + "?mode=" + str('myxxx.myxxx_info')
                          + "&url=" + urllib_parse.quote_plus(videopage))
        contextmenu.append(('[COLOR deeppink]Lookup info[/COLOR]', 'RunPlugin(' + contexturl + ')'))
        name = utils.cleantext(name)
        imgmatch = re.search('data-src="([^"]+)', img, re.IGNORECASE | re.DOTALL)
        if imgmatch:
            img = imgmatch.group(1)
        else:
            img = ''
        site.add_download_link(name, videopage, 'myxxx_play', img, name, contextm=contextmenu)

    np = re.compile('rel="next" href="([^"]+)', re.DOTALL | re.IGNORECASE).search(listhtml)
    if np:
        site.add_dir('Next Page ({0})'.format(np.group(1).split('/')[-2]), np.group(1), 'myxxx_list', site.img_next)
    utils.eod()


@site.register()
def myxxx_cat(url):
    cathtml = utils.getHtml(url, url)
    match = re.compile('<article.*?href="([^"]+)" title="([^"]+)".*?src="([^"]+)', re.DOTALL | re.IGNORECASE).findall(cathtml)
    for catpage, name, img in match:
        name = utils.cleantext(name)
        site.add_dir(name, catpage, 'myxxx_list', img)
    np = re.compile(r'class="current">\d+?</a></li><li><a href="([^"]+)', re.DOTALL | re.IGNORECASE).search(cathtml)
    if np:
        site.add_dir('Next Page ({0})'.format(np.group(1).split('/')[-2]), np.group(1), 'myxxx_cat', site.img_next)

    utils.eod()


@site.register()
def myxxx_info(url):
    siteurl = getBaselink(url)
    try:
        listhtml = utils.getHtml(url)
    except:
        return None

    infodict = {}

    actors = re.compile('(actor/[^"]+)" title="([^"]+)', re.DOTALL | re.IGNORECASE).findall(listhtml)
    if actors:
        for url, actor in actors:
            actor = "Actor - " + actor.strip()
            infodict[actor] = siteurl + url

    categories = re.compile('(category/[^"]+)" class="label" title="([^"]+)', re.DOTALL | re.IGNORECASE).findall(listhtml)
    if categories:
        for url, category in categories:
            category = "Cat - " + category.strip()
            infodict[category] = siteurl + url

    tags = re.compile('(tag/[^"]+)" class="label" title="([^"]+)', re.DOTALL | re.IGNORECASE).findall(listhtml)
    if tags:
        for url, tag in tags:
            tag = "Tag - " + tag.strip()
            infodict[tag] = siteurl + url

    if infodict:
        selected_item = utils.selector('Choose item', infodict, sort_by=lambda x: x[1], show_on_one=True)
        if not selected_item:
            return
        contexturl = (utils.addon_sys
                      + "?mode=" + str('myxxx.myxxx_list')
                      + "&url=" + urllib_parse.quote_plus(selected_item))
        xbmc.executebuiltin('Container.Update(' + contexturl + ')')
    else:
        utils.notify('Notify', 'No actors, categories or tags found for this video')
    return


@site.register()
def myxxx_search(url, keyword=None):
    if not keyword:
        site.search_dir(url, 'myxxx_search')
    else:
        url += keyword.replace(' ', '+')
        myxxx_list(url)


@site.register()
def myxxx_play(url, name, download=None):
    vp = utils.VideoPlayer(name, download=download, regex=r'''<iframe.+?src\s*=\s*["']([^'"]+)''')
    vp.play_from_site_link(url)
