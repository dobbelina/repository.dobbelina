'''
    Cumination
    Copyright (C) 2021 Team Cumination

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

from resources.lib import utils
from resources.lib.adultsite import AdultSite

site = AdultSite('javhoho', '[COLOR hotpink]JavHoHo[/COLOR]', 'https://www1.javhoho.com/', 'https://www1.javhoho.com/wp-content/uploads/2019/11/JAVHOHO-logo-x.png', 'javhoho')


@site.register(default_mode=True)
def Main():
    site.add_dir('[COLOR hotpink]Categories[/COLOR]', site.url, 'Cat', site.img_cat)
    site.add_dir('[COLOR hotpink]Search[/COLOR]', site.url + 'search/', 'Search', site.img_search)
    List(site.url)


@site.register()
def List(url):
    try:
        listhtml = utils.getHtml(url)
    except:
        return None
    match = re.compile('div id="post(.+?)href="([^"]+)".+?src="([^"]+)".+?title="([^"]+)"', re.DOTALL | re.IGNORECASE).findall(listhtml)
    for badges, videopage, img, name in match:
        badge = ''
        if '4k-porn-icon.png' in badges.lower():
            badge = '[COLOR orange][4k][/COLOR]'
        if 'scat.png' in badges.lower():
            badge += '[COLOR brown][scat][/COLOR]'
        if 'premium-icon.png' in badges.lower():
            badge += '[COLOR blue][premium][/COLOR]'
        name = utils.cleantext(name)
        if 'Collection' in name:
            site.add_dir('{} [COLOR dimgray]{}[/COLOR]'.format(badge, name), videopage, 'Collection', img)
        else:
            site.add_download_link(name, videopage, 'Playvid', img, name)
    try:
        next_page = re.compile('href="([^"]+)">&raquo;<').findall(listhtml)[0]
        last_page = re.compile('class="last" href="([^"]+)"').findall(listhtml)
        if last_page:
            last = last_page[0].split('/')[-2]
        page_nr = re.findall(r'\d+', next_page)[-1]
        site.add_dir('Next Page (' + page_nr + ('/' + last if last_page else '') + ')', next_page, 'List', site.img_next)
    except:
        pass
    utils.eod()


@site.register()
def Collection(url):
    listhtml = utils.getHtml(url)
    match = re.compile(r'data-token="([^"]+)"\s*data-account-id="([^"]+)"\s*data-drive-id="([^"]+)".+?data-path="([^"]+)"', re.DOTALL | re.IGNORECASE).findall(listhtml)
    if match:
        listtoken, account_id, drive_id, folderPath = match[0]
        posturl = 'https://www1.javhoho.com/wp-admin/admin-ajax.php'
        form_data = {}
        form_data['listtoken'] = listtoken
        form_data['account_id'] = account_id
        form_data['drive_id'] = drive_id
        form_data['folderPath'] = folderPath
        form_data['lastFolder'] = ''
        form_data['sort'] = 'name:asc'
        form_data['action'] = 'shareonedrive-get-filelist'
        form_data['_ajax_nonce'] = '44a0ac11f9'
        form_data['mobile'] = 'false'
        form_data['query'] = ''
        response = utils.postHtml(posturl, form_data=form_data)
    else:
        return
    match = re.compile(r'''class='entry file.+?data-src='([^']+)'(.+?)<span>([^<]+)<.+?<source data-src=\\"([^"]+)"''', re.DOTALL | re.IGNORECASE).findall(response)
    if match:
        for img, duration, name, videourl in match:
            m = re.compile(r"class='entry-duration'.+?>([\s\d:]+)<", re.DOTALL | re.IGNORECASE).findall(duration)
            duration = m[0] if m else ''
            name = name.replace('\\', '')
            img = img.replace('\\', '')
            videourl = videourl.replace('\\', '')
            site.add_download_link(name, videourl, 'Playvideo', img, duration=duration)
        utils.eod()


@site.register()
def Playvideo(url, name, download=None):
    vp = utils.VideoPlayer(name, download)
    vp.progress.update(20, "[CR]Loading video page[CR]")
    vp.play_from_direct_link(url)


@site.register()
def Search(url, keyword=None):
    searchUrl = url
    if not keyword:
        site.search_dir(url, 'Search')
    else:
        title = keyword.replace(' ', '%20')
        searchUrl = searchUrl + title
        List(searchUrl)


@site.register()
def Cat(url):
    cathtml = utils.getHtml(url, '')
    cathtml = cathtml.split('id="categories-3"')[-1].split('</div>')[0]
    match = re.compile('href="([^"]+)".*?>([^<]+)<', re.DOTALL | re.IGNORECASE).findall(cathtml)
    for catpage, name in match:
        site.add_dir(name, catpage, 'List', '')
    utils.eod()


@site.register()
def Playvid(url, name, download=None):
    vp = utils.VideoPlayer(name, download)
    vp.progress.update(20, "[CR]Loading video page[CR]")

    listhtml = utils.getHtml(url, site.url)
    listhtml = listhtml.split('Free Player<')[1].split('>VIP Download')[0]
    match = re.compile('src="([^"]+)"',).findall(listhtml)
    videoArray = {}
    for item in match:
        vp.progress.update(30, "[CR]Loading video page[CR]")
        if 'javhoho.com' in item:
            item = utils.getVideoLink(item, site.url)
        # if 'hxdrive.xyz' in item:
        #     if '/embed/' not in item:
        #         item = item.replace('hxdrive.xyz/', 'hxdrive.xyz/embed/')
        #     try:
        #         listhtml = utils.getHtml(item)
        #         item = re.compile('<iframe src="([^"]+)"', re.DOTALL).findall(listhtml)[0]
        #         if item.startswith('//'):
        #             item = 'https:' + item
        #     except:
        #         pass
        if 'bitporno' in item:
            try:
                listhtml = utils.getHtml(item)
                videourl = re.compile('file: "(.+?)"', re.DOTALL).findall(listhtml)[0]
                if videourl.startswith('/'):
                    videourl = 'https://www.bitporno.com' + videourl
                videoArray['Bitporno'] = videourl
            except:
                pass
        if 'streamz.cc' in item:
            try:
                listhtml = utils.getHtml(item)
                packed = re.compile(r'(eval\(function\(p,a,c,k,e,d\).+?)\s*</script>', re.DOTALL | re.IGNORECASE).findall(listhtml)[0]
                unpacked = utils.unpack(packed)
                videourl = re.compile("'(http.+?)\\\\'", re.DOTALL | re.IGNORECASE).findall(unpacked)[0]
                videoArray['Streamz.cc'] = videourl
            except:
                pass
        # if 'gdriveplayer.to' in item:
        #     try:
        #         listhtml = utils.getHtml(item)
        #         packed = re.compile(r'(eval\(function\(p,a,c,k,e,d\).+?)\s*</script>', re.DOTALL | re.IGNORECASE).findall(listhtml)[0]
        #         unpacked = utils.unpack(packed)
        #         videourl = re.compile("'(http.+?)'", re.DOTALL | re.IGNORECASE).findall(unpacked)[0]
        #         videoArray['Gdriveplayer.to'] = videourl
        #     except:
        #         pass
        if 'youvideos.ru' in item:
            item = item.replace('youvideos.ru/f/', 'youvideos.ru/v/')
            videoArray['YouVideos.ru'] = item
    if not videoArray:
        utils.notify('Oh oh', 'Couldn\'t find a video')
        return
    choice = utils.selector('Select server', videoArray)
    if not choice:
        return
    videourl = choice
    if 'youvideos.ru' in videourl:
        videourl = videourl.replace('youvideos.ru/v', 'feurl.com/v')
        vp.play_from_link_to_resolve(videourl)
    else:
        vp.play_from_direct_link(videourl)
    return
