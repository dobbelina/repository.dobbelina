"""
    Cumination
    Copyright (C) 2018 Whitecream, Fr33m1nd, holisticdioxide, Team Cumination

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

import re
import xbmc
from six.moves import urllib_parse
from resources.lib import utils
from resources.lib.adultsite import AdultSite

site = AdultSite('elreyx', '[COLOR hotpink]ElReyX[/COLOR]', 'https://elreyx.co/', 'elreyx.png', 'elreyx')
progress = utils.progress


@site.register(default_mode=True)
def EXMain():
    site.add_dir('[COLOR hotpink]Categories[/COLOR]', '{0}categories/'.format(site.url), 'EXCat', site.img_cat)
    site.add_dir('[COLOR hotpink]Search[/COLOR]', '{0}?s='.format(site.url), 'EXSearch', site.img_search)
    site.add_dir('[COLOR hotpink]Pornstars[/COLOR]', '{0}actors/'.format(site.url), 'EXPornstars', '', '')
    EXList(site.url)
    utils.eod()


@site.register()
def EXList(url):
    listhtml = utils.getHtml(url, '')
    vlist = re.compile(r'<main.+?</main>', re.DOTALL | re.IGNORECASE).findall(listhtml)[0]
    match = re.compile(r'<article.+?href="([^"]+).+?data-src="([^"]+).+?<span>([^<]+)', re.DOTALL | re.IGNORECASE).findall(vlist)
    for videopage, img, name in match:
        name = utils.cleantext(name).strip()
        contextmenu = []
        contexturl = (utils.addon_sys
                          + "?mode=" + str('elreyx.EXPornstar')
                          + "&url=" + urllib_parse.quote_plus(videopage))
        contextmenu.append(('[COLOR deeppink]Search Pornstars[/COLOR]', 'RunPlugin(' + contexturl + ')'))
        sitematch = re.compile(r"\[([^\]]*)\]", re.DOTALL | re.IGNORECASE).findall(name)
        if sitematch:
            sitename = sitematch[0]
            siteurl = 'https://elreyx.co/tag/{}/'.format(sitename.lower())

            contexturl = (utils.addon_sys
                          + "?mode=" + str('elreyx.EXList')
                          + "&url=" + urllib_parse.quote_plus(siteurl))
            contextmenu.append(('[COLOR deeppink]Search {}[/COLOR]'.format(sitename.strip()), 'Container.Update(' + contexturl + ')'))
        site.add_download_link(name, videopage, 'EXPlayvid', img, name, contextm=contextmenu)


    nextp = re.compile('<link rel="next" href="([^"]+)"', re.DOTALL | re.IGNORECASE).search(listhtml)
    if nextp:
        nextp = nextp.group(1)
        lp = re.compile(r'href=[^>]+/(\d+)/[^>]+>Last<', re.DOTALL | re.IGNORECASE).search(vlist)
        lp = lp.group(1) if lp else 1
        np = re.findall(r'/\d+/', nextp)[-1].replace('/', '')
        site.add_dir('Next Page ({}/{})'.format(np, lp), nextp, 'EXList', site.img_next)
    utils.eod()


@site.register()
def EXSearch(url, keyword=None):
    searchUrl = url
    if not keyword:
        site.search_dir(url, 'EXSearch')
    else:
        title = keyword.replace(' ', '+')
        searchUrl = searchUrl + title
        EXList(searchUrl)


@site.register()
def EXCat(url):
    cathtml = utils.getHtml(url, '')
    vlist = re.compile(r'<main.+?</main>', re.DOTALL | re.IGNORECASE).findall(cathtml)[0]
    match = re.compile('<article.+?href="([^"]+).+?data-src="([^"]+).+?cat-title">([^<]+)', re.DOTALL | re.IGNORECASE).findall(vlist)
    for catpage, img, name in match:
        name = utils.cleantext(name).strip()
        site.add_dir(name, catpage, 'EXList', img)

    nextp = re.compile(r'pagination".+?current.+?href="([^"]+)', re.DOTALL | re.IGNORECASE).search(vlist)
    if nextp:
        nextp = nextp.group(1)
        lp = re.findall(r'class="inactive">\d+<', vlist, re.DOTALL | re.IGNORECASE)
        lp = len(lp) + 1
        np = re.findall(r'/\d+/', nextp)[-1].replace('/', '')
        site.add_dir('Next Page ({}/{})'.format(np, lp), nextp, 'EXCat', site.img_next)
    utils.eod()


@site.register()
def EXPornstar(url):
    try:
        listhtml = utils.getHtml(url)
    except:
        return None
    pornstars = {}
    matches = re.compile('/actor/([^"]+)" title="([^"]+)"', re.DOTALL | re.IGNORECASE).findall(listhtml)
    if matches:
        for url, model in matches:
            model = model.strip()
            pornstars[model] = url
        selected_model = utils.selector('Choose model to view', pornstars, sort_by=lambda x: x[1], show_on_one=True)
        if not selected_model:
            return

        modelurl = 'https://elreyx.co/actor/' + selected_model
        contexturl = (utils.addon_sys
                      + "?mode=" + str('elreyx.EXList')
                      + "&url=" + urllib_parse.quote_plus(modelurl))
        xbmc.executebuiltin('Container.Update(' + contexturl + ')')

    else:
        utils.notify('Notify', 'No tagged pornstars found in this video')
    return


@site.register()
def EXPlayvid(url, name, download=None):
    vp = utils.VideoPlayer(name, download)
    vp.progress.update(25, "[CR]Loading video page[CR]")
    videopage = utils.getHtml(url, '')
    links = []

    videoplayer = re.compile(r'video-player">(.+?)advertising --', re.DOTALL | re.IGNORECASE).findall(videopage)
    if videoplayer:
        ilink = re.compile(r'src="(.+?//([^/]+)[^"]+)', re.DOTALL | re.IGNORECASE).findall(videoplayer[0])
    if ilink:
        links += ilink

    mlinks = re.compile(r'>Mirror<.+?href="([^"]+)[^>]+>([^<]+)<', re.DOTALL | re.IGNORECASE).findall(videopage)
    if mlinks:
        links.extend(mlinks)

    links = {host: link for link, host in links if vp.resolveurl.HostedMediaFile(link)}

    if links:
        link = utils.selector('Select link', links)
        if 'videos.sh' in link:
            vp.direct_regex = r'{src: "([^"]+)"'
            vp.play_from_site_link(link, url)
        else:
            vp.play_from_link_to_resolve(link)
    else:
        utils.notify('Oh Oh', 'No Videos found')
        vp.progress.close()
        return


@site.register()
def EXPornstars(url):
    cathtml = utils.getHtml(url, '')
    vlist = re.compile(r'<main.+?</main>', re.DOTALL | re.IGNORECASE).findall(cathtml)[0]
    match = re.compile('<article.+?href="([^"]+).+?data-src="([^"]+).+?actor-title">([^<]+)', re.DOTALL | re.IGNORECASE).findall(vlist)
    for catpage, img, name in match:
        name = utils.cleantext(name).strip()
        site.add_dir(name, catpage, 'EXList', img)

    nextp = re.compile(r'pagination".+?href="([^"]+)">Next<', re.DOTALL | re.IGNORECASE).search(vlist)
    if nextp:
        nextp = nextp.group(1)
        lp = re.compile(r'href=[^>]+/(\d+)/[^>]+>Last<', re.DOTALL | re.IGNORECASE).search(vlist)
        lp = lp.group(1) if lp else 1
        np = re.findall(r'/\d+/', nextp)[-1].replace('/', '')
        site.add_dir('Next Page ({}/{})'.format(np, lp), nextp, 'EXPornstars', site.img_next)
    utils.eod()
