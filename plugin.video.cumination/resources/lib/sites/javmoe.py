"""
    Cumination Site Plugin
    Copyright (C) 2018 Team Cumination

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
import string
import codecs
import time
from six.moves import urllib_parse
from resources.lib import utils, jsunpack
from resources.lib.adultsite import AdultSite

site = AdultSite('javmoe', '[COLOR hotpink]JAV Moe[/COLOR]', 'https://javmama.me/', 'javmoe.png', 'javmoe')

enames = {'FS': 'FileStar',
          'sb': 'StreamSB',
          'fembed': 'FEmbed',
          'r': 'RapidVideo',
          'ST': 'Motonews'}


@site.register(default_mode=True)
def Main():
    site.add_dir('[COLOR hotpink]Genres[/COLOR]', site.url + 'genres/', 'Categories', site.img_cat)
    site.add_dir('[COLOR hotpink]Pornstars[/COLOR]', site.url + 'pornstars/', 'Letters', '', '')
    site.add_dir('[COLOR hotpink]Search[/COLOR]', site.url + '?s={}&post_type=post', 'Search', site.img_search)
    List(site.url)
    utils.eod()


@site.register()
def List(url):
    items = 0
    while items < 36 and url:
        try:
            listhtml = utils.getHtml(url, site.url)
        except:
            return None
        divs = re.compile(r'<div\s*class="epshen">(.+?</h2>)', re.DOTALL | re.IGNORECASE).findall(listhtml)
        for div in divs:
            match = re.compile(r'href="([^"]+).+?src="([^"]+).+?title">([^<]+)', re.DOTALL | re.IGNORECASE).search(div)
            if match:
                videopage, img, name = match.groups()
                name = utils.cleantext(name)
                img = urllib_parse.quote(img, safe=':/')
                videopage = urllib_parse.quote(videopage, safe=':/')
                site.add_download_link(name, videopage, 'Playvid', img, name)
                items += 1
        try:
            url = re.compile(r'class="next\s*page-numbers"\s*href="([^"]+)', re.DOTALL | re.IGNORECASE).findall(listhtml)[0]
        except:
            url = None
    if url:
        site.add_dir('Next Page', url, 'List', site.img_next)
    utils.eod()


@site.register()
def Search(url, keyword=None):
    searchUrl = url
    if not keyword:
        site.search_dir(url, 'Search')
    else:
        title = keyword.replace(' ', '+')
        searchUrl = searchUrl.format(title)
        List(searchUrl)


@site.register()
def Categories(url):
    cathtml = utils.getHtml(url, '')
    match = re.compile(r'<li><a\s*href="([^"]+)"\s*>([^<]+)', re.DOTALL | re.IGNORECASE).findall(cathtml)
    for catpage, name in match:
        site.add_dir(name, catpage, 'List', site.img_cat)
    utils.eod()


@site.register()
def Letters(url):
    site.add_dir('#', r'\d', 'Pornstars', site.img_cat)
    for name in string.ascii_uppercase:
        site.add_dir(name, name, 'Pornstars', site.img_cat)
    utils.eod()


@site.register()
def Pornstars(url):
    caturl = site.url + 'pornstars/'
    cathtml = utils.getHtml(caturl, '')
    match = re.compile(r'<li><a\s*href="([^"]+)"\s*>({}[^<]+)'.format(url), re.DOTALL | re.IGNORECASE).findall(cathtml)
    for catpage, name in match:
        site.add_dir(name, catpage.strip(), 'List')
    utils.eod()


@site.register()
def Playvid(url, name, download=None):
    vp = utils.VideoPlayer(name, download)
    vp.progress.update(25, "[CR]Loading video page[CR]")
    videopage = utils.getHtml(url, site.url)

    eurls = re.compile(r'<li><a\s*href="([^"]+)"\s*>\s*([^<]+)', re.DOTALL | re.IGNORECASE).findall(videopage)
    sources = {enames.get(ename): eurl for eurl, ename in eurls}
    eurl = utils.selector('Select Hoster', sources)
    if not eurl:
        vp.progress.close()
        return

    vp.progress.update(50, "[CR]Loading embed page[CR]")
    if eurl != '?server=1':
        videopage = utils.getHtml(url + eurl, site.url)
    videourl = re.compile('<iframe.+?src="([^"]+)', re.DOTALL | re.IGNORECASE).findall(videopage)[0]
    if 'filestar.club' in videourl:
        videourl = utils.getVideoLink(videourl, url)

    if 'gdriveplayer.to' in videourl:
        videourl = videourl.split('data=')[-1]
        while '%' in videourl:
            videourl = urllib_parse.unquote(videourl)
        videohtml = utils.getHtml('https:' + videourl, site.url)
        ptext = jsunpack.unpack(videohtml).replace('\\', '')
        ct = re.findall(r'"ct":"([^"]+)', ptext)[0]
        salt = codecs.decode(re.findall(r'"s":"([^"]+)', ptext)[0], 'hex')
        pf = re.findall(r'''null,\s*['"]([^'"]+)''', ptext, re.S)[0]
        pf = re.compile(r"[a-zA-Z]{1,}").split(pf)
        passphrase = ''.join([chr(int(c)) for c in pf])
        passphrase = re.findall(r'var\s+pass\s*=\s*"([^"]+)', passphrase)[0]
        from resources.lib.jscrypto import jscrypto
        etext = jscrypto.decode(ct, passphrase, salt)
        ctext = jsunpack.unpack(etext).replace('\\', '')
        frames = re.findall(r'sources:\s*(\[[^]]+\])', ctext)[0]
        frames = re.findall(r'file":"([^"]+)[^}]+label":"(\d+p)"', frames)
        t = int(time.time() * 1000)
        sources = {qual: "{0}{1}&ref={2}&res={3}".format(source, t, site.url, qual[:-1] if qual.endswith('p') else qual) for source, qual in frames}
        surl = utils.prefquality(sources)
        source = surl.split('&t=')[0]
        qual = surl.split('=')[-1]
        vp.progress.update(75, "[CR]Processed embed page[CR]")
        if surl:
            if surl.startswith('//'):
                surl = 'https:' + surl
            attempt = 1
            while 'redirect' in surl:
                surl = utils.getVideoLink(surl, headers={'Range': 'bytes=0-'})
                if 'server' not in surl:
                    attempt += 1
                    t = int(time.time() * 1000)
                    surl = "{0}&t={1}&ref={2}%26play_error_file%3Dyes&try={3}&res={4}".format(source, t, site.url, attempt, qual)
                elif 'redirector.' in surl:
                    surl = ''
            if surl:
                vp.play_from_direct_link(surl)
        vp.progress.close()
        utils.notify('Oh oh', 'No video found')
        return
    elif 'motonews' in videourl:
        if videourl.startswith('//'):
            videourl = 'https:' + videourl
        epage = utils.getHtml(videourl, url)
        s = re.findall(r'file":"(?P<url>[^"]+)","label":"(?P<label>[^"]+)', epage)
        vp.progress.update(75, "[CR]Processed embed page[CR]")
        if s:
            sources = {qual: source.replace('\\/', '/') for source, qual in s}
            surl = utils.prefquality(sources)
            if surl.startswith('//'):
                surl = 'https:' + surl
            vp.play_from_direct_link(surl + '|Referer={0}&verifypeer=false'.format(urllib_parse.urljoin(videourl, '/')))
        else:
            vp.progress.close()
            utils.notify('Oh oh', 'No video found')
            return
    else:
        vp.progress.update(75, "[CR]Processed embed page[CR]")
        vp.play_from_link_to_resolve(videourl)
