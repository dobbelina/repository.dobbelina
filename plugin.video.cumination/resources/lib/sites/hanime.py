"""
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
"""

import json
import hashlib
import time
import xbmc
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
htvlogged = 'true' in utils.addon.getSetting('htvlogged')
getinput = utils._get_keyboard
apiurl = 'https://www.universal-cdn.com'


@site.register(default_mode=True)
def hanime_main():
    site.add_dir('[COLOR hotpink]Uncensored[/COLOR]', 'uncensored', 'hanime_list', site.img_cat, 0)
    site.add_dir('[COLOR hotpink]Filter by tags[/COLOR]', site.url, 'hanime_filter', site.img_search)
    site.add_dir('[COLOR hotpink]Search[/COLOR]', site.url, 'hanime_search', site.img_search)
    if not htvlogged:
        site.add_dir('[COLOR hotpink]Login[/COLOR]', apiurl, 'hanime_login', site.img_search, Folder=False)
    else:
        site.add_dir('[COLOR hotpink]Logout[/COLOR]', apiurl, 'hanime_login', site.img_search)
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
        utils.notify('Notify', str(e))
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
        site.add_download_link(name, videoid, 'hanime_play_combined', img, plot, noDownload=True, contextm=contextmenu, fanart=fanart)

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


def get_videos(url, member=False):
    videos = {}
    if member:
        headers = makeXheaders()
        session_token = utils.addon.getSetting('session_token')
        build_number = utils.addon.getSetting('build_number')
        headers.update({"X-Session-Token": session_token})
        video_api = "{0}/rapi/v4/downloads/{1}?v={2}".format(apiurl, url, build_number)
    else:
        headers = hanime_headers
        video_api = "https://hanime.tv/rapi/v7/videos_manifests/{0}".format(url)

    videojson = utils.getHtml(video_api, headers=headers)
    if videojson:
        data = json.loads(videojson)
        if member:
            videos = {video['height']: video['url'] for video in data['transcodes'] if video['url']}
        else:
            streams = data['videos_manifest']['servers'][0]['streams']
            videos = {stream.get('height'): stream.get('url') for stream in streams if stream.get('url')}
    return videos


@site.register()
def hanime_play_combined(url, name, download=None):
    htvlogged = utils.addon.getSetting('htvlogged') == 'true'
    videos = {}

    try:
        if htvlogged and hanime_login(action='refresh'):
            member_videos = get_videos(url, member=True)
            videos.update(member_videos)
        if not videos:
            free_videos = get_videos(url)
            videos.update(free_videos)
    except Exception as e:
        utils.notify('Notify', str(e))
        return

    if videos:
        vp = utils.VideoPlayer(name, download=download)
        videourl = utils.selector('Select quality', videos, setting_valid='qualityask', sort_by=lambda x: int(x), reverse=True)
        if videourl:
            videourl = videourl + '|User-Agent:' + ua
            vp.play_from_direct_link(videourl)


@site.register()
def hanime_eps(url):
    url = 'https://hanime.tv/api/v8/video?id=' + url
    try:
        listhtml = utils.getHtml(url, headers=hanime_headers)
    except Exception as e:
        utils.notify('Notify', str(e))
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


def sha256(s):
    return hashlib.sha256(s.encode()).hexdigest()


def makeXheaders():
    t = lambda: str(int(time.time()))
    return {
        "X-Signature-Version": "web2",
        "X-Claim"            : t(),
        "X-Signature"        : sha256("9944822{0}8{0}113".format(t)),
        "User-Agent"         : "okhttp/3.12.1"
    }


    
@site.register()
def hanime_login(action='login'):
    htvlogged = utils.addon.getSetting('htvlogged')
    
    if not htvlogged or htvlogged == 'false':
        htvuser = utils.addon.getSetting('htvuser') if utils.addon.getSetting('htvuser') else ''
        htvpass = utils.addon.getSetting('htvpass') if utils.addon.getSetting('htvpass') else ''
        
        if htvuser == '':
            htvuser = getinput(default=htvuser, heading='Input your Hanime.tv member email')
            htvpass = getinput(default=htvpass, heading='Input your Hanime.tv password', hidden=True)
            utils.addon.setSetting('htvuser', htvuser)
            utils.addon.setSetting('htvpass', htvpass)

        data = json.dumps({'burger': htvuser, 'fries': htvpass})
        headers = makeXheaders()
        headers.update({"Content-Type": "application/json"})
        response = utils._getHtml(apiurl+'/rapi/v4/sessions', data=data, headers=headers)
        if response:
            response_dict = json.loads(response)
            apidata = response_dict['env']['mobile_apps']
            build_numbers = ['_build_number', 'osts_build_number', 'severilous_build_number']

            for build_number in build_numbers:
                if apidata.get(build_number):
                    apidata = apidata[build_number]
                    break
            if type(apidata) != int:
                utils.notify('Error', 'Could not find build number')
                utils.addon.setSetting('htvlogged', 'false')
                return False
        else:
            utils.notify('Error', 'Could not login')
            utils.addon.setSetting('htvlogged', 'false')
            return False
        utils.addon.setSetting('session_token', response_dict['session_token'])
        utils.addon.setSetting('build_number', str(apidata))
        utils.addon.setSetting('htvlogged', 'true')
        
        if action == 'login':
            utils.notify('Notify', 'Login successful')
            xbmc.executebuiltin('Container.Refresh')
    elif action != 'refresh':
        clear = utils.selector('Clear stored user & password?', ['Yes', 'No'], reverse=True)
        if clear:
            if clear == 'Yes':
                utils.addon.setSetting('htvuser', '')
                utils.addon.setSetting('htvpass', '')
            utils.addon.setSetting('session_token', '')
            utils.addon.setSetting('build_number', '')
            utils.addon.setSetting('htvlogged', 'false')
            
            contexturl = (utils.addon_sys
                          + "?mode=" + str('hanime.hanime_main'))
            xbmc.executebuiltin('Container.Update(' + contexturl + ')')
    return True
