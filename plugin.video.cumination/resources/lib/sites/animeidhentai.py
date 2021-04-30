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


site = AdultSite("animeid", "[COLOR hotpink]Animeid Hentai[/COLOR]", "https://animeidhentai.com", "ah.png", "animeid")


@site.register(default_mode=True)
def animeidhentai_main():
    site.add_dir('[COLOR hotpink]Uncensored[/COLOR]', '{0}/genre/hentai-uncensored/'.format(site.url), 'animeidhentai_list', site.img_cat)
    site.add_dir('[COLOR hotpink]Genres[/COLOR]', '{0}/search/'.format(site.url), 'animeidhentai_genres', site.img_cat)
    site.add_dir('[COLOR hotpink]Previews[/COLOR]', '{0}/genre/preview/'.format(site.url), 'animeidhentai_list', site.img_cat)
    site.add_dir('[COLOR hotpink]Trending[/COLOR]', '{0}/trending/'.format(site.url), 'animeidhentai_list', site.img_cat)
    site.add_dir('[COLOR hotpink]Search[/COLOR]', '{0}/search/'.format(site.url), 'animeidhentai_search', site.img_search)
    animeidhentai_list('{0}/genre/2021/'.format(site.url))


@site.register()
def animeidhentai_list(url):
    listhtml = utils.getHtml(url)
    match = re.compile(r'<article.+?data-src="(.*?)" alt="([^"]+)".*?lnk-blk" href="([^"]+)"', re.DOTALL | re.IGNORECASE).findall(listhtml)
    for img, name, video in match:
        if 'uncensored' in name.lower():
            name = name.replace('Uncensored', '') + " [COLOR hotpink][I]Uncensored[/I][/COLOR]"
        site.add_download_link(utils.cleantext(name), video, 'animeidhentai_play', img, name)
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
    listhtml = utils.getHtml(url)
    genres = re.findall("(?si)tt-genres.*?years-filter", listhtml)[0]
    r = re.compile('icr"><span>([^<]+)</span', re.DOTALL | re.IGNORECASE).findall(genres)
    for genre in sorted(r, key=lambda x: x[0].lower()):
        site.add_dir(genre, '{0}/genre/{1}/'.format(site.url, genre.replace(' ', '-')), 'animeidhentai_list', site.img_cat)
    utils.eod()


@site.register()
def animeidhentai_play(url, name, download=None):
    vp = utils.VideoPlayer(name, download)
    vp.progress.update(25, "[CR]Loading video page[CR]")
    videopage = utils.getHtml(url, '')
    r = re.compile(r'<iframe\s*src="([^"]+)', re.DOTALL | re.IGNORECASE).search(videopage)
    if r:
        vp.play_from_link_to_resolve(r.group(1))
    else:
        vp.progress.close()
        return
