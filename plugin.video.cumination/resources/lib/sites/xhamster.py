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
    site.add_dir('[COLOR hotpink]Channels[/COLOR]', site.url + 'channels', 'Channels', site.img_cat)
    site.add_dir('[COLOR hotpink]Pornstars[/COLOR]', site.url + 'pornstars', 'Pornstars', site.img_cat)
    site.add_dir('[COLOR hotpink]Celebrities[/COLOR]', site.url + 'celebrities', 'Celebrities', site.img_cat)
    site.add_dir('[COLOR hotpink]Search[/COLOR]', site.url + 'search/', 'Search', site.img_search)
    List(site.url + 'newest')
    utils.eod()


@site.register()
def List(url):
    url = update_url(url)

    context_category = (utils.addon_sys + "?mode=" + str('xhamster.ContextCategory'))
    context_length = (utils.addon_sys + "?mode=" + str('xhamster.ContextLength'))
    context_quality = (utils.addon_sys + "?mode=" + str('xhamster.ContextQuality'))
    contextmenu = [('[COLOR violet]Category[/COLOR] [COLOR orange]{}[/COLOR]'.format(get_setting('category')), 'RunPlugin(' + context_category + ')'),
                   ('[COLOR violet]Length[/COLOR] [COLOR orange]{}[/COLOR]'.format(get_setting('length')), 'RunPlugin(' + context_length + ')'),
                   ('[COLOR violet]Quality[/COLOR] [COLOR orange]{}[/COLOR]'.format(get_setting('quality')), 'RunPlugin(' + context_quality + ')')]

    try:
        response = utils.getHtml(url, site.url)
    except Exception as e:
        if '404' in str(e):
            site.add_dir('No videos found. [COLOR hotpink]Clear all filters.[/COLOR]', '', 'ResetFilters', Folder=False, contextm=contextmenu)
            utils.eod()
        return

    if 'data-video-id="' in response:
        videos = response.split('data-video-id="')
        videos.pop(0)
        for video in videos:
            match = re.compile(r'src="([^"]+)".+?duration>([^<]+)<.+?href="([^"]+)">([^<]+)<', re.DOTALL | re.IGNORECASE).findall(video)
            if match:
                (img, length, videolink, name) = match[0]
                if 'icon--uhd' in video:
                    hd = '4k'
                elif 'icon--hd' in video:
                    hd = 'HD'
                else:
                    hd = ''
                name = utils.cleantext(name)
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
    cat = get_setting('category')
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
def Channels(url):
    cat = get_setting('category')
    if cat == 'gay':
        url = url.replace('/channels', '/gay/channels')
    elif cat == 'shemale':
        url = url.replace('/channels', '/shemale/channels')
    cathtml = utils.getHtml(url, site.url)
    cathtml = cathtml.split('class="alphabet')[-1].split('class="letter-blocks')[0]
    match = re.compile('href="([^"]+)"[^>]*>([^<]+)<').findall(cathtml)
    for url, name in match:
        site.add_dir(name.strip(), url, 'ChannelsA', '')
    utils.eod()


@site.register()
def ChannelsA(url):
    cathtml = utils.getHtml(url, site.url)
    cathtml = cathtml.split('class="letter-blocks')[-1].split('class="alphabet')[0]
    match = re.compile('href="([^"]+)"[^>]*>([^<]+)<').findall(cathtml)
    for url, name in match:
        site.add_dir(name.strip(), url + '/newest', 'List', '')
    utils.eod()


@site.register()
def Pornstars(url):
    cat = get_setting('category')
    if cat == 'gay':
        url = url.replace('/pornstars', '/gay/pornstars')
    elif cat == 'shemale':
        url = url.replace('/pornstars', '/shemale/pornstars')
    cathtml = utils.getHtml(url, site.url)
    cathtml = cathtml.split('class="alphabet')[-1].split('class="letter-blocks')[0]
    match = re.compile('href="([^"]+)"[^>]*>([^<]+)<').findall(cathtml)
    for url, name in match:
        site.add_dir(name.strip(), url, 'PornstarsA', '')
    utils.eod()


@site.register()
def PornstarsA(url):
    cathtml = utils.getHtml(url, site.url)
    cathtml = cathtml.split('class="letter-blocks')[-1].split('class="search"')[0]
    match = re.compile('href="([^"]+)"[^>]*>([^<]+)<').findall(cathtml)
    for url, name in match:
        site.add_dir(name.strip(), url + '/newest', 'List', '')
    utils.eod()


@site.register()
def Celebrities(url):
    cat = get_setting('category')
    if cat == 'gay':
        url = url.replace('/celebrities', '/gay/celebrities')
    elif cat == 'shemale':
        url = url.replace('/celebrities', '/shemale/celebrities')
    cathtml = utils.getHtml(url, site.url)
    cathtml = cathtml.split('class="alphabet')[-1].split('class="letter-blocks')[0]
    match = re.compile('href="([^"]+)"[^>]*>([^<]+)<').findall(cathtml)
    for url, name in match:
        site.add_dir(name.strip(), url, 'CelebritiesA', '')
    utils.eod()


@site.register()
def CelebritiesA(url):
    cathtml = utils.getHtml(url, site.url)
    cathtml = cathtml.split('class="letter-blocks')[-1].split('class="search"')[0]
    match = re.compile('href="([^"]+)"[^>]*>([^<]+)<').findall(cathtml)
    for url, name in match:
        site.add_dir(name.strip(), url + '/newest', 'List', '')
    utils.eod()


@site.register()
def Search(url, keyword=None):
    searchUrl = url
    if not keyword:
        site.search_dir(url, 'Search')
    else:
        title = keyword.replace(' ', '%20')
        searchUrl = searchUrl + title + '?orientations=' + get_setting('category')
        List(searchUrl)


@site.register()
def ContextCategory():
    categories = {'straight': 1, 'gay': 2, 'shemale': 3}
    cat = utils.selector('Select category', categories.keys(), sort_by=lambda x: categories[x])
    if cat:
        utils.addon.setSetting('xhamstercat', cat)
        if cat == 'straight':
            utils._getHtml('https://xhamster.com/?straight=', site.url)
        else:
            utils._getHtml('https://xhamster.com/' + cat, site.url)
        utils.refresh()


@site.register()
def ContextLength():
    categories = {'ALL': 1, '40+ min': 2, '10-40 min': 3, '0-10 min': 4}
    cat = utils.selector('Select category', categories.keys(), sort_by=lambda x: categories[x])
    if cat:
        utils.addon.setSetting('xhamsterlen', cat)
        utils.refresh()


@site.register()
def ContextQuality():
    categories = {'ALL': 1, 'hd': 2, '4k': 3, 'vr': 4}
    cat = utils.selector('Select category', categories.keys(), sort_by=lambda x: categories[x])
    if cat:
        utils.addon.setSetting('xhamsterqual', cat)
        utils.refresh()


def get_setting(x):
    if x == 'category':
        ret = utils.addon.getSetting('xhamstercat') if utils.addon.getSetting('xhamstercat') else 'straight'
    if x == 'length':
        ret = utils.addon.getSetting('xhamsterlen') if utils.addon.getSetting('xhamsterlen') else 'ALL'
    if x == 'quality':
        ret = utils.addon.getSetting('xhamsterqual') if utils.addon.getSetting('xhamsterqual') else 'ALL'
    return ret


def update_url(url):
    cat = get_setting('category')
    old_cat = 'straight'
    if url.startswith(site.url + 'gay') or 'orientations=gay' in url:
        old_cat = 'gay'
    elif url.startswith(site.url + 'shemale') or 'orientations=shemale' in url:
        old_cat = 'shemale'

    if cat != old_cat:
        if '/search/' in url:
            url = re.sub(r'[\?&]page=[^\?&]+', '', url)
            url = re.sub(r'[\?&]orientations=[^\?&]+', '', url)
            if cat != 'straight':
                url += '&orientations=' + cat if '?' in url else '?orientations=' + cat
        else:
            url = re.sub(r'newest/\d+', 'newest', url)
            if old_cat == 'straight':
                url = url.replace(site.url, site.url + cat + '/')
            else:
                url = url.replace(site.url + old_cat, site.url[:-1]) if cat == 'straight' else url.replace(site.url + old_cat, site.url + cat)

    qual = get_setting('quality')
    q = url.split('/')
    if 'hd' in q or 'quality=hd' in url:
        old_qual = 'hd'
    elif '4k' in q or 'quality=4k' in url:
        old_qual = '4k'
    elif 'vr' in q or 'quality=vr' in url:
        old_qual = 'vr'
    else:
        old_qual = 'ALL'

    if qual != old_qual:
        url = re.sub(r'[\?&]page=[^\?&]+', '', url)
        if 'search' in url:
            url = re.sub(r'[\?&]quality=[^\?&]+', '', url)
            if qual != 'ALL':
                url += '&quality=' + qual if '?' in url else '?quality=' + qual
        else:
            url = re.sub(r'newest/\d+', 'newest', url)
            url = url.replace('/hd', '').replace('/4k', '').replace('/vr', '')
            if qual != 'ALL':
                url = url.split('newest')
                url[0] += qual + '/'
                url = 'newest'.join(url)

    length = get_setting('length')
    if 'max-duration=10' in url:
        old_length = '0-10 min'
    elif 'max-duration=40' in url:
        old_length = '10-40 min'
    elif 'max-duration=40' in url:
        old_length = '40+ min'
    else:
        old_length = 'ALL'

    if length != old_length:
        url = re.sub(r'[\?&]page=[^\?&]+', '', url)
        url = re.sub(r'newest/\d+', 'newest', url)
        url = re.sub(r'[\?&]min-duration=[^\?&]+', '', url)
        url = re.sub(r'[\?&]max-duration=[^\?&]+', '', url)
        if length == '0-10 min':
            url += '&max-duration=10' if '?' in url else '?max-duration=10'
        elif length == '10-40 min':
            url += '&min-duration=10' if '?' in url else '?min-duration=10'
            url += '&max-duration=40'
        elif length == '40+ min':
            url += '&min-duration=40' if '?' in url else '?min-duration=40'
    return url


@site.register()
def ResetFilters():
    utils.addon.setSetting('xhamstercat', 'straight')
    utils.addon.setSetting('xhamsterlen', 'ALL')
    utils.addon.setSetting('xhamsterqual', 'ALL')
    utils.refresh()
    return
