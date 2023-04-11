'''
    Cumination
    Copyright (C) 2016 Whitecream

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
import random
from six.moves import urllib_parse
import json
from resources.lib import utils
import websocket
from resources.lib.adultsite import AdultSite

site = AdultSite('myfreecams', '[COLOR hotpink]MyFreeCams[/COLOR]', 'https://www.myfreecams.com/', 'myfreecams.jpg', 'myfreecams', True)


def getMFC():
    serverlist = utils.getHtml('https://app.myfreecams.com/server')
    jsonlist = json.loads(serverlist)
    MFC_SERVERS = {
        'WZOBSSERVERS': jsonlist.get("wzobs_servers"),
        'H5SERVERS': jsonlist.get("h5video_servers"),
        'NGSERVERS': jsonlist.get("ngvideo_servers"),
        'CHATSERVERS': [x for x in jsonlist.get("chat_servers") if x.startswith('wchat')]
    }
    return MFC_SERVERS


@site.register(default_mode=True)
def Main():
    site.add_dir('[COLOR hotpink]Tags[/COLOR]', site.url + 'php/model_tags.php?vcc=1545329519', 'Tags', '')
    List(site.url + 'php/model_explorer.php?get_contents=1&sort=cam_score&selection=public&page=1')


@site.register()
def List(url, page=1):
    MFC_SERVERS = getMFC()
    listhtml = utils._getHtml(url)
    res = re.compile(r"broadcaster_id:(\d+).+?avatar_border.+?src=([^\s]+).+?:19px;'>([^<]+).+?<X>(.+?)<X>", re.IGNORECASE | re.DOTALL).findall(listhtml)

    for model_id, pic, name, plot in res:
        pic = pic.replace('100x100', '300x300')
        idx = random.choice(list(MFC_SERVERS['H5SERVERS'].keys()))
        imgserver = MFC_SERVERS.get('H5SERVERS').get(idx)[5:]
        img = 'https://snap.mfcimg.com/snapimg/{0}/640x480/mfc_{1}?no-cache={2}'.format(imgserver, int(model_id) + 100000000, random.random())
        site.add_download_link(name, name, 'Playvid', pic, utils.cleantext(plot), noDownload=True, fanart=img)

    if len(res) >= 50:
        page += 1
        site.add_dir('Next Page... [COLOR hotpink]({0})[/COLOR]'.format(page), url[:-1] + str(page), 'List', site.img_next, page)
    utils.eod()


@site.register()
def Playvid(url, name):
    videourl = myfreecam_start(url)
    if videourl:
        vp = utils.VideoPlayer(name)
        vp.play_from_direct_link(videourl)
    else:
        utils.notify('Oh oh', 'Couldn\'t find a playable webcam link')


@site.register()
def Tags(url):
    url = site.url + 'php/model_tags.php?get_tags=1&tag_sort=&word_source=tags&display_style=list&member_mode=0'

    page = utils._getHtml(url)
    res = re.compile(r"g_oTags.SelectTag\('selected_field','(.+?)'.+?10px.+?>(.+?)<", re.IGNORECASE | re.MULTILINE | re.DOTALL).findall(page)

    for item, models in res:
        url = site.url + 'php/model_tags.php?get_users=1&selected_field={0}&display_style=list'.format(urllib_parse.quote_plus(item)) \
            + '&word_source=tags&member_mode=0&page=1&stand_alone=true'
        site.add_dir('{0} [COLOR hotpink]{1}[/COLOR]'.format(item, models), url, 'TagsList', '', '')
    utils.eod()


@site.register()
def TagsList(url):
    page = utils._getHtml(url)
    res = re.compile(r"avatar_border\s*src=([^\s]+).+?:19px;'>([^<]+)", re.IGNORECASE | re.DOTALL).findall(page)
    for img, name in res:
        img = img.replace('\\/', '/').replace('100x100', '300x300')
        site.add_download_link(name, name, 'Playvid', img, name, noDownload=True)
    utils.eod()


# from iptvplayer

vs_str = {}
vs_str[0] = "PUBLIC"
vs_str[2] = "AWAY"
vs_str[12] = "PVT"
vs_str[13] = "GROUP"
vs_str[90] = "CAM OFF"
vs_str[127] = "OFFLINE"
vs_str[128] = "TRUEPVT"


def fc_decode_json(m):
    try:
        m = m.replace('\r', '\\r').replace('\n', '\\n')
        return json.loads(m[m.find("{"):].decode("utf-8", "ignore") if utils.PY2 else m[m.find("{"):])
    except:
        return {'lv': 0}


def read_model_data(m, MFC_SERVERS):
    global CAMGIRLSERVER
    global CAMGIRLCHANID
    global CAMGIRLUID
    global PHASE
    WZOBSSERVERS = MFC_SERVERS['WZOBSSERVERS']
    H5SERVERS = MFC_SERVERS['H5SERVERS']
    NGSERVERS = MFC_SERVERS['NGSERVERS']

    usr = ''
    msg = fc_decode_json(m)
    # try:
    #     sid = msg['sid']
    #     level = msg['lv']
    # except:
    #     return

    vs = msg['vs']

    if vs == 127:
        return

    usr = msg['nm']
    CAMGIRLUID = msg['uid']
    CAMGIRLCHANID = msg['uid'] + 100000000
    camgirlinfo = msg['m']
    flags = camgirlinfo['flags']
    u_info = msg['u']

    if 'phase' in u_info:
        PHASE = u_info['phase']
    else:
        PHASE = ''

    try:
        idx = str(u_info['camserv'])
        idx = idx.encode("utf-8") if utils.PY2 else idx
        if idx in WZOBSSERVERS:
            CAMGIRLSERVER = WZOBSSERVERS[idx]
        else:
            if idx in H5SERVERS:
                CAMGIRLSERVER = H5SERVERS[idx]
            else:
                if idx in NGSERVERS:
                    CAMGIRLSERVER = NGSERVERS[idx]

        if vs != 0:
            CAMGIRLSERVER = 0
    except KeyError:
        CAMGIRLSERVER = 0

    truepvt = ((flags & 8) == 8)

    buf = usr + " =>"
    try:
        if truepvt == 1:
            buf += " (TRUEPVT)"
        else:
            buf += " ({0})".format(vs_str[vs])
    except KeyError:
        pass


def myfreecam_start(url):
    global CAMGIRL
    global CAMGIRLSERVER
    global CAMGIRLUID
    global CAMGIRLCHANID

    CAMGIRL = url
    CAMGIRLSERVER = 0

    MFC_SERVERS = getMFC()

    try:
        # host = "ws://{0}.myfreecams.com:8080/fcsl".format(random.choice(MFC_SERVERS['CHATSERVERS']))
        host = "wss://{0}.myfreecams.com/fcsl".format(random.choice(MFC_SERVERS['CHATSERVERS']))
        ws = websocket.WebSocket()
        ws = websocket.create_connection(host)
        ws.send("hello fcserver\n\0")
        ws.send("1 0 0 20071025 0 guest:guest\n\0")
    except Exception as e:
        utils.kodilog('MyFreeCams WS connect error [{0}]'.format(e))
        return ''

    rembuf = ""
    quitting = 0
    while quitting == 0:
        sock_buf = ws.recv()
        sock_buf = rembuf + sock_buf
        rembuf = ""
        while True:
            hdr = re.search(r"(\w+) (\w+) (\w+) (\w+) (\w+)", sock_buf)
            if bool(hdr) == 0:
                break

            fc = hdr.group(1)

            mlen = int(fc[0:6])
            fc_type = int(fc[6:])

            msg = sock_buf[6: 6 + mlen]

            if len(msg) < mlen:
                rembuf = ''.join(sock_buf)
                break

            msg = urllib_parse.unquote(msg)

            if fc_type == 1:
                ws.send("10 0 0 20 0 %s\n\0" % CAMGIRL)
            elif fc_type == 10:
                read_model_data(msg, MFC_SERVERS)
                quitting = 1

            sock_buf = sock_buf[6 + mlen:]

            if len(sock_buf) == 0:
                break
    ws.close()
    if CAMGIRLSERVER != 0:
        if PHASE == '':
            Url = "https://{0}.myfreecams.com/NxServer/ngrp:mfc_{1}.f4v_mobile/playlist.m3u8?nc=0.5863279394620062".format(CAMGIRLSERVER, CAMGIRLCHANID)
        else:
            Url = "https://{0}.myfreecams.com/NxServer/ngrp:mfc_a_{1}.f4v_mobile/playlist.m3u8?nc=0.5863279394620062".format(CAMGIRLSERVER, CAMGIRLCHANID)

        return Url
    else:
        pass
