'''
    Cumination
    Copyright (C) 2017 Whitecream, hdgdl, Team Cumination
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

import os
import sqlite3
import json
import re
from six.moves import urllib_parse, urllib_error
from resources.lib import utils
from resources.lib.adultsite import AdultSite

site = AdultSite('bongacams', '[COLOR hotpink]BongaCams[/COLOR]', 'https://bongacams.com/', 'bongacams.png', 'bongacams', True)


@site.register(default_mode=True)
def Main():
    female = utils.addon.getSetting("chatfemale") == "true"
    male = utils.addon.getSetting("chatmale") == "true"
    couple = utils.addon.getSetting("chatcouple") == "true"
    trans = utils.addon.getSetting("chattrans") == "true"
    site.add_dir('[COLOR red]Refresh bongacams.com images[/COLOR]', '', 'clean_database', '', Folder=False)
    site.add_dir('Hour\'s TOP chat rooms', 'https://bongacams.com/contest/top-room?cp=1', 'List2', '', '')
    bu = "http://tools.bongacams.com/promo.php?c=226355&type=api&api_type=json&categories[]="
    if female:
        site.add_dir('[COLOR hotpink]Female[/COLOR]', '{0}female'.format(bu), 'List', '', '')
        site.add_dir('[COLOR yellow]Online Favorites[/COLOR]', "http://tools.bongacams.com/promo.php?c=226355&type=api&api_type=json", 'onlineFav', '', '')
        site.add_dir('  International - Queen of Queens', site.url + 'contest/queen-of-queens-international', 'List3', '', '')
        site.add_dir('  North America & Western Europe\'s - Queen of Queens', site.url + 'contest/queen-of-queens', 'List3', '', '')
        site.add_dir('  Latin American - Queen of Queens', site.url + 'contest/queen-of-queens-latin-america', 'List3', '', '')
    if couple:
        site.add_dir('[COLOR hotpink]Couples[/COLOR]', '{0}couples'.format(bu), 'List', '', '')
        site.add_dir('  Couples\' Top 50', site.url + 'contest/top-couple-models', 'List3', '', '')
    if male:
        site.add_dir('[COLOR hotpink]Male[/COLOR]', '{0}male'.format(bu), 'List', '', '')
        site.add_dir('  Guys and Trans\' Top 10', site.url + 'contest/top-male-models', 'List3', '', '')
    if trans:
        site.add_dir('[COLOR hotpink]Transsexual[/COLOR]', '{0}transsexual'.format(bu), 'List', '', '')
        site.add_dir('  Guys and Trans\' Top 10', site.url + 'contest/top-male-models', 'List3', '', '')

    utils.eod()


@site.register()
def List(url):
    if utils.addon.getSetting("chaturbate") == "true":
        clean_database(False)

    data = utils._getHtml(url)
    model_list = json.loads(data)
    for model in model_list:
        img = 'https:' + model['profile_images']['thumbnail_image_big_live']
        username = model['username']
        name = model['display_name']
        age = model['display_age']
        name += ' [COLOR hotpink][{}][/COLOR]'.format(age)
        if model['hd_cam']:
            name += ' [COLOR gold]HD[/COLOR]'
        subject = ''
        if model.get('is_geo'):
            subject += u'[B][COLOR hotpink]GeoLocked[/COLOR][/B]\n'
        if model.get('hometown'):
            subject += u'Location: {}'.format(model.get('hometown'))
        if model.get('homecountry'):
            subject += u', {}\n'.format(model.get('homecountry')) if subject else u'Location: {}\n'.format(model.get('homecountry'))
        if model['ethnicity']:
            subject += u'\n- {}\n'.format(model['ethnicity'])
        if model['primary_language']:
            subject += u'- Speaks {}\n'.format(model['primary_language'])
        if model['secondary_language']:
            subject = subject[:-1] + u', {}\n'.format(model['secondary_language'])
        if model['eye_color']:
            subject += u'- {} Eyed\n'.format(model['eye_color'])
        if model['hair_color']:
            subject = subject[:-1] + u' {}\n'.format(model['hair_color'])
        if model['height']:
            subject += u'- {} tall\n'.format(model['height'])
        if model['weight']:
            subject += u'- {} weight\n'.format(model['weight'])
        if model['bust_penis_size']:
            subject += u'- {} Boobs\n'.format(model['bust_penis_size']) if 'Female' in model['gender'] else u'- {} Cock\n'.format(model['bust_penis_size'])
        if model['pubic_hair']:
            subject = subject[:-1] + u' and {} Pubes\n'.format(model['pubic_hair'])
        if model['vibratoy']:
            subject += u'- Lovense Toy\n\n'
        if model['turns_on']:
            subject += u'- Likes: {}\n'.format(model['turns_on'])
        if model['turns_off']:
            subject += u'- Dislikes: {}\n\n'.format(model['turns_off'])
        if model.get('tags'):
            subject += u', '.join(model.get('tags'))
        contextrecord = (utils.addon_sys + "?mode=chaturbate.Record&id=" + urllib_parse.quote_plus(username))
        contextmenu=[(('[COLOR violet]Find recordings featuring [/COLOR]{}[COLOR violet] on Cloudbate[/COLOR]'.format(name), 'RunPlugin(' + contextrecord + ')'))]
        site.add_download_link(name, username, 'Playvid', img, subject.encode('utf-8') if utils.PY2 else subject, contextm=contextmenu, noDownload=True)
    utils.eod()


@site.register(clean_mode=True)
def clean_database(showdialog=True):
    conn = sqlite3.connect(utils.TRANSLATEPATH("special://database/Textures13.db"))
    try:
        with conn:
            list = conn.execute("SELECT id, cachedurl FROM texture WHERE url LIKE '%%%s%%';" % "bongacams.com")
            for row in list:
                conn.execute("DELETE FROM sizes WHERE idtexture LIKE '%s';" % row[0])
                try:
                    os.remove(utils.TRANSLATEPATH("special://thumbnails/" + row[1]))
                except:
                    pass
            conn.execute("DELETE FROM texture WHERE url LIKE '%%%s%%';" % "bongacams.com")
            if showdialog:
                utils.notify('Finished', 'bongacams.com images cleared')
    except:
        pass


@site.register()
def Playvid(url, name):
    if url is None or url == '':
        utils.notify(name, 'Model Offline', icon='thumb')
        return

    vp = utils.VideoPlayer(name)
    vp.progress.update(25, "[CR]Loading video page[CR]")
    try:
        postRequest = [
            ('method', 'getRoomData'),
            ('args[]', str(url)),
            ('args[]', ''),
            ('args[]', '')
        ]
        hdr = utils.base_hdrs
        hdr.update({'X-Requested-With': 'XMLHttpRequest'})
        response = utils._postHtml('{0}tools/amf.php'.format(site.url), form_data=postRequest, headers=hdr, compression=False)
    except:
        utils.notify('Oh oh', 'Couldn\'t find a playable webcam link', icon='thumb')
        return None

    amf_json = json.loads(response)
    if amf_json['status'] == 'error':
        utils.notify('Oh oh', 'Couldn\'t find a playable webcam link', icon='thumb')
        return
    # if amf_json.get('performerData', {}).get('is_Online') is None: 
    #     utils.notify(name, 'Model Offline', icon='thumb')
    #     return       

    if 'private' in amf_json.get('performerData', {}).get('showType'):
        utils.notify(name, 'Model in private chat', icon='thumb')
        vp.progress.close()
        return

    amf = amf_json.get('localData', {}).get('videoServerUrl')

    if amf is None:
        utils.notify(name, 'Model Offline', icon='thumb')
        vp.progress.close()
        return
    elif amf.startswith("//mobile"):
        videourl = 'https:' + amf + '/hls/stream_' + amf_json.get('performerData', {}).get('username') + '.m3u8'
    else:
        videourl = 'https:' + amf + '/hls/stream_' + amf_json.get('performerData', {}).get('username') + '/playlist.m3u8'
        try:
            m3u8 = utils._getHtml(videourl, referer=site.url)
        except:     # urllib_error.HTTPError:
            utils.notify(name, 'Model Offline or GeoLocked', icon='thumb')
            vp.progress.close()
            return
        quals = re.findall(r'\d+x(\d+).+\n(.+)', m3u8)
        if quals:
            sources = {qual: urllib_parse.urljoin(videourl, vurl) for qual, vurl in quals}
            videourl = utils.selector('Select quality', sources, setting_valid='qualityask', sort_by=lambda x: int(x.split('x')[-1]), reverse=True)

    videourl += '|User-Agent={0}&Referer={1}&Origin={2}'.format(utils.USER_AGENT, site.url, site.url[:-1])
    vp.progress.update(75, "[CR]Found Stream[CR]")
    vp.play_from_direct_link(videourl)


@site.register()
def List2(url):
    headers = {'X-Requested-With': 'XMLHttpRequest'}
    data = utils._getHtml(url, site.url, headers=headers)
    timePeriod = json.loads(data).get("data").get("topRooms").get("content").get("winners").get("timePeriod")

    site.add_download_link('Current contest standings: {} - [COLOR red][B]Refresh[/B][/COLOR]'.format(timePeriod), url, 'utils.refresh', '', '', noDownload=True)
    if utils.addon.getSetting("online_only") == "true":
        online_only = True
        url = url + '?isOnlineOnly=on'
        site.add_download_link('[COLOR red][B]Show all models[/B][/COLOR]', url, 'online', '', '', noDownload=True)
    else:
        online_only = False
        site.add_download_link('[COLOR red][B]Show only models online[/B][/COLOR]', url, 'online', '', '', noDownload=True)

    if utils.addon.getSetting("chaturbate") == "true":
        clean_database(False)

    items = (
        json.loads(data)
        .get("data", {})
        .get("topRooms", {})
        .get("content", {})
        .get("winners", {})
        .get("thumbs", [])
    )

    for item in items:
        is_live = item.get("liveBadge") is not None
        status = "Online" if is_live else "Offline"

        if online_only and status == "Offline":
            continue

        name = item.get("footer", {}).get("displayName", "")
        if utils.PY2 and name:
            name = name.encode("utf8")

        link_path = item.get("link", {}).get("url", {}).get("url", "")
        if status == "Online":
            username = link_path.strip("/") if link_path else ""
        else:
            username = " "

        img_src = item.get("avatar", {}).get("src", "")
        if img_src.startswith("//"):
            img = "https:" + img_src
        else:
            img = "https://" + img_src if img_src else ""

        place = item.get("stripe", {}).get("place", "")

        content_list = item.get("content", [])
        viewers = ""
        prize_formatted = ""

        for c in content_list:
            text_val = c.get("text", "")
            if "members" in text_val.lower():
                viewers = "".join(filter(str.isdigit, text_val))
            elif "prize" in text_val.lower():
                prize_formatted = text_val

        subject = "Status: {0}[CR]".format(status)
        subject += "Place: {0}[CR]".format(place)
        subject += "Viewers: {0}[CR]".format(viewers)
        subject += "Prize: {0}[CR]".format(prize_formatted)

        site.add_download_link(
            name, username, "Playvid", img, subject, noDownload=True
        )
    utils.eod()
  


@site.register()
def List3(url):
    site.add_download_link('[COLOR red][B]Refresh[/B][/COLOR]', url, 'utils.refresh', '', '', noDownload=True)
    if utils.addon.getSetting("online_only") == "true":
        url = url + '?online_only=1'
        site.add_download_link('[COLOR red][B]Show all models[/B][/COLOR]', url, 'online', '', '', noDownload=True)
    else:
        site.add_download_link('[COLOR red][B]Show only models online[/B][/COLOR]', url, 'online', '', '', noDownload=True)

    if utils.addon.getSetting("chaturbate") == "true":
        clean_database(False)
    headers = {'X-Requested-With': 'XMLHttpRequest'}
    data = utils._getHtml(url, site.url, headers=headers)
    #timePeriod = json.loads(data).get("data").get("topModels").get("content").get("winners").get("thumbs", [])   #.get("content").get("winners").get("timePeriod")
    json_data = json.loads(data).get("data", {})

    top_winners_list = (
        json_data.get("topModels", {})
        .get("content", {})
        .get("topWinners", {})
        .get("thumbs", [])
    )

    winners_list = (
        json_data.get("topModels", {})
        .get("content", {})
        .get("winners", {})
        .get("thumbs", [])
    )

    items = top_winners_list + winners_list

    for item in items:
        is_live = item.get("liveBadge") is not None
        status = "Online" if is_live else "Offline"

        # if online_only and status == "Offline":
        #     continue

        name = item.get("footer", {}).get("displayName", "")
        if utils.PY2 and name:
            name = name.encode("utf8")

        link_path = item.get("link", {}).get("url", {}).get("url", "")
        if status == "Online":
            username = link_path.strip("/") if link_path else ""
        else:
            username = " "

        img_src = item.get("avatar", {}).get("src", "")
        if img_src.startswith("//"):
            img = "https:" + img_src
        else:
            img = "https://" + img_src if img_src else ""

        place = item.get("stripe", {}).get("place", "")

        content_list = item.get("content", [])
        viewers = ""
        prize_formatted = ""

        for c in content_list:
            text_val = c.get("text", "")
            if "members" in text_val.lower():
                viewers = "".join(filter(str.isdigit, text_val))
            elif "prize" in text_val.lower():
                prize_formatted = text_val

        subject = "Status: {0}[CR]".format(status)
        subject += "Place: {0}[CR]".format(place)
        subject += "Viewers: {0}[CR]".format(viewers)
        subject += "Prize: {0}[CR]".format(prize_formatted)

        site.add_download_link(
            name, username, "Playvid", img, subject, noDownload=True
        )
    utils.eod()



@site.register()
def online(url):
    if utils.addon.getSetting("online_only") == "true":
        utils.addon.setSetting("online_only", "false")
    else:
        utils.addon.setSetting("online_only", "true")
    utils.refresh()


@site.register()
def onlineFav(url):
    data = utils._getHtml(url)
    model_list = json.loads(data)

    conn = sqlite3.connect(utils.favoritesdb)
    conn.text_factory = str
    c = conn.cursor()
    c.execute("SELECT DISTINCT name, url, image FROM favorites WHERE mode='bongacams.Playvid'")
    favorite_data = {
        row[0].split('[COLOR')[0].strip(): {'db_url': row[1], 'db_image': row[2]} 
        for row in c.fetchall()
    }
    c.close()

    model_lookup = {
        item['display_name']: item | favorite_data[item['display_name']]
        for item in model_list
        if item['display_name'] in favorite_data
    }

    for model_name, info in model_lookup.items():
        username = info['username']
        name = info['display_name']
        img = info['db_image']
        age = info['display_age']
        name += ' [COLOR hotpink][{}][/COLOR]'.format(age)
        if info['hd_cam']:
            name += ' [COLOR gold]HD[/COLOR]'
        subject = ''
        if info['is_geo']:
            subject += u'[B][COLOR hotpink]GeoLocked[/COLOR][/B]\n'
        if info['hometown']:
            subject += u'Location: {}'.format(info['hometown'])
        if info['homecountry']:
            subject += u', {}\n'.format(info['homecountry']) if subject else u'Location: {}\n'.format(info['homecountry'])
        if info['ethnicity']:
            subject += u'\n- {}\n'.format(info['ethnicity'])
        if info['primary_language']:
            subject += u'- Speaks {}\n'.format(info['primary_language'])
        if info['secondary_language']:
            subject = subject[:-1] + u', {}\n'.format(info['secondary_language'])
        if info['eye_color']:
            subject += u'- {} Eyed\n'.format(info['eye_color'])
        if info['hair_color']:
            subject = subject[:-1] + u' {}\n'.format(info['hair_color'])
        if info['height']:
            subject += u'- {} tall\n'.format(info['height'])
        if info['weight']:
            subject += u'- {} weight\n'.format(info['weight'])
        if info['bust_penis_size']:
            subject += u'- {} Boobs\n'.format(info['bust_penis_size']) if 'Female' in info['gender'] else u'- {} Cock\n'.format(info['bust_penis_size'])
        if info['pubic_hair']:
            subject = subject[:-1] + u' and {} Pubes\n'.format(info['pubic_hair'])
        if info['vibratoy']:
            subject += u'- Lovense Toy\n\n'
        if info['turns_on']:
            subject += u'- Likes: {}\n'.format(info['turns_on'])
        if info['turns_off']:
            subject += u'- Dislikes: {}\n\n'.format(info['turns_off'])
        chat_status = ''
        if info['chat_status']:
            if info['chat_status'] != 'public':
                current_show = '[COLOR blue] {}[/COLOR]'.format(info['chat_status'])

        contextrecord = (utils.addon_sys + "?mode=chaturbate.Record&id=" + urllib_parse.quote_plus(username))
        contextmenu=[(('[COLOR violet]Find recordings featuring [/COLOR]{}[COLOR violet] on Cloudbate[/COLOR]'.format(name), 'RunPlugin(' + contextrecord + ')'))]
        site.add_download_link(name, username, 'Playvid', img, subject.encode('utf-8') if utils.PY2 else subject, contextm=contextmenu, noDownload=True)
    utils.eod()
