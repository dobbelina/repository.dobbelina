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

site = AdultSite('myfreecams', '[COLOR hotpink]MyFreeCams[/COLOR]', 'https://www.myfreecams.com', 'myfreecams.jpg', 'myfreecams', True)
MFC_SERVERS = {}


@site.register(default_mode=True)
def Main():
    List('https://www.myfreecams.com/')


@site.register()
def List(url):
    listhtml = utils._getHtml2(url)
    match = re.compile(r'<div\s*class=slm_c>.+?<a\s*href="([^"]+)".+?src="([^"]+)".+?style=".+?>(.+?)<', re.DOTALL | re.IGNORECASE).findall(listhtml)
    for _, img, name in match:
        url = name
        name = utils.cleantext(name)
        img = img.replace('90x90', '300x300')
        site.add_download_link(name, url, 'Playvid', img, name, noDownload=True)
    utils.eod()


@site.register()
def Playvid(url, name):
    global MFC_SERVERS
    serverlist = utils.getHtml2('https://app.myfreecams.com/server')
    jsonlist = json.loads(serverlist)
    MFC_SERVERS['WZOBSSERVERS'] = jsonlist["wzobs_servers"]
    MFC_SERVERS['H5SERVERS'] = jsonlist["h5video_servers"]
    MFC_SERVERS['NGSERVERS'] = jsonlist["ngvideo_servers"]
    MFC_SERVERS['CHATSERVERS'] = jsonlist["chat_servers"]
    videourl = myfreecam_start(url)
    if videourl:
        vp = utils.VideoPlayer(name)
        vp.play_from_direct_link(videourl)
    else:
        utils.notify('Oh oh', 'Couldn\'t find a playable webcam link')


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


def read_model_data(m):
    global CAMGIRLSERVER
    global CAMGIRLCHANID
    global CAMGIRLUID
    global PHASE
    WZOBSSERVERS = MFC_SERVERS['WZOBSSERVERS']
    H5SERVERS = MFC_SERVERS['H5SERVERS']
    NGSERVERS = MFC_SERVERS['NGSERVERS']

    usr = ''
    msg = fc_decode_json(m)
    try:
        sid = msg['sid']
        level = msg['lv']
    except:
        return

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

    try:
        host = "ws://{0}.myfreecams.com:8080/fcsl".format(random.choice(MFC_SERVERS['CHATSERVERS']))
        ws = websocket.WebSocket()
        ws = websocket.create_connection(host)
        ws.send("hello fcserver\n\0")
        ws.send("1 0 0 20071025 0 guest:guest\n\0")
    except:
        import traceback
        traceback.print_exc()
        utils.kodilog('fucked')
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
                read_model_data(msg)
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
