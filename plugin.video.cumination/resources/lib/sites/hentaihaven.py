"""
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
"""

import re
from resources.lib import utils
from resources.lib.adultsite import AdultSite

site = AdultSite('hentaihaven', '[COLOR hotpink]Hentaihaven[/COLOR]', 'https://hentaihaven.org/', 'hh.png', 'hentaihaven')


@site.register(default_mode=True)
def Main():
    site.add_dir('[COLOR hotpink]Categories[/COLOR]', '{0}pick-your-poison/'.format(site.url), 'Categories', site.img_cat)
    site.add_dir('[COLOR hotpink]A to Z[/COLOR]', '{0}pick-your-series/'.format(site.url), 'A2Z', '', '')
    site.add_dir('[COLOR hotpink]Uncensored[/COLOR]', '{0}ajax.php?action=pukka_infinite_scroll&page_no=1&grid_params=infinite_scroll=on&infinite_page=2&infinite_more=true&current_page=taxonomy&front_page_cats=&inner_grid%5Buse_inner_grid%5D=on&inner_grid%5Btax%5D=post_tag&inner_grid%5Bterm_id%5D=53&inner_grid%5Bdate%5D=&search_query=&tdo_tag=uncensored&sort=date'.format(site.url), 'List', '', '')
    site.add_dir('[COLOR hotpink]Search[/COLOR]', "{0}search/".format(site.url), 'Search', site.img_search)
    List('{0}ajax.php?action=pukka_infinite_scroll&page_no=1&grid_params=infinite_scroll=on'.format(site.url))
    utils.eod()


@site.register()
def List(url):
    listhtml = utils.getHtml(url, '')
    listhtml = listhtml.replace('\\', '')
    match = re.compile(r'<a\s+class="thumbnail-image" href="([^"]+)".*?data-src="([^"]+)"(.*?)<h3>[^>]+>([^<]+)<', re.DOTALL | re.IGNORECASE).findall(listhtml)
    for videopage, img, other, name in match:
        name = utils.cleantext(name)
        if 'uncensored' in other:
            name = name + " [COLOR orange]Uncensored[/COLOR]"
        site.add_download_link(name, videopage, 'Playvid', img, '')

    page = re.compile(r'page_no=(\d+)', re.DOTALL | re.IGNORECASE).search(url)
    if page:
        page = int(page.group(1))
        npage = page + 1
        maxpages = re.compile(r'max_num_pages":(\d+)', re.DOTALL | re.IGNORECASE).findall(listhtml)[0]
        if int(maxpages) > page:
            nextp = url.replace("no=" + str(page), "no=" + str(npage))
            site.add_dir('Next Page (' + str(npage) + ')', nextp, 'List', site.img_next)

    utils.eod()


@site.register()
def Playvid(url, name, download=None):
    links = {}
    vp = utils.VideoPlayer(name, download)
    vp.progress.update(25, "[CR]Loading video page[CR]")
    videopage = utils.getHtml(url)
    iframes = re.compile(r'<iframe.+?src="([^"]+)"[^>]+>.*?</iframe', re.DOTALL | re.IGNORECASE).findall(videopage)
    if iframes:
        for link in iframes:
            if vp.resolveurl.HostedMediaFile(link).valid_url():
                links[link.split('/')[2]] = link
    srcs = re.compile(r'label="([^"]+)"\s*src="([^"]+)" type=', re.DOTALL | re.IGNORECASE).findall(videopage)
    if srcs:
        for quality, videourl in srcs:
            links['Direct ' + quality] = videourl.replace(' ', '%20') + '|Referer=%s&User-Agent=%s&verifypeer=false' % (url, utils.USER_AGENT)

    videourl = utils.selector('Select link', links)
    if '|Referer' in videourl:
        vp.play_from_direct_link(videourl)
    else:
        vp.play_from_link_to_resolve(videourl)


@site.register()
def Categories(url):
    cathtml = utils.getHtml(url, '')
    match = re.compile(r'/tag/([^/]+)/" cla[^>]+>([^<]+)<', re.DOTALL | re.IGNORECASE).findall(cathtml)
    for catpage, name in match:
        catpage = "{0}ajax.php?action=pukka_infinite_scroll&page_no=1&grid_params=infinite_scroll=on&infinite_page=2&infinite_more=true&current_page=taxonomy&front_page_cats=&inner_grid%5Buse_inner_grid%5D=on&inner_grid%5Btax%5D=post_tag&inner_grid%5Bterm_id%5D=53&inner_grid%5Bdate%5D=&search_query=&tdo_tag=".format(site.url) + catpage + "&sort=date"
        site.add_dir(name, catpage, 'List', '')
    utils.eod()


@site.register()
def A2Z(url):
    cathtml = utils.getHtml(url, '')
    match = re.compile(r'class="cat_section"><a\s+href="([^"]+)"[^>]+>([^<]+)<.*?src="([^"]+)"(.*?)</div>', re.DOTALL | re.IGNORECASE).findall(cathtml)
    for catpage, name, img, other in match:
        if 'uncensored' in other:
            name = name + " [COLOR hotpink]Uncensored[/COLOR]"
        site.add_dir(name, catpage, 'List', img)
    utils.eod()


@site.register()
def Search(url, keyword=None):
    searchUrl = url
    if not keyword:
        site.search_dir(url, 'Search')
    else:
        title = keyword.replace(' ', '+')
        searchUrl = searchUrl + title
        List(searchUrl)
