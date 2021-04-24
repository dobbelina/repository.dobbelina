'''
    Cumination
    Copyright (C) 2016 Whitecream, hdgdl, holisticdioxide

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

site = AdultSite('xhamster', '[COLOR hotpink]xHamster[/COLOR]', 'https://xhamster.com/', 'xhamster.png', 'xhamster')


@site.register(default_mode=True)
def Main():
    site.add_dir('[COLOR hotpink]Categories[/COLOR]', site.url + 'categories', 'Categories', site.img_cat)
    site.add_dir('[COLOR hotpink]Search[/COLOR]', site.url + 'search/', 'Search', site.img_search)
    List(site.url + 'newest')
    utils.eod()


@site.register()
def List(url):
    url = url.replace('/gay/', '/').replace('/shemale/', '/').replace('?straight=', '')
    cat = get_category()
    if '/search/' in url:
        if 'orientations' not in url:
            url += '&orientations=straight' if '?' in url else '?orientations=straight'
        url = re.sub(r'orientations=[^&]+', 'orientations=' + cat, url)
    else:
        if cat == 'straight':
            url += '?straight='
        else:
            url = url.replace(site.url, site.url + cat + '/')

    response = utils.getHtml(url, site.url)
    if 'data-video-id="' in response:
        videos = response.split('data-video-id="')
        videos.pop(0)
        for video in videos:
            match = re.compile(r'"(.+)src="([^"]+)".+?duration>([^<]+)<.+?href="([^"]+)">([^<]+)<', re.DOTALL | re.IGNORECASE).findall(video)
            if match:
                (hd, img, length, videolink, name) = match[0]
                if 'icon--uhd' in hd:
                    hd = '4k'
                elif 'icon--hd' in hd:
                    hd = 'HD'
                else:
                    hd = ''
                name = utils.cleantext(name)
                context_category = (utils.addon_sys + "?mode=" + str('xhamster.ContextCategory'))
                contextmenu = [('[COLOR violet]Category[/COLOR] [COLOR orange]{}[/COLOR]'.format(get_category()), 'RunPlugin(' + context_category + ')')]
                site.add_download_link(name, videolink, 'Playvid', img, name, contextm=contextmenu, duration=length, quality=hd)

        nextp = re.compile(r'data-page="next"\s*href="([^"]+)', re.DOTALL | re.IGNORECASE).findall(videos[-1])
        if nextp:
            nextp = nextp[0].replace('&#x3D;', '=').replace('&amp;', '&')
            np = re.findall(r'\d+', nextp)[-1]
            lp = re.compile(r'>([\d,]+)<\D+?class="next"', re.DOTALL | re.IGNORECASE).findall(videos[-1])
            lp = '/' + lp[0] if lp else ''
            site.add_dir('Next Page (' + np + lp + ')', nextp, 'List', site.img_next)
    else:
        utils.notify('Cumination', 'No video found.')
    utils.eod()


@site.register()
def Playvid(url, name, download=None):
    vp = utils.VideoPlayer(name, download)
    vp.progress.update(25, "[CR]Loading video page[CR]")
    vp.play_from_link_to_resolve(url)


@site.register()
def Categories(url):
    cat = get_category()
    if cat == 'gay':
        url = url.replace('/categories', '/gay/categories')
    elif cat == 'shemale':
        url = url.replace('/categories', '/shemale/categories')
    cathtml = utils.getHtml(url, site.url)
    cathtml = cathtml.split('class="alphabet"')[-1].split('class="letter-blocks page"')[0]
    match = re.compile('href="([^"]+)"[^>]*>([^<]+)<').findall(cathtml)
    for url, name in match:
        site.add_dir(name.strip(), url, 'CategoriesA', '')
    utils.eod()


@site.register()
def CategoriesA(url):
    cathtml = utils.getHtml(url, site.url)
    cathtml = cathtml.split('class="letter-blocks page"')[-1].split('class="search"')[0]
    match = re.compile('href="([^"]+)"[^>]*>([^<]+)<').findall(cathtml)
    for url, name in match:
        site.add_dir(name.strip(), url + '/newest', 'List', '')
    utils.eod()


@site.register()
def ContextCategory():
    categories = {'straight': 1, 'gay': 2, 'shemale': 3}
    cat = utils.selector('Select category', categories.keys(), sort_by=lambda x: categories[x])
    if cat:
        utils.addon.setSetting('xhamstercat', cat)
        utils.refresh()


def get_category():
    return utils.addon.getSetting('xhamstercat') if utils.addon.getSetting('xhamstercat') else 'straight'


@site.register()
def Search(url, keyword=None):
    searchUrl = url
    if not keyword:
        site.search_dir(url, 'Search')
    else:
        title = keyword.replace(' ', '_')
        searchUrl = searchUrl + title + '?orientations=' + get_category()
        List(searchUrl)
