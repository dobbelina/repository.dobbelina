"""
    Cumination
    Copyright (C) 2020 Whitecream

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
import json
from six.moves import urllib_parse
from resources.lib import utils
from resources.lib.adultsite import AdultSite

site = AdultSite("hentaidude", "[COLOR hotpink]Hentaidude[/COLOR]", 'https://hentaidude.com/', "https://i.shoujoramune.com/wp-content/themes/awp/images/logo.png", "hentaidude")


@site.register(default_mode=True)
def hentaidude_main():
    site.add_dir('[COLOR hotpink]Uncensored[/COLOR]', site.url + 'tag/uncensored/page/1/?orderby=date', 'hentaidude_list', site.img_cat, 1)
    site.add_dir('[COLOR hotpink]Search[/COLOR]', site.url + 'page/1/?s=', 'hentaidude_search', site.img_search)
    hentaidude_list(site.url + 'page/1/?orderby=date')


@site.register()
def hentaidude_list(url, page=1):
    listhtml = utils.getHtml(url, site.url)
    match = re.compile(r'<a title="([^"]+)".*?href="([^"]+)".*?data-src="([^"]+)(.*?)</a>', re.DOTALL | re.IGNORECASE).findall(listhtml)
    for name, video, img, other in match:
        name = utils.cleantext(name)
        if 'uncensored' in other.lower() or 'uncensored' in name.lower():
            name += " [COLOR hotpink][I]Uncensored[/I][/COLOR]"
        contexturl = (utils.addon_sys
                      + "?mode=" + str('hentaidude.hentaidude_eps')
                      + "&url=" + urllib_parse.quote_plus(video))
        contextmenu = ('[COLOR deeppink]Check other episodes[/COLOR]', 'RunPlugin(' + contexturl + ')')
        site.add_download_link(name, video, 'hentaidude_play', img, name, contextm=contextmenu)
    if 'Next &rsaquo;' in listhtml:
        npage = page + 1
        url = url.replace('/{0}/'.format(page), '/{0}/'.format(npage))
        site.add_dir('Next Page', url, 'hentaidude_list', site.img_next, npage)

    utils.eod()


@site.register()
def hentaidude_search(url, keyword=None):
    if not keyword:
        site.search_dir(url, 'hentaidude_search')
    else:
        title = keyword.replace(' ', '+')
        url += title
        hentaidude_list(url, 1)


@site.register()
def hentaidude_play(url, name, download=None):
    listhtml = utils.getHtml(url, site.url)
    matches = re.compile(r"id:\s*'([^']+)',\s*nonce:\s*'([^']+)'", re.DOTALL | re.IGNORECASE).findall(listhtml)
    if matches:
        posturl = site.url + '/wp-admin/admin-ajax.php'
        postdata = {'action': 'msv-get-sources',
                    'id': matches[0][0],
                    'nonce': matches[0][1]}
        postreturn = utils.postHtml(posturl, form_data=postdata)
        sources = json.loads(postreturn)['sources']
        for i in sources:
            videourl = sources[i]

        vp = utils.VideoPlayer(name, download=download)
        vp.play_from_direct_link(videourl)


@site.register()
def hentaidude_eps(url):
    listhtml = utils.getHtml(url, site.url)
    if 'More Episodes From This Series:' in listhtml:
        episodes = re.findall(r"""href='([^']+)'\s*class="dudep".*?<p>([^<]+)""", listhtml, re.DOTALL | re.IGNORECASE)
        if episodes:
            eps = {}
            for url, episode in episodes:
                episode = episode.strip()
                eps[episode] = url
            selected_episode = utils.selector('Choose episode', eps, show_on_one=True)
            if not selected_episode:
                return
            hentaidude_play(selected_episode, list(eps.keys())[list(eps.values()).index(selected_episode)])
    else:
        utils.notify('Notify', 'No other episodes found')
