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

site = AdultSite('analgalore', '[COLOR hotpink]Anal Galore[/COLOR]', 'https://www.analgalore.com/', 'https://www.analgalore.com/templates/analgalore/images/logo.png', 'awmnet')
site2 = AdultSite('asiangalore', '[COLOR hotpink]Asian Galore[/COLOR]', 'https://www.asiangalore.com/', 'https://www.asiangalore.com/templates/asiangalore/images/logo.png', 'awmnet')
site3 = AdultSite('assoass', "[COLOR hotpink]Ass'O'Ass[/COLOR]", 'https://www.assoass.com/', 'https://www.assoass.com/templates/assoass/images/logo-8.png', 'awmnet')
site4 = AdultSite('cpv', '[COLOR hotpink]Cartoon Porn Videos[/COLOR]', 'https://www.cartoonpornvideos.com/', 'https://www.cartoonpornvideos.com/templates/cartoonpornvideos/images/logo.png', 'awmnet')
site5 = AdultSite('dinotube', '[COLOR hotpink]Dino Tube[/COLOR]', 'https://www.dinotube.com/', 'https://www.dinotube.com/templates/dinotube/images/logo.png', 'awmnet')
site6 = AdultSite('ebonygalore', '[COLOR hotpink]Ebony Galore[/COLOR]', 'https://www.ebonygalore.com/', 'https://www.ebonygalore.com/templates/ebonygalore/images/logo-8.png', 'awmnet')
site7 = AdultSite('elladies', '[COLOR hotpink]EL Ladies[/COLOR]', 'https://www.el-ladies.com/', 'https://www.el-ladies.com/templates/el-ladies/images/logo.png', 'awmnet')
site8 = AdultSite('forhertube', '[COLOR hotpink]For Her Tube[/COLOR]', 'https://www.forhertube.com/', 'https://www.forhertube.com/templates/forhertube/images/logo.png', 'awmnet')
site9 = AdultSite('fucd', '[COLOR hotpink]Fucd[/COLOR]', 'https://www.fucd.com/', 'https://www.fucd.com/templates/fucd/images/logo.png', 'awmnet')
site10 = AdultSite('fuq', '[COLOR hotpink]Fuq[/COLOR]', 'https://www.fuq.com/', 'https://www.fuq.com/templates/fuq/images/logo-8.png', 'awmnet')
site11 = AdultSite('gaymaletube', '[COLOR hotpink]GayMale Tube[/COLOR]', 'https://www.gaymaletube.com/', 'https://www.gaymaletube.com/templates/gaymaletube/images/logo.png', 'awmnet')
site12 = AdultSite('gotporn', '[COLOR hotpink]Got Porn[/COLOR]', 'https://www.gotporn.com/', 'https://www.gotporn.com/templates/gotporn/images/logo.png', 'awmnet')
site13 = AdultSite('homemadegalore', '[COLOR hotpink]Homemade Galore[/COLOR]', 'https://www.homemadegalore.com/', 'https://www.homemadegalore.com/templates/homemadegalore/images/logo.png', 'awmnet')
site14 = AdultSite('ixxx', '[COLOR hotpink]iXXX[/COLOR]', 'https://www.ixxx.com/', 'https://www.ixxx.com/templates/ixxx/images/logo.png', 'awmnet')
site15 = AdultSite('latingalore', '[COLOR hotpink]Latin Galore[/COLOR]', 'https://www.latingalore.com/', 'https://www.latingalore.com/templates/latingalore/images/logo.png', 'awmnet')
site16 = AdultSite('lpv', '[COLOR hotpink]Lesbian Porn Videos[/COLOR]', 'https://www.lesbianpornvideos.com/', 'https://www.lesbianpornvideos.com/templates/lesbianpornvideos/images/logo.png', 'awmnet')
site17 = AdultSite('lobstertube', '[COLOR hotpink]Lobster Tube[/COLOR]', 'https://www.lobstertube.com/', 'https://www.lobstertube.com/templates/lobstertube/images/logo.png', 'awmnet')
site18 = AdultSite('lupoporno', '[COLOR hotpink]Lupo Porno[/COLOR]', 'https://www.lupoporno.com/', 'https://www.lupoporno.com/templates/lupoporno/images/logo.png', 'awmnet')
site19 = AdultSite('maturetube', '[COLOR hotpink]Mature Tube[/COLOR]', 'https://www.maturetube.com/', 'https://www.maturetube.com/templates/maturetube/images/logo.png', 'awmnet')
site20 = AdultSite('melonstube', '[COLOR hotpink]Melons Tube[/COLOR]', 'https://www.melonstube.com/', 'https://www.melonstube.com/templates/melonstube/images/logo.png', 'awmnet')
site21 = AdultSite('metaporn', '[COLOR hotpink]Meta Porn[/COLOR]', 'https://www.metaporn.com/', 'https://www.metaporn.com/templates/metaporn/images/logo.png', 'awmnet')
site22 = AdultSite('pornhd', '[COLOR hotpink]Porn HD[/COLOR]', 'https://www.pornhd.com/', 'https://www.pornhd.com/templates/pornhd/images/logo.png', 'awmnet')
site23 = AdultSite('porntv', '[COLOR hotpink]Porn TV[/COLOR]', 'https://www.porntv.com/', 'https://www.porntv.com/templates/porntv/images/logo.png', 'awmnet')
site24 = AdultSite('porzo', '[COLOR hotpink]Porzo[/COLOR]', 'https://www.porzo.com/', 'https://www.porzo.com/templates/porzo/images/logo.png', 'awmnet')
site25 = AdultSite('qorno', '[COLOR hotpink]Qorno[/COLOR]', 'https://www.qorno.com/', 'https://www.qorno.com/templates/qorno/images/logo.png', 'awmnet')
site26 = AdultSite('sambaporno', '[COLOR hotpink]Samba Porno[/COLOR]', 'https://www.sambaporno.com/', 'https://www.sambaporno.com/templates/sambaporno/images/logo.png', 'awmnet')
site27 = AdultSite('stocktease', '[COLOR hotpink]Stocking Tease[/COLOR]', 'https://www.stocking-tease.com/', 'https://www.stocking-tease.com/templates/stocking-tease/images/logo-8.png', 'awmnet')
site28 = AdultSite('tgtube', '[COLOR hotpink]TG Tube[/COLOR]', 'https://www.tgtube.com/', 'https://www.tgtube.com/templates/tgtube/images/logo.png', 'awmnet')
site29 = AdultSite('tiava', '[COLOR hotpink]Tiava[/COLOR]', 'https://www.tiava.com/', 'https://www.tiava.com/templates/tiava/images/logo.png', 'awmnet')
site30 = AdultSite('toroporno', '[COLOR hotpink]Toro Porno[/COLOR]', 'https://www.toroporno.com/', 'https://www.toroporno.com/templates/toroporno/images/logo.png', 'awmnet')
site31 = AdultSite('tubebdsm', '[COLOR hotpink]Tube BDSM[/COLOR]', 'https://www.tubebdsm.com/', 'https://www.tubebdsm.com/templates/tubebdsm/images/logo-8.png', 'awmnet')
site32 = AdultSite('tubegalore', '[COLOR hotpink]Tube Galore[/COLOR]', 'https://www.tubegalore.com/', 'https://www.tubegalore.com/templates/tubegalore/images/logo.png', 'awmnet')
site33 = AdultSite('tubeporn', '[COLOR hotpink]Tube Porn[/COLOR]', 'https://www.tubeporn.com/', 'https://www.tubeporn.com/templates/tubeporn/images/logo.png', 'awmnet')
site34 = AdultSite('tubepornstars', '[COLOR hotpink]Tube Pornstars[/COLOR]', 'https://www.tubepornstars.com/', 'https://www.tubepornstars.com/templates/tubepornstars/images/logo.png', 'awmnet')
site35 = AdultSite('vrxxx', '[COLOR hotpink]VR XXX[/COLOR]', 'https://www.vrxxx.com/', 'https://www.vrxxx.com/templates/vrxxx/images/logo.png', 'awmnet')


def getBaselink(url):
    if 'analgalore.com' in url:
        siteurl = site.url
    elif 'asiangalore.com' in url:
        siteurl = site2.url
    elif 'assoass.com' in url:
        siteurl = site3.url
    elif 'cartoonpornvideos.com' in url:
        siteurl = site4.url
    elif 'dinotube.com' in url:
        siteurl = site5.url
    elif 'ebonygalore.com' in url:
        siteurl = site6.url
    elif 'el-ladies.com' in url:
        siteurl = site7.url
    elif 'forhertube.com' in url:
        siteurl = site8.url
    elif 'fucd.com' in url:
        siteurl = site9.url
    elif 'fuq.com' in url:
        siteurl = site10.url
    elif 'gaymaletube.com' in url:
        siteurl = site11.url
    elif 'gotporn.com' in url:
        siteurl = site12.url
    elif 'homemadegalore.com' in url:
        siteurl = site13.url
    elif 'ixxx.com' in url:
        siteurl = site14.url
    elif 'latingalore.com' in url:
        siteurl = site15.url
    elif 'lesbianpornvideos.com' in url:
        siteurl = site16.url
    elif 'lobstertube.com' in url:
        siteurl = site17.url
    elif 'lupoporno.com' in url:
        siteurl = site18.url
    elif 'maturetube.com' in url:
        siteurl = site19.url
    elif 'melonstube.com' in url:
        siteurl = site20.url
    elif 'metaporn.com' in url:
        siteurl = site21.url
    elif 'pornhd.com' in url:
        siteurl = site22.url
    elif 'porntv.com' in url:
        siteurl = site23.url
    elif 'porzo.com' in url:
        siteurl = site24.url
    elif 'qorno.com' in url:
        siteurl = site25.url
    elif 'sambaporno.com' in url:
        siteurl = site26.url
    elif 'stocking-tease.com' in url:
        siteurl = site27.url
    elif 'tgtube.com' in url:
        siteurl = site28.url
    elif 'tiava.com' in url:
        siteurl = site29.url
    elif 'toroporno.com' in url:
        siteurl = site30.url
    elif 'tubebdsm.com' in url:
        siteurl = site31.url
    elif 'tubegalore.com' in url:
        siteurl = site32.url
    elif 'tubeporn.com' in url:
        siteurl = site33.url
    elif 'tubepornstars.com' in url:
        siteurl = site34.url
    elif 'vrxxx.com' in url:
        siteurl = site35.url
    return siteurl


@site.register(default_mode=True)
@site2.register(default_mode=True)
@site3.register(default_mode=True)
@site4.register(default_mode=True)
@site5.register(default_mode=True)
@site6.register(default_mode=True)
@site7.register(default_mode=True)
@site8.register(default_mode=True)
@site9.register(default_mode=True)
@site10.register(default_mode=True)
@site11.register(default_mode=True)
@site12.register(default_mode=True)
@site13.register(default_mode=True)
@site14.register(default_mode=True)
@site15.register(default_mode=True)
@site16.register(default_mode=True)
@site17.register(default_mode=True)
@site18.register(default_mode=True)
@site19.register(default_mode=True)
@site20.register(default_mode=True)
@site21.register(default_mode=True)
@site22.register(default_mode=True)
@site23.register(default_mode=True)
@site24.register(default_mode=True)
@site25.register(default_mode=True)
@site26.register(default_mode=True)
@site27.register(default_mode=True)
@site28.register(default_mode=True)
@site29.register(default_mode=True)
@site30.register(default_mode=True)
@site31.register(default_mode=True)
@site32.register(default_mode=True)
@site33.register(default_mode=True)
@site34.register(default_mode=True)
@site35.register(default_mode=True)
def Main(url):
    siteurl = getBaselink(url)
    site.add_dir('[COLOR hotpink]Categories[/COLOR]', siteurl, 'Categories', site.img_cat)
    site.add_dir('[COLOR hotpink]Pornstars[/COLOR]', siteurl + 'pornstar/', 'Tags', site.img_cat)
    site.add_dir('[COLOR hotpink]Tags[/COLOR]', siteurl + 'a-z/', 'Tags', site.img_cat)
    site.add_dir('[COLOR hotpink]Search[/COLOR]', siteurl + 'search/', 'Search', site.img_search)
    List(siteurl + 'new')
    utils.eod()


@site.register()
def List(url):
    siteurl = getBaselink(url)
    listhtml = utils.getHtml(url, siteurl)
    match = re.compile(r'class="item-link.+?href="([^"]+).+?<img.+?src="([^"]+).+?pbw-rounded">(.*?)</div.+?<h3.+?>([^<]+).+?pbw-text-sm"><a.+?>([^<]+)', re.DOTALL | re.IGNORECASE).findall(listhtml)
    for videourl, thumb, info, name, provider in match:
        name = '[COLOR yellow][{}] [/COLOR]'.format(provider) + utils.cleantext(name)
        hd = 'HD' if ' HD' in info else ''
        duration = re.findall(r'([\d:]+)', info)[0]
        site.add_download_link(name, siteurl[:-1] + videourl.replace('&amp;', '&'), 'Playvid', thumb, name, duration=duration, quality=hd)

    p = re.search(r'label="Next\s*Page".+?href="([^"]+)', listhtml, re.DOTALL | re.IGNORECASE)
    if p:
        purl = siteurl[:-1] + p.group(1)
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
        searchUrl = searchUrl + title
        List(searchUrl)


@site.register()
def Tags(url):
    siteurl = getBaselink(url)
    cathtml = utils.getHtml(url, siteurl)
    match = re.compile(r'<li\s*class="category".+?href="([^"]+)">([^<]+).+?>([^<]+)', re.DOTALL | re.IGNORECASE).findall(cathtml)
    for catpage, name, videos in match:
        name = utils.cleantext(name) + " [COLOR deeppink](" + videos + " videos)[/COLOR]"
        site.add_dir(name, siteurl[:-1] + catpage, 'List', site.img_cat)
    utils.eod()


@site.register()
def Categories(url):
    siteurl = getBaselink(url)
    cathtml = utils.getHtml(url, siteurl)
    match = re.compile(r'<div class="pbw-card".+?href="([^"]+).+?<img.+?src="([^"]+).+?pbw-rounded">(?:<i.+?</i>)?\s*([^<]+).+?<h3.+?>\s*(.*?)[\n<]', re.DOTALL | re.IGNORECASE).findall(cathtml)
    for catpage, image, videos, name in match:
        name = utils.cleantext(name) + " [COLOR deeppink](" + videos + " videos)[/COLOR]"
        site.add_dir(name, siteurl[:-1] + catpage, 'List', image)
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
        return

    vp.play_from_link_to_resolve(vlink)
