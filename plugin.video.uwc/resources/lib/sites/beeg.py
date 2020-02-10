'''
    Ultimate Whitecream
    Copyright (C) 2015 Whitecream

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
import sys
import json

import xbmc
import xbmcplugin
import xbmcgui
from resources.lib import utils

'''
# from youtube-dl
from resources.lib.compat import (
    compat_chr,
    compat_ord,
    compat_urllib_parse_unquote,
)
'''

dialog = utils.dialog
addon = utils.addon


def BGVersion():
    bgpage = utils.getHtml('https://beeg.com','')
    bgversion = re.compile(r"var beeg_version = (\d+);", re.DOTALL | re.IGNORECASE).findall(bgpage)[0]
    bgsavedversion = addon.getSetting('bgversion')
    if bgversion != bgsavedversion or not addon.getSetting('bgsalt'):
        addon.setSetting('bgversion',bgversion)
#        bgjspage = utils.getHtml('https://beeg.com/static/cpl/'+bgversion+'.js','https://beeg.com')
#        bgsalt = re.compile('beeg_salt="([^"]+)"', re.DOTALL | re.IGNORECASE).findall(bgjspage)[0]
#        addon.setSetting('bgsalt',bgsalt)


@utils.url_dispatcher.register('80')
def BGMain():
    BGVersion()
    bgversion = addon.getSetting('bgversion')
    utils.addDir('[COLOR hotpink]Categories[/COLOR]','https://beeg.com/api/v6/'+bgversion+'/index/main/0/pc',83,'','')
    utils.addDir('[COLOR hotpink]Channels[/COLOR]','https://beeg.com/api/v6/'+bgversion+'/channels',85,'','')
    utils.addDir('[COLOR hotpink]Search[/COLOR]','https://beeg.com/api/v6/'+bgversion+'/index/tag/0/pc?tag=',84,'','')
    BGList('https://beeg.com/api/v6/'+bgversion+'/index/main/0/pc')
    xbmcplugin.endOfDirectory(utils.addon_handle)


@utils.url_dispatcher.register('81', ['url'])
def BGList(url):
    bgversion = addon.getSetting('bgversion')
    try:
        listjson = utils.getHtml(url,'https://beeg.com/')
    except:
        return None   
    js = json.loads(listjson)
    color = False
    for video in js["videos"]:
        color = not color
        title = replaceunicode(video["title"])
        if video["thumbs"]:
            img = "https://img.beeg.com/400x225/" + video["thumbs"][0]["image"]
        else:
            continue
        svid = video["svid"]
        m, s = divmod(video["duration"], 60)
        duration = '{:d}:{:02d}'.format(m, s)
        name = title + "[COLOR deeppink] " + duration + "[/COLOR]"
        videopage = ''
        thstart = 0
        thend = 0
        thoffset = 0
        for thumb in sorted(video["thumbs"], key = lambda x: x["start"]):
            if thumb["start"] != None:
                if thumb["start"] == thstart and thumb["end"] == thend and thumb["offset"] == thoffset:
                    continue
                thstart = thumb["start"]
                thend = thumb["end"]
                thoffset = thumb["offset"]
                img = "https://img.beeg.com/400x225/" + thumb["image"]
                m, s = divmod(thumb["start"], 60)
                start = '{:d}:{:02d}'.format(m, s)
                m, s = divmod(thumb["end"], 60)
                end = '{:d}:{:02d}'.format(m, s)
                videopage = "https://beeg.com/api/v6/" + bgversion + "/video/" + str(svid) + "?v=2&s=" + str(thumb["start"]) + "&e=" + str(thumb["end"])
                if color:
                    name = "[COLOR powderblue]" + title
                else:
                    name = "[COLOR mediumaquamarine]" + title
                name = name + "[COLOR deeppink] " + duration + "" + "[COLOR blue]  (" + start + " - " + end + ")[/COLOR]"
                utils.addDownLink(name, videopage, 82, img, '')
        if videopage == '':
            videopage = "https://beeg.com/api/v6/" + bgversion + "/video/" + str(svid) + "?v=2"
            utils.addDownLink(name, videopage, 82, img, '')
        
    # match = re.compile(r'\{"cid":\d+,"title":"([^"]*)","start":([^,]+),"end":([^,]+),.+?"image":"([^"]+)".+?"svid":(\d+),"duration":(\d+),', re.DOTALL | re.IGNORECASE).findall(listjson)
    # for title, start, end, img, svid, duration in match:
        # img = "https://img.beeg.com/400x225/" + img
        # videopage = "https://beeg.com/api/v6/" + bgversion + "/video/" + svid + "?v=2"
        # if start != 'null':
            # videopage += '&s=' + start
        # if end != 'null':
            # videopage += '&e=' + end
        # m, s = divmod(int(duration), 60)
        # duration = '{:d}:{:02d}'.format(m, s)
        # name = replaceunicode(title) + "[COLOR deeppink] " + duration + "[/COLOR]"
        # utils.addDownLink(name, videopage, 82, img, '')
    try:
        page=re.compile('https://beeg.com/api/v6/' + bgversion + '/index/[^/]+/([0-9]+)/pc', re.DOTALL | re.IGNORECASE).findall(url)[0]
        page = int(page)
        npage = page + 1
        jsonpage = re.compile(r'pages":(\d+)', re.DOTALL | re.IGNORECASE).findall(listjson)[0]
        if int(jsonpage) > page + 1:
            nextp = url.replace("/"+str(page)+"/", "/"+str(npage)+"/")
            utils.addDir('Next Page (' + str(npage+1) + ' / ' + jsonpage + ')', nextp,81,'')
    except: pass
    xbmcplugin.endOfDirectory(utils.addon_handle)

def replaceunicode(str):
    if str:
        try:
            unicodechar = re.compile(r'\\u(....)').findall(str)
            for x in unicodechar:
                str = str.replace('\u' + x, unichr(int(x,16)))
            str = str.replace('\\r','')
            str = str.encode("utf8")
        except:
            str = "unicode_error"
    else:
        str = ""
    return str


'''
# from youtube-dl
def split(o, e):
    def cut(s, x):
        n.append(s[:x])
        return s[x:]
    n = []
    r = len(o) % e
    if r > 0:
        o = cut(o, r)
    while len(o) > e:
        o = cut(o, e)
    n.append(o)
    return n

def decrypt_key(key):
    bgsalt = addon.getSetting('bgsalt')
    # Reverse engineered from http://static.beeg.com/cpl/1738.js
    a = bgsalt
    e = compat_urllib_parse_unquote(key)
    o = ''.join([
        compat_chr(compat_ord(e[n]) - compat_ord(a[n % len(a)]) % 21)
        for n in range(len(e))])
    return ''.join(split(o, 3)[::-1])
'''

@utils.url_dispatcher.register('82', ['url', 'name'], ['download'])
def BGPlayvid(url, name, download=None):
    videopage = utils.getHtml4(url)
    videopage = json.dumps(videopage) 
    list = {}
    match = re.compile('"(\d+p)":\s*?"([^"]+)"', re.DOTALL | re.IGNORECASE).findall(videopage)
    for quality, url in match:
        list[quality] = url
    url = utils.selector('Select quality', list, dont_ask_valid=True,  sort_by=lambda x: int(x[:-1]), reverse=True)
    if not url:
        return
    url = url.replace("{DATA_MARKERS}","data=pc_XX")
    if not url.startswith("http:"): url = "https:" + url
    videourl = url
    if download == 1:
        utils.downloadVideo(videourl, name)
    else:
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


@utils.url_dispatcher.register('83', ['url'])
def BGCat(url):
    bgversion = addon.getSetting('bgversion')
    caturl = utils.getHtml5(url)
    tags = re.compile('{"tag":"(.+?)","videos":(.+?)}', re.DOTALL | re.IGNORECASE).findall(caturl)
    for tag, count in tags:
        videolist = "https://beeg.com/api/v6/"+bgversion+"/index/tag/0/pc?tag=" + tag.encode("utf8")
        videolist = videolist.replace(" ","%20")
        name = replaceunicode(tag)
        name = name.title() +' [COLOR deeppink]' + count + '[/COLOR]'
        utils.addDir(name, videolist, 81, '')
    xbmcplugin.endOfDirectory(utils.addon_handle)

@utils.url_dispatcher.register('85', ['url'])
def BGChannels(url):
    bgversion = addon.getSetting('bgversion')
    caturl = utils.getHtml5(url)
    tags = re.compile('"id":(\d+),.+?"channel":"([^"]+)",.+?,"ps_name":"([^"]+)".+?"ps_about":"([^"]*)",.+?"videos":(\d*),"image":(\d+),', re.DOTALL | re.IGNORECASE).findall(caturl)
    for id, channel, name, about, count, img in tags:
        if img != '0':
            img = "https://beeg.com/media/channels/" + id + ".png?_=" + bgversion
        else:
            img = "https://beeg.com/img/icons/avatars/channel-512.png"
        videolist = "https://beeg.com/api/v6/"+bgversion+"/index/channel/0/pc?channel=" + channel.encode("utf8")
        videolist = videolist.replace(" ","%20")        
        name = replaceunicode(name)
        name = name.title() +' [COLOR deeppink]' + count + '[/COLOR] ... ' + '[COLOR brown]' + about + '[/COLOR]' 
        utils.addDir(name, videolist, 81, img)
    xbmcplugin.endOfDirectory(utils.addon_handle)

@utils.url_dispatcher.register('84', ['url'], ['keyword'])
def BGSearch(url, keyword=None):
    searchUrl = url
    if not keyword:
        utils.searchDir(url, 84)
    else:
        title = keyword.replace(' ','+')
        searchUrl = searchUrl + title
        print "Searching URL: " + searchUrl
        BGList(searchUrl)
