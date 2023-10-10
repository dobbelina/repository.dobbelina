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
from six.moves import urllib_parse
from resources.lib import utils
from resources.lib.adultsite import AdultSite

site = AdultSite('fuxmovies', '[COLOR hotpink]FuxMovies[/COLOR]', 'https://www.fuxmovies.com/', 'fuxmovies.png', 'fuxmovies')


@site.register(default_mode=True)
def Main(url):
    site.add_dir('[COLOR hotpink]Top Channels[/COLOR]', site.url + 'channels.html', 'Categories', site.img_cat)
    site.add_dir('[COLOR hotpink]Most Viewed[/COLOR]', site.url + 'most-viewed-videos.html', 'List', site.img_cat)
    site.add_dir('[COLOR hotpink]Pornstars Female[/COLOR]', site.url + 'pornstars-female.html', 'Categories', site.img_cat)
    site.add_dir('[COLOR hotpink]Pornstars Male[/COLOR]', site.url + 'pornstars-male.html', 'Categories', site.img_cat)
    site.add_dir('[COLOR hotpink]Categories[/COLOR]', site.url + 'categories.html', 'Categories', site.img_cat)
    site.add_dir('[COLOR hotpink]Search[/COLOR]', site.url + 'search/', 'Search', site.img_search)
    List(site.url + 'page/01.html')
    utils.eod()


@site.register()
def List(url):
    try:
        listhtml = utils.getHtml(url, '')
    except Exception:
        return None

    match = re.compile(r'fullthumbvid"><a\s*?href="/([^"]+)"\s*?title="([^"]+)".*?data-(?:lazy-)*src="([^"]+)".*?class="timer">([^<]+)<', re.DOTALL | re.IGNORECASE).findall(listhtml)
    for videopage, name, img, duration in match:
        name = utils.cleantext(name)
        videopage = videopage if videopage.startswith('http') else site.url + videopage

        contexturl = (utils.addon_sys
                      + "?mode=fuxmovies.Lookupinfo"
                      + "&url=" + urllib_parse.quote_plus(videopage))
        contextmenu = [('[COLOR deeppink]Lookup info[/COLOR]', 'RunPlugin(' + contexturl + ')')]

        site.add_download_link(name, videopage, 'Playvid', img, name, contextm=contextmenu, duration=duration)

    np = re.compile(r'<li\s*?class="active"><a\s*?href="#">\d+?</a></li><li><a href="/([^"]+)">(\d+)<', re.DOTALL | re.IGNORECASE).search(listhtml)
    if np:
        nexturl = np.group(1)
        nexturl = nexturl if nexturl.startswith('http') else site.url + nexturl
        site.add_dir('Next Page ({})'.format(np.group(2)), nexturl, 'List', site.img_next)
    utils.eod()


@site.register()
def Playvid(url, name, download=None):
    vp = utils.VideoPlayer(name, download)
    vp.progress.update(25, "[CR]Loading video page[CR]")
    html = utils.getHtml(url, site.url)
    mydaddy_id = re.search(r'embed_one.php\?id=([^"]+)"', html)
    if mydaddy_id:
        mydaddy_id = mydaddy_id.group(1)
        mydaddy_url = 'https://mydaddy.cc/video/{}/'.format(mydaddy_id)
    else:
        vp.progress.close()
        return
    vp.progress.update(75, "[CR]Video found[CR]")
    vp.play_from_link_to_resolve(mydaddy_url)


@site.register()
def Categories(url):
    try:
        cathtml = utils.getHtml(url, '')
    except Exception:
        return None
    match = re.compile(r'class="fullthumb">\s*?<a\s*?href="/([^"]+)".*?data-(?:lazy-)*src="/([^"]+)"[^<]+<[^>]+?>([^<]+)<', re.DOTALL | re.IGNORECASE).findall(cathtml)
    for catpage, img, name in sorted(match, key=lambda x: x[1]):
        name = utils.cleantext(name)
        img = img if img.startswith('http') else site.url + img
        catpage = catpage if catpage.startswith('http') else site.url + catpage
        site.add_dir(name, catpage, 'List', img)
    utils.eod()


@site.register()
def Search(url, keyword=None):
    if not keyword:
        site.search_dir(url, 'Search')
    else:
        title = keyword.replace(' ', '-')
        url = url + title + '.html'
        List(url)


@site.register()
def Lookupinfo(url):
    class TabootubeLookup(utils.LookupInfo):
        def url_constructor(self, url):
            return url if url.startswith('http') else site.url + url

    lookup_list = [
        ("Tag", r'btn-success"\s*?href="/(tag[^"]+)"\s*?title="([^"]+)"', ''),
    ]

    lookupinfo = TabootubeLookup(site.url, url, 'fuxmovies.List', lookup_list)
    lookupinfo.getinfo()
