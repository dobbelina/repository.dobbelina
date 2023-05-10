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
from resources.lib import utils
from resources.lib.adultsite import AdultSite



site = AdultSite('noodlemagazine', '[COLOR hotpink]Noodlemagazine[/COLOR]', 'https://noodlemagazine.com/', 'noodlemagazine', 'noodlemagazine')

data = {
    "sort": {
        "0": {
            "label": "Date Added",
            "default": True
        },
        "1": {
            "label": "Duration"
        },
        "2": {
            "label": "Relevance"
        }
    },
    "hd": {
        "0": {
            "label": "Everything",
            "default": True
        },
        "1": {
            "label": "HD Only"
        }
    },
    "len": {
        "long": {
            "label": "Long"
        },
        "short": {
            "label": "Short"
        },
        "any": {
            "label": "Any",
            "default": True
        }
    }
}


@site.register(default_mode=True)
def Main(url):
    site.add_download_link(getFilterLabels(), site.url, 'setFilters', '')
    site.add_dir('[COLOR hotpink]Search[/COLOR]', site.url + 'video/', 'Search', site.img_search)
    site.add_dir('[COLOR hotpink]Babepedia Top 100 Pornstar to search for[/COLOR]', 'https://www.babepedia.com/pornstartop100', 'Babepedia', site.img_search)
    utils.eod()


@site.register()
def List(url, page=0):
    utils.kodilog('Url: ' + url)
    try:
        listhtml = utils.getHtml(url, '')
    except:
        return None

    match = re.compile(r'class="item">\s+?<a href="/([^"]+)".*?data-src="([^"]+)".*?alt="([^"]+)">(.*?)</div>.*?</svg> ([^<]+)<', re.DOTALL | re.IGNORECASE).findall(listhtml)
    for videopage, img, name, hd, duration in match:
        name = utils.cleantext(name)
        videopage = site.url + videopage
        hd = " [COLOR orange]HD[/COLOR]" if 'hd_mark' in hd else ''
        img = img.replace('&amp;', '&') + '|Referer=' + site.url

        site.add_download_link(name, videopage, 'Playvid', img, name, duration=duration, quality=hd)

    np = re.compile('class="more" data-page="([^"]+)">', re.DOTALL | re.IGNORECASE).search(listhtml)
    if np:
        np = np.group(1)
        nextp = url.replace('p=' + str(page), 'p=' + np)
        site.add_dir('Next Page ({})'.format(np), nextp, 'List', site.img_next, page=np)
    utils.eod()


@site.register()
def Playvid(url, name, download=None):
    vp = utils.VideoPlayer(name, download)
    vp.progress.update(25, "[CR]Loading video page[CR]")
    html = utils.getHtml(url, site.url)
    srcs = re.compile('/player/([^"]+)', re.DOTALL | re.IGNORECASE).findall(html)
    if srcs:
        surl = srcs[0]
        vp.progress.update(50, "[CR]Video found[CR]")
        surl = site.url + 'playlist/' + surl
        sources = {}
        plhtml = utils.getHtml(surl, site.url)
        videos = re.compile('file": "([^"]+)", "label": "([^"]+)"', re.IGNORECASE | re.DOTALL).findall(plhtml)
        for src, quality in videos:
            sources[quality] = src
        videourl = utils.prefquality(sources, sort_by=lambda x: int(''.join([y for y in x if y.isdigit()])), reverse=True)
        videourl = videourl + '|Referer=' + site.url
        vp.play_from_direct_link(videourl)
    else:
        vp.progress.close()
        utils.notify('Oh oh', 'No video found')
        return


@site.register()
def Search(url, keyword=None):
    searchUrl = url
    if not keyword:
        site.search_dir(url, 'Search')
    else:
        title = keyword.replace(' ', '%20')
        searchUrl = searchUrl + title +  getFilters(0)
        List(searchUrl, 0)

@site.register()
def Babepedia(url):
    try:
        listhtml = utils.getHtml(url, '')
    except:
        return None

    match = re.compile('class="(?:thumbimg|thumbimg lazy)" border="0" (?:data-)*src="([^"]+)" alt="([^"]+)', re.DOTALL | re.IGNORECASE).findall(listhtml)
    for img, name in match:
        name = utils.cleantext(name)
        img = 'https://www.babepedia.com'  + img
        videopage = site.url + 'video/' + name.replace(' ', '%20') + getFilters(0)
        site.add_dir(name, videopage, 'List', img, page=0)
    utils.eod()


@site.register()
def setFilters():
    filters = {'Sort': 'sort', 'Quality': 'hd', 'Length': 'len'}
    chosenfilter = utils.selector('Select filter', filters)
    if chosenfilter:
        options = {v['label']: k for k, v in data[chosenfilter].items()}
        chosenoption = utils.selector('Choose option', options)
        if chosenoption:
            utils.addon.setSetting('noodle' + chosenfilter, chosenoption)
            utils.refresh()


def getFilters(page):
    defaults = getDefaults()
    sortvalue = utils.addon.getSetting('noodlesort') if utils.addon.getSetting('noodlesort') else next(iter(defaults['sort'].keys()))
    hdvalue = utils.addon.getSetting('noodlehd') if utils.addon.getSetting('noodlehd') else next(iter(defaults['hd'].keys()))
    lenvalue = utils.addon.getSetting('noodlelen') if utils.addon.getSetting('noodlelen') else next(iter(defaults['len'].keys()))
    return '?sort={}&hd={}&len={}&p={}'.format(sortvalue, hdvalue, lenvalue, page)


def getFilterLabels():
    defaults = getDefaults()
    sortvalue = utils.addon.getSetting('noodlesort') if utils.addon.getSetting('noodlesort') else next(iter(defaults['sort'].keys()))
    hdvalue = utils.addon.getSetting('noodlehd') if utils.addon.getSetting('noodlehd') else next(iter(defaults['hd'].keys()))
    lenvalue = utils.addon.getSetting('noodlelen') if utils.addon.getSetting('noodlelen') else next(iter(defaults['len'].keys()))

    sortlabel = data['sort'][sortvalue]['label']
    hdlabel = data['hd'][hdvalue]['label']
    lenlabel = data['len'][lenvalue]['label']
    return 'Sort: {} - Quality: {} - Length: {}'.format(sortlabel, hdlabel, lenlabel)


def getDefaults():
    default_items = {}

    for category, options in data.items():
        for key, details in options.items():
            if details.get("default"):
                default_items[category] = {
                    key: {
                        "label": details["label"]
                    }
                }
    return default_items
