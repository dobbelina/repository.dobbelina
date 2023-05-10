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
import xbmc
from resources.lib import utils
from resources.lib.adultsite import AdultSite
from resources.lib.decrypters.kvsplayer import kvs_decode
from six.moves import urllib_parse

site = AdultSite('pornhat', '[COLOR hotpink]Pornhat[/COLOR]', 'https://www.pornhat.com/', 'pornhat.png', 'pornhat')
site1 = AdultSite('helloporn', '[COLOR hotpink]Hello Porn[/COLOR]', 'https://hello.porn/', 'helloporn.png', 'helloporn')
site2 = AdultSite('okporn', '[COLOR hotpink]OK Porn[/COLOR]', 'https://ok.porn/', 'okporn.png', 'okporn')
site3 = AdultSite('okxxx', '[COLOR hotpink]OK XXX[/COLOR]', 'https://ok.xxx/', 'okxxx.png', 'okxxx')
site4 = AdultSite('pornstarstube', '[COLOR hotpink]Pornstars Tube[/COLOR]', 'https://pornstars.tube/', 'pornstarstube.png', 'pornstarstube')
site5 = AdultSite('maxporn', '[COLOR hotpink]Max Porn[/COLOR]', 'https://max.porn/', 'maxporn.png', 'maxporn')
# site6 = AdultSite('homoxxx', '[COLOR hotpink]Homo XXX[/COLOR]', 'https://homo.xxx/', 'homoxxx.png', 'homoxxx')


def getBaselink(url):
    if 'pornhat.com' in url:
        siteurl = site.url
    elif 'hello.porn' in url:
        siteurl = site1.url
    elif 'ok.porn' in url:
        siteurl = site2.url
    elif 'ok.xxx' in url:
        siteurl = site3.url
    elif 'pornstars.tube' in url:
        siteurl = site4.url
    elif 'max.porn' in url:
        siteurl = site5.url
    # elif 'homo.xxx' in url:
    #     siteurl = site6.url
    return siteurl


@site.register(default_mode=True)
@site1.register(default_mode=True)
@site2.register(default_mode=True)
@site3.register(default_mode=True)
@site4.register(default_mode=True)
@site5.register(default_mode=True)
# @site6.register(default_mode=True)
def Main(url):
    siteurl = getBaselink(url)
    if 'max.porn' not in url and 'pornstars.tube' not in url:
        site.add_dir('[COLOR hotpink]Channels[/COLOR]', siteurl + 'channels/', 'Cat', site.img_cat)
        if 'hello.porn' in url:
            site.add_dir('[COLOR hotpink]Models[/COLOR]', siteurl + 'pornstars/videos/', 'Cat', site.img_cat)
        else:
            site.add_dir('[COLOR hotpink]Models[/COLOR]', siteurl + 'models/', 'Cat', site.img_cat)
    if 'pornstars.tube' in url:
        site.add_dir('[COLOR hotpink]Search Pornstars[/COLOR]', siteurl + 'search/', 'Search', site.img_search)
    else:
        site.add_dir('[COLOR hotpink]Search[/COLOR]', siteurl + 'search/', 'Search', site.img_search)
    if 'hello' in siteurl:
        List(siteurl + 'new/')
    elif 'max.porn' in siteurl or 'pornstars.tube' in siteurl:
        Cat(siteurl)
    else:
        List(siteurl)


@site.register()
def List(url):
    siteurl = getBaselink(url)
    listhtml = utils.getHtml(url)
    match = re.compile(r'(?:class="thumb|class="item  ").+?href="([^"]+)"\s*title="([^"]+)".+?data-(?:original|src)="([^"]+)"', re.DOTALL | re.IGNORECASE).findall(listhtml)
    for video, name, img in match:
        name = utils.cleantext(name)
        img = 'https:' + img if img.startswith('//') else img
        video = siteurl[:-1] + video if video.startswith('/') else video

        cm_related = (utils.addon_sys + "?mode=" + str('pornhat.ContextRelated') + "&url=" + urllib_parse.quote_plus(video))
        cm = [('[COLOR violet]Related videos[/COLOR]', 'RunPlugin(' + cm_related + ')')]

        site.add_download_link(name, video, 'Play', img, name, contextm=cm)
    nextp = re.compile(r'href="([^"]+)"[^>]*>\s*Next', re.DOTALL | re.IGNORECASE).search(listhtml)
    if nextp:
        nextp = nextp.group(1)
        nextp = siteurl[:-1] + nextp if nextp.startswith('/') else nextp
        np = re.findall(r'\d+', nextp)[-1]
        site.add_dir('[COLOR hotpink]Next Page...[/COLOR] ({0})'.format(np), nextp, 'List', site.img_next)
    utils.eod()


@site.register()
def Cat(url):
    siteurl = getBaselink(url)
    listhtml = utils.getHtml(url)
    listhtml = listhtml.split('<div class="content"')[-1]
    listhtml = listhtml.split('<div class="main"')[-1]
    listhtml = listhtml.split('<div class="footer')[0]

    if 'class="thumb-bl' in listhtml:
        cats = listhtml.split('class="thumb-bl')
    elif '<div class="item">' in listhtml:
        cats = listhtml.split('<div class="item">')
    elif '<a class="item"' in listhtml:
        cats = listhtml.split('<a class="item"')
    else:
        return
    if 'class="alphabet' in cats[0]:
        # site.add_dir('[COLOR red]ABC list[/COLOR]', cats[0], 'CatABC', '')
        site.add_dir('[COLOR violet]Alphabet[/COLOR]', siteurl, 'Letters', site.img_next)
    cats.pop(0)
    for cat in cats:
        catpage = re.compile(r'href="([^"]+)"', re.DOTALL | re.IGNORECASE).search(cat)
        catpage = catpage.group(1) if catpage else ''
        name = re.compile(r'title="([^"]+)"', re.DOTALL | re.IGNORECASE).search(cat)
        name = name.group(1) if name else ''
        if 'max.porn' in url:
            img = re.compile(r'data-src="([^"]+)"', re.DOTALL | re.IGNORECASE).search(cat)
        else:
            img = re.compile(r'src="([^"]+)"', re.DOTALL | re.IGNORECASE).search(cat)
        img = img.group(1) if img else ''
        img = 'https:' + img if img.startswith('//') else img
        videos = re.compile(r'>([\d\svideos\(\)]+\S)<', re.DOTALL | re.IGNORECASE).search(cat.replace('</span>', ''))
        videos = videos.group(1).strip() if videos else ''
        name += ' [COLOR hotpink]' + videos + '[/COLOR]'
        catpage = siteurl[:-1] + catpage if catpage.startswith('/') else catpage
        site.add_dir(name, catpage, 'List', img)
    nextp = re.compile(r'href="([^"]+)"[^>]*>\s*Next', re.DOTALL | re.IGNORECASE).search(cats[-1])
    if nextp:
        nextp = nextp.group(1)
        nextp = siteurl[:-1] + nextp if nextp.startswith('/') else nextp
        np = re.findall(r'\d+', nextp)[-1]
        lp = re.compile(r'"pagination-last".+?>(\d+)<', re.DOTALL | re.IGNORECASE).search(cats[-1])
        lp = '/' + lp.group(1) if lp else ''
        site.add_dir('[COLOR hotpink]Next Page...[/COLOR] ({0}{1})'.format(np, lp), nextp, 'Cat', site.img_next)
    utils.eod()


@site.register()
def Search(url, keyword=None):
    if not keyword:
        site.search_dir(url, 'Search')
    else:
        url = "{0}{1}/".format(url, keyword.replace(' ', '-'))
        if 'pornstars.tube' in url:
            Cat(url)
        else:
            List(url)


@site.register()
def Play(url, name, download=None):
    siteurl = getBaselink(url)
    vp = utils.VideoPlayer(name, download)
    vp.progress.update(25, "[CR]Loading video page[CR]")
    vpage = utils.getHtml(url, siteurl)
    sources = {}
    license = re.compile(r"license_code:\s*'([^']+)", re.DOTALL | re.IGNORECASE).findall(vpage)[0]
    patterns = [r"video_url:\s*'([^']+)[^;]+?video_url_text:\s*'([^']+)",
                r"video_alt_url:\s*'([^']+)[^;]+?video_alt_url_text:\s*'([^']+)",
                r"video_alt_url2:\s*'([^']+)[^;]+?video_alt_url2_text:\s*'([^']+)",
                r"video_url:\s*'([^']+)',\s*postfix:\s*'\.mp4',\s*(preview)"]
    for pattern in patterns:
        items = re.compile(pattern, re.DOTALL | re.IGNORECASE).findall(vpage)
        for surl, qual in items:
            qual = '00' if qual == 'preview' else qual
            surl = kvs_decode(surl, license)
            sources.update({qual: surl})
    videourl = utils.selector('Select quality', sources, setting_valid='qualityask', sort_by=lambda x: 1081 if x == '4k' else int(x[:-1]), reverse=True)

    if not videourl:
        vp.progress.close()
        return
    videourl = utils.getVideoLink(videourl, siteurl)
    vp.play_from_direct_link(videourl)


@site.register()
def Letters(url):
    letters = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z']
    letter = utils.selector('Select letter', letters)
    if letter:
        if 'hello.porn' in url:
            Cat(url + 'pornstars/' + letter + '/')
        elif 'max.porn' in url or 'pornstars.tube' in url:
            Cat(url + letter + '/')
        else:
            Cat(url + 'models/abc/?section=' + letter)


@site.register()
def ContextRelated(url):
    contexturl = (utils.addon_sys
                  + "?mode=" + str('pornhat.List')
                  + "&url=" + urllib_parse.quote_plus(url))
    xbmc.executebuiltin('Container.Update(' + contexturl + ')')
