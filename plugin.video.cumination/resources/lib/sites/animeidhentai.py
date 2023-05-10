'''
    Cumination
    Copyright (C) 2018 Whitecream

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

from resources.lib import utils
from resources.lib.adultsite import AdultSite

site = AdultSite("animeid", "[COLOR hotpink]Animeid Hentai[/COLOR]", "https://animeidhentai.com/", "ah.png", "animeid")


@site.register(default_mode=True)
def animeidhentai_main():
    site.add_dir('[COLOR hotpink]Uncensored[/COLOR]', '{0}genre/hentai-uncensored/'.format(site.url), 'animeidhentai_list', site.img_cat)
    site.add_dir('[COLOR hotpink]Genres[/COLOR]', site.url, 'animeidhentai_genres', site.img_cat)
    site.add_dir('[COLOR hotpink]Trending[/COLOR]', '{0}trending/'.format(site.url), 'animeidhentai_list', site.img_cat)
    site.add_dir('[COLOR hotpink]Years[/COLOR]', '{0}?s='.format(site.url), 'Years', site.img_cat)
    site.add_dir('[COLOR hotpink]Search[/COLOR]', '{0}?s='.format(site.url), 'animeidhentai_search', site.img_search)
    animeidhentai_list('{0}year/2023/'.format(site.url))


@site.register()
def animeidhentai_list(url):
    listhtml = utils.getHtml(url, site.url)
    match = re.compile(r'<article.+?loading="lazy"\s+(?:src|data-src)="(.*?)".+?link-co">([^<]+).+?mgr(.+?)description\s*dn">\s*(?:<p>)?([^<]+).+?href="([^"]+)', re.DOTALL | re.IGNORECASE).findall(listhtml)
    for img, name, hd, plot, video in match:
        quality = ''
        if '>hd<' in hd.lower():
            quality = 'HD'
        elif '1080p' in hd.lower():
            quality = 'FHD'
        if 'uncensored' in name.lower():
            name = name.replace('Uncensored', '') + " [COLOR hotpink][I]Uncensored[/I][/COLOR]"
        match = re.search(r'>(\d\d\d\d)<', hd)
        year = " [COLOR blue](" + match.group(1) + ")[/COLOR]" if match else ''
        name += year
        site.add_download_link(utils.cleantext(name), video, 'animeidhentai_play', img, utils.cleantext(plot), quality=quality)
    next_page = re.compile('rel="next" href="([^"]+)"', re.DOTALL | re.IGNORECASE).search(listhtml)
    if next_page:
        site.add_dir('Next Page', next_page.group(1), 'animeidhentai_list', site.img_next)
    utils.eod()


@site.register()
def animeidhentai_search(url, keyword=None):
    if not keyword:
        site.search_dir(url, 'animeidhentai_search')
    else:
        title = keyword.replace(' ', '+')
        url += title
        animeidhentai_list(url)


@site.register()
def animeidhentai_genres(url):
    listhtml = utils.getHtml(url, site.url)
    r = re.compile(r'<article\s*class="anime\s*xs.+?src="([^"]+).+?link-co">([^<]+).+?fwb">([^<]+).+?href="([^"]+)', re.DOTALL | re.IGNORECASE).findall(listhtml)
    for img, name, count, iurl in sorted(r, key=lambda x: x[1].lower()):
        name = name + " [COLOR cyan]{0} Videos[/COLOR]".format(count)
        site.add_dir(name, iurl, 'animeidhentai_list', img)
    utils.eod()


@site.register()
def Years(url):
    yearhtml = utils.getHtml(url, site.url)
    match = re.compile(r'name="years"\s+id="year-\d+"\s+value="\d+"\s+data-name="(\d+)">', re.DOTALL | re.IGNORECASE).findall(yearhtml)
    if match:
        year = utils.selector('Select link', match, reverse=True)
        if year:
            animeidhentai_list(site.url + 'year/' + year + '/')


@site.register()
def animeidhentai_play(url, name, download=None):
    vp = utils.VideoPlayer(name, download)
    vp.progress.update(25, "[CR]Loading video page[CR]")
    videopage = utils.getHtml(url, site.url)

    match = re.compile(r'data-player>\s+<iframe.+?-src="([^"]+)', re.DOTALL | re.IGNORECASE).search(videopage)
    if match:
        videourl = match.group(1)
        if 'nhplayer.com' in videourl:
            videopage = utils.getHtml(videourl, site.url)
            match = re.compile(r'<li data-id="([^"]+)').search(videopage)
            if match:
                videourl = match.group(1)
                if videourl.startswith('/'):
                    videourl = 'https://nhplayer.com' + videourl
                    videohtml = utils.getHtml(videourl, site.url)
                    vp.direct_regex = r'file:\s*"([^"]+)"'
                    vp.play_from_html(videohtml)
                    vp.progress.close()
                    return
            else:
                vp.progress.close()
                utils.notify('Oh oh', 'Couldn\'t find a playable link')
        vp.play_from_link_to_resolve(videourl)
    else:
        vp.progress.close()
        utils.notify('Oh oh', 'Couldn\'t find a playable link')
    return
