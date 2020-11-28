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
    bgpage = utils.getHtml('https://beeg.com','')
    jsversion = re.compile(r"link href=(\/js\/app.+?.js) rel", re.DOTALL | re.IGNORECASE).findall(bgpage)[0]
    bgversion = re.compile(r'service-worker\.js\?version=\"\).concat\(\"(.+?)\"', re.DOTALL | re.IGNORECASE).findall(utils.getHtml('https://beeg.com' + jsversion, ''))[0]
    bgsavedversion = addon.getSetting('bgversion')
    if bgversion != bgsavedversion or not addon.getSetting('bgsalt'):
        addon.setSetting('bgversion',bgversion)
    return str(bgversion)

bgversion = BGVersion()
@utils.url_dispatcher.register('80')
def BGMain():

    bgversion = addon.getSetting('bgversion')
    utils.addDir('[COLOR hotpink]Channels[/COLOR]','https://api.beeg.com/api/v6/'+bgversion+'/channels',84,'','')
    utils.addDir('[COLOR hotpink]People[/COLOR]','https://api.beeg.com/api/v6/'+bgversion+'/people',85,'','')
    utils.addDir('[COLOR hotpink]Tags[/COLOR]','https://api.beeg.com/api/v6/'+bgversion+'/tags',83,'','')
    BGList('https://beeg.com/api/v6/'+bgversion+'/index/main/0/pc')
    xbmcplugin.endOfDirectory(utils.addon_handle)


@utils.url_dispatcher.register('81', ['url'])
def BGList(url):
	bgversion = addon.getSetting('bgversion')
	try:
            listjson = utils.getHtml(url,'')
	except Exception as e:
		return utils.notify(url, e.message)
        model_list = json.loads(listjson)
        for model in model_list['videos']:
            title = model['ps_name']
            img = 'https://img.beeg.com/400x225/' + model['thumbs'][0]['image']
            name = title + ' - ' + model['title'].encode("ascii", errors="ignore")  # ).encode("ascii", errors="ignore") + model['nt_name'] if model['nt_name'] else ''
            dur = int(model['duration'])
            m, s = divmod(model["duration"], 60)
            duration = '{:d}:{:02d}'.format(m, s)
            name = name + ' [COLOR orange]' + duration + '[/COLOR] '
            svid = 'https://api.beeg.com/api/v6/' + bgversion + '/video/' + str(model['svid']) + '?v=2&s=' + str(model['thumbs'][0]['start']) + '&e=' + str(model['thumbs'][0]['end']) + '&p=' + str(model['thumbs'][0]['pid'])
            desc = 'Status: ' + title #+ '\n' + img + '\n' + svid
            utils.addDownLink(name, svid, 82, img, desc)

        mmatch = re.compile('index/(.+?)/pc', re.DOTALL | re.IGNORECASE).findall(url)
        if mmatch: 
            match = mmatch[0].split('/')[1]
            totalPages = model_list['pages']
            if int(match)<totalPages-1:
                nextPage = int(match) + 1
                if 'main' in url:
                    nextUrl = url.replace('main/' + match + '/pc', 'main/' + str(nextPage) + '/pc')
                else:
                    nextUrl = url.replace('channel/' + match + '/pc', 'channel/' + str(nextPage) + '/pc')

                utils.addDir('Next page (' + str(nextPage + 1) + ')', nextUrl, 81, '', '')
 
        xbmcplugin.endOfDirectory(utils.addon_handle)

@utils.url_dispatcher.register('82', ['url', 'name'], ['download'])
def BGPlayvid(url, name, download=None):
	page = utils.getHtml(url)
 	videopage = json.loads(page)

        urlArray = []

        if videopage['240p']: urlArray.append(['240p','https:' + videopage["240p"].replace("{DATA_MARKERS}","data=pc_GB__" + str(videopage['id']) + '_')])
        if videopage['480p']: urlArray.append(['480p','https:' + videopage["480p"].replace("{DATA_MARKERS}","data=pc_GB__" + str(videopage['id']) + '_')])
        if videopage['720p']: urlArray.append(['720p','https:' + videopage["720p"].replace("{DATA_MARKERS}","data=pc_GB__" + str(videopage['id']) + '_')])
        if videopage['1080p']: urlArray.append(['1080p','https:' + videopage["1080p"].replace("{DATA_MARKERS}","data=pc_GB__" + str(videopage['id']) + '_')])
        if videopage['2160p']: urlArray.append(['2160p','https:' + videopage["2160p"].replace("{DATA_MARKERS}","data=pc_GB__" + str(videopage['id']) + '_')])

        choice = xbmcgui.Dialog().select('Select resolution', [item[0] for item in urlArray])
        videourl = urlArray[choice][1]
	
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
def BGTag(url):

	caturl = utils.getHtml5(url)
	tags = re.compile('{"tag":"(.+?)","videos":(.+?)}', re.DOTALL | re.IGNORECASE).findall(caturl)	
	for tag,count in tags:
		videolist = "https://api.beeg.com/api/v6/" + bgversion + "/index/tag/0/pc?tag=" + urllib.quote(tag.encode("utf8").lower())
		name = tag.encode("utf8")
		name = name.upper() +' [COLOR deeppink]' + count + '[/COLOR]'
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
            svid = 'https://api.beeg.com/api/v6/' + bgversion + '/index/channel/0/pc?channel=' + ch
            img = 'https://thumbs.beeg.com/channels/' + str(channel['id']) + '.png'
            utils.addDir(name, svid, 81, img, '')
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
            url = 'https://api.beeg.com/api/v6/' + bgversion + '/index/people/0/pc?search_mode=code&people=' + person['code']
            utils.addDir(name +' [COLOR deeppink]' + str(videos) + '[/COLOR]', url, 81, img)
	xbmcplugin.endOfDirectory(utils.addon_handle)
