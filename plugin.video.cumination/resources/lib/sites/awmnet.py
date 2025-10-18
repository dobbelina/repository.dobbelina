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
from resources.lib.decrypters.kvsplayer import kvs_decode
from resources.lib.decrypters import txxx


site = AdultSite('awmnet', '[COLOR hotpink]AWM Network[/COLOR] - [COLOR deeppink]46 sites[/COLOR]', '', 'awmnet.jpg', 'awmnet')

sitelist = [
    ['4tube', 'https://www.4tube.com/templates/4tube/images/logo.png', 'https://www.4tube.com/'],
    ['Anal Galore', 'https://www.analgalore.com/templates/analgalore/images/logo.png', 'https://www.analgalore.com/'],
    ['Asian Galore', 'https://www.asiangalore.com/templates/asiangalore/images/logo.png', 'https://www.asiangalore.com/'],
    ['Ass O Ass', 'https://www.assoass.com/templates/assoass/images/logo.png', 'https://www.assoass.com/'],
    ['Biporn', 'https://www.biporn.com/templates/biporn/images/logo.png', 'https://www.biporn.com/'],
    ['Cartoon Porn Videos', 'https://www.cartoonpornvideos.com/templates/cartoonpornvideos/images/logo.png', 'https://www.cartoonpornvideos.com/'],
    ['Dino Tube', 'https://www.dinotube.com/templates/dinotube/images/logo.png', 'https://www.dinotube.com/'],
    ['Ebony Galore', 'https://www.ebonygalore.com/templates/ebonygalore/images/logo.png', 'https://www.ebonygalore.com/'],
    ['EL Ladies', 'https://www.el-ladies.com/templates/el-ladies/images/logo.png', 'https://www.el-ladies.com/'],
    ['Find Tubes', 'https://www.findtubes.com/templates/findtubes/images/logo.png', 'https://www.findtubes.com/'],
    ['For Her Tube', 'https://www.forhertube.com/templates/forhertube/images/logo.png', 'https://www.forhertube.com/'],
    ['Fucd', 'https://www.fucd.com/templates/fucd/images/logo.png', 'https://www.fucd.com/'],
    ['Full Porn Videos', 'https://www.fullpornvideos.com/templates/fullpornvideos/images/logo.png', 'https://www.fullpornvideos.com/'],
    ['Fuq', 'https://www.fuq.com/templates/fuq/images/logo.png', 'https://www.fuq.com/'],
    ['Fux', 'https://www.fux.com/templates/fux/images/logo.png', 'https://www.fux.com/'],
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
    ['Model Galore', 'https://www.modelgalore.com/templates/modelgalore/images/logo.png', 'https://www.modelgalore.com/'],
    ['Muy Cerdas', 'https://www.muycerdas.xxx/templates/muycerdas/images/logo.png', 'https://www.muycerdas.xxx/'],
    ['New Porno', 'https://www.newporno.com/templates/newporno/images/logo.png', 'https://www.newporno.com/'],
    ['Porner Bros', 'https://www.pornerbros.com/templates/pornerbros/images/logo.png', 'https://www.pornerbros.com/'],
    ['Porn HD', 'https://www.pornhd.com/templates/pornhd/images/logo.png', 'https://www.pornhd.com/'],
    ['Porn MD', 'https://www.pornmd.com/templates/pornmd/images/logo.png', 'https://www.pornmd.com/'],
    ['Porn TV', 'https://www.porntv.com/templates/porntv/images/logo.png', 'https://www.porntv.com/'],
    ['Porzo', 'https://www.porzo.com/templates/porzo/images/logo.png', 'https://www.porzo.com/'],
    ['Qorno', 'https://www.qorno.com/templates/qorno/images/logo.png', 'https://www.qorno.com/'],
    ['Samba Porno', 'https://www.sambaporno.com/templates/sambaporno/images/logo.png', 'https://www.sambaporno.com/'],
    ['Short Porn', 'https://www.shortporn.com/templates/shortporn/images/logo.png', 'https://www.shortporn.com/'],
    ['Stocking Tease', 'https://www.stocking-tease.com/templates/stocking-tease/images/logo.png', 'https://www.stocking-tease.com/'],
    ['TG Tube', 'https://www.tgtube.com/templates/tgtube/images/logo.png', 'https://www.tgtube.com/'],
    ['Tiava', 'https://www.tiava.com/templates/tiava/images/logo.png', 'https://www.tiava.com/'],
    ['Toro Porno', 'https://www.toroporno.com/templates/toroporno/images/logo.png', 'https://www.toroporno.com/'],
    ['Tube BDSM', 'https://www.tubebdsm.com/templates/tubebdsm/images/logo.png', 'https://www.tubebdsm.com/'],
    ['Tube Galore', 'https://www.tubegalore.com/templates/tubegalore/images/logo.png', 'https://www.tubegalore.com/'],
    ['Tube Porn', 'https://www.tubeporn.com/templates/tubeporn/images/logo.png', 'https://www.tubeporn.com/'],
    ['Tube Pornstars', 'https://www.tubepornstars.com/templates/tubepornstars/images/logo.png', 'https://www.tubepornstars.com/'],
    ['VR XXX', 'https://www.vrxxx.com/templates/vrxxx/images/logo.png', 'https://www.vrxxx.com/']
]


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
    site.add_dir('[COLOR hotpink]Pornstars[/COLOR]', siteurl + 'pornstar', 'Tags', site.img_cat)
    site.add_dir('[COLOR hotpink]Tags[/COLOR]', siteurl + 'a-z', 'Tags', site.img_cat)
    site.add_dir('[COLOR hotpink]Search[/COLOR]', siteurl + 'search/', 'Search', site.img_search)
    List(siteurl + 'new?pricing=free')


@site.register()
def List(url):
    siteurl = getBaselink(url)
    listhtml = utils.getHtml(url, siteurl)
    match = re.compile(r'class="item-link.+?href="([^"]+)".+?title="([^"]+)".+?src="([^"]+)".+?float-right"(.*?)class="item-rating.+?text-xsm"></i>([^<]+)</a>', re.DOTALL | re.IGNORECASE).findall(listhtml)
    for videourl, name, thumb, info, provider in match:
        name = '[COLOR yellow][{}][/COLOR] {}'.format(provider.strip(), utils.cleantext(name))
        hd = 'HD' if ' HD' in info else ''
        duration = re.findall(r'([\d:]+)', info)
        duration = duration[0] if duration else ""
        site.add_download_link(name, siteurl[:-1] + videourl.replace('&amp;', '&'), 'Playvid', thumb, name, duration=duration, quality=hd)
    p = re.search(r'href="([^"]+)"[^>]+?label="Next\s*Page"', listhtml, re.DOTALL | re.IGNORECASE)
    if p:
        purl = siteurl[:-1] + p.group(1).replace('&amp;', '&')
        curr_pg = re.findall(r'label="Current\s*Page.+?(\d+)', listhtml, re.DOTALL | re.IGNORECASE)[0]
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
    match = re.compile(r'<li\s*class="category".+?href="([^"]+)"><span class="category-title">([^<]+).+?>([\d\.km]+)<', re.DOTALL | re.IGNORECASE).findall(cathtml)
    for catpage, name, videos in match:
        name = utils.cleantext(name) + " [COLOR deeppink](" + videos + " videos)[/COLOR]"
        site.add_dir(name, siteurl[:-1] + catpage + '?pricing=free', 'List', site.img_cat)
    utils.eod()


@site.register()
def Categories(url):
    siteurl = getBaselink(url)
    cathtml = utils.getHtml(url, siteurl)
    match = re.compile(r'class="card\s*group".+?href="([^"]+)"\s*title="([^"]+)".+?src="([^"]+).+?>([\d\.km]+)<', re.DOTALL | re.IGNORECASE).findall(cathtml)
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
        if '&lander=' in vlink:
            vlink = vlink.split('&lander=')[-1]
            vlink = urllib_parse.unquote(vlink)

        vpage = utils.getHtml(url, site.url)

        patterns = [r'''<source\s+[^>]*src=['"]([^'"]+\.mp4[^'"]*)['"]\s+[^>]*title=['"]([^'"]+)''',
                    r'\{"src":"([^"]+)","desc":"([^"]+)"']
        sources = {}
        for pattern in patterns:
            match = re.compile(pattern, re.DOTALL | re.IGNORECASE).findall(vpage)
            if match:
                sources.update({title: src for src, title in match})
        videourl = utils.prefquality(sources, sort_by=lambda x: 2160 if x == '4k' else int(x[:-1]), reverse=True)
        if videourl:
            videourl = videourl.replace(r'\/', '/')
            vp.play_from_direct_link(videourl)
            return

        patterns = [r'embed_url:\s*"([^"]+)"',
                    r"video_url:\s*'([^']+.mp4)'",
                    r'rel="video_src" href="([^"]+)"']
        sources = []
        for pattern in patterns:
            match = re.compile(pattern, re.DOTALL | re.IGNORECASE).findall(vpage)
            if match:
                sources = sources + match
        videourl = utils.selector('Select source', sources)
        if videourl:
            videourl = 'https:' + match[0] if match[0].startswith('//') else match[0]
            vp.play_from_direct_link(videourl)
            return

        if 'function/0/http' not in vpage and '<div class="embed-wrap"' in vpage:
            match = re.compile(r'<div class="embed-wrap".+?src="([^"]+)"', re.DOTALL | re.IGNORECASE).findall(vpage)
            if match:
                vpage = utils.getHtml(match[0], url)

        if "license_code: '" in vpage:
            sources = {}
            license = re.compile(r"license_code:\s*'([^']+)", re.DOTALL | re.IGNORECASE).findall(vpage)[0]
            patterns = [r"video_url:\s*'([^']+)[^;]+?video_url_text:\s*'([^']+)",
                        r"video_alt_url:\s*'([^']+)[^;]+?video_alt_url_text:\s*'([^']+)",
                        r"video_alt_url2:\s*'([^']+)[^;]+?video_alt_url2_text:\s*'([^']+)",
                        r"video_url:\s*'([^']+)',[^/]+(postfix):\s*'\.mp4'",
                        r"video_url:\s*'([^']+)',[^/]+(preview)"]
            for pattern in patterns:
                items = re.compile(pattern, re.DOTALL | re.IGNORECASE).findall(vpage)
                for surl, qual in items:
                    qual = '0p' if qual == 'preview' or qual == 'postfix' else qual
                    qual = '720p' if qual == 'HD' else qual
                    if 'function/0/http' in surl:
                        surl = kvs_decode(surl, license)

                    surl = utils.getVideoLink(surl)
                    surl = surl.replace('//', '/%2F').replace('https:/%2F', 'https://')
                    if '.mp4' in surl:
                        sources.update({qual: surl})
            videourl = utils.selector('Select quality', sources, setting_valid='qualityask', sort_by=lambda x: 2160 if x == '4k' else int(x[:-1]), reverse=True)

            if videourl:
                vp.play_from_direct_link(videourl)
                return

        match = re.search(r'^(http[s]?://[^/]+/)videos*/(\d+)/', vlink, re.IGNORECASE)
        if match:
            host = match.group(1)
            id = match.group(2)
            apiurl = "{0}api/videofile.php?video_id={1}&lifetime=8640000".format(host, id)
            try:
                jsondata = utils.getHtml(apiurl, url)
                r = re.search('video_url":"([^"]+)', jsondata)
                if r:
                    videourl = host + txxx.Tdecode(r.group(1))
                    vp.play_from_direct_link(videourl)
                    return
            except Exception as e:
                utils.kodilog('Error getting video from API: ' + str(e))
                utils.kodilog(vlink)
        else:
            utils.notify('Oh Oh', 'No Videos found')
            vp.progress.close()
            utils.kodilog(vlink)
            return

    if 'xhamster' in vlink:
        from resources.lib.sites.xhamster import Playvid as xhamsterPlayvid
        xhamsterPlayvid(vlink, name, download)
        return

    vp.play_from_link_to_resolve(vlink)
