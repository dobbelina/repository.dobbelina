#-*- coding: utf-8 -*-

import re
import urllib, requests

import xbmc
import xbmcplugin
import xbmcgui
from resources.lib import utils
from resources.lib import websocket
import json

progress = utils.progress


@utils.url_dispatcher.register('590')
def Main():
    utils.addDir('[COLOR hotpink]Search[/COLOR]','https://api.redtube.com/?data=redtube.Videos.searchVideos&output=json&page=1&ordering=newest&search=', 594, '', '')
    utils.addDir('[COLOR hotpink]Categories[/COLOR]','https://api.redtube.com/?data=redtube.Categories.getCategoriesList&output=json', 593, '', '')
    #utils.addDir('[COLOR hotpink]Tags[/COLOR]', 'https://api.redtube.com/?data=redtube.Tags.getTagList&output=json', 595, '', '')
    utils.addDir('[COLOR hotpink]Pornstars[/COLOR]', 'https://api.redtube.com/?data=redtube.Stars.getStarDetailedList&page=1&output=json', 597, '', '')

    utils.addDir('[COLOR hotpink]Newest[/COLOR]', 'https://api.redtube.com/?data=redtube.Videos.searchVideos&output=json&page=1&ordering=newest', 591, '', '')
    utils.addDir('[COLOR hotpink]Most Viewed[/COLOR]', 'https://api.redtube.com/?data=redtube.Videos.searchVideos&output=json&page=1&ordering=mostviewed', 591, '', '')
    utils.addDir('[COLOR hotpink]Top Rated[/COLOR]', 'https://api.redtube.com/?data=redtube.Videos.searchVideos&output=json&page=1&ordering=rating', 591, '', '')

    List('https://api.redtube.com/?data=redtube.Videos.searchVideos&page=1&output=json')
    xbmcplugin.endOfDirectory(utils.addon_handle)


@utils.url_dispatcher.register('591', ['url'])
def List(url):
    # newest: https://api.redtube.com/?data=redtube.Videos.searchVideos&output=json&page=1&ordering=newest
    try:
        listhtml = utils.getHtml(url.replace(' ', '+'), '')
    except:
        return None
    movieJson = json.loads(listhtml)
    if movieJson['count'] == 0:
        utils.notify(url, 'No movie found!', '')
        return
    for movie in movieJson['videos']:
        title = movie['video']['title'].encode("ascii", errors="ignore")
        movieUrl = movie['video']['url']
        imgUrl = movie['video']['thumb']
        duration = movie['video']['duration']
        name = "[COLOR deeppink]" + duration + "[/COLOR] " + title
        # name = "[COLOR deeppink]" + duration + "[/COLOR]"
      
        utils.addDownLink(name, movieUrl, 592, imgUrl, '')
    #try:
    thisP=re.compile('&page=(.+?)&', re.DOTALL).findall(url)[0]
    totalMovies = movieJson['count']
    maxPages = int(totalMovies/20) + 1
    # xbmcgui.Dialog().textviewer(url, str(thisP) + '\n' + str(totalMovies) + '\n' + url.replace('&page=' + str(thisP) + '&', '&page=' + str(int(thisP) +1) + '&'))
    if int(thisP)<maxPages:
        nextP = int(thisP) + 1
        utils.addDir('Next Page (' + str(nextP) + '/' + str(maxPages) + ')', url.replace('&page=' + thisP + '&', '&page=' + str(nextP) + '&'), 591,'')

    #except: pass
    xbmcplugin.endOfDirectory(utils.addon_handle)


@utils.url_dispatcher.register('594', ['url'], ['keyword'])
def Search(url, keyword=None):
    searchUrl = url
    if not keyword:
        utils.searchDir(url, 594)
    else:
        title = keyword.replace(' ','+')
        searchUrl = searchUrl + title
        print "Searching URL: " + searchUrl
        List(searchUrl)


@utils.url_dispatcher.register('593', ['url'])
def Categories(url):
    cathtml = utils.getHtml(url, '')
    catJson = json.loads(cathtml)
    for cat in catJson['categories']:
        name = cat['category']
        catUrl = 'https://api.redtube.com/?data=redtube.Videos.searchVideos&output=json&page=1&ordering=newest&search=' + name
        utils.addDir(name, catUrl, 591, '', '')
    xbmcplugin.endOfDirectory(utils.addon_handle)


@utils.url_dispatcher.register('595', ['url'])
def Tags(url):
    taghtml = utils.getHtml(url, '')
    tagJson = json.loads(taghtml)
    for cat in tagJson['tags']:
        name = str(cat['tag']['tag_name']).encode("ascii", errors="ignore")
        tagUrl = 'https://api.redtube.com/?data=redtube.Videos.searchVideos&output=json&page=1&ordering=newest&tag[]=' + name
        utils.addDir(name, tagUrl, 591, '', '')
    xbmcplugin.endOfDirectory(utils.addon_handle)


@utils.url_dispatcher.register('596', ['url'])
def ListChannel(url):
    try:
        listhtml = utils.getHtml(url, '')
    except:
        return None
    match = re.compile('<li class=" js-pop.*?<a href="([^"]+)" title="([^"]+)".*?data-mediumthumb="([^"]+)".*?<var class="duration">([^<]+)</var>(.*?)</div', re.DOTALL).findall(listhtml)
    for videopage, name, img, duration, hd in match:
        if hd.find('HD') > 0:
            hd = " [COLOR orange]HD[/COLOR] "
        else:
            hd = " "
        name = utils.cleantext(name)
        name = name + hd + "[COLOR deeppink]" + duration + "[/COLOR]"
        utils.addDownLink(name, 'https://www.pornhub.com' + videopage, 592, img, '')
    try:
        nextp=re.compile('<li class="page_next"><a href="(.+?)" class="orangeButton">Next', re.DOTALL).findall(listhtml)
        utils.addDir('Next Page', 'https://www.pornhub.com' + nextp[0].replace('&amp;','&'), 596,'')
    except: pass
    xbmcplugin.endOfDirectory(utils.addon_handle)



@utils.url_dispatcher.register('592', ['url', 'name'], ['download'])
def Playvid(url, name, download=None):
    try:
        listhtml = utils.getHtml(url, '')
    except:
        return None
    media = re.compile('mediaDefinition: (.+?),\n', re.DOTALL | re.IGNORECASE).findall(listhtml)[0]
    movieJson = json.loads(media)
    movieJson = sorted([item for item in json.loads(media) if ('hls' in item['format'] and item['defaultQuality']==False)], key = lambda x: int(x['quality']), reverse=True)
    choice = xbmcgui.Dialog().select('Select resolution', [str(item['quality']) for item in movieJson])
    if choice==-1: return
    videourl = movieJson[choice]['videoUrl']
    iconimage = xbmc.getInfoImage("ListItem.Thumb")
    listitem = xbmcgui.ListItem(name, iconImage="DefaultVideo.png", thumbnailImage=iconimage)
    listitem.setInfo('video', {'Title': name, 'Genre': 'RedTube'})
    xbmc.Player().play(videourl, listitem)
    if utils.addon.getSetting("dwnld_stream") == "true" or download == 1: utils.dwnld_stream(videourl, name)

@utils.url_dispatcher.register('597', ['url'])
def PStars(url):
    try:
        listhtml = utils.getHtml(url, '')
    except:
        return None
    starsJson = json.loads(listhtml)
    for pstar in starsJson['stars']:
        name = pstar['star']
        slug = pstar['star_url'].split('/')[-1]
        starUrl = 'https://api.redtube.com/?data=redtube.Videos.searchVideos&page=1&output=json' + '&ordering=newest&stars[]=' + urllib.quote_plus(name)
        #utils.kodilog('[myUWC] - RedTube - ' + name + ' - ' + starUrl)

        imgUrl = pstar['star_thumb']
        utils.addDir(name, starUrl, 591, imgUrl)
    #try:
    thisP=re.compile('&page=(.+?)&', re.DOTALL).findall(url)[0]
    totalMovies = starsJson['count']
    maxPages = int(int(totalMovies)/20) + 1
    #xbmcgui.Dialog().textviewer(url, str(thisP) + '\n' + str(totalMovies) + '\n' + url.replace('&page=' + str(thisP) + '&', '&page=' + str(int(thisP) +1) + '&'))
    if int(thisP)<maxPages:
        nextP = int(thisP) + 1
        utils.addDir('Next Page (' + str(nextP) + '/' + str(maxPages) + ')', url.replace('&page=' + thisP + '&', '&page=' + str(nextP) + '&'), 597,'')

    #except: pass
    xbmcplugin.endOfDirectory(utils.addon_handle)

#---- RedTube Live Cams
@utils.url_dispatcher.register('580')
def MainLive():
    utils.addDir('[COLOR hotpink]Categories[/COLOR]','http://api.naiadsystems.com/search/v1/categories', 583, '', '')
    utils.addDir('[COLOR hotpink]Search[/COLOR]','http://api.naiadsystems.com/search/v1/list?results_per_page=10000',584,'','')

    ListLive('http://api.naiadsystems.com/search/v1/list?results_per_page=10000')
    xbmcplugin.endOfDirectory(utils.addon_handle)


@utils.url_dispatcher.register('581', ['url'], ['page', 'searchStr'])
def ListLive(url, page=1, searchStr=None):
    if utils.addon.getSetting("chaturbate") == "true":
        clean_database(False)
    ssearch = "x['LiveStatus']=='live'"
    if searchStr:
        #xbmcgui.Dialog().textviewer(url, str(searchStr))
        utils.kodilog('STREAMATE URL cu search: ' + url)
        if 'name' in searchStr:
            ssearch = ssearch + ' and ' + "'" + searchStr['name'].lower() + "' in x['Nickname'].lower()"
        if 'age' in searchStr:
            ssearch = ssearch + ' and ' + "x['Age']==int(" + str(searchStr['age']) + ")"
        if 'country' in searchStr:
            ssearch = ssearch + ' and ' + "'" + searchStr['country'].lower() + "' in x['Country'].lower()"
        if 'gender' in searchStr:
            ssearch = ssearch + ' and ' + "'" + str(searchStr['gender']).lower() + "' in str(x['Gender'])"
        #xbmcgui.Dialog().textviewer(url, ssearch)

    try:
        data = utils.getHtml(url + "&page_number=" + str(page))
    except:
        return None
    model_list = json.loads(data)

    #xx = sorted(list(set([x['Gender'] for x in model_list['Results']])))
    imgBase = "https://m1.nsimg.net/biopic/original4x3/%s" if utils.addon.getSetting("bio_pic") == "true" else "https://m1.nsimg.net/media/snap/%s.jpg"
    for camgirl in (x for x in model_list['Results'] if eval(ssearch)):
        performerID = str(camgirl['PerformerId'])
        img = imgBase%performerID
        name = camgirl['Nickname']
        if (not name) or name == ' ' or name == '': continue
        utils.addDownLink(name, performerID, 582, img, '')
    #npage = page + 1
    #utils.addDir('Next Page (' + str(npage) + ')', url, 581, '', npage)
    xbmcplugin.endOfDirectory(utils.addon_handle)
    return

@utils.url_dispatcher.register('582', ['url', 'name'], ['check', 'download'])
def PlayCam(url, name, check=False, download=None):
    global CAMGIRLPLOT
    global NAME
    CAMGIRLPLOT = ''
    payload = {"name":"%s"%name,"sabasic":"","sakey":"","sk":"www.redtube.com","userid":0,"version":"9.48.1","platform":"blacklabel","shownFeatures":[],"useDebugPerformerData":"false"}
    r = requests.post('https://hybridclient.naiadsystems.com/api/v3/setupplayer/', data=payload).text
    pJson = json.loads(r)
    if 'error' in pJson:
        utils.notify(name, pJson['msg'])
        return
    performerId = pJson['config']['performer']['id']
    stream = pJson['config']['stream']
    attribJson = pJson['performer']['About']['Attributes']
    NAME = attribJson['Name']

    wssUrl = stream['nodeHost'] + '/socket.io/?performerid=' + str(performerId) + '&sserver=' + stream['serverId'] + '&streamid=' + stream['streamId'] + '&sakey=&sessiontype=preview&perfdiscountid=0&minduration=0&goldshowid=0&version=7&referrer=blacklabel/hybrid.client.9.48.1/avchat.swf&usertype=false&lang=en&EIO=3&transport=websocket'
    #utils.kodilog('REDTUBE LIVE wss: ' + wssUrl)
    roomid = get_roomid(wssUrl)
    if not roomid:
        return
    server = pJson['config']['liveservices']['host'].replace('wss:', 'https:') + '/videourl?payload={"puserid":' + str(performerId) + ',"roomid":"' + roomid + '","showtype":1,"nginx":1}'
    with requests.get(server) as req:
        r = json.loads(req.text)[0]['url']
    with requests.get(r) as req1:
        try:
            encodings = json.loads(req1.text)['formats']['mp4-hls']['encodings']
        except:
            utils.notify(name, 'I\'m currently performing live...')
            return

    #movieJson = sorted([item for item in json.loads(media) if ('hls' in item['format'] and item['defaultQuality']==False)], key = lambda x: int(x['quality']), reverse=True)
    #choice = xbmcgui.Dialog().select('Select resolution', [str(item['quality']) for item in movieJson])

    choice = xbmcgui.Dialog().select('Select resolution', sorted([str(item['videoWidth']) + ' x ' + str(item['videoHeight']) for item in encodings], key = lambda x: int(x[:4]), reverse=True))
    if choice == -1: return
    videourl = encodings[choice]['location']

    CAMGIRLPLOT = CAMGIRLPLOT + '\n[B]Name:[/B] ' + attribJson['Name']
    CAMGIRLPLOT = CAMGIRLPLOT + '\n[B]Country:[/B] ' + attribJson['Country']
    CAMGIRLPLOT = CAMGIRLPLOT + '\n[B]Age:[/B] ' + str(attribJson['Age'])
    CAMGIRLPLOT = CAMGIRLPLOT + '\n[B]Height:[/B] ' + attribJson['Height']
    CAMGIRLPLOT = CAMGIRLPLOT + '\n[B]Weight:[/B] ' + attribJson['Weight']
    CAMGIRLPLOT = CAMGIRLPLOT + '\n[B]About my show:[/B] ' + pJson['performer']['About']['AboutMyShow']
    CAMGIRLPLOT = CAMGIRLPLOT + '\n[B]Last performance:[/B] ' + pJson['performer']['About']['LastPerformance']

    iconimage = xbmc.getInfoImage("ListItem.Thumb")
    listitem = xbmcgui.ListItem(name, iconImage="DefaultVideo.png", thumbnailImage=iconimage)
    listitem.setInfo('video', {'Title': name, 'Genre': 'RedTube Live', 'Plot': CAMGIRLPLOT})
    listitem.setProperty("IsPlayable","true")

    xbmc.Player().play(videourl, listitem)
    if utils.addon.getSetting("dwnld_stream") == "true" or download == 1: utils.dwnld_stream(videourl, name)


def get_roomid(url):
    global CAMGIRLPLOT
    global NAME
    CAMGIRLPLOT = ''
    ws = websocket.WebSocket()
    try:
        ws = websocket.create_connection(url)
    except:
        xbmc.log('[myUWC] ' + NAME + ' - RedTube Connection error', xbmc.LOGERROR)
        if not check: utils.notify('Connection error!')
        return

    quitting = 0
    while quitting == 0:
        message = ws.recv()
        if message.startswith('42'):
            utils.kodilog(message)
            if 'Success' not in message:
                utils.notify(NAME, 'Offline?')
                return ''
            if 'NaiadFreeze' in message:
                data = re.compile('"data":.*?"(.+?)"', re.IGNORECASE | re.MULTILINE | re.DOTALL).findall(message)[0]
                utils.kodilog(str(message[0]))
                utils.notify(NAME, str(data))
                return ''            
            if 'roomid' not in message:
                utils.notify(NAME, re.compile('"data".+?"(.+?)"', re.IGNORECASE | re.MULTILINE | re.DOTALL).findall(message)[0]) 
                return ''
            roomid = re.compile('"roomid":"(.+?)"', re.IGNORECASE | re.MULTILINE | re.DOTALL).findall(message)[0]
            plot = re.compile('"roomtopic":"(.+?)"', re.IGNORECASE | re.MULTILINE | re.DOTALL).findall(message)
            if plot:
                CAMGIRLPLOT = plot[0].encode("ascii", errors="ignore")
            #xbmcgui.Dialog().textviewer(url, str(message) + '\nroomid= ' + roomid + '\nplot= ' + CAMGIRLPLOT)
            quitting = 1
    ws.close()
    return roomid

@utils.url_dispatcher.register('583', ['url'])
def LiveCategories(url):
    try:
        cathtml = utils.getHtml(url, '')
    except Exception as e:
        utils.notify('Categories', e.message)
        return
    cJson = json.loads(cathtml)
    cat = [item for item in cJson if ('status' not in item and 'requestkey' not in item)]
    
    selectedCat = utils.selector('Select server', cat)
    #xbmcgui.Dialog().textviewer(url, str(selectedCat))
    for item in cJson[selectedCat]:
        catId = str(item['CategoryId'])
        catName = item['Name']
        catLive = str(item['LiveCount'])
        utils.addDir(catName + ' [COLOR hotpink]' + catLive + '[/COLOR]', 'http://api.naiadsystems.com/search/v1/list?categoryid=' + catId, 581, '', '')
    xbmcplugin.endOfDirectory(utils.addon_handle)



@utils.url_dispatcher.register('584', ['url'])
def LiveSearch(url):
    keyword = {}
    if not (utils.addon.getSetting('rName')=="true" or \
       utils.addon.getSetting('rAge')=="true" or \
       utils.addon.getSetting('rCountry')=="true" or \
       utils.addon.getSetting('rGender')=="true"):
        utils.addon.openSettings()
    if utils.addon.getSetting('rName')=="true":
        word = utils._get_keyboard(heading="Searching for..." + "\nName")
        if word:
            keyword['name'] = word
    if utils.addon.getSetting('rAge')=="true":
        word = utils._get_keyboard(heading="Searching for..." + "\nAge")
        if word:
            keyword['age'] = word
    if utils.addon.getSetting('rCountry')=="true":
        data = utils.getHtml(url)	# + "&page_number=" + str(page))
        model_list = json.loads(data)
        allCountries = sorted(list(set([x['Country'] for x in model_list['Results'] if x['Country']])))
        choice = xbmcgui.Dialog().select('Select country', [item for item in allCountries])
        keyword['country'] = allCountries[choice]
    if utils.addon.getSetting('rGender')=="true":
        if 'data' not in locals():
            data = utils.getHtml(url)	# + "&page_number=" + str(page))
            model_list = json.loads(data)
        allGender = sorted(list(set([x['Gender'] for x in model_list['Results'] if x['Gender']])))
        choice = xbmcgui.Dialog().select('Select Gender', [item for item in allGender])
        keyword['gender'] = allGender[choice]

    if (not keyword): return False, 0
    ListLive(url, searchStr=keyword)
