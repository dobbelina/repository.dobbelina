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
import urllib

import xbmc
import xbmcplugin
import xbmcgui
from resources.lib import utils



dialog = utils.dialog
addon = utils.addon


def BGVersion():
    try:
        bgpage = utils.getHtml('https://beeg.com','')
    except:
        return None
    jsversion = re.compile(r"link href=(\/js\/app.+?.js) rel", re.DOTALL | re.IGNORECASE).findall(bgpage)[0]
    bgversion = re.compile(r'service-worker\.js\?version=\"\).concat\(\"(.+?)\"', re.DOTALL | re.IGNORECASE).findall(utils.getHtml('https://beeg.com' + jsversion, ''))[0]
    bgsavedversion = addon.getSetting('bgversion')
    if bgversion != bgsavedversion or not addon.getSetting('bgsalt'):
        addon.setSetting('bgversion',bgversion)
    return str(bgversion)

@utils.url_dispatcher.register('80')
def BGMain():
    bgversion = BGVersion()
    bgversion = addon.getSetting('bgversion')
    utils.addDir('[COLOR hotpink]Channels[/COLOR]','https://api.beeg.com/api/v6/'+bgversion+'/channels',84,'','')
    utils.addDir('[COLOR hotpink]People[/COLOR]','https://api.beeg.com/api/v6/'+bgversion+'/people',85,'','')
    utils.addDir('[COLOR hotpink]Tags[/COLOR]','https://api.beeg.com/api/v6/'+bgversion+'/tags',83,'','')
    BGList('https://beeg.com/api/v6/'+bgversion+'/index/main/0/pc')


@utils.url_dispatcher.register('81', ['url'])
def BGList(url):
    bgversion = addon.getSetting('bgversion')
    try:
            listjson = utils.getHtml(url,'')
    except Exception as e:
        return utils.notify(url, e.message)

    js = json.loads(listjson)
    color = False
    for video in js["videos"]:
        color = not color
        title = video['ps_name'] + ' - ' + video['title'].encode("ascii", errors="ignore")
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
    try:
        page=re.compile('/([0-9]+)/pc', re.DOTALL | re.IGNORECASE).findall(url)[0]
        page = int(page)
        npage = page + 1
        totalpages = js['pages']
        if int(totalpages) > page + 1:
            nextp = url.replace("/"+str(page)+"/pc", "/"+str(npage)+"/pc")
            utils.addDir('Next Page (' + str(npage+1) + ' / ' + str(totalpages) + ')', nextp,81,'')
    except: pass
    xbmcplugin.endOfDirectory(utils.addon_handle)


@utils.url_dispatcher.register('82', ['url', 'name'], ['download'])
def BGPlayvid(url, name, download=None):
    vp = utils.VideoPlayer(name, download)
    vp.progress.update(25, "", "Loading video page", "")

    videopage = utils.getHtml(url)
    vp.progress.update(50, "", "Loading video page", "")
    list = {}
    match = re.compile('"(\d+p)":\s*?"([^"]+)"', re.DOTALL | re.IGNORECASE).findall(videopage)
    for quality, url in match:
        list[quality] = url
    videourl = utils.selector('Select quality', list, dont_ask_valid=True,  sort_by=lambda x: int(x[:-1]), reverse=True)
    if not videourl:
        return
    videourl = videourl.replace("{DATA_MARKERS}","data=pc_GB__" + str(addon.getSetting('bgversion')) + '_')
    if not videourl.startswith("http"): videourl = "https:" + videourl

    vp.progress.update(75, "", "Loading video page", "")
    vp.play_from_direct_link(videourl)


@utils.url_dispatcher.register('83', ['url'])
def BGTag(url):
    caturl = utils.getHtml5(url)
    tags = re.compile('{"tag":"(.+?)","videos":(.+?)}', re.DOTALL | re.IGNORECASE).findall(caturl)
    for tag,count in tags:
        videolist = "https://api.beeg.com/api/v6/" + str(addon.getSetting('bgversion')) + "/index/tag/0/pc?tag=" + urllib.quote(tag.encode("utf8").lower())
        name = tag.encode("utf8")
        name = name.title() +' [COLOR deeppink]' + count + '[/COLOR]'
        utils.addDir(name, videolist, 81, '')
    xbmcplugin.endOfDirectory(utils.addon_handle)


@utils.url_dispatcher.register('84', ['url'])
def BGChannel(url):
    try:
        listjson = utils.getHtml(url,'')
    except Exception as e:
        return utils.notify(url, e.message)
    channel_list = json.loads(listjson)
    for channel in channel_list['channels']:
        ch = channel['channel']
        videos = str(channel['videos'])
        name = channel['ps_name'] + ' [COLOR orange]' + videos + '[/COLOR] '
        about = channel['ps_about']
        svid = 'https://api.beeg.com/api/v6/' + str(addon.getSetting('bgversion')) + '/index/channel/0/pc?channel=' + ch
        img = 'https://thumbs.beeg.com/channels/' + str(channel['id']) + '.png'
        utils.addDir(name, svid, 81, img, desc=about)
    npage = 2
    offset = 100
    if '?offset=' in url:
        offset = int(url.split('?offset=')[-1]) + 100
        npage = offset / 100 + 1
    utils.addDir('Next Page (' + str(npage) + ')','https://api.beeg.com/api/v6/'+str(addon.getSetting('bgversion'))
                 +'/channels?offset=' + str(offset),84,'','')
    xbmcplugin.endOfDirectory(utils.addon_handle)


@utils.url_dispatcher.register('85', ['url'])
def BGPeople(url):
    try:
            listjson = utils.getHtml(url,'')
    except Exception as e:
        return utils.notify(url, e.message)
    people_list = json.loads(listjson)
    for person in people_list['people']:
        name = person['name']
        img = 'https://thumbs.beeg.com/img/cast/' + str(person['id']) + '.png'
        videos = person['videos']
        url = 'https://api.beeg.com/api/v6/' + str(addon.getSetting('bgversion')) + '/index/people/0/pc?search_mode=code&people=' + person['code']
        utils.addDir(name +' [COLOR deeppink]' + str(videos) + '[/COLOR]', url, 81, img)
    npage = 2
    offset = 100
    if '?offset=' in url:
        offset = int(url.split('?offset=')[-1]) + 100
        npage = offset / 100 + 1
    utils.addDir('Next Page (' + str(npage) + ')','https://api.beeg.com/api/v6/'+str(addon.getSetting('bgversion'))
                 +'/people?offset=' + str(offset),85,'','')
    xbmcplugin.endOfDirectory(utils.addon_handle)
