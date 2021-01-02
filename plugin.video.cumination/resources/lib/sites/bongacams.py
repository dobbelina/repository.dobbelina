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
from resources.lib import utils
from resources.lib.adultsite import AdultSite

site = AdultSite('bongacams', '[COLOR hotpink]bongacams.com[/COLOR]', 'http://bongacams.com', 'bongacams.png', 'bongacams', True)


@site.register(default_mode=True)
def Main():
    female = True if utils.addon.getSetting("chatfemale") == "true" else False
    male = True if utils.addon.getSetting("chatmale") == "true" else False
    couple = True if utils.addon.getSetting("chatcouple") == "true" else False
    trans = True if utils.addon.getSetting("chattrans") == "true" else False
    site.add_dir('[COLOR red]Refresh bongacams.com images[/COLOR]', '', 'clean_database', '', Folder=False)

    bu = "http://tools.bongacams.com/promo.php?c=226355&type=api&api_type=json&categories[]="
    if female:
        site.add_dir('[COLOR hotpink]Female[/COLOR]', '{0}female'.format(bu), 'List', '', '')
    if couple:
        site.add_dir('[COLOR hotpink]Couples[/COLOR]', '{0}couples'.format(bu), 'List', '', '')
    if male:
        site.add_dir('[COLOR hotpink]Male[/COLOR]', '{0}male'.format(bu), 'List', '', '')
    if trans:
        site.add_dir('[COLOR hotpink]Transsexual[/COLOR]', '{0}transsexual'.format(bu), 'List', '', '')
    utils.eod()


@site.register()
def List(url):
    if utils.addon.getSetting("chaturbate") == "true":
        clean_database(False)

    data = utils.getHtml(url)
    model_list = json.loads(data)
    for model in model_list:
        img = 'https:' + model['profile_images']['thumbnail_image_big_live']
        username = model['username']
        name = model['display_name']
        subject = name
        age = model['display_age']
        name += ' [COLOR hotpink][{}][/COLOR]'.format(age)
        if model['hd_cam']:
            name += ' [COLOR gold]HD[/COLOR]'
        subject += u', {}'.format(age)
        subject += u', {}\n'.format(model['hometown']) if model['hometown'] else u'\n'
        if model['ethnicity']:
            subject += u'- {}\n'.format(model['ethnicity'])
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
            subject += u'- Lovense Toy\n'
        if model['turns_on']:
            subject += u'- Likes: {}\n'.format(model['turns_on'])
        if model['turns_off']:
            subject += u'- Dislikes: {}\n'.format(model['turns_off'])
        site.add_download_link(name, username, 'Playvid', img, subject, noDownload=True)
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
        postRequest = {'method': 'getRoomData', 'args[]': str(url)}
        response = utils.postHtml('{0}/tools/amf.php'.format(site.url), form_data=postRequest, headers={'X-Requested-With': 'XMLHttpRequest'}, compression=False)
    except:
        utils.notify('Oh oh', 'Couldn\'t find a playable webcam link')
        return None

    amf_json = json.loads(response)
    if amf_json['localData']['videoServerUrl'].startswith("//mobile"):
        videourl = 'https:' + amf_json['localData']['videoServerUrl'] + '/hls/stream_' + url + '.m3u8'
    else:
        videourl = 'https:' + amf_json['localData']['videoServerUrl'] + '/hls/stream_' + url + '/playlist.m3u8'

    videourl += '|User-Agent={0}'.format(utils.USER_AGENT)
    vp.progress.update(75, "[CR]Found Stream[CR]")
    vp = utils.VideoPlayer(name)
    vp.play_from_direct_link(videourl)
