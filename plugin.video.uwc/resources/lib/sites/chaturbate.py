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
import os
import sys
import sqlite3
import urllib

import xbmc
import xbmcplugin
import xbmcgui
from resources.lib import utils
genders = dict(f='Female', m='Male', c='Couple', s='Trans')

addon = utils.addon

HTTP_HEADERS_IPAD = {'User-Agent': 'Mozilla/5.0 (iPad; CPU OS 8_1 like Mac OS X) AppleWebKit/600.1.4 (KHTML, like Gecko) Version/8.0 Mobile/12B410 Safari/600.1.4'}
cbheaders = {'User-Agent': HTTP_HEADERS_IPAD,
       'Accept': '*/*',
       'Connection': 'keep-alive'}

@utils.url_dispatcher.register('220')
def Main():
    female = True if addon.getSetting("chatfemale") == "true" else False
    male = True if addon.getSetting("chatmale") == "true" else False
    couple = True if addon.getSetting("chatcouple") == "true" else False
    trans = True if addon.getSetting("chattrans") == "true" else False 
    utils.addDir('[COLOR red]Refresh Chaturbate images[/COLOR]','',223,'',Folder=False)
    if female:utils.addDir('[COLOR hotpink]Tags - Female [/COLOR]','https://chaturbate.com/tags/female/',225,'','')  
    if couple:utils.addDir('[COLOR hotpink]Tags - Couple [/COLOR]','https://chaturbate.com/tags/couple/',225,'','') 
    if male:utils.addDir('[COLOR hotpink]Tags - Male [/COLOR]','https://chaturbate.com/tags/male/',225,'','')   
    utils.addDir('[COLOR hotpink]Featured[/COLOR]','https://chaturbate.com/?page=1',221,'','')
    if female: utils.addDir('[COLOR hotpink]Female[/COLOR]','https://chaturbate.com/female-cams/?page=1',221,'','')
    if couple: utils.addDir('[COLOR hotpink]Couple[/COLOR]','https://chaturbate.com/couple-cams/?page=1',221,'','')
    if male: utils.addDir('[COLOR hotpink]Male[/COLOR]','https://chaturbate.com/male-cams/?page=1',221,'','')
    if trans: utils.addDir('[COLOR hotpink]Transsexual[/COLOR]','https://chaturbate.com/transsexual-cams/?page=1',221,'','')
    #new
    utils.addDir('[COLOR hotpink]New Cams[/COLOR]','https://chaturbate.com/new-cams/?page=1',221,'','')
    if female: utils.addDir('[COLOR hotpink]New Cams - Female[/COLOR]','https://chaturbate.com/new-cams/female/?page=1',221,'','')
    if couple: utils.addDir('[COLOR hotpink]New Cams - Couple[/COLOR]','https://chaturbate.com/new-cams/couple/?page=1',221,'','')
    if male: utils.addDir('[COLOR hotpink]New Cams - Male[/COLOR]','https://chaturbate.com/new-cams/male/?page=1',221,'','')
    if trans: utils.addDir('[COLOR hotpink]New Cams - Transsexual[/COLOR]','https://chaturbate.com/new-cams/transsexual/?page=1',221,'','')    
    #age
    utils.addDir('[COLOR hotpink]Teen Cams (18+)[/COLOR]','https://chaturbate.com/teen-cams/?page=1',221,'','')
    if female: utils.addDir('[COLOR hotpink]Teen Cams (18+) - Female[/COLOR]','https://chaturbate.com/teen-cams/female/?page=1',221,'','')
    if couple: utils.addDir('[COLOR hotpink]Teen Cams (18+) - Couple[/COLOR]','https://chaturbate.com/teen-cams/couple/?page=1',221,'','')
    if male: utils.addDir('[COLOR hotpink]Teen Cams (18+) - Male[/COLOR]','https://chaturbate.com/teen-cams/male/?page=1',221,'','')
    if trans: utils.addDir('[COLOR hotpink]Teen Cams (18+) - Transsexual[/COLOR]','https://chaturbate.com/teen-cams/transsexual/?page=1',221,'','')
    utils.addDir('[COLOR hotpink]18 to 21 Cams[/COLOR]','https://chaturbate.com/18to21-cams/?page=1',221,'','')
    if female: utils.addDir('[COLOR hotpink]18 to 21 Cams - Female[/COLOR]','https://chaturbate.com/18to21-cams/female/?page=1',221,'','')
    if couple: utils.addDir('[COLOR hotpink]18 to 21 Cams - Couple[/COLOR]','https://chaturbate.com/18to21-cams/couple/?page=1',221,'','')
    if male: utils.addDir('[COLOR hotpink]18 to 21 Cams - Male[/COLOR]','https://chaturbate.com/18to21-cams/male/?page=1',221,'','')
    if trans: utils.addDir('[COLOR hotpink]18 to 21 Cams - Transsexual[/COLOR]','https://chaturbate.com/18to21-cams/transsexual/?page=1',221,'','')
    utils.addDir('[COLOR hotpink]20 to 30 Cams[/COLOR]','https://chaturbate.com/20to30-cams/?page=1',221,'','')
    if female: utils.addDir('[COLOR hotpink]20 to 30 Cams - Female[/COLOR]','https://chaturbate.com/20to30-cams/female/?page=1',221,'','')
    if couple: utils.addDir('[COLOR hotpink]20 to 30 Cams - Couple[/COLOR]','https://chaturbate.com/20to30-cams/couple/?page=1',221,'','')
    if male: utils.addDir('[COLOR hotpink]20 to 30 Cams - Male[/COLOR]','https://chaturbate.com/20to30-cams/male/?page=1',221,'','')
    if trans: utils.addDir('[COLOR hotpink]20 to 30 Cams - Transsexual[/COLOR]','https://chaturbate.com/20to30-cams/transsexual/?page=1',221,'','')
    utils.addDir('[COLOR hotpink]30 to 50 Cams[/COLOR]','https://chaturbate.com/30to50-cams/?page=1',221,'','')
    if female: utils.addDir('[COLOR hotpink]30 to 50 Cams - Female[/COLOR]','https://chaturbate.com/30to50-cams/female/?page=1',221,'','')
    if couple: utils.addDir('[COLOR hotpink]30 to 50 Cams - Couple[/COLOR]','https://chaturbate.com/30to50-cams/couple/?page=1',221,'','')
    if male: utils.addDir('[COLOR hotpink]30 to 50 Cams - Male[/COLOR]','https://chaturbate.com/30to50-cams/male/?page=1',221,'','')
    if trans: utils.addDir('[COLOR hotpink]30 to 50 Cams - Transsexual[/COLOR]','https://chaturbate.com/30to50-cams/transsexual/?page=1',221,'','')
    utils.addDir('[COLOR hotpink]Mature Cams (50+)[/COLOR]','https://chaturbate.com/mature-cams/?page=1',221,'','')
    if female: utils.addDir('[COLOR hotpink]Mature Cams (50+) - Female[/COLOR]','https://chaturbate.com/mature-cams/female/?page=1',221,'','')
    if couple: utils.addDir('[COLOR hotpink]Mature Cams (50+) - Couple[/COLOR]','https://chaturbate.com/mature-cams/couple/?page=1',221,'','')
    if male: utils.addDir('[COLOR hotpink]Mature Cams (50+) - Male[/COLOR]','https://chaturbate.com/mature-cams/male/?page=1',221,'','')
    if trans: utils.addDir('[COLOR hotpink]Mature Cams (50+) - Transsexual[/COLOR]','https://chaturbate.com/mature-cams/transsexual/?page=1',221,'','')    
    #status
    utils.addDir('[COLOR hotpink]HD Cams[/COLOR]','https://chaturbate.com/hd-cams/?page=1',221,'','')
    if female: utils.addDir('[COLOR hotpink]HD Cams - Female[/COLOR]','https://chaturbate.com/hd-cams/female/?page=1',221,'','')
    if couple: utils.addDir('[COLOR hotpink]HD Cams - Couple[/COLOR]','https://chaturbate.com/hd-cams/couple/?page=1',221,'','')
    if male: utils.addDir('[COLOR hotpink]HD Cams - Male[/COLOR]','https://chaturbate.com/hd-cams/male/?page=1',221,'','')
    if trans: utils.addDir('[COLOR hotpink]HD Cams - Transsexual[/COLOR]','https://chaturbate.com/hd-cams/transsexual/?page=1',221,'','')   
    #region
    utils.addDir('[COLOR hotpink]North American Cams[/COLOR]','https://chaturbate.com/north-american-cams/?page=1',221,'','')
    if female: utils.addDir('[COLOR hotpink]North American Cams - Female[/COLOR]','https://chaturbate.com/north-american-cams/female/?page=1',221,'','')
    if couple: utils.addDir('[COLOR hotpink]North American Cams - Couple[/COLOR]','https://chaturbate.com/north-american-cams/couple/?page=1',221,'','')
    if male: utils.addDir('[COLOR hotpink]North American Cams - Male[/COLOR]','https://chaturbate.com/north-american-cams/male/?page=1',221,'','')
    if trans: utils.addDir('[COLOR hotpink]North American Cams - Transsexual[/COLOR]','https://chaturbate.com/north-american-cams/transsexual/?page=1',221,'','') 
    utils.addDir('[COLOR hotpink]Other Region Cams[/COLOR]','https://chaturbate.com/other-region-cams/?page=1',221,'','')
    if female: utils.addDir('[COLOR hotpink]Other Region Cams - Female[/COLOR]','https://chaturbate.com/other-region-cams/female/?page=1',221,'','')
    if couple: utils.addDir('[COLOR hotpink]Other Region Cams - Couple[/COLOR]','https://chaturbate.com/other-region-cams/couple/?page=1',221,'','')
    if male: utils.addDir('[COLOR hotpink]Other Region Cams - Male[/COLOR]','https://chaturbate.com/other-region-cams/male/?page=1',221,'','')
    if trans: utils.addDir('[COLOR hotpink]Other Region Cams - Transsexual[/COLOR]','https://chaturbate.com/other-region-cams/transsexual/?page=1',221,'','') 
    utils.addDir('[COLOR hotpink]Euro Russian Cams[/COLOR]','https://chaturbate.com/euro-russian-cams/?page=1',221,'','')
    if female: utils.addDir('[COLOR hotpink]Euro Russian Cams - Female[/COLOR]','https://chaturbate.com/euro-russian-cams/female/?page=1',221,'','')
    if couple: utils.addDir('[COLOR hotpink]Euro Russian Cams - Couple[/COLOR]','https://chaturbate.com/euro-russian-cams/couple/?page=1',221,'','')
    if male: utils.addDir('[COLOR hotpink]Euro Russian Cams - Male[/COLOR]','https://chaturbate.com/euro-russian-cams/male/?page=1',221,'','')
    if trans: utils.addDir('[COLOR hotpink]Euro Russian Cams - Transsexual[/COLOR]','https://chaturbate.com/euro-russian-cams/transsexual/?page=1',221,'','') 
    utils.addDir('[COLOR hotpink]Philippines Cams[/COLOR]','https://chaturbate.com/philippines-cams/?page=1',221,'','')
    if female: utils.addDir('[COLOR hotpink]Philippines Cams - Female[/COLOR]','https://chaturbate.com/philippines-cams/female/?page=1',221,'','')
    if couple: utils.addDir('[COLOR hotpink]Philippines Cams - Couple[/COLOR]','https://chaturbate.com/philippines-cams/couple/?page=1',221,'','')
    if male: utils.addDir('[COLOR hotpink]Philippines Cams - Male[/COLOR]','https://chaturbate.com/philippines-cams/male/?page=1',221,'','')
    if trans: utils.addDir('[COLOR hotpink]Philippines Cams - Transsexual[/COLOR]','https://chaturbate.com/philippines-cams/transsexual/?page=1',221,'','') 
    utils.addDir('[COLOR hotpink]Asian Cams[/COLOR]','https://chaturbate.com/asian-cams/?page=1',221,'','')
    if female: utils.addDir('[COLOR hotpink]Asian Cams - Female[/COLOR]','https://chaturbate.com/asian-cams/female/?page=1',221,'','')
    if couple: utils.addDir('[COLOR hotpink]Asian Cams - Couple[/COLOR]','https://chaturbate.com/asian-cams/couple/?page=1',221,'','')
    if male: utils.addDir('[COLOR hotpink]Asian Cams - Male[/COLOR]','https://chaturbate.com/asian-cams/male/?page=1',221,'','')
    if trans: utils.addDir('[COLOR hotpink]Asian Cams - Transsexual[/COLOR]','https://chaturbate.com/asian-cams/transsexual/?page=1',221,'','') 
    utils.addDir('[COLOR hotpink]South American Cams[/COLOR]','https://chaturbate.com/south-american-cams/?page=1',221,'','')
    if female: utils.addDir('[COLOR hotpink]South American Cams - Female[/COLOR]','https://chaturbate.com/south-american-cams/female/?page=1',221,'','')
    if couple: utils.addDir('[COLOR hotpink]South American Cams - Couple[/COLOR]','https://chaturbate.com/south-american-cams/couple/?page=1',221,'','')
    if male: utils.addDir('[COLOR hotpink]South American Cams - Male[/COLOR]','https://chaturbate.com/south-american-cams/male/?page=1',221,'','')
    utils.addDir('[COLOR hotpink]South American Cams - Transsexual[/COLOR]','https://chaturbate.com/south-american-cams/transsexual/?page=1',221,'','')    
    xbmcplugin.endOfDirectory(utils.addon_handle)


@utils.url_dispatcher.register('221', ['url'], ['page'])
def List(url, page=1):
    if addon.getSetting("chaturbate") == "true":
        clean_database(False)
    try:
        listhtml = utils.getHtml2(url)
    except:
        
        return None		
    listhtml = listhtml.replace('title=""','title=" "')
    match = re.compile(r'<li.+?data-slug="(.+?)".+?<a href="(\/.+?)".+?<img\s+src="(.+?)".+?_label.+?>(.+?)<.+?age.+?gender(.+?).+?>(.+?)<.+?<li title="(.+?)".+?class="location".+?>(.+?)<.+?class="cams">(.+?)<', re.DOTALL | re.IGNORECASE).findall(listhtml)
    for name,videopage, img, status, gender, age, roomtopic, location, activity in match:	

        age = utils.cleantext(age.strip())
        name = utils.cleantext(name.strip())
        status = status.replace("\n","").strip()
        name = name + " [COLOR deeppink][" + age + "][/COLOR] " + status
        videopage = "https://chaturbate.com" + videopage
        info = "\n\n[B]Status:[/B] " + status + "\n\n[B]Gender:[/B] " + genders[gender] + "\n\n[B]Age:[/B] " + age + "\n\n[B]Location:[/B] " + location + "\n\n[B]Activity:[/B] " + activity + "\n\n[B]Room topic:[/B] " + roomtopic
        info = info.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">").replace("&#39;", "'").replace("&quot;", '"')
        utils.addDownLink(name, videopage, 222, img, info, noDownload=True)
    try:
        page = page + 1
        nextp=re.compile('<a href="([^"]+)" class="next', re.DOTALL | re.IGNORECASE).findall(listhtml)
        next = "https://chaturbate.com" + nextp[0]
        utils.addDir('Next Page ('+str(page)+')', next, 221,'', page)
    except: pass
    xbmcplugin.endOfDirectory(utils.addon_handle)


@utils.url_dispatcher.register('225', ['url'])
def Tag(url):
    link = utils.getHtml(url, '')
    tags = re.compile('<span class="tag">.*?<a href="([^"]+)" title="([^"]+)".*?src="([^"]+)"', re.DOTALL | re.IGNORECASE).findall(link)
    tags = sorted(tags, key=lambda x: x[1])
    for tagurl, tagname, tagimg in tags:
        tagurl = "https://chaturbate.com" + tagurl 
        utils.addDir(tagname,tagurl,221,tagimg, 1)
    xbmcplugin.endOfDirectory(utils.addon_handle)



@utils.url_dispatcher.register('223')
def clean_database(showdialog=True):
    conn = sqlite3.connect(xbmc.translatePath("special://database/Textures13.db"))
    try:
        with conn:
            list = conn.execute("SELECT id, cachedurl FROM texture WHERE url LIKE '%%%s%%';" % ".highwebmedia.com")
            for row in list:
                conn.execute("DELETE FROM sizes WHERE idtexture LIKE '%s';" % row[0])
                try: os.remove(xbmc.translatePath("special://thumbnails/" + row[1]))
                except: pass
            conn.execute("DELETE FROM texture WHERE url LIKE '%%%s%%';" % ".highwebmedia.com")
            if showdialog:
                utils.notify('Finished','Chaturbate images cleared')
    except:
        pass


@utils.url_dispatcher.register('222', ['url', 'name'])
def Playvid(url, name):
    playmode = int(addon.getSetting('chatplay'))
    chatslow = int(addon.getSetting('chatslow'))
    listhtml = utils.getHtml(url, hdr=cbheaders)
    iconimage = xbmc.getInfoImage("ListItem.Thumb")
    info = ""

    listhtml = listhtml.replace('\\u0022','"')
    m3u8url = re.compile(r'"hls_source":\s*"([^"]+m3u8)"', re.DOTALL | re.IGNORECASE).findall(listhtml)
    listhtml2 = listhtml.replace('<div class="data"></div>','<div class="data"> </div>')
    match = re.compile(r'<div class="label">(.+?)</div>.+?<div class="data">(.+?)</div>', re.DOTALL | re.IGNORECASE).findall(listhtml2)
    for label, data in match:
        if label != "About Me:" and label != "Wish List:" and data != "None":
           info = info + "[B]" + label + "[/B] " + data + "\n"
        info = info.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">").replace("&#39;", "'").replace("&quot;", '"')

    if m3u8url:
        m3u8stream = m3u8url[0].replace('\\u002D','-')
        if chatslow == 1:
            m3u8stream = m3u8stream.replace('_fast','')
    else:
        m3u8stream = False
    
    if playmode == 0:
        if m3u8stream:
            videourl = m3u8stream
        else:
            utils.notify('Oh oh','Couldn\'t find a playable webcam link')
            return
        
    elif playmode == 1:
        if m3u8stream:
            from F4mProxy import f4mProxyHelper
            f4mp=f4mProxyHelper()
            f4mp.playF4mLink(m3u8stream,name,proxy=None,use_proxy_for_chunks=False, maxbitrate=0, simpleDownloader=False, auth=None, streamtype='HLS',setResolved=False,swf=None , callbackpath="",callbackparam="", iconImage=iconimage)
            return
        else:
            utils.notify('Oh oh','Couldn\'t find a playable webcam link')
            return        
    
    elif playmode == 2:
        flv_info = []
        embed = re.compile(r"EmbedViewerSwf\(*(.+?)\);", re.DOTALL).findall(listhtml)[0]
        for line in embed.split("\n"):
            data = re.search("""\s+["']([^"']+)["'],""", line)
            if data:
                flv_info.append(data.group(1))
        
        streamserver = "rtmp://%s/live-edge"%(flv_info[2])
        modelname = flv_info[1]
        username = flv_info[8]
        password = urllib.unquote(flv_info[12])
        unknown = flv_info[13]
        swfurl = "https://chaturbate.com/static/flash/CBV_2p650.swf"
        
        videourl = "%s app=live-edge swfUrl=%s tcUrl=%s pageUrl=http://chaturbate.com/%s/ conn=S:%s conn=S:%s conn=S:2.650 conn=S:%s conn=S:%s playpath=mp4"%(streamserver,swfurl,streamserver,modelname,username,modelname,password,unknown)

    listitem = xbmcgui.ListItem(name, iconImage="DefaultVideo.png", thumbnailImage=iconimage)
    listitem.setInfo('video', {'Title': name, 'Genre': 'Porn', 'Plot': info})
    listitem.setProperty("IsPlayable","true")
    xbmc.Player().play(videourl, listitem)

