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
import xbmcplugin
from six.moves import urllib_parse
from resources.lib import utils
from resources.lib.adultsite import AdultSite

site = AdultSite('awmnet', '[COLOR hotpink]AWM Network[/COLOR] - [COLOR deeppink]35 sites[/COLOR]', '', 'awmnet.jpg', 'awmnet')

sitelist = [['Anal Galore', 'https://www.analgalore.com/templates/analgalore/images/logo.png', 'https://www.analgalore.com/'],
            ['Asian Galore', 'https://www.asiangalore.com/templates/asiangalore/images/logo.png', 'https://www.asiangalore.com/'],
            ["Ass'O'Ass", 'https://www.assoass.com/templates/assoass/images/logo-8.png', 'https://www.assoass.com/'],
            ['Cartoon Porn Videos', 'https://www.cartoonpornvideos.com/templates/cartoonpornvideos/images/logo.png', 'https://www.cartoonpornvideos.com/'],
            ['Dino Tube', 'https://www.dinotube.com/templates/dinotube/images/logo.png', 'https://www.dinotube.com/'],
            ['Ebony Galore', 'https://www.ebonygalore.com/templates/ebonygalore/images/logo-8.png', 'https://www.ebonygalore.com/'],
            ['EL Ladies', 'https://www.el-ladies.com/templates/el-ladies/images/logo.png', 'https://www.el-ladies.com/'],
            ['For Her Tube', 'https://www.forhertube.com/templates/forhertube/images/logo.png', 'https://www.forhertube.com/'],
            ['Fucd', 'https://www.fucd.com/templates/fucd/images/logo.png', 'https://www.fucd.com/'],
            ['Fuq', 'https://www.fuq.com/templates/fuq/images/logo-8.png', 'https://www.fuq.com/'],
            ['GayMale Tube', 'https://www.gaymaletube.com/templates/gaymaletube/images/logo.png', 'https://www.gaymaletube.com/'],
            ['Got Porn', 'https://www.gotporn.com/templates/gotporn/images/logo.png', 'https://www.gotporn.com/'],
            ['Homemade Galore', 'https://www.homemadegalore.com/templates/homemadegalore/images/logo.png', 'https://www.homemadegalore.com/'],
            ['iXXX', 'https://www.ixxx.com/templates/ixxx/images/logo.png', 'https://www.ixxx.com/'],
            ['Latin Galore', 'https://www.latingalore.com/templates/latingalore/images/logo.png', 'https://www.latingalore.com/'],
            ['Lesbian Porn Videos', 'https://www.lesbianpornvideos.com/templates/lesbianpornvideos/images/logo.png', 'https://www.lesbianpornvideos.com/'],
            ['Lobster Tube', 'https://www.lobstertube.com/templates/lobstertube/images/logo.png', 'https://www.lobstertube.com/'],
            ['Lupo Porno', 'https://www.lupoporno.com/templates/lupoporno/images/logo.png', 'https://www.lupoporno.com/'],
            ['Mature Tube', 'https://www.maturetube.com/templates/maturetube/images/logo.png', 'https://www.maturetube.com/'],
            ['Melons Tube', 'https://www.melonstube.com/templates/melonstube/images/logo.png', 'https://www.melonstube.com/'],
            ['Meta Porn', 'https://www.metaporn.com/templates/metaporn/images/logo.png', 'https://www.metaporn.com/'],
            ['Porn HD', 'https://www.pornhd.com/templates/pornhd/images/logo.png', 'https://www.pornhd.com/'],
            ['Porn TV', 'https://www.porntv.com/templates/porntv/images/logo.png', 'https://www.porntv.com/'],
            ['Porzo', 'https://www.porzo.com/templates/porzo/images/logo.png', 'https://www.porzo.com/'],
            ['Qorno', 'https://www.qorno.com/templates/qorno/images/logo.png', 'https://www.qorno.com/'],
            ['Samba Porno', 'https://www.sambaporno.com/templates/sambaporno/images/logo.png', 'https://www.sambaporno.com/'],
            ['Stocking Tease', 'https://www.stocking-tease.com/templates/stocking-tease/images/logo-8.png', 'https://www.stocking-tease.com/'],
            ['TG Tube', 'https://www.tgtube.com/templates/tgtube/images/logo.png', 'https://www.tgtube.com/'],
            ['Tiava', 'https://www.tiava.com/templates/tiava/images/logo.png', 'https://www.tiava.com/'],
            ['Toro Porno', 'https://www.toroporno.com/templates/toroporno/images/logo.png', 'https://www.toroporno.com/'],
            ['Tube BDSM', 'https://www.tubebdsm.com/templates/tubebdsm/images/logo-8.png', 'https://www.tubebdsm.com/'],
            ['Tube Galore', 'https://www.tubegalore.com/templates/tubegalore/images/logo.png', 'https://www.tubegalore.com/'],
            ['Tube Porn', 'https://www.tubeporn.com/templates/tubeporn/images/logo.png', 'https://www.tubeporn.com/'],
            ['Tube Pornstars', 'https://www.tubepornstars.com/templates/tubepornstars/images/logo.png', 'https://www.tubepornstars.com/'],
            ['VR XXX', 'https://www.vrxxx.com/templates/vrxxx/images/logo.png', 'https://www.vrxxx.com/']]


def getBaselink(url):
    for pornsite in sitelist:
        domain = urllib_parse.urlparse(pornsite[2]).netloc
        if domain in url:
            siteurl = pornsite[2]
            break
    return siteurl


@site.register(default_mode=True)
def Main():
    for pornsite in sorted(sitelist):
        site.add_dir('[COLOR hotpink]{0}[/COLOR]'.format(pornsite[0]), pornsite[2], 'SiteMain', pornsite[1])
    utils.eod()


@site.register()
def SiteMain(url):
    siteurl = getBaselink(url)
    site.add_dir('[COLOR hotpink]Categories[/COLOR]', siteurl, 'Categories', site.img_cat)
    site.add_dir('[COLOR hotpink]Pornstars[/COLOR]', siteurl + 'pornstar/', 'Tags', site.img_cat)
    site.add_dir('[COLOR hotpink]Tags[/COLOR]', siteurl + 'a-z/', 'Tags', site.img_cat)
    site.add_dir('[COLOR hotpink]Search[/COLOR]', siteurl + 'search/', 'Search', site.img_search)
    List(siteurl + 'new?pricing=free')


@site.register()
def List(url):
    siteurl = getBaselink(url)
    listhtml = utils.getHtml(url, siteurl)
    match = re.compile(r'class="item-link.+?href="([^"]+).+?<img.+?src="([^"]+).+?rounded">(.*?)</div.+?<h3.+?>([^<]+).+?text-sm"><a.+?>([^<]+)', re.DOTALL | re.IGNORECASE).findall(listhtml)
    for videourl, thumb, info, name, provider in match:
        name = '[COLOR yellow][{}][/COLOR] {}'.format(provider, utils.cleantext(name))
        hd = 'HD' if ' HD' in info else ''
        duration = re.findall(r'([\d:]+)', info)[0]
        site.add_download_link(name, siteurl[:-1] + videourl.replace('&amp;', '&'), 'Playvid', thumb, name, duration=duration, quality=hd)

    p = re.search(r'label="Next\s*Page".+?href="([^"]+)', listhtml, re.DOTALL | re.IGNORECASE)
    if p:
        purl = siteurl[:-1] + p.group(1).replace('&amp;', '&')
        curr_pg = re.findall(r'label="Current\s*Page".+?>(\d+)', listhtml)[0]
        site.add_dir('Next Page... [COLOR hotpink](Currently in Page {})[/COLOR]'.format(curr_pg), purl, 'List', site.img_next)
    utils.eod()


@site.register()
def Search(url, keyword=None):
    searchUrl = url
    if not keyword:
        site.search_dir(url, 'Search')
    else:
        title = keyword.replace(' ', '%20')
        searchUrl = searchUrl + title + '?pricing=free'
        List(searchUrl)


@site.register()
def Tags(url):
    siteurl = getBaselink(url)
    cathtml = utils.getHtml(url, siteurl)
    match = re.compile(r'<li\s*class="category".+?href="([^"]+)">([^<]+).+?>([^<]+)', re.DOTALL | re.IGNORECASE).findall(cathtml)
    for catpage, name, videos in match:
        name = utils.cleantext(name) + " [COLOR deeppink](" + videos + " videos)[/COLOR]"
        site.add_dir(name, siteurl[:-1] + catpage + '?pricing=free', 'List', site.img_cat)
    utils.eod()


@site.register()
def Categories(url):
    siteurl = getBaselink(url)
    cathtml = utils.getHtml(url, siteurl)
    match = re.compile(r'class="item-link\s*relative\s*block"\s*href="([^"]+)"\s*title="([^"]+).+?<img.+?src="([^"]+).+?fa-video[^<]+</i>\s*([^<]+)<', re.DOTALL | re.IGNORECASE).findall(cathtml)
    for catpage, name, image, videos in match:
        name = utils.cleantext(name) + " [COLOR deeppink](" + videos + " videos)[/COLOR]"
        site.add_dir(name, siteurl[:-1] + catpage + '?pricing=free', 'List', image)
    xbmcplugin.addSortMethod(utils.addon_handle, xbmcplugin.SORT_METHOD_TITLE)
    utils.eod()


@site.register()
def Playvid(url, name, download=None):
    vp = utils.VideoPlayer(name, download)
    vp.progress.update(25, "[CR]Loading video page[CR]")
    found = False
    while not found:
        vlink = utils.getVideoLink(url, site.url)
        if vlink != url:
            if vlink.startswith('/'):
                vlink = urllib_parse.urljoin(url, vlink)
            url = vlink
        else:
            found = True
    vp.progress.update(50, "[CR]Scraping video page[CR]")
    if not vp.resolveurl.HostedMediaFile(vlink):
        utils.notify('Oh Oh', 'No Videos found')
        vp.progress.close()
        utils.kodilog(vlink)
        return

    vp.play_from_link_to_resolve(vlink)
