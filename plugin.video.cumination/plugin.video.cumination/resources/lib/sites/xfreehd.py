'''
    Cumination
    Copyright (C) 2018 Whitecream

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
import xbmc
import xbmcgui
from six.moves import urllib_parse
from resources.lib import utils
from resources.lib.adultsite import AdultSite

site = AdultSite('xfreehd', '[COLOR hotpink]XFreeHD[/COLOR]', 'https://www.xfreehd.com/', 'xfreehd.png', 'xfreehd')

getinput = utils._get_keyboard
xflogged = 'true' in utils.addon.getSetting('xflogged')


@site.register(default_mode=True)
def xfreehd_main():
    search_orders = {'Relevance': '', 'Most Recent': 'mr', 'Being Watched': 'bw', 'Most Viewed': 'mv', 'Most Commented': 'md', 'Top Rated': 'tr', 'Top Favorited': 'tf', 'Longest': 'lg'}
    search_order = utils.addon.getSetting("xfreeorder") or 'Relevance'
    search_order = search_order if search_order in search_orders.keys() else 'Relevance'
    context = (utils.addon_sys + "?mode=" + str('xfreehd.Sortorder'))
    contextmenu = [('[COLOR orange]Search Order[/COLOR]', 'RunPlugin(' + context + ')')]

    site.add_dir('[COLOR hotpink]Categories[/COLOR]', site.url + 'categories', 'xfreehd_cat', site.img_cat)
    site.add_dir('[COLOR hotpink]Search[/COLOR] [COLOR orange][{}][/COLOR]'.format(search_order), site.url + 'search?search_query=', 'xfreehd_search', site.img_search, contextm=contextmenu)
    if not xflogged:
        site.add_dir('[COLOR hotpink]Login[/COLOR]', '', 'Login', '', Folder=False)
    elif xflogged:
        xfuser = utils.addon.getSetting('xfuser')
        site.add_dir('[COLOR hotpink]Logout [/COLOR][COLOR orange][{}][/COLOR]'.format(xfuser), '', 'Logout', '', Folder=False)
    xfreehd_list(site.url + 'videos?o=mr')


@site.register()
def xfreehd_list(url):
    hdr = dict(utils.base_hdrs)
    hdr['Cookie'] = get_cookies()
    try:
        listhtml = utils.getHtml(url, site.url, headers=hdr)
    except:
        return None

    if xflogged and '"/user">My Profile<' not in listhtml:
        Login()
        hdr['Cookie'] = get_cookies()
        listhtml = utils._getHtml(url, site.url, headers=hdr)

    match = re.compile(r'''class="well\s*well-sm.+?href="([^"]+).+?src="(.+?).\s*title[^>]+>(.+?)duration-new">\s*([^\s]+).+?title-new.+?>([^<]+)''', re.DOTALL | re.IGNORECASE).findall(listhtml)
    for video, img, hd, duration, name in match:
        if '>PRIVATE<' in hd:
            if not xflogged:
                continue
            else:
                name = '[COLOR blue][PV][/COLOR] ' + utils.cleantext(name)
        hd = 'HD' if '>HD<' in hd else ''
        if 'data-src' in img:
            img = img.split('data-src="')[1]
        else:
            img = site.url[:-1] + img
        site.add_download_link(name, site.url[:-1] + video, 'xfreehd_play', img, name, duration=duration, quality=hd)

    match = re.compile(r'''<li><a\s*href="([^"]+)"\s*class="prevnext"''', re.DOTALL | re.IGNORECASE).search(listhtml)
    if match:
        lp = re.compile(r'Showing.+?>\d+<.+?>\d+<.+?>(\d+)</span>\s*videos', re.DOTALL | re.IGNORECASE).findall(listhtml)
        if lp:
            pages = int(lp[0]) // 30 + 1
            last_page = '/' + str(pages) if lp else ''
        else:
            pages = None
            last_page = ''
        next_page = match.group(1).replace('&amp;', '&')
        page_number = ''.join([nr for nr in next_page.split('=')[-1] if nr.isdigit()])

        cm_page = (utils.addon_sys + "?mode=xfreehd.GotoPage" + "&url=" + urllib_parse.quote_plus(next_page) + "&np=" + str(page_number) + "&lp=" + str(pages))
        cm = [('[COLOR violet]Goto Page #[/COLOR]', 'RunPlugin(' + cm_page + ')')]

        site.add_dir('Next Page (' + page_number + last_page + ')', next_page, 'xfreehd_list', site.img_next, contextm=cm)
    utils.eod()


@site.register()
def xfreehd_cat(url):
    listhtml = utils.getHtml(url)
    match = re.compile(r'''class="col-xs-6\s*col-sm-4\scol.+?href="([^"]+).+?data-src="([^"]+)"\s*title="([^"]+).+?badge">([^<]+)''', re.DOTALL | re.IGNORECASE).findall(listhtml)
    for catpage, img, name, videos in match:
        name = utils.cleantext(name.strip()) + " [COLOR hotpink]%s Videos[/COLOR]" % videos
        site.add_dir(name, site.url[:-1] + catpage, 'xfreehd_list', site.url[:-1] + img)
    utils.eod()


@site.register()
def xfreehd_search(url, keyword=None):
    if not keyword:
        site.search_dir(url, 'xfreehd_search')
    else:
        title = keyword.replace(' ', '%20')
        search_orders = {'Relevance': '', 'Most Recent': 'mr', 'Being Watched': 'bw', 'Most Viewed': 'mv', 'Most Commented': 'md', 'Top Rated': 'tr', 'Top Favorited': 'tf', 'Longest': 'lg'}
        search_order = utils.addon.getSetting("xfreeorder") or 'Relevance'
        search_order = search_order if search_order in search_orders.keys() else 'Relevance'
        url = url + title + '&search_type=videos&o={}'.format(search_orders[search_order]) if search_order != 'Relevance' else url + title + '&search_type=videos'
        xfreehd_list(url)


@site.register()
def Sortorder():
    search_orders = {'Relevance': '', 'Most Recent': 'mr', 'Being Watched': 'bw', 'Most Viewed': 'mv', 'Most Commented': 'md', 'Top Rated': 'tr', 'Top Favorited': 'tf', 'Longest': 'lg'}
    order = utils.selector('Select sort order', search_orders.keys())
    if order:
        utils.addon.setSetting('xfreeorder', order)
        utils.refresh()


@site.register()
def xfreehd_play(url, name, download=None):
    vp = utils.VideoPlayer(name, download)
    vp.progress.update(25, "[CR]Loading video page[CR]")

    hdr = dict(utils.base_hdrs)
    hdr['Cookie'] = get_cookies()
    html = utils.getHtml(url, site.url, headers=hdr)

    if 'This is a private video.' in html:
        if '"/user">My Profile<' not in html:
            utils.notify('Cumination', 'Not logged in!')
            return
        match = re.compile(r'data-id="([^"]+)">', re.DOTALL | re.IGNORECASE).findall(html)
        if match:
            userid = match[0]
            posturl = site.url + 'ajax/subscribe'
            postdata = {'user_id': userid}
            response = utils._postHtml(posturl, form_data=postdata, headers=hdr)
            html = utils._getHtml(url, site.url, headers=hdr)
        if not match or '"status":-1' in response:
            utils.notify('Cumination', 'Subscribe error...')
            return

    sources = {}
    srcs = re.compile(r'''src="([^"]+)"\s*title="(SD|HD)"''', re.DOTALL | re.IGNORECASE).findall(html)

    if srcs:
        sources = {x[1]: x[0] for x in srcs}
        videourl = utils.selector('Select quality', sources, setting_valid='qualityask', sort_by=lambda x: x)
        if videourl:
            vp.play_from_direct_link(videourl)


@site.register()
def Login():
    xfuser = utils.addon.getSetting('xfuser') if utils.addon.getSetting('xfuser') else ''
    xfpass = utils.addon.getSetting('xfpass') if utils.addon.getSetting('xfpass') else ''
    if xfuser == '':
        xfuser = getinput(default=xfuser, heading='Input your XFreeHD username')
        xfpass = getinput(default=xfpass, heading='Input your XFreeHD password', hidden=True)
    loginurl = '{0}login'.format(site.url)
    postRequest = {'username': xfuser,
                   'password': xfpass,
                   'submit_login': ''}
    response = utils._postHtml(loginurl, form_data=postRequest)
    if 'Welcome {}!'.format(xfuser) in response:
        utils.addon.setSetting('xflogged', 'true')
        utils.addon.setSetting('xfuser', xfuser)
        utils.addon.setSetting('xfpass', xfpass)
        success = True
        utils.refresh()
    else:
        utils.notify('Failure logging in', 'Failure, please check your username or password')
        utils.addon.setSetting('xfuser', '')
        utils.addon.setSetting('xfpass', '')
        success = False
    return success


@site.register()
def Logout():
    clear = utils.selector('Clear stored user & password?', ['Yes', 'No'], reverse=True)
    if clear:
        if clear == 'Yes':
            utils.addon.setSetting('xfuser', '')
            utils.addon.setSetting('xfpass', '')
        utils.addon.setSetting('xflogged', 'false')
        utils._getHtml(site.url + 'logout')
        utils.refresh()


@site.register()
def GotoPage(url, np, lp):
    dialog = xbmcgui.Dialog()
    pg = dialog.numeric(0, 'Enter Page number')
    if pg:
        if int(lp) > 0 and int(pg) > int(lp):
            utils.notify(msg='Out of range!')
            return
        if 'page=' in url:
            url = url.replace('page={}'.format(np), 'page={}'.format(pg))
        contexturl = (utils.addon_sys + "?mode=xfreehd.xfreehd_list&url=" + urllib_parse.quote_plus(url))
        xbmc.executebuiltin('Container.Update(' + contexturl + ')')


def get_cookies():
    domain = site.url.split('//')[-1][:-1]
    cookiestr = ''
    for cookie in utils.cj:
        if cookie.domain == domain and cookie.name == 'AVS':
            cookiestr = 'AVS=' + cookie.value
    if xflogged and 'AVS=' not in cookiestr:
        Login()
    return cookiestr
