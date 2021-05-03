'''
    Cumination
    Copyright (C) 2020 Team Cumination

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
from six.moves import urllib_parse
from resources.lib import utils
from resources.lib.adultsite import AdultSite
import json

site = AdultSite('xvideos', '[COLOR hotpink]xVideos[/COLOR]', 'https://www.xvideos.com/', 'xvideos.png', 'xvideos')


@site.register(default_mode=True)
def Main():
    categories = {'Straight': '', 'Gay': 'gay/', 'Trans': 'shemale/'}
    category = utils.addon.getSetting('xvideoscategory') if utils.addon.getSetting('xvideoscategory') else 'Straight'
    country = utils.addon.getSetting('xvideoscountry') if utils.addon.getSetting('xvideoscountry') else 'USA'
    site.add_dir('[COLOR hotpink]Country: [/COLOR] [COLOR orange]{}[/COLOR]'.format(country), site.url, 'Country', site.img_cat)
    site.add_dir('[COLOR hotpink]Category: [/COLOR] [COLOR orange]{}[/COLOR]'.format(category), site.url, 'Category', site.img_cat)
    site.add_dir('[COLOR hotpink]Categories[/COLOR]', site.url + categories[category], 'Categories', site.img_cat)
    cat = 'trans/' if category == 'Trans' else categories[category]
    country = country.lower().replace(' ', '_').replace(',', '_') + '/'
    site.add_dir('[COLOR hotpink]Pornstars[/COLOR]', site.url + 'pornstars-index/{}{}from/worldwide'.format(cat, country), 'Pornstars', site.img_cat)
    site.add_dir('[COLOR hotpink]Tags[/COLOR]', site.url + 'tags', 'Tags', site.img_cat)
    cat = 'straight' if category == 'Straight' else categories[category][:-1]
    site.add_dir('[COLOR hotpink]Search[/COLOR]', site.url + '?typef={}&k='.format(cat), 'Search', site.img_search)
    List(site.url + categories[category])
    utils.eod()


@site.register()
def List(url):
    hdr = dict(utils.base_hdrs)
    hdr['User-Agent'] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:84.0) Gecko/20100101 Firefox/84.0'
    try:
        listhtml = utils.getHtml(url, headers=hdr)
    except:
        return None
    match = re.compile(r'div id="video.+?href="([^"]+)".+?data-src="([^"]+)"(.+?)title="([^"]+)">.+?duration">([^<]+)<', re.DOTALL | re.IGNORECASE).findall(listhtml)
    for videopage, img, res, name, duration in match:
        match = re.search(r'mark">(.+?)<', res)
        res = match.group(1) if match else ''
        name = utils.cleantext(name)

        cm_related = (utils.addon_sys + "?mode=" + str('xvideos.ContextRelated') + "&url=" + urllib_parse.quote_plus(videopage))
        cm = [('[COLOR violet]Related videos[/COLOR]', 'RunPlugin(' + cm_related + ')')]

        site.add_download_link(name, site.url[:-1] + videopage, 'Playvid', img, name, contextm=cm, duration=duration, quality=res)
    npage = re.compile(r'href="([^"]+)" class="no-page next-page', re.DOTALL | re.IGNORECASE).findall(listhtml)
    if npage:
        npage = npage[0].replace('&amp;', '&')
        np = re.findall(r'\d+', npage)[-1]
        if url.split(site.url)[-1] in ('', 'gay/', 'shemale/'):
            npage = npage.replace('/2', '/1')
        else:
            np = str(int(np) + 1)
        if npage == '#1':
            npage = url + '/1'
        elif npage.startswith('#'):
            new = npage.split('#')[-1]
            old = str(int(new) - 1)
            npage = url.replace('/{}'.format(old), '/{}'.format(new))
        if not npage.startswith('http'):
            npage = site.url[:-1] + npage
        site.add_dir('Next Page ({})'.format(np), npage, 'List', site.img_next)
    utils.eod()


@site.register()
def Category(url):
    categories = {'Straight': '', 'Gay': 'gay/', 'Trans': 'shemale/'}
    cat = utils.selector('Select category', categories.keys())
    if cat:
        utils.addon.setSetting('xvideoscategory', cat)
        utils.refresh()


@site.register()
def Country(url):
    countries = {'Afghanistan': 'af', 'Argentina': 'ar', 'Australia': 'au', 'Austria': 'at', 'Azerbaijan': 'az', 'Bangladesh': 'bd', 'Belgium': 'be', 'Bolivia': 'bo', 'Brazil': 'br', 'Bulgaria': 'bg', 'Cambodia': 'kh', 'Cameroon': 'cm', 'Canada': 'ca', 'Chile': 'cl', 'China': 'cn', 'Colombia': 'co', 'Cyprus': 'cy', 'Czech Republic': 'cz', 'Denmark': 'dk', 'Dominican Republic': 'do', 'Ecuador': 'ec', 'Egypt': 'eg', 'Finland': 'fi', 'France': 'fr', 'Georgia': 'ge', 'Germany': 'de', 'Greece': 'gr', 'Guatemala': 'gt', 'Hong Kong': 'hk', 'Hungary': 'hu', 'Iceland': 'is', 'India': 'in', 'Indonesia': 'id', 'Iraq': 'iq', 'Ireland': 'ie', 'Israel': 'il', 'Italy': 'it', 'Japan': 'jp', 'Jordan': 'jo', 'Kenya': 'ke', 'Korea': 'kr', 'Lao People\'s Democratic Republic': 'la', 'Latvia': 'lv', 'Lebanon': 'lb', 'Malaysia': 'my', 'Malta': 'mt', 'Mexico': 'mx', 'Moldova, Republic of': 'md', 'Morocco': 'ma', 'Myanmar': 'mm', 'Netherlands': 'nl', 'New Zealand': 'nz', 'Nigeria': 'ng', 'Norway': 'no', 'Pakistan': 'pk', 'Peru': 'pe', 'Philippines': 'ph', 'Poland': 'pl', 'Portugal': 'pt', 'Qatar': 'qa', 'Romania': 'ro', 'Russia': 'ru', 'Senegal': 'sn', 'Serbia': 'rs', 'Singapore': 'sg', 'Slovakia': 'sk', 'South Africa': 'za', 'Spain': 'es', 'Sri Lanka': 'lk', 'Sweden': 'se', 'Switzerland': 'ch', 'Taiwan': 'tw', 'Tanzania, United Republic of': 'tz', 'Thailand': 'th', 'Tunisia': 'tn', 'USA': 'us', 'Ukraine': 'ua', 'United Kingdom': 'gb', 'Venezuela': 've', 'Vietnam': 'vn'}
    country = utils.selector('Select country', countries.keys())
    if country:
        utils.addon.setSetting('xvideoscountry', country)
        curl = '{}change-country/{}'.format(site.url, countries[country])
        utils._getHtml(curl, site.url)
        utils.clear_cache()
        utils.refresh()


@site.register()
def Categories(url):
    try:
        cathtml = utils.getHtml(url)
    except:
        return None
    match = re.compile(r'href="([^"]+)" class="btn btn-default">([^<]+)<', re.DOTALL | re.IGNORECASE).findall(cathtml)
    for catpage, name in sorted(match, key=lambda x: x[1]):
        site.add_dir(name, site.url[:-1] + catpage, 'List', site.img_cat)
    utils.eod()


@site.register()
def Pornstars(url):
    try:
        cathtml = utils.getHtml(url)
    except:
        return None
    match = re.compile(r'div id="profile.+?src="([^"]+)".+?href="([^"]+)">([^<]+)<\/a><\/p>.+?(\d+ videos)', re.DOTALL | re.IGNORECASE).findall(cathtml)
    for img, catpage, name, videos in match:
        name = '{} [COLOR deeppink]{}[/COLOR]'.format(name, videos)
        catpage += '/videos/best'
        site.add_dir(name, site.url[:-1] + catpage, 'List', img)
    npage = re.compile(r'href="([^"]+)" class="no-page next-page', re.DOTALL | re.IGNORECASE).findall(cathtml)
    if npage:
        npage = npage[0].replace('&amp;', '&')
        np = re.findall(r'\d+', npage)[-1]
        np = int(np) + 1
        site.add_dir('Next Page ({})'.format(np), site.url[:-1] + npage, 'Pornstars', site.img_next)
    utils.eod()


@site.register()
def Tags(url):
    category = utils.addon.getSetting('xvideoscategory') if utils.addon.getSetting('xvideoscategory') else 'Straight'
    try:
        cathtml = utils.getHtml(url)
    except:
        return None
    match = re.compile(r'href="([^"]+)"><b>([^<]+)</b>.+?>([^<]+)<', re.DOTALL | re.IGNORECASE).findall(cathtml)
    for catpage, name, count in match:
        name = utils.cleantext(name) + "[COLOR deeppink] " + count + "[/COLOR]"
        if '/t:' in catpage:
            catpage = re.sub(r'/t:\w+/', '/', catpage)
        if category == 'Gay':
            catpage = catpage.replace('/tags/', '/tags/t:gay/')
        elif category == 'Trans':
            catpage = catpage.replace('/tags/', '/tags/t:shemale/')
        site.add_dir(name, site.url[:-1] + catpage, 'List', site.img_next)
    utils.eod()


@site.register()
def Playvid(url, name, download=None):
    vp = utils.VideoPlayer(name, download, 'src=&quot;([^&]+)&quot;')
    vp.play_from_site_link(url)


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
def ContextRelated(url):
    contexturl = (utils.addon_sys
                  + "?mode=" + str('xvideos.ListRelated')
                  + "&url=" + urllib_parse.quote_plus(url))
    xbmc.executebuiltin('Container.Update(' + contexturl + ')')


@site.register()
def ListRelated(url):
    url = site.url[:-1] + url
    html = utils.getHtml(url, site.url)
    jhtml = html.split('video_related=[')[-1].split('];')[0]
    jdata = json.loads('[' + jhtml + ']')
    for video in jdata:
        videopage = video['u']
        name = utils.cleantext(str(video['t']))
        namef = utils.cleantext(str(video['tf']))
        duration = video['d']
        img = video['i'].replace(r'\/', '/')
        quality = ''
        if video['td'] == 1:
            quality = '1440p'
        elif video['hp'] == 1:
            quality = '1080p'
        elif video['h'] == 1:
            quality = '720p'
        elif video['hm'] == 1:
            quality = '480p'
        else:
            quality = '360p'
        cm_related = (utils.addon_sys + "?mode=" + str('xvideos.ContextRelated') + "&url=" + urllib_parse.quote_plus(videopage))
        cm = [('[COLOR violet]Related videos[/COLOR]', 'RunPlugin(' + cm_related + ')')]
        site.add_download_link(name, site.url[:-1] + videopage, 'Playvid', img, namef, contextm=cm, duration=duration, quality=quality)
    utils.eod()
