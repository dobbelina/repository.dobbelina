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

import json
from six.moves import urllib_parse
from resources.lib import utils
from resources.lib.adultsite import AdultSite

site = AdultSite("hanime", "[COLOR hotpink]hanime.tv[/COLOR]", 'https://hanime.tv', "hanime.png", "hanime")
ua = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.129 Safari/537.36'
tags = ['3D', 'Ahegao', 'Anal', 'BDSM', 'Big Boobs', 'Blow Job', 'Bondage', 'Boob Job', 'Censored', 'Comedy', 'Cosplay',
        'Creampie', 'Dark Skin', 'Facial', 'Fantasy', 'Filmed', 'Foot Job', 'Futanari', 'Gangbang', 'Glasses', 'Hand Job',
        'Harem', 'HD', 'Horror', 'Incest', 'Inflation', 'Lactation', 'Loli', 'Maid', 'Masturbation', 'Milf', 'Mind Break',
        'Mind Control', 'Monster', 'Nekomimi', 'NTR', 'Nurse', 'Orgy', 'Plot', 'POV', 'Pregnant', 'Public Sex', 'Rape',
        'Reverse Rape', 'Rimjob', 'Scat', 'School Girl', 'Shota', 'Softcore', 'Swimsuit', 'Teacher', 'Tentacle', 'Threesome',
        'Toys', 'Trap', 'Tsundere', 'Ugly Bastard', 'Uncensored', 'Vanilla', 'Virgin', 'Watersports', 'X-Ray', 'Yaoi', 'Yuri']
hanime_headers = {'x-directive': 'api',
                  'x-time': '0',
                  'x-signature-version': 'web2',
                  'User-Agent': ua,
                  'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                  'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.3',
                  'Accept-Encoding': 'gzip',
                  'Accept-Language': 'en-US,en;q=0.8',
                  'Connection': 'keep-alive'}


@site.register(default_mode=True)
def hanime_main():
    site.add_dir('[COLOR hotpink]Uncensored[/COLOR]', 'uncensored', 'hanime_list', site.img_cat, 0)
    site.add_dir('[COLOR hotpink]Filter by tags[/COLOR]', site.url, 'hanime_filter', site.img_search)
    site.add_dir('[COLOR hotpink]Search[/COLOR]', site.url, 'hanime_search', site.img_search)
    hanime_list('', '', 0)


@site.register()
def hanime_list(url='', search='', page=0):
    tag = []
    if url:
        if '|' in url:
            tag = url.split('|')
        else:
            tag.append(url)
    mode = 'OR' if len(tag) == 1 else 'AND'

    siteurl = 'https://search.htv-services.com/'
    data = {"search_text": search,
            "tags": tag,
            "tags_mode": mode,
            "brands": [],
            "blacklist": [],
            "order_by": "created_at_unix",
            "ordering": "desc",
            "page": page
            }
    _user_agent = 'Mozilla/5.0 (X11; Linux i686) AppleWebKit/535.1 ' + \
                  '(KHTML, like Gecko) Chrome/13.0.782.99 Safari/535.1'
    try:
        listhtml = utils.postHtml(siteurl, json_data=data, headers={'User-Agent': _user_agent})
    except Exception as e:
        utils.notify('Notify', e)
        return None
    hits = json.loads(listhtml)
    videos = json.loads(hits['hits'])
    for video in videos:
        name = video['name']
        if video['is_censored'] is False:
            name = name + " [COLOR hotpink][I]Uncensored[/I][/COLOR]"
        videoid = video['slug']
        img = video['cover_url'].replace('highwinds-cdn.com', 'droidbuzz.top')
        fanart = video['poster_url'].replace('highwinds-cdn.com', 'droidbuzz.top')
        plot = video['description'].replace('<p>', '').replace('</p>', '')
        if utils.PY2:
            plot = plot.encode('ascii', 'ignore')
        tags = ', '.join(sorted(video['tags']))
        plot = '[COLOR hotpink][I]Tags: {1}[/I][/COLOR]\n\n{0}'.format(plot, tags)
        contexturl = (utils.addon_sys
                      + "?mode=" + str('hanime.hanime_eps')
                      + "&url=" + urllib_parse.quote_plus(videoid))
        contextmenu = ('[COLOR deeppink]Check other episodes[/COLOR]', 'RunPlugin(' + contexturl + ')')
        site.add_download_link(name, videoid, 'hanime_play', img, plot, noDownload=True, contextm=contextmenu, fanart=fanart)

    if 'nbPages' in hits:
        totalp = hits['nbPages']
        npage = page + 1
        if npage < totalp:
            site.add_dir('Next Page', url, 'hanime_list', site.img_next, npage)

    utils.eod()


@site.register()
def hanime_search(url, keyword=None):
    if not keyword:
        site.search_dir(url, 'hanime_search')
    else:
        hanime_list('', keyword, 0)


@site.register()
def hanime_filter():
    selected_tags = utils.dialog.multiselect('Select (multiple) tags to filter on', tags)
    if selected_tags:
        stags = '|'.join([tags[x].lower() for x in selected_tags])
        hanime_list(stags, '', 0)


@site.register()
def hanime_play(url, name, download=None):
    url = 'https://hanime.tv/rapi/v7/videos_manifests/{0}'.format(url)
    listhtml = utils.getHtml(url, headers=hanime_headers)
    streams = json.loads(listhtml)['videos_manifest']['servers'][0]['streams']
    sources = {stream.get('height'): stream.get('url') for stream in streams if stream.get('url')}
    if sources:
        vp = utils.VideoPlayer(name, download=download)
        videourl = utils.selector('Select quality', sources, setting_valid='qualityask', sort_by=lambda x: int(x), reverse=True)
        if videourl:
            videourl = videourl + '|User-Agent:' + ua
            vp.play_from_direct_link(videourl)


@site.register()
def hanime_eps(url):
    url = 'https://hanime.tv/api/v8/video?id=' + url
    try:
        listhtml = utils.getHtml(url, headers=hanime_headers)
    except Exception as e:
        utils.notify('Notify', e)
        return None
    try:
        eps = {}
        episodes = json.loads(listhtml)['hentai_franchise_hentai_videos']
        for episode in episodes:
            name = episode['name']
            if episode['is_censored'] is False:
                name = name + " [COLOR hotpink][I]Uncensored[/I][/COLOR]"
            eps[name] = episode['slug']
        selected_episode = utils.selector('Choose episode', eps, show_on_one=True)
        if not selected_episode:
            return
        hanime_play(selected_episode, [x for x, y in eps.items() if y is selected_episode][0])
    except:
        utils.notify('Notify', 'No other episodes found')
