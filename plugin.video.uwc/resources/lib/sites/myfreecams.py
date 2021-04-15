'''
    Ultimate Whitecream
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

import urllib2
import re
import sys
import random
import urllib
import os

try:
    import simplejson
except:
    import json as simplejson

import xbmc
import xbmcplugin
import xbmcgui
from resources.lib import utils
from resources.lib import websocket

@utils.url_dispatcher.register('270')
def Main():
    utils.addDir('[COLOR hotpink]TAGS[/COLOR]', 'https://www.myfreecams.com/php/model_tags.php?vcc=1545329519', 273,
                 os.path.join(utils.imgDir, 'uwc-next.png'), '')
    List('https://www.myfreecams.com/php/model_explorer.php?get_contents=1&page=1')


@utils.url_dispatcher.register('271', ['url'])
def List(url):
    try:
        llist = utils.getHtml2(url)
        res = re.compile("avatar_border src=(.+?) .+?:19px;'>(.+?)<.+?<X>(.+?)<X>", re.IGNORECASE | re.MULTILINE | re.DOTALL).findall(llist)
    except:
        return None

    for img, name, plot in res:
        img = img.replace('100x100','300x300')
        utils.addDownLink(name, name, 272, img, plot)
    utils.addDir('[COLOR hotpink]Next page[/COLOR]', url[:-1] + str(int(url[-1]) + 1), 271, os.path.join(utils.imgDir, 'uwc-next.png'), '')
    xbmcplugin.endOfDirectory(utils.addon_handle)





@utils.url_dispatcher.register('272', ['url', 'name'], ['check', 'download'])
def Playvid(url, name, check=False, download=0):
    global CAMGIRLPLOT
    global MFC_SERVERS
    MFC_SERVERS = {}

    serverlist = utils.getHtml2('https://new.myfreecams.com/server')
    jsonlist =  simplejson.loads(serverlist)

    MFC_SERVERS['WZOBSSERVERS'] = jsonlist["wzobs_servers"]
    MFC_SERVERS['H5SERVERS'] = jsonlist["h5video_servers"]
    MFC_SERVERS['NGSERVERS'] = jsonlist["ngvideo_servers"]
    MFC_SERVERS['CHATSERVERS'] = jsonlist["chat_servers"]

    videourl = myfreecam_start(url)

    if videourl:
        iconimage = xbmc.getInfoImage("ListItem.Thumb")
        listitem = xbmcgui.ListItem(name, iconImage="DefaultVideo.png", thumbnailImage=iconimage)
        listitem.setInfo('video', {'Title': name, 'Genre': 'Porn'})
        listitem.setProperty("IsPlayable","true")
        if int(sys.argv[1]) == -1:
            pl = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
            pl.clear()
            pl.add(videourl, listitem)
            xbmc.Player().play(pl)
        else:
            listitem.setPath(str(videourl))
            xbmcplugin.setResolvedUrl(utils.addon_handle, True, listitem)
        if utils.addon.getSetting("dwnld_stream")=="true" or download==1: utils.dwnld_stream(videourl, name)
    else:
        utils.notify('Oh oh','Couldn\'t find a playable webcam link')


#from iptvplayer

vs_str={}
vs_str[0]="PUBLIC"
vs_str[2]="AWAY"
vs_str[12]="PVT"
vs_str[13]="GROUP"
vs_str[90]="CAM OFF"
vs_str[127]="OFFLINE"
vs_str[128]="TRUEPVT"

def fc_decode_json(m):
    try:
        m = m.replace('\r', '\\r').replace('\n', '\\n')
        return simplejson.loads(m[m.find("{"):].decode("utf-8","ignore"))
    except:
        return simplejson.loads("{\"lv\":0}")

def read_model_data(m):
    global CAMGIRLSERVER
    global CAMGIRLCHANID
    global CAMGIRLUID
    global CAMGIRLPLOT
    global PHASE

    global MFC_SERVERS
    WZOBSSERVERS = MFC_SERVERS['WZOBSSERVERS']
    H5SERVERS = MFC_SERVERS['H5SERVERS']
    NGSERVERS = MFC_SERVERS['NGSERVERS']

    usr = ''
    msg = fc_decode_json(m)
    CAMGIRLPLOT = ''
    try:
        sid=msg['sid']
        level  = msg['lv']
    except:
        return

    vs     = msg['vs']

    if vs == 127:
        return

    usr    = msg['nm']
    CAMGIRLUID    = msg['uid']
    CAMGIRLCHANID = msg['uid'] + 100000000
    camgirlinfo=msg['m']
    flags  = camgirlinfo['flags']
    u_info=msg['u']

    if 'phase' in u_info:
        PHASE = u_info['phase']
    else:
        PHASE = ''

    try:
        idx = str(u_info['camserv']).encode("utf-8")
        if idx in WZOBSSERVERS:
            CAMGIRLSERVER = WZOBSSERVERS[idx]
            utils.kodilog('  WZOB')
        else:
            if idx in H5SERVERS:
                CAMGIRLSERVER = H5SERVERS[idx]
                utils.kodilog('  H5')
            else:
                if idx in NGSERVERS:
                    utils.kodilog('  NG')
                    CAMGIRLSERVER = NGSERVERS[idx]

        if vs != 0:
            CAMGIRLSERVER = 0
    except KeyError:
        CAMGIRLSERVER=0

    truepvt = ((flags & 8) == 8)

    buf=usr+" =>"
    try:
        if truepvt == 1:
            buf+=" (TRUEPVT)"
        else:
            buf+=" ("+vs_str[vs]+")"
    except KeyError:
        pass


def myfreecam_start(url):
    global CAMGIRL
    global CAMGIRLSERVER
    global CAMGIRLUID
    global CAMGIRLCHANID
    global MFC_SERVERS

    CAMGIRL= url
    CAMGIRLSERVER = 0

    try:
        host = "ws://"+str(random.choice(MFC_SERVERS['CHATSERVERS']))+".myfreecams.com:8080/fcsl"
#        utils.kodilog(host)
        ws = websocket.WebSocket()
        ws = websocket.create_connection(host)

        ws.send("fcsws_20180422\n\0")
        ws.send("1 0 0 20071025 0 guest:guest\n\0")
    except Exception as e:
        xbmc.log('myUWC - MyFreeCams WS connect error- [' + e.message + '] ', xbmc.LOGNOTICE)

        return ''
    rembuf=""
    quitting = 0
    while quitting == 0:
        try:
            sock_buf =  ws.recv()
        except:
            utils.kodilog('myUWC - ' + url + ' - MyFreeCams Error receiving from websocket')
            return
        sock_buf=rembuf+sock_buf
        rembuf=""
        while True:
            hdr=re.search (r"(\w+) (\w+) (\w+) (\w+) (\w+)", sock_buf)
            if bool(hdr) == 0:
                break

            fc = hdr.group(1)
            mlen   = int(fc[0:6])
            fc_type = int(fc[6:])

            msg=sock_buf[6:6+mlen]

            if len(msg) < mlen:
                rembuf=''.join(sock_buf)
                break

            msg=urllib.unquote(msg)
            if fc_type == 1:
                ws.send("10 0 0 20 0 %s\n\0" % CAMGIRL)
            elif fc_type == 10:
                read_model_data(msg)
                quitting=1

            sock_buf=sock_buf[6+mlen:]

            if len(sock_buf) == 0:
                break
    ws.close()
    if CAMGIRLSERVER != 0:
        if PHASE == '':
            Url="https://" + str(CAMGIRLSERVER) + ".myfreecams.com/NxServer/ngrp:mfc_" + str(CAMGIRLCHANID) + ".f4v_mobile/playlist.m3u8?nc=0.5863279394620062"
        else:
            Url="https://" + str(CAMGIRLSERVER) + ".myfreecams.com/NxServer/ngrp:mfc_a_" + str(CAMGIRLCHANID) + ".f4v_mobile/playlist.m3u8?nc=0.5863279394620062"

        return Url
    else:
        pass

@utils.url_dispatcher.register('273', ['url'])
def tagsList(url):
    url = 'https://www.myfreecams.com/php/model_tags.php?get_tags=1&tag_sort=&word_source=tags&display_style=list&member_mode=0&style_override=&night_mode=0&0.057073103870574515'

    page = utils.getHtml2(url)
    res = re.compile("g_oTags.SelectTag\(\'selected_field\',\'(.+?)\'.+?10px.+?>(.+?)<", re.IGNORECASE | re.MULTILINE | re.DOTALL).findall(page)
    # xbmcgui.Dialog().textviewer('TAGS', str(res))
    for item, models in res:
        url = 'https://www.myfreecams.com/php/model_tags.php?get_users=1&selected_field={field}&display_style=list&word_source=tags&member_mode=0&style_override=&sort=&page=1&stand_alone=true&night_mode=0&0.39258079289014247'.format(field = urllib.quote_plus(item))
        utils.addDir(item + ' - ' + models, url, 274, '', '')
    xbmcplugin.endOfDirectory(utils.addon_handle)
    # uurl =  'https://www.myfreecams.com/php/model_tags.php?get_users=1&selected_field=sexy&display_style=list&word_source=tags&member_mode=0&style_override=&sort=&page=1&stand_alone=true&night_mode=0&0.8154651658335239'
    # res = re.compile("javascript:g_oTags.SelectTag\('selected_field','(.+?)'", re.IGNORECASE | re.MULTILINE | re.DOTALL).findall(page)
    # 'https://www.myfreecams.com/php/model_tags.php?get_users=1&selected_field=cook&display_style=list&word_source=tags&member_mode=0&style_override=&sort=&page=1&stand_alone=true&night_mode=0&0.39258079289014247'
    pass

@utils.url_dispatcher.register('274', ['url'])
def tagsListDir(url):
    page = utils.getHtml2(url)
    res = re.compile("avatar_border src=(.+?) .+?:19px;'>(.+?)<",
                     re.IGNORECASE | re.MULTILINE | re.DOTALL).findall(page)
    if not res:
        return
    for img, name in res:
        img = img.replace('\\/', '/').replace('100x100','300x300')
        utils.addDownLink(name, name, 272, img, '', noDownload=True)
    # utils.addDir('[COLOR hotpink]Next page[/COLOR]', url[:-1] + str(int(url[-1]) + 1), 271, os.path.join(utils.imgDir, 'uwc-next.png'), '')
    xbmcplugin.endOfDirectory(utils.addon_handle)

    pass