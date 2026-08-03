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
import json
import xbmc
from six.moves import urllib_parse


site = AdultSite('noodlemagazine', '[COLOR hotpink]Noodlemagazine[/COLOR]', 'https://noodlemagazine.com/', 'noodlemagazine.png', 'noodlemagazine')

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
    List(site.url + 'now' + getFilters(0), page=0)
    utils.eod()


@site.register()
def List(url, page=0):
    listhtml = utils.getHtml(url, '')

    if 'data-i18n="nothing_found">' in listhtml:
        utils.notify('No results found', 'Try a different search term')
        return

    delimiter = '<div class="item">'
    re_videopage = '<a href="([^"]+)"'
    re_name = 'class="title">([^<]+)<'
    re_img = 'src="(https[^"]+)"'
    re_duration = r'</svg>\s*([:\d]+)<'
    re_quality = r'class="hd_mark">([^<]+)<'
    skip = '${video.title}'

    cm = []
    cm_lookupinfo = (utils.addon_sys + "?mode=noodlemagazine.Lookupinfo&url=")
    cm.append(('[COLOR deeppink]Lookup info[/COLOR]', 'RunPlugin(' + cm_lookupinfo + ')'))
    cm_related = (utils.addon_sys + "?mode=noodlemagazine.Related&url=")
    cm.append(('[COLOR deeppink]Related videos[/COLOR]', 'RunPlugin(' + cm_related + ')'))

    utils.videos_list(site, 'noodlemagazine.Play', listhtml, delimiter, re_videopage, re_name, re_img, re_duration=re_duration, re_quality=re_quality, contextm=cm, skip=skip)

    np = re.compile('class="more" data-page="([^"]+)" data-i18n="show_more"', re.DOTALL | re.IGNORECASE).search(listhtml)
    if np:
        np = np.group(1)
        nextp = url.replace('p=' + str(page), 'p=' + np)
        site.add_dir('Next Page ({})'.format(int(np) + 1), nextp, 'List', site.img_next, page=np)
    utils.eod()


@site.register()
def Play(url, name, download=None):
    vp = utils.VideoPlayer(name, download)
    vp.progress.update(25, "[CR]Loading video page[CR]")
    html = utils.getHtml(url, site.url)
    p = re.compile(r'window.playlist\s*=\s*([^;]+);', re.DOTALL | re.IGNORECASE).search(html)
    if p:
        js = json.loads(p.group(1))
        src = js["sources"]
        sources = {x["label"]: x["file"] for x in src}
        videourl = utils.prefquality(sources, sort_by=lambda x: int(''.join([y for y in x if y.isdigit()])), reverse=True)
        if videourl:
            videourl += '|Referer=' + site.url
        vp.play_from_direct_link(videourl)
    else:
        utils.notify('Oh oh', 'No video found')
        return


@site.register()
def Search(url, keyword=None):
    if not keyword:
        site.search_dir(url, 'Search')
    else:
        title = keyword.replace(' ', '%20')
        searchUrl = url + title + getFilters(0)
        List(searchUrl, 0)


@site.register()
def Babepedia(url):
    try:
        listhtml = utils.getHtml(url, '')
    except Exception:
        return None

    match = re.compile('class="(?:thumbimg|thumbimg lazy)" border="0" (?:data-)*src="([^"]+)" alt="([^"]+)', re.DOTALL | re.IGNORECASE).findall(listhtml)
    for img, name in match:
        name = utils.cleantext(name)
        img = 'https://www.babepedia.com' + img
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
    sortvalue = utils.addon.getSetting('noodlesort') or next(iter(defaults['sort'].keys()))
    hdvalue = utils.addon.getSetting('noodlehd') or next(iter(defaults['hd'].keys()))
    lenvalue = utils.addon.getSetting('noodlelen') or next(iter(defaults['len'].keys()))
    return '?sort={}&hd={}&len={}&p={}'.format(sortvalue, hdvalue, lenvalue, page)


def getFilterLabels():
    defaults = getDefaults()
    sortvalue = utils.addon.getSetting('noodlesort') or next(iter(defaults['sort'].keys()))
    hdvalue = utils.addon.getSetting('noodlehd') or next(iter(defaults['hd'].keys()))
    lenvalue = utils.addon.getSetting('noodlelen') or next(iter(defaults['len'].keys()))

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


@site.register()
def Related(url):
    contexturl = (utils.addon_sys + "?mode=" + str('noodlemagazine.List') + "&url=" + urllib_parse.quote_plus(url))
    xbmc.executebuiltin('Container.Update(' + contexturl + ')')


@site.register()
def Lookupinfo(url):
    lookup_list = [
        ("Tags", r'<a class="vtag" href="/([^"]+)".+?</svg>([^<]+)</a>', ''),
    ]
    lookupinfo = utils.LookupInfo(site.url, url, 'noodlemagazine.List', lookup_list)
    lookupinfo.getinfo()

