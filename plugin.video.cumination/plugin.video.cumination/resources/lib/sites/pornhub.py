'''
    Cumination
    Copyright (C) 2015 Whitecream
    Copyright (C) 2015 anton40
    Copyright (C) 2015 Team Cumination

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

site = AdultSite('pornhub', '[COLOR hotpink]PornHub[/COLOR]', 'https://www.pornhub.com/', 'pornhub.png', 'pornhub')
cookiehdr = {'Cookie': 'accessAgeDisclaimerPH=1'}


@site.register(default_mode=True)
def Main():
    site.add_dir('[COLOR hotpink]Search[/COLOR]', site.url + 'video/search?search=', 'Search', site.img_search)
    site.add_dir('[COLOR hotpink]Categories[/COLOR]', site.url + 'categories', 'Categories', site.img_cat)
    List(site.url + 'video?o=cm')
    utils.eod()


@site.register()
def List(url):
    url = update_url(url)

    cm_production = (utils.addon_sys + "?mode=" + str('pornhub.ContextProduction'))
    cm_min_length = (utils.addon_sys + "?mode=" + str('pornhub.ContextMinLength'))
    cm_max_length = (utils.addon_sys + "?mode=" + str('pornhub.ContextMaxLength'))
    cm_quality = (utils.addon_sys + "?mode=" + str('pornhub.ContextQuality'))
    cm_country = (utils.addon_sys + "?mode=" + str('pornhub.ContextCountry'))
    cm_sortby = (utils.addon_sys + "?mode=" + str('pornhub.ContextSortby'))
    cm_time = (utils.addon_sys + "?mode=" + str('pornhub.ContextTime'))
    cm_filter = [('[COLOR violet]Production[/COLOR] [COLOR orange]{}[/COLOR]'.format(get_setting('production')), 'RunPlugin(' + cm_production + ')'),
                 ('[COLOR violet]Min Length[/COLOR] [COLOR orange]{}[/COLOR]'.format(get_setting('minlength')), 'RunPlugin(' + cm_min_length + ')'),
                 ('[COLOR violet]Max Length[/COLOR] [COLOR orange]{}[/COLOR]'.format(get_setting('maxlength')), 'RunPlugin(' + cm_max_length + ')'),
                 ('[COLOR violet]Quality[/COLOR] [COLOR orange]{}[/COLOR]'.format(get_setting('quality')), 'RunPlugin(' + cm_quality + ')'),
                 ('[COLOR violet]Country[/COLOR] [COLOR orange]{}[/COLOR]'.format(get_setting('country')), 'RunPlugin(' + cm_country + ')'),
                 ('[COLOR violet]Sort By[/COLOR] [COLOR orange]{}[/COLOR]'.format(get_setting('sortby')), 'RunPlugin(' + cm_sortby + ')'),
                 ('[COLOR violet]Time[/COLOR] [COLOR orange]{}[/COLOR]'.format(get_setting('time')), 'RunPlugin(' + cm_time + ')')]

    listhtml = utils.getHtml(url, site.url, cookiehdr)
    if 'Error Page Not Found' in listhtml or not listhtml:
        site.add_dir('No videos found. [COLOR hotpink]Clear all filters.[/COLOR]', '', 'ResetFilters', Folder=False, contextm=cm_filter)
        utils.eod()
        return

    match = re.compile(r'(?:<h1>|<h1  class="searchPageTitle">)([^<]+)</h1>', re.DOTALL).findall(listhtml)
    if match:
        title = utils.cleantext(match[0].strip())
        site.add_dir('[COLOR orange]' + title + ' [COLOR hotpink]*** Clear all filters.[/COLOR]', '', 'ResetFilters', Folder=False, contextm=cm_filter)

    main_block = re.compile(r'videos\s*search-video-thumbs.*?">(.*?)<div\s*class="reset">', re.DOTALL).findall(listhtml)[0]
    match = re.compile(r'class="pcVideoListItem.+?data-mediumthumb\s*=\s*"([^"]+).+?tion">([^<]+)(.*?)</div.+?href="([^"]+).+?>\s*(.+?)\s*<', re.DOTALL).findall(main_block)
    for img, duration, hd, videopage, name in match:
        hd = 'HD' if 'HD' in hd else ''
        name = utils.cleantext(name)
        site.add_download_link(name, site.url[:-1] + videopage, 'Playvid', img, name, contextm=cm_filter, duration=duration, quality=hd)

    nextp = re.compile(r'<li\s*class="page_next">\s*<a\s*href="([^"]+)"', re.DOTALL).search(listhtml)
    if nextp:
        np = re.compile(r'page=(\d+)').search(nextp.group(1))
        if np:
            np = np.group(1)
        else:
            np = ''
        match = re.compile(r'Showing \d+-\d+\s*of\s*\d+', re.DOTALL).search(listhtml)
        if match:
            lp = '[COLOR hotpink] ... ' + match.group(0) + '[/COLOR]'
        else:
            lp = ''
        site.add_dir('Next Page ({}){}'.format(np, lp), site.url[:-1] + nextp.group(1).replace('&amp;', '&'), 'List', site.img_next)
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


@site.register()
def Categories(url):
    cathtml = utils.getHtml(url, site.url, cookiehdr)
    match = re.compile(r'<div class="category-wrapper.*?<a href="([^"]+)"\s*alt="([^"]+)".*?img\s+src="([^"]+).+?<var>([^<]+)<', re.DOTALL).findall(cathtml)
    for catpage, name, img, videos in match:
        catpage = site.url[:-1] + catpage
        site.add_dir(name, catpage, 'List', img, '')
    utils.eod()


@site.register()
def Playvid(url, name, download=None):
    vp = utils.VideoPlayer(name, download)
    vp.play_from_link_to_resolve(url)


def get_setting(x):
    dict = {'production': 'All', 'minlength': '0', 'maxlength': '40+ Min', 'quality': 'All', 'country': 'World', 'sortby': 'Newest', 'time': 'All Time'}
    if x in dict.keys():
        ret = utils.addon.getSetting('pornhub' + x) if utils.addon.getSetting('pornhub' + x) else dict[x]
    else:
        ret = ''
    return ret


@site.register()
def ContextProduction():
    filters = {'All': 1, 'Professional': 2, 'Homemade': 3}
    cat = utils.selector('Select production', filters.keys(), sort_by=lambda x: filters[x])
    if cat:
        utils.addon.setSetting('pornhubproduction', cat)
        utils.refresh()


@site.register()
def ContextMinLength():
    filters = {'0': 1, '10 min': 2, '20 min': 3, '30 min': 4}
    cat = utils.selector('Select Min Legth', filters.keys(), sort_by=lambda x: filters[x])
    if cat:
        utils.addon.setSetting('pornhubminlength', cat)
        utils.refresh()


@site.register()
def ContextMaxLength():
    filters = {'10 Min': 1, '20 Min': 2, '30 Min': 3, '40+ Min': 4}
    cat = utils.selector('Select Max Legth', filters.keys(), sort_by=lambda x: filters[x])
    if cat:
        utils.addon.setSetting('pornhubmaxlength', cat)
        utils.refresh()


@site.register()
def ContextQuality():
    filters = {'All': 1, 'HD': 2}
    cat = utils.selector('Select Quality', filters.keys(), sort_by=lambda x: filters[x])
    if cat:
        utils.addon.setSetting('pornhubquality', cat)
        utils.refresh()


@site.register()
def ContextCountry():
    cc = {'World': '', 'Argentina': 'cc=ar', 'Australia': 'cc=au', 'Austria': 'cc=at', 'Belgium': 'cc=be', 'Brazil': 'cc=br', 'Bulgaria': 'cc=bg',
          'Canada': 'cc=ca', 'Chile': 'cc=cl', 'Croatia': 'cc=hr', 'Czech Republic': 'cc=cz', 'Denmark': 'cc=dk', 'Egypt': 'cc=eg', 'Finland': 'cc=fi',
          'France': 'cc=fr', 'Germany': 'cc=de', 'Greece': 'cc=gr', 'Hungary': 'cc=hu', 'India': 'cc=in', 'Ireland': 'cc=ie', 'Israel': 'cc=il',
          'Italy': 'cc=it', 'Japan': 'cc=jp', 'Mexico': 'cc=mx', 'Morocco': 'cc=ma', 'Netherlands': 'cc=nl', 'New Zealand': 'cc=nz', 'Norway': 'cc=no',
          'Pakistan': 'cc=pk', 'Poland': 'cc=pl', 'Portugal': 'cc=pt', 'Romania': 'cc=ro', 'Russian Federation': 'cc=ru', 'Serbia': 'cc=rs',
          'Slovakia': 'cc=sk', 'Korea => Republic of': 'cc=kr', 'Spain': 'cc=es', 'Sweden': 'cc=se', 'Switzerland': 'cc=ch', 'United Kingdom': 'cc=gb',
          'Ukraine': 'cc=ua', 'United States': 'cc=us'}
    cat = utils.selector('Select Country', cc.keys())
    if cat:
        utils.addon.setSetting('pornhubcountry', cat)
        utils.refresh()


@site.register()
def ContextSortby():
    filters = {'Newest': 1, 'Hottest': 2, 'Longest': 3, 'Top Rated': 4, 'Most Viewed': 5, 'Featured Recently/Most Relevant': 6}
    cat = utils.selector('Select Sort Order', filters.keys(), sort_by=lambda x: filters[x])
    if cat:
        utils.addon.setSetting('pornhubsortby', cat)
        utils.refresh()


@site.register()
def ContextTime():
    filters = {'All Time': 1, 'Daily': 2, 'Weekly': 3, 'Monthly': 4, 'Yearly': 5}
    cat = utils.selector('Select time', filters.keys(), sort_by=lambda x: filters[x])
    if cat:
        utils.addon.setSetting('pornhubtime', cat)
        utils.refresh()


def param(x):
    cc = {'World': '', 'Argentina': 'cc=ar', 'Australia': 'cc=au', 'Austria': 'cc=at', 'Belgium': 'cc=be', 'Brazil': 'cc=br', 'Bulgaria': 'cc=bg',
          'Canada': 'cc=ca', 'Chile': 'cc=cl', 'Croatia': 'cc=hr', 'Czech Republic': 'cc=cz', 'Denmark': 'cc=dk', 'Egypt': 'cc=eg', 'Finland': 'cc=fi',
          'France': 'cc=fr', 'Germany': 'cc=de', 'Greece': 'cc=gr', 'Hungary': 'cc=hu', 'India': 'cc=in', 'Ireland': 'cc=ie', 'Israel': 'cc=il',
          'Italy': 'cc=it', 'Japan': 'cc=jp', 'Mexico': 'cc=mx', 'Morocco': 'cc=ma', 'Netherlands': 'cc=nl', 'New Zealand': 'cc=nz', 'Norway': 'cc=no',
          'Pakistan': 'cc=pk', 'Poland': 'cc=pl', 'Portugal': 'cc=pt', 'Romania': 'cc=ro', 'Russian Federation': 'cc=ru', 'Serbia': 'cc=rs',
          'Slovakia': 'cc=sk', 'Korea => Republic of': 'cc=kr', 'Spain': 'cc=es', 'Sweden': 'cc=se', 'Switzerland': 'cc=ch', 'United Kingdom': 'cc=gb',
          'Ukraine': 'cc=ua', 'United States': 'cc=us'}
    dict = {'All': '', 'Professional': 'p=professional', 'Homemade': 'p=homemade',
            '0': '', '10 min': 'min_duration=10', '20 min': 'min_duration=20', '30 min': 'min_duration=30',
            '10 Min': 'max_duration=10', '20 Min': 'max_duration=20', '30 Min': 'max_duration=30', '40+ Min': '',
            'HD': 'hd=1',
            'Newest': 'o=cm', 'Hottest': 'o=ht', 'Longest': 'o=lg', 'Top Rated': 'o=tr', 'Most Viewed': 'o=mv', 'Featured Recently/Most Relevant': '',
            'All Time': 't=a', 'Daily': 't=t', 'Weekly': 't=w', 'Monthly': '', 'Yearly': 't=y'}
    dict.update(cc)
    if x in dict.keys():
        ret = dict[x]
    else:
        utils.kodilog('Key error: ' + str(x))
        ret = ''
    return ret


def update_url(url):
    old_params = url.split('?')[-1].split('&')
    old_params.sort()
    url = re.sub(r'[\?&]p=[^\?&]+', '', url)
    url = re.sub(r'[\?&]min_duration=[^\?&]+', '', url)
    url = re.sub(r'[\?&]max_duration=[^\?&]+', '', url)
    url = re.sub(r'[\?&]hd=[^\?&]+', '', url)
    url = re.sub(r'[\?&]o=[^\?&]+', '', url)
    url = re.sub(r'[\?&]t=[^\?&]+', '', url)
    url = re.sub(r'[\?&]cc=[^\?&]+', '', url)

    params = {param(get_setting('production')), param(get_setting('minlength')), param(get_setting('maxlength')),
              param(get_setting('quality')), param(get_setting('country')), param(get_setting('sortby')), param(get_setting('time'))}

    for x in params:
        if x != '':
            url += '&' + x

    if 'search?' in url:
        url = url.replace('o=cm', 'o=mr')
        url = re.sub(r'[\?&]o=ht[^\?&]+', '', url)

    if 'o=' not in url or 'o=lg' in url or 'o=cm' in url or 'o=mr' in url:
        url = re.sub(r'[\?&]t=[^\?&]+', '', url)
        url = re.sub(r'[\?&]cc=[^\?&]+', '', url)
    if 'o=tr' in url:
        url = re.sub(r'[\?&]cc=[^\?&]+', '', url)
    if 'o=ht' in url:
        url = re.sub(r'[\?&]t=[^\?&]+', '', url)
    if '?' not in url:
        url = url.replace('&', '?', 1)

    new_params = url.split('?')[-1].split('&')
    new_params.sort()

    if new_params != old_params:
        url = re.sub(r'[\?&]page=[^\?&]+', '', url)
    if '?' not in url:
        url = url.replace('&', '?', 1)
    return url


@site.register()
def ResetFilters():
    dict = {'production': 'All', 'minlength': '0', 'maxlength': '40+ Min', 'quality': 'All', 'country': 'World', 'sortby': 'Newest', 'time': 'All Time'}
    for x in dict.keys():
        utils.addon.setSetting('pornhub' + x, dict[x])
    utils.refresh()
    return
