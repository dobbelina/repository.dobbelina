"""
    Cumination
    Copyright (C) 2018 Whitecream, holisticdioxide
    Copyright (C) 2020 Team Cumination

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
"""

import re
from six.moves import urllib_parse, urllib_error
from random import randint
import xbmc
from resources.lib import utils
from resources.lib.adultsite import AdultSite

site = AdultSite('porntrex', '[COLOR hotpink]PornTrex[/COLOR]', 'https://www.porntrex.com/', 'pt.png', 'porntrex')

getinput = utils._get_keyboard
ptlogged = 'true' in utils.addon.getSetting('ptlogged')
lengthChoices = {'All': '', '0-10 min': 'ten-min/', '10-30 min': 'ten-thirty-min/', '30+': 'thirty-all-min/'}
ptlength = utils.addon.getSetting("ptlength") or 'All'


@site.register(default_mode=True)
def PTMain():
    site.add_dir('[COLOR hotpink]Length: [/COLOR] [COLOR orange]{0}[/COLOR]'.format(ptlength), '', 'PTLength', '', Folder=False)
    site.add_dir('[COLOR hotpink]Categories[/COLOR]', '{0}categories/'.format(site.url), 'PTCat', site.img_cat)
    site.add_dir('[COLOR hotpink]Models[/COLOR]', '', 'PTModelsAZ', site.img_cat)
    site.add_dir('[COLOR hotpink]Search[/COLOR]', '{0}search/'.format(site.url), 'PTSearch', site.img_search)
    if not ptlogged:
        site.add_dir('[COLOR hotpink]Login[/COLOR]', '', 'PTLogin', '', Folder=False)
    elif ptlogged:
        site.add_dir('[COLOR hotpink]Porntrex account (favorites, subscriptions)[/COLOR]', '', 'PTAccount', '')
    ptlist = PTList('{0}latest-updates/{1}'.format(site.url, lengthChoices[ptlength]), 1)
    if not ptlist:
        utils.eod()


@site.register()
def PTAccount():
    ptuser = utils.addon.getSetting('ptuser')
    site.add_dir('[COLOR hotpink]Subscription videos[/COLOR]', '{0}my/subscriptions/?mode=async&function=get_block&block_id=list_videos_videos_from_my_subscriptions&sort_by=&from_my_subscriptions_videos=1'.format(site.url), 'PTList', page=1)
    site.add_dir('[COLOR hotpink]Manage subscriptions[/COLOR]', '{0}my/subscriptions/?mode=async&function=get_block&block_id=list_members_subscriptions_my_subscriptions&sort_by=added_date&from_my_subscriptions=1'.format(site.url), 'PTSubscriptions')
    site.add_dir('[COLOR hotpink]PT Favorites[/COLOR]', site.url + 'my/favourites/videos/?mode=async&function=get_block&block_id=list_videos_my_favourite_videos&fav_type=0&playlist_id=0&sort_by=&from_my_fav_videos=1', 'PTList', site.img_cat)
    site.add_dir('[COLOR hotpink]Logout {0}[/COLOR]'.format(ptuser), '', 'PTLogin', '', Folder=False)
    utils.eod()


@site.register()
def PTLength():
    input = utils.selector('Select Length', lengthChoices.keys())
    if input:
        ptlength = input
        utils.addon.setSetting('ptlength', ptlength)
        xbmc.executebuiltin('Container.Refresh')


@site.register()
def PTList(url, page=1):
    hdr = dict(utils.base_hdrs)
    hdr['Cookie'] = get_cookies()
    try:
        listhtml = utils.getHtml(url, site.url, headers=hdr, error='raise')
    except urllib_error.HTTPError as e:
        if e.code == 403:
            if PTLogin(False):
                hdr['Cookie'] = get_cookies()
                listhtml = utils.getHtml(url, site.url, headers=hdr)
    if ptlogged and ('>Log in<' in listhtml):
        if PTLogin(False):
            hdr['Cookie'] = get_cookies()
            listhtml = utils.getHtml(url, site.url, headers=hdr)
        else:
            return None
    try:
        videos = listhtml.split('class="video-preview-screen')
        videos.pop(0)
    except:
        videos = []
    if len(videos) == 0:
        utils.notify("Oh oh", "No videos found")
        return
    for video in videos:
        match = re.compile(r'data-src="([^"]+)".+?/>(.+?)class="quality">([^<]+).+?clock-o"></i>\s*([\d:]+).+?href="([^"]+).+?>([^<]+)</a>.+?li>([^<]+)<', re.DOTALL | re.IGNORECASE).findall(video)
        if match:
            img, private, hd, duration, videopage, name, age = match[0]
            name = utils.cleantext(name)
            if 'private' in private.lower():
                if not ptlogged:
                    continue
                private = "[COLOR blue][PV][/COLOR] "
            else:
                private = ""
            if any(x in hd for x in ['720', '1080']):
                hd = "[COLOR orange]HD[/COLOR] "
            elif any(x in hd for x in ['1440', '2160']):
                hd = "[COLOR yellow]4K[/COLOR] "
            else:
                hd = ""
            name = "{0}{1}".format(private, name)  # , hd, duration)
            if img.startswith('//'):
                img = 'https:' + img
            elif img.startswith('/'):
                img = site.url[:-1] + img
            img = re.sub(r"http:", "https:", img)
            imgint = randint(1, 10)
            newimg = str(imgint) + '.jpg'
            img = img.replace('1.jpg', newimg)
            img = img.replace(' ', '%20')
            img = img + '|Referer=' + url
            contextmenu = []
            contexturl = (utils.addon_sys
                        + "?mode=" + str('porntrex.Lookupinfo')
                        + "&url=" + urllib_parse.quote_plus(videopage))
            contextmenu.append(('[COLOR deeppink]Lookup info[/COLOR]', 'RunPlugin(' + contexturl + ')'))
            if ptlogged:
                if '/models' in url:
                    contexturl = (utils.addon_sys
                                  + "?mode=" + str('porntrex.PTSubscribe_pornstar')
                                  + "&url=" + urllib_parse.quote_plus(url))
                    contextmenu.append(('[COLOR deeppink]Subscribe to pornstar[/COLOR]', 'RunPlugin(' + contexturl + ')'))
                if 'my_favourite_videos' in url:
                    contextdel = (utils.addon_sys
                                  + "?mode=" + str('porntrex.ContextMenu')
                                  + "&url=" + urllib_parse.quote_plus(videopage)
                                  + "&fav=del")
                    contextmenu.append(('[COLOR deeppink]Delete from PT favorites[/COLOR]', 'RunPlugin(' + contextdel + ')'))
                else:
                    contextadd = (utils.addon_sys
                                  + "?mode=" + str('porntrex.ContextMenu')
                                  + "&url=" + urllib_parse.quote_plus(videopage)
                                  + "&fav=add")
                    contextmenu.append(('[COLOR deeppink]Add to PT favorites[/COLOR]', 'RunPlugin(' + contextadd + ')'))
            plot = '{}\n{}'.format(name, age)
            site.add_download_link(name, videopage, 'PTPlayvid', img, plot, contextm=contextmenu, duration=duration, quality=hd)
        else:
            utils.notify("Oh oh", "No videos found")
    if re.search('<li class="next">', videos[-1], re.DOTALL | re.IGNORECASE):
        search = True
        if not page:
            page = 1
        npage = page + 1

        if '?' in url:
            for x in ('from=', 'from4=', 'from5=', 'from_my_subscriptions_videos=', 'from_my_fav_videos=', 'from_videos=', 'from_uploaded_videos='):
                url = url.replace(x + str(page), x + str(npage))
                url = url.replace(x + '0' + str(page), x + str(npage))
        elif url.endswith('/{}/'.format(str(page))):
            url = url.replace('/{}/'.format(str(page)), '/{}/'.format(str(npage)))
        else:
            url += '{}/'.format(str(npage))

        lastp = re.compile(r'class="pagination".+data-max="(\d+)"', re.DOTALL | re.IGNORECASE).findall(listhtml)
        if lastp:
            lastp = '/{}'.format(lastp[0])
            if npage > int(lastp[1:]):
                search = False
        else:
            lastp = ''

        if search:
            site.add_dir('Next Page (' + str(npage) + lastp + ')', url, 'PTList', site.img_next, npage)
    utils.eod()
    return True


@site.register()
def PTPlayvid(url, name, download=None):
    vp = utils.VideoPlayer(name, download)
    vp.progress.update(25, "[CR]Loading video page[CR]")

    hdr = dict(utils.base_hdrs)
    hdr['Cookie'] = get_cookies()
    videopage = utils.getHtml(url, site.url, headers=hdr)

    if 'video_url_text' not in videopage:
        videourl = re.compile("video_url: '([^']+)'", re.DOTALL | re.IGNORECASE).search(videopage).group(1)
    else:
        sources = {}
        srcs = re.compile("video(?:_alt_|_)url(?:[0-9]|): '([^']+)'.*?video(?:_alt_|_)url(?:[0-9]|)_text: '([^']+)'", re.DOTALL | re.IGNORECASE).findall(videopage)
        for src, quality in srcs:
            sources[quality] = src
        videourl = utils.prefquality(sources, sort_by=lambda x: int(''.join([y for y in x if y.isdigit()])), reverse=True)
    if not videourl:
        vp.progress.close()
        return
    vp.progress.update(75, "[CR]Video found[CR]")
    vp.play_from_direct_link(videourl)


@site.register()
def PTCat(url):
    cathtml = utils.getHtml(url, '')
    cat_block = re.compile('<span class="icon type-video">(.*?)<div class="footer-margin">', re.DOTALL | re.IGNORECASE).search(cathtml).group(1)
    match = re.compile('<a class="item" href="([^"]+)" title="([^"]+)".*?src="([^"]+)".+?class="videos">([^<]+)<', re.DOTALL | re.IGNORECASE).findall(cat_block)
    for catpage, name, img, videos in sorted(match, key=lambda x: x[1]):
        if img.startswith('//'):
            img = 'https:' + img
        catpage += lengthChoices[ptlength]
        catpage += '?mode=async&function=get_block&block_id=list_videos_common_videos_list&sort_by=post_date&from=1'
        name = name + '[COLOR deeppink] ' + videos + '[/COLOR]'
        site.add_dir(name, catpage, 'PTList', img, 1)
    utils.eod()


@site.register()
def PTSearch(url, keyword=None):
    searchUrl = url
    if not keyword:
        site.search_dir(url, 'PTSearch')
    else:
        searchUrl += keyword.replace(' ', '%20')
        searchUrl += '/' + lengthChoices[ptlength]
        PTList(searchUrl, 1)


@site.register()
def PTLogin(logged=True):
    ptlogged = utils.addon.getSetting('ptlogged')
    if not logged:
        ptlogged = False
        utils.addon.setSetting('ptlogged', 'false')

    if not ptlogged or 'false' in ptlogged:
        ptuser = utils.addon.getSetting('ptuser') if utils.addon.getSetting('ptuser') else ''
        ptpass = utils.addon.getSetting('ptpass') if utils.addon.getSetting('ptpass') else ''
        if ptuser == '':
            ptuser = getinput(default=ptuser, heading='Input your Porntrex username')
            ptpass = getinput(default=ptpass, heading='Input your Porntrex password', hidden=True)

        loginurl = '{0}ajax-login/'.format(site.url)
        postRequest = {'action': 'login',
                       'email_link': '{0}email/'.format(site.url),
                       'format': 'json',
                       'mode': 'async',
                       'pass': ptpass,
                       'remember_me': '1',
                       'username': ptuser}
        response = utils._postHtml(loginurl, form_data=postRequest)
        if 'success' in response.lower():
            utils.addon.setSetting('ptlogged', 'true')
            utils.addon.setSetting('ptuser', ptuser)
            utils.addon.setSetting('ptpass', ptpass)
            success = True
        else:
            utils.notify('Failure logging in', 'Failure, please check your username or password')
            utils.addon.setSetting('ptuser', '')
            utils.addon.setSetting('ptpass', '')
            success = False
    elif ptlogged:
        clear = utils.selector('Clear stored user & password?', ['Yes', 'No'], reverse=True)
        if clear:
            if clear == 'Yes':
                utils.addon.setSetting('ptuser', '')
                utils.addon.setSetting('ptpass', '')
            utils.addon.setSetting('ptlogged', 'false')
            utils._getHtml(site.url + 'logout/')
            contexturl = (utils.addon_sys
                          + "?mode=" + str('porntrex.PTMain'))
            xbmc.executebuiltin('Container.Update(' + contexturl + ')')
    if logged:
        xbmc.executebuiltin('Container.Refresh')
    else:
        return success


@site.register()
def PTSubscriptions(url, page=1):
    suburl = url
    hdr = dict(utils.base_hdrs)
    hdr['Cookie'] = get_cookies()
    listhtml = utils._getHtml(url, site.url, headers=hdr)

    results = re.findall('href="([^"]+)".*?data-original="([^"]+)" alt="([^"]+).+?data-id="([^"]+)', listhtml, re.DOTALL)
    for url, img, name, id in results:
        if img.startswith('//'):
            img = 'https:' + img
            img = img.replace(' ', '%20')
            img = img + '|Referer=' + url
        if ptlogged:
            contexturl = (utils.addon_sys
                          + "?mode=" + str('porntrex.PTSubscribe_pornstar')
                          + "&url=" + urllib_parse.quote_plus(url)
                          + "&id=" + str(id)
                          + "&what=" + str('unsubscribe'))
            contextmenu = ('[COLOR deeppink]Unsubscribe[/COLOR]', 'RunPlugin(' + contexturl + ')')
        url = url + '?mode=async&function=get_block&block_id=list_videos_common_videos_list_norm&sort_by=post_date&from4=1'
        site.add_dir(name, url, 'PTList', img, 1, contextm=contextmenu)
    if len(results) == 11:
        if not page:
            page = 1
        npage = page + 1
        suburl = suburl.replace('from_my_subscriptions=' + str(page), 'from_my_subscriptions=' + str(npage))
        site.add_dir('Next Page', suburl, 'PTSubscriptions', site.img_next, npage)
    utils.eod()


@site.register()
def PTSubscribe_pornstar(url, id=None, what='subscribe'):
    if not id:
        url2 = url.split('?')[0]
        try:
            modelhtml = utils.getHtml(url2)
        except:
            return None
        id = re.findall(r'data-subscribe-to="model"\s*data-id="(\d+)"', modelhtml, re.DOTALL)[0]

    url = url2 if '?' in url else url
    url = url + '/' if not url.endswith('/') else url

    suburl = '%s?mode=async&format=json&action=subscribe&subscribe_model_id=%s' % (url, id)
    if what == 'unsubscribe':
        suburl = suburl.replace('subscribe', 'unsubscribe')
    response = utils._getHtml(suburl, url)
    if 'success' in response.lower():
        success = True
        if what == 'unsubscribe':
            utils.notify('Success', 'Pornstar removed successfully from your subscriptions')
            xbmc.executebuiltin('Container.Refresh')
        else:
            utils.notify('Success', 'Pornstar added successfully to your subscriptions')
    else:
        if what == 'unsubscribe':
            utils.notify('Failure', 'Failure removing the pornstar from your subscriptions')
        else:
            utils.notify('Failure', 'Failure adding the pornstar to your subscriptions')
        success = False

    return success


@site.register()
def ContextMenu(url, fav):
    id = url.split("/")[4]
    fav_addurl = url + '?mode=async&format=json&action=add_to_favourites&video_id=' + id + '&album_id=&fav_type=0&playlist_id=0'
    fav_delurl = url + '?mode=async&format=json&action=delete_from_favourites&video_id=' + id + '&album_id=&fav_type=0&playlist_id=0'
    fav_url = fav_addurl if fav == 'add' else fav_delurl

    hdr = dict(utils.base_hdrs)
    hdr['Cookie'] = get_cookies()
    resp = utils._getHtml(fav_url, site.url, headers=hdr)

    if fav == 'add':
        if ('success') in resp:
            utils.notify('Favorites', 'Added to PT Favorites')
        else:
            msg = re.findall('message":"([^"]+)"', resp)[0]
            utils.notify('Favorites', msg)
        return
    if fav == 'del':
        if ('success') in resp:
            utils.notify('Deleted from PT Favorites')
            xbmc.executebuiltin('Container.Refresh')
        else:
            msg = re.findall('message":"([^"]+)"', resp)[0]
            utils.notify(msg)
        return


def get_cookies():
    domain = site.url.split('www')[-1][:-1]
    cookiestr = 'kt_tcookie=1'
    for cookie in utils.cj:
        if cookie.domain == domain and cookie.name == 'PHPSESSID':
            cookiestr += '; PHPSESSID=' + cookie.value
        if cookie.domain == domain and cookie.name == 'kt_ips':
            cookiestr += '; kt_ips=' + cookie.value
        if cookie.domain == domain and cookie.name == 'kt_member':
            cookiestr += '; kt_member=' + cookie.value
    if ptlogged and 'kt_member' not in cookiestr:
        PTLogin(False)
    return cookiestr


@site.register()
def PTModelsAZ():
    for i in range(65, 91):
        url = '{0}/models/?mode=async&function=get_block&block_id=list_models_models_list&section={1}&sort_by=title&from=1'.format(site.url, chr(i))
        site.add_dir(chr(i), url, 'PTModels', '', 1)
    utils.eod()


@site.register()
def PTModels(url, page=1):
    listhtml = utils.getHtml(url, site.url)
    results = re.findall('(?si)href="([^"]+)" title="([^"]+).*?src="([^"]+)".*?videos">([^<]+)<', listhtml)
    for modelurl, name, img, videos in results:
        url2 = modelurl + '?mode=async&function=get_block&block_id=list_videos_common_videos_list_norm&sort_by=post_date&from4=1'
        if img.startswith('//'):
            img = 'https:' + img
            img = img.replace(' ', '%20')
        id = img.split('/')[5] if 'no-image-model' not in img else None
        name = name + '[COLOR deeppink] ' + videos + '[/COLOR]'
        if ptlogged and id:
            contexturl = (utils.addon_sys
                          + "?mode=" + str('porntrex.PTSubscribe_pornstar')
                          + "&url=" + urllib_parse.quote_plus(modelurl)
                          + "&id=" + str(id)
                          + "&what=" + str('subscribe'))
            contextmenu = ('[COLOR deeppink]Subscribe[/COLOR]', 'RunPlugin(' + contexturl + ')')
            site.add_dir(name, url2, 'PTList', img, 1, contextm=contextmenu)
        else:
            site.add_dir(name, url2, 'PTList', img, 1)
    if len(results) == 160:
        if not page:
            page = 1
        npage = page + 1
        url = url.replace('from=' + str(page), 'from=' + str(npage))
        site.add_dir('Next Page', url, 'PTModels', site.img_next, npage)
    utils.eod()


@site.register()
def Lookupinfo(url):
    class PorntrexLookup(utils.LookupInfo):
        def url_constructor(self, url):
            if 'categories/' in url:
                return site.url + url + '?mode=async&function=get_block&block_id=list_videos_common_videos_list&sort_by=post_date&from=1'
            if any(x in url for x in ['models/', 'tags/']):
                return site.url + url + '?mode=async&function=get_block&block_id=list_videos_common_videos_list_norm&sort_by=post_date&from4=1'
            if 'members/' in url:
                return site.url + url + 'videos/'

    lookup_list = [
        ("Cat", r'/(categories/[^"]+)">([^<]+)<', ''),
        ("Model", r'/(models[^"]+)"><i class="fa fa-star"></i>([^<]+)</a>', ''),
        ("Tag", r'/(tags[^"]+)">([^<]+)</a>', ''),
        ("Uploader", r'/(members/[^"]+)">([^<]+)<', '')
    ]
    lookupinfo = PorntrexLookup(site.url, url, 'porntrex.PTList', lookup_list)
    lookupinfo.getinfo()
