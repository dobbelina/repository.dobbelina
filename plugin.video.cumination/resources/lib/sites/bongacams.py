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
        site.add_download_link(name, username, 'Playvid', img, subject.encode('utf-8') if utils.PY2 else subject, noDownload=True)
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
        videourl = 'https:' + amf + '/hls/stream_' + url + '.m3u8'
    else:
        videourl = 'https:' + amf + '/hls/stream_' + url + '/playlist.m3u8'
        try:
            m3u8 = utils._getHtml(videourl, referer=site.url)
        except urllib_error.HTTPError:
            utils.notify(name, 'Model Offline', icon='thumb')
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
    items = json.loads(data).get('result').get('chatActivities')
    for item in items:
        username = item.get('user').get('username')
        name = item.get('user').get('displayName')
        name = name.encode('utf8') if utils.PY2 else name
        img = 'https:' + item.get('user').get('profileImageUrls').get('thumb_xbig_lq')
        if item.get('user').get('isOnline'):
            status = 'Online'
        else:
            status = 'Offline'
            username = ' '
        subject = 'Status: {0}[CR]'.format(status)
        subject += 'Place: {0}[CR]'.format(item.get('chatActivity').get('place'))
        subject += 'Viewers: {0}[CR]'.format(item.get('chatActivity').get('viewers'))
        subject += 'Prize: {0}[CR]'.format(item.get('chatActivity').get('prizeFormatted'))
        site.add_download_link(name, username, 'Playvid', img, subject, noDownload=True)
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
    items = json.loads(data).get('result').get('contestItems')
    for item in items:
        username = item.get('user').get('username')
        name = item.get('user').get('displayName')
        name = name.encode('utf8') if utils.PY2 else name
        img = 'https:' + item.get('user').get('profileImageUrls').get('thumb_xbig_lq')
        if item.get('user').get('isOnline'):
            status = 'Online'
        else:
            status = 'Offline'
            username = ' '
        subject = 'Status: {0}[CR]'.format(status)
        subject += 'Place: {0}[CR]'.format(item.get('contestItem').get('place'))
        subject += 'Points: {0}[CR]'.format(item.get('contestItem').get('points'))
        subject += 'Prize: {0}[CR]'.format(item.get('contestItem').get('prizeFormatted'))
        site.add_download_link(name, username, 'Playvid', img, subject, noDownload=True)
    utils.eod()


@site.register()
def online(url):
    if utils.addon.getSetting("online_only") == "true":
        utils.addon.setSetting("online_only", "false")
    else:
        utils.addon.setSetting("online_only", "true")
    utils.refresh()
