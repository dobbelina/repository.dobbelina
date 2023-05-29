'''
    Cumination
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
'''

import re
import json
from resources.lib import utils
from resources.lib.adultsite import AdultSite

site = AdultSite('txxx', '[COLOR hotpink]Txxx[/COLOR]', 'https://txxx.com/', 'txxx.png', 'txxx')
site1 = AdultSite('tubepornclassic', '[COLOR hotpink]TubePornClassic[/COLOR]', 'https://tubepornclassic.com/', 'tubepornclassic.png', 'tubepornclassic')
site2 = AdultSite('voyeurhit', '[COLOR hotpink]VoyeurHit[/COLOR]', 'https://voyeurhit.com/', 'voyeurhit.png', 'voyeurhit')
site3 = AdultSite('hclips', '[COLOR hotpink]HClips[/COLOR]', 'https://hclips.com/', 'hclips.png', 'hclips')
site4 = AdultSite('hdzog', '[COLOR hotpink]HD Zog[/COLOR]', 'https://hdzog.com/', 'hdzog.png', 'hdzog')
site5 = AdultSite('vjav', '[COLOR hotpink]Vjav[/COLOR]', 'https://vjav.com/', 'vjav.png', 'vjav')
site6 = AdultSite('shemalez', '[COLOR hotpink]ShemaleZ[/COLOR]', 'https://shemalez.com/', 'shemalez.png', 'shemalez')
site7 = AdultSite('upornia', '[COLOR hotpink]Upornia[/COLOR]', 'https://upornia.com/', 'upornia.png', 'upornia')
# site8 = AdultSite('pornzog', '[COLOR hotpink]Pornzog[/COLOR]', 'https://pornzog.com/', 'pornzog.png', 'pornzog')
site9 = AdultSite('manysex', '[COLOR hotpink]Manysex[/COLOR]', 'https://manysex.com/', 'manysex.png', 'manysex')
site10 = AdultSite('hotmovs', '[COLOR hotpink]Hotmovs[/COLOR]', 'https://hotmovs.com/', 'hotmovs.png', 'hotmovs')
# site11 = AdultSite('tporn', '[COLOR hotpink]TPorn[/COLOR]', 'https://tporn.xxx/', 'tporn.png', 'tporn')
# site12 = AdultSite('seexxx', '[COLOR hotpink]See XXX[/COLOR]', 'https://see.xxx/', 'seexxx.png', 'seexxx')
site13 = AdultSite('thegay', '[COLOR hotpink]The Gay[/COLOR]', 'https://thegay.com/', 'thegay.png', 'thegay')
site14 = AdultSite('inporn', '[COLOR hotpink]Inporn[/COLOR]', 'https://inporn.com/', 'inporn.png', 'inporn')
site15 = AdultSite('desiporn', '[COLOR hotpink]Desiporn[/COLOR]', 'https://desi-porn.tube/', 'desiporn.png', 'desiporn')


def getBaselink(url):
    if 'txxx.com' in url:
        siteurl = site.url
    elif 'tubepornclassic.com' in url:
        siteurl = site1.url
    elif 'voyeurhit.com' in url:
        siteurl = site2.url
    elif 'hclips.com' in url:
        siteurl = site3.url
    elif 'hdzog.com' in url:
        siteurl = site4.url
    elif 'vjav.com' in url:
        siteurl = site5.url
    elif 'shemalez.com' in url:
        siteurl = site6.url
    elif 'upornia.com' in url:
        siteurl = site7.url
    # elif 'pornzog.com' in url:
    #     siteurl = site8.url
    elif 'manysex.com' in url:
        siteurl = site9.url
    elif 'hotmovs.com' in url:
        siteurl = site10.url
    # elif 'tporn.xxx' in url:
    #     siteurl = site11.url
    # elif 'see.xxx' in url:
    #     siteurl = site12.url
    elif 'thegay.com' in url:
        siteurl = site13.url
    elif 'inporn.com' in url:
        siteurl = site14.url
    elif 'desi-porn.tube' in url:
        siteurl = site15.url
    return siteurl


@site.register(default_mode=True)
@site1.register(default_mode=True)
@site2.register(default_mode=True)
@site3.register(default_mode=True)
@site4.register(default_mode=True)
@site5.register(default_mode=True)
@site6.register(default_mode=True)
@site7.register(default_mode=True)
# @site8.register(default_mode=True)
@site9.register(default_mode=True)
@site10.register(default_mode=True)
# @site11.register(default_mode=True)
# @site12.register(default_mode=True)
@site13.register(default_mode=True)
@site14.register(default_mode=True)
@site15.register(default_mode=True)
def Main(url):
    siteurl = getBaselink(url)
    site.add_dir('[COLOR hotpink]Categories[/COLOR]', siteurl + 'categories', 'Categories', site.img_cat)
    if any(x in siteurl for x in ['hclips', 'hdzog', 'txxx', 'shemalez', 'upornia', 'hotmovs', 'inporn', 'manysex']):
        site.add_dir('[COLOR hotpink]Channels[/COLOR]', siteurl + 'channels', 'Channels')
    if any(x in siteurl for x in ['hdzog', 'txxx', 'tubepornclassic', 'vjav', 'shemalez', 'upornia', 'thegay', 'tporn', 'seexxx', 'pornzog', 'hotmovs', 'inporn', 'manysex']):
        site.add_dir('[COLOR hotpink]Models[/COLOR]', siteurl + 'models', 'Models')
    site.add_dir('[COLOR hotpink]Search[/COLOR]', siteurl + 'search.', 'Search', site.img_search)
    List(siteurl + 'latest-updates')
    utils.eod()


@site.register()
def List(url, page=1):
    siteurl, url = url.rsplit('/', 1)
    siteurl += '/'
    apiurl = siteurl + 'api/json/videos/86400/str/{0}/60/{1}.{2}.{3}.all..{4}.json'
    surl = siteurl + 'api/videos.php?params=259200/str/relevance/60/search..{0}.all..&s={1}&sort=latest-updates&date=all&type=all&duration=all'
    if url.startswith('search.'):
        aurl = surl.format(page, url.split('search.')[-1])
    elif '.' in url:
        c1, c2 = url.split('.')
        aurl = apiurl.format('latest-updates', c1, c2, page, 'day')
    else:
        aurl = apiurl.format(url, '', '', page, 'day')
    if 'manysex.com' in aurl:
        aurl = aurl.replace('json/videos/', 'json/videos2/')
        aurl = aurl.replace('api/videos.', 'api/videos2.')
        aurl = aurl.replace('.day.', '..')
    jdata = json.loads(utils.getHtml(aurl, siteurl))

    if not jdata.get('videos'):
        utils.eod()
        return

    for item in jdata.get('videos'):
        name = item.get('title') if utils.PY3 else item.get('title').encode('utf-8')
        duration = item.get('duration')

        hd = False
        if "props" in item.keys():
            if item["props"]:
                if "hd" in item["props"].keys():
                    if item["props"]["hd"] == "1":
                        hd = True
        if not hd and "categories" in item.keys():
            if "HD" in item["categories"].split(','):
                hd = True

        hd = 'HD' if hd else ''
        name = utils.cleantext(name)
        site.add_download_link(name, siteurl + item.get('video_id'), 'Playvid', item.get('scr'), name, duration=duration, quality=hd)

    if int(jdata.get('total_count')) - (60 * page) > 0:
        page += 1
        last_page = -(-int(jdata.get('total_count')) // 60)
        site.add_dir('Next Page ({}/{})'.format(str(page), str(last_page)), siteurl + url, 'List', site.img_next, page)

    utils.eod()


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
def Categories(url):
    siteurl, url = url.rsplit('/', 1)
    siteurl += '/'
    aurl = '{0}api/json/{1}/14400/str.all.en.json'.format(siteurl, url)
    jdata = json.loads(utils.getHtml(aurl, siteurl))
    for item in sorted(jdata.get(url), key=lambda x: x.get('title')):
        catpage = '{0}.{1}'.format(url, item.get('dir'))
        name = item.get('title') if utils.PY3 else item.get('title').encode('utf-8')
        videos = " [COLOR deeppink](" + item.get('total_videos') + " videos)[/COLOR]"
        name = name + videos if utils.PY3 else (name.decode('utf-8') + videos).encode('utf-8')
        site.add_dir(name, siteurl + catpage, 'List', site.img_cat, page=1)

    utils.eod()


@site.register()
def Channels(url, page=1):
    siteurl, url = url.rsplit('/', 1)
    siteurl += '/'
    page = 1 if not page else page
    aurl = '{0}api/json/{1}/14400/str/alphabetaz/80/..{2}.json'.format(siteurl, url, page)
    jdata = json.loads(utils.getHtml(aurl, siteurl))
    for item in jdata.get(url, []):
        catpage = '{0}.{1}'.format(url[:-1], item.get('dir'))
        name = item.get('title') if utils.PY3 else item.get('title').encode('utf-8')
        videos = " [COLOR deeppink](" + item.get('statistics').get('videos') + " videos)[/COLOR]"
        name = name + videos if utils.PY3 else (name.decode('utf-8') + videos).encode('utf-8')
        site.add_dir(name, siteurl + catpage, 'List', item.get('img'), page=1)

    if int(jdata.get('total_count', '0')) - (80 * page) > 0:
        page += 1
        last_page = -(-int(jdata.get('total_count')) // 80)
        site.add_dir('> Next Page ({}/{})'.format(str(page), str(last_page)), siteurl + url, 'Channels', site.img_next, page=page)
        if page + 5 < last_page:
            page += 4
            site.add_dir('>> Page {}'.format(str(page)), siteurl + url, 'Channels', site.img_next, page=page)

    utils.eod()


@site.register()
def Models(url, page=1):
    siteurl, url = url.rsplit('/', 1)
    siteurl += '/'
    letter = '' if url == 'models' else url.lower()
    page = 1 if not page else page
    gender = 'she' if 'shemalez' in siteurl else 'str'
    gender = 'gay' if 'thegay' in siteurl else 'str'
    pagesize = 80
    aurl = '{0}api/json/models/86400/{1}/filt.{2}........./most-popular/{3}/{4}.json'.format(siteurl, gender, letter, pagesize, page)
    jdata = json.loads(utils.getHtml(aurl, siteurl))
    if url == 'models':
        site.add_dir('[COLOR violet]Alphabet[/COLOR]', siteurl, 'Letters', site.img_next, page=1)

    for item in jdata.get('models', []):
        catpage = 'model.{}'.format(item.get('dir'))
        name = item.get('title') if utils.PY3 else item.get('title').encode('utf-8')
        videos = " [COLOR deeppink](" + item.get('statistics').get('videos') + " videos)[/COLOR]"
        name = name + videos if utils.PY3 else (name.decode('utf-8') + videos).encode('utf-8')
        site.add_dir(name, siteurl + catpage, 'List', item.get('img'), page=1)

    if int(jdata.get('total_count', '0')) - (pagesize * page) > 0:
        page += 1
        last_page = -(-int(jdata.get('total_count')) // pagesize)
        site.add_dir('> Next Page ({}/{})'.format(str(page), str(last_page)), siteurl + url, 'Models', site.img_next, page=page)
    utils.eod()


@site.register()
def Letters(url):
    letters = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z']
    letter = utils.selector('Select letter', letters)
    if letter:
        Models(url + letter, page=1)


@site.register()
def Playvid(url, name, download=None):
    siteurl, url = url.rsplit('/', 1)
    siteurl += '/'

    from resources.lib.decrypters import txxx
    vp = utils.VideoPlayer(name, download)
    vp.progress.update(25, "[CR]Loading video page[CR]")
    vurl = '{0}api/videofile.php?video_id={1}&lifetime=8640000'.format(siteurl, url)
    vidhtml = utils.getHtml(vurl, siteurl)
    r = re.search('video_url":"([^"]+)', vidhtml)
    if r:
        videourl = txxx.Tdecode(r.group(1)) + '|Referer=' + siteurl
        if not videourl.startswith('http'):
            videourl = siteurl[:-1] + videourl
            videourl = utils.getVideoLink(videourl, referer=siteurl)
        vp.play_from_direct_link(videourl)
    else:
        vp.progress.close()
        return
