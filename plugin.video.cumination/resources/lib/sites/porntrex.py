"""
    Cumination
    Copyright (C) 2018 Whitecream, holisticdioxide

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
from six.moves import urllib_parse
from random import randint
import xbmc
import xbmcgui
from resources.lib import utils
from resources.lib.adultsite import AdultSite

site = AdultSite('porntrex', '[COLOR hotpink]PornTrex[/COLOR]', 'https://www.porntrex.com/', 'pt.png', 'porntrex')

progress = utils.progress
getinput = utils._get_keyboard
ptlogged = 'true' in utils.addon.getSetting('ptlogged')


@site.register(default_mode=True)
def PTMain():
    site.add_dir('[COLOR hotpink]Categories[/COLOR]', '{0}categories/'.format(site.url), 'PTCat', site.img_cat)
    site.add_dir('[COLOR hotpink]Search[/COLOR]', '{0}search/'.format(site.url), 'PTSearch', site.img_search)
    if not ptlogged:
        site.add_dir('[COLOR hotpink]Login[/COLOR]', '', 'PTLogin', '', Folder=False)
    elif ptlogged:
        ptuser = utils.addon.getSetting('ptuser')
        site.add_dir('[COLOR hotpink]Subscription videos[/COLOR]', '{0}my/subscriptions/?mode=async&function=get_block&block_id=list_videos_videos_from_my_subscriptions&sort_by=&from_my_subscriptions_videos=1'.format(site.url), 'PTList', page=1)
        site.add_dir('[COLOR hotpink]Manage subscriptions[/COLOR]', '{0}my/subscriptions/?mode=async&function=get_block&block_id=list_members_subscriptions_my_subscriptions'.format(site.url), 'PTSubsciptions')
        site.add_dir('[COLOR hotpink]Logout {0}[/COLOR]'.format(ptuser), '', 'PTLogin', '', Folder=False)
    ptlist = PTList('{0}latest-updates/?mode=async&function=get_block&block_id=list_videos_latest_videos_list_norm&sort_by=post_date&from=1'.format(site.url), 1)
    if not ptlist:
        utils.eod()


@site.register()
def PTList(url, page=1):
    try:
        listhtml = utils.getHtml(url)
    except ValueError as e:
        if e.args[0] == 403:
            if PTLogin(False):
                listhtml = utils.getHtml(url)
            else:
                return None
    except Exception as e:
        utils.kodilog('PT error')
        return None
    match = re.compile(r'class="video-.+?data-src="([^"]+)".+?/ul>(.+?)title.+?class="quality">([^<]+).+?clock-o"></i>\s*([^<]+).+?href="([^"]+).+?>([^<]+)', re.DOTALL | re.IGNORECASE).findall(listhtml)
    for img, private, hd, duration, videopage, name in match:
        name = utils.cleantext(name)
        if 'private' in private.lower():
            if not ptlogged:
                continue
            private = "[COLOR orange][PV][/COLOR] "
        else:
            private = ""
        if any(x in hd for x in ['720', '1080']):
            hd = "[COLOR orange]HD[/COLOR] "
        elif any(x in hd for x in ['1440', '2160']):
            hd = "[COLOR yellow]4K[/COLOR] "
        else:
            hd = ""
        name = "{0}{1} {2}[COLOR deeppink]{3}[/COLOR]".format(private, name, hd, duration)
        if img.startswith('//'):
            img = 'https:' + img
        elif img.startswith('/'):
            baseurl = 'https://www.porntrex.com' if 'porntrex.com' in url else 'https://www.javwhores.com'
            img = baseurl + img
        img = re.sub(r"http:", "https:", img)
        imgint = randint(1, 10)
        newimg = str(imgint) + '.jpg'
        img = img.replace('1.jpg', newimg)
        img = img.replace(' ', '%20')
        img = img + '|Referer=' + url
        contextmenu = []
        if ptlogged:
            contexturl = (utils.addon_sys
                          + "?mode=" + str('porntrex.PTCheck_pornstars')
                          + "&url=" + urllib_parse.quote_plus(videopage))
            contextmenu.append(('[COLOR deeppink]Add pornstar to subscriptions[/COLOR]', 'RunPlugin(' + contexturl + ')'))
        contexturl = (utils.addon_sys
                      + "?mode=" + str('porntrex.PTCheck_tags')
                      + "&url=" + urllib_parse.quote_plus(videopage))
        contextmenu.append(('[COLOR deeppink]Lookup tags[/COLOR]', 'RunPlugin(' + contexturl + ')'))
        site.add_download_link(name, videopage, 'PTPlayvid', img, '', contextm=contextmenu)
    if re.search('<li class="next">', listhtml, re.DOTALL | re.IGNORECASE):
        search = False
        npage = page + 1
        if 'list_videos_latest_videos_list' in url:
            url = url.replace('from=' + str(page), 'from=' + str(npage))
            search = True
        elif '/categories/' in url:
            url = url.replace('from=' + str(page), 'from=' + str(npage))
            search = True
        elif 'list_videos_common_videos_list_norm' in url:
            if len(match) == 120:
                url = url.replace('from4=' + str(page), 'from4=' + str(npage))
                search = True
        elif '/search/' in url:
            url = url.replace('from_videos=' + str(page), 'from_videos=' + str(npage)).replace('from_albums=' + str(page), 'from_albums=' + str(npage))
            search = True
        elif 'from_my_subscriptions_videos' in url:
            if len(match) == 10:
                url = url.replace('from_my_subscriptions_videos=' + str(page), 'from_my_subscriptions_videos=' + str(npage))
                search = True
        else:
            url = url.replace('/' + str(page) + '/', '/' + str(npage) + '/')
            search = True
        if search:
            site.add_dir('Next Page (' + str(npage) + ')', url, 'PTList', site.img_next, npage)
    utils.eod()
    return True


@site.register()
def PTPlayvid(url, name, download=None):
    progress.create('Play video', 'Searching for videofile.')
    progress.update(25, "[CR]Loading video page[CR]")
    videopage = utils.getHtml(url)
    if 'Only active members can watch private videos' in videopage:
        if PTLogin(False):
            videopage = utils.getHtml(url)
        else:
            progress.close()
            return
    if 'video_url_text' not in videopage:
        videourl = re.compile("video_url: '([^']+)'", re.DOTALL | re.IGNORECASE).search(videopage).group(1)
    else:
        sources = {}
        srcs = re.compile("video(?:_alt_|_)url(?:[0-9]|): '([^']+)'.*?video(?:_alt_|_)url(?:[0-9]|)_text: '([^']+)'", re.DOTALL | re.IGNORECASE).findall(videopage)
        for src, quality in srcs:
            sources[quality] = src
        videourl = utils.prefquality(sources, sort_by=lambda x: int(''.join([y for y in x if y.isdigit()])), reverse=True)
    if not videourl:
        progress.close()
        return
    progress.update(75, "[CR]Video found[CR]")
    progress.close()
    if download == 1:
        utils.downloadVideo(videourl, name)
    else:
        iconimage = xbmc.getInfoImage("ListItem.Thumb")
        listitem = xbmcgui.ListItem(name)
        listitem.setArt({'thumb': iconimage, 'icon': "DefaultVideo.png", 'poster': iconimage})
        listitem.setInfo('video', {'Title': name, 'Genre': 'Porn'})
        xbmc.Player().play(videourl, listitem)


@site.register()
def PTCat(url):
    cathtml = utils.getHtml(url, '')
    cat_block = re.compile('<span class="icon type-video">(.*?)<div class="footer-margin">', re.DOTALL | re.IGNORECASE).search(cathtml).group(1)
    match = re.compile('<a class="item" href="([^"]+)" title="([^"]+)".*?src="([^"]+)"', re.DOTALL | re.IGNORECASE).findall(cat_block)
    for catpage, name, img in sorted(match, key=lambda x: x[1]):
        if img.startswith('//'):
            img = 'https:' + img
        catpage = catpage + '?mode=async&function=get_block&block_id=list_videos_common_videos_list&sort_by=post_date&from=1'
        site.add_dir(name, catpage, 'PTList', img, 1)
    utils.eod()


@site.register()
def PTSearch(url, keyword=None):
    searchUrl = url
    if not keyword:
        site.search_dir(url, 'PTSearch')
    else:
        searchUrl += keyword.replace(' ', '%20')
        searchUrl += '/latest-updates/'
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
        if logged:
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
        response = utils.postHtml(loginurl, form_data=postRequest)
        if 'success' in response.lower():
            utils.addon.setSetting('ptlogged', 'true')
            utils.addon.setSetting('ptuser', ptuser)
            utils.addon.setSetting('ptpass', ptpass)
            success = True
        else:
            utils.notify('Failure logging in', 'Failure, please check your username or password')
            success = False
    elif ptlogged:
        utils.addon.setSetting('ptlogged', 'false')
        utils.addon.setSetting('ptuser', '')
        utils.addon.setSetting('ptpass', '')
    if logged:
        xbmc.executebuiltin('Container.Refresh')
    else:
        return success


@site.register()
def PTSubsciptions(url):
    try:
        listhtml = utils.getHtml(url)
    except ValueError as e:
        if e.args[0] == 403:
            if PTLogin(False):
                listhtml = utils.getHtml(url)
            else:
                return None
    except Exception as e:
        return None

    results = re.findall('(?si)href="([^"]+)".*?data-original="([^"]+)" alt="([^"]+)', listhtml)
    for url, img, name in results:
        if img.startswith('//'):
            img = 'https:' + img
            img = img.replace(' ', '%20')
        id = img.split('/')[5]
        if ptlogged:
            contexturl = (utils.addon_sys
                          + "?mode=" + str('porntrex.PTSubscribe_pornstar')
                          + "&url=" + urllib_parse.quote_plus(url)
                          + "&id=" + str(id)
                          + "&what=" + str('unsubscribe'))
            contextmenu = ('[COLOR deeppink]Unsubscribe[/COLOR]', 'RunPlugin(' + contexturl + ')')
        url = url + '?mode=async&function=get_block&block_id=list_videos_common_videos_list_norm&sort_by=post_date&from4=1'
        site.add_dir(name, url, 'PTList', img, 1, contextm=contextmenu)
    utils.eod()


@site.register()
def PTCheck_tags(url):
    try:
        listhtml = utils.getHtml(url)
    except Exception as _:
        return None
    tags = {}
    matches = re.compile('<a href="([^"]+tags[^"]+)">([^<]+)</a>', re.DOTALL | re.IGNORECASE).findall(listhtml)
    if matches:
        for url, tag in matches:
            tag = tag.strip()
            tags[tag] = url
        selected_tag = utils.selector('Pick a tag to look up videos', tags, show_on_one=True)
        if not selected_tag:
            return

        tagurl = selected_tag + '?mode=async&function=get_block&block_id=list_videos_common_videos_list_norm&sort_by=post_date&from4=1'
        contexturl = (utils.addon_sys
                      + "?mode=" + str('porntrex.PTList')
                      + "&url=" + urllib_parse.quote_plus(tagurl))
        xbmc.executebuiltin('XBMC.Container.Update(' + contexturl + ')')
    else:
        utils.notify('Notify', 'No tags found at this video')
        return


@site.register()
def PTCheck_pornstars(url):
    try:
        listhtml = utils.getHtml(url)
    except Exception as _:
        return None
    pornstars = {}
    matches = re.compile('<a href="([^"]+models[^"]+)"><i class="fa fa-star"></i>([^<]+)</a>', re.DOTALL | re.IGNORECASE).findall(listhtml)
    if matches:
        for url, model in matches:
            model = model.strip()
            pornstars[model] = url
        selected_model = utils.selector('Choose model to add', pornstars, sort_by=lambda x: x[1], show_on_one=True)
        if not selected_model:
            return

        try:
            modelhtml = utils.getHtml(selected_model)
        except Exception as _:
            return None
        id = re.findall(r'(?si)data-subscribe-to="model" data-id="(\d+)"', modelhtml)[0]
        if id:
            success = PTSubscribe_pornstar(selected_model, id)
            if success:
                utils.notify('Success', 'Pornstar added successfull to your subscriptions')
    else:
        utils.notify('Notify', 'No tagged pornstars found in this video')
    return


@site.register()
def PTSubscribe_pornstar(url, id, what='subscribe'):
    url = url + '/' if not url.endswith('/') else url
    suburl = '%s?mode=async&format=json&action=subscribe&subscribe_model_id=%s' % (url, id)
    if what == 'unsubscribe':
        suburl = suburl.replace('subscribe', 'unsubscribe')
    response = utils.getHtml(suburl, url)
    if 'success' in response.lower():
        success = True
    else:
        if what == 'unsubscribe':
            utils.notify('Failure', 'Failure removing the pornstar from your subscriptions')
        else:
            utils.notify('Failure', 'Failure adding the pornstar to your subscriptions')
        success = False
    if what == 'unsubscribe':
        utils.notify('Success', 'Pornstar removed successfull from your subscriptions')
        xbmc.executebuiltin('Container.Refresh')
    return success
