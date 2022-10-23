'''
    Cumination
    Copyright (C) 2022 Team Cumination

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

import json
# import random
import re

import xbmc
import xbmcgui
from resources.lib import utils
from resources.lib.adultsite import AdultSite
from six.moves import urllib_parse

site = AdultSite('avple', '[COLOR hotpink]Avple[/COLOR]', 'https://avple.tv/', 'https://assert.avple.tv/file/avple-images/logo.png', 'avple')
CDN = [
    "q2cyl7.cdnedge.live", "d862cp.cdnedge.live", "47b61.cdnedge.live", "e2fa6.cdnedge.live", "je40u.cdnedge.live",
    "10j99.cdnedge.live", "u89ey.cdnedge.live", "1xp60.cdnedge.live", "w9n76.cdnedge.live", "zo392.cdnedge.live"
]


@site.register(default_mode=True)
def Main():
    site.add_dir('[COLOR hotpink]Tags[/COLOR]', site.url, 'Cat', site.img_cat)
    site.add_dir('[COLOR hotpink]Uncensored[/COLOR]', site.url + 'tags/93/1/date', 'List', site.img_cat)
    site.add_dir('[COLOR hotpink]Search[/COLOR]', site.url + 'search?page=1&sort=date&key=', 'Search', site.img_search)
    List(site.url)
    utils.eod()


@site.register()
def List(url):
    html = utils.getHtml(url, '')
    if '>404<' in html:
        utils.notify(msg='Nothing found')
        utils.eod()
        return

    jdata = re.compile(r'application/json">([^<]+)', re.DOTALL | re.IGNORECASE).findall(html)[0]
    jdata = json.loads(jdata).get("props").get("pageProps")
    page = jdata.get("page")
    pages = jdata.get("totalPage")

    if "indexListObj" in jdata.keys():
        indexListObj = jdata.get("indexListObj")
    else:
        indexListObj = {'obj': jdata["data"]}

    for obj in indexListObj.keys():
        videos = indexListObj[obj]
        for video in videos:
            name = video["title"] if utils.PY3 else video["title"].encode('utf-8')
            name = utils.cleantext(name)
            img = video.get("img_preview", "")
            duration = "" if video.get("timeLengh") is None else video.get("timeLengh")
            videopage = '{0}video/{1}'.format(site.url, video.get("_id"))
            site.add_download_link(name, str(videopage), 'Playvid', img, name, duration=duration)
    if page < pages:
        if 'page=' in url:
            npurl = url.replace('page={}'.format(page), 'page={}'.format(page + 1))
        elif '/{}/date'.format(page) in url:
            npurl = url.replace('/{}/date'.format(page), '/{}/date'.format(page + 1))
        else:
            npurl = url
        cm_page = (utils.addon_sys + "?mode=avple.GotoPage&list_mode=avple.List&url=" + urllib_parse.quote_plus(npurl) + "&np=" + str(page + 1) + "&lp=" + str(pages))
        cm = [('[COLOR violet]Goto Page #[/COLOR]', 'RunPlugin(' + cm_page + ')')]
        site.add_dir('[COLOR hotpink]Next Page...[/COLOR] ({0}/{1})'.format(page + 1, pages), npurl, 'List', site.img_next, contextm=cm)
    utils.eod()


@site.register()
def Cat(url):
    # tags = {}
    # for i in range(0, 134):
    #     caturl = 'tags/{}/1/date'.format(i)
    #     cathtml = utils.getHtml(site.url + caturl)
    #     name = cathtml.split('MuiTypography-gutterBottom">')[-1].split('<')[0]
    #     tags[name] = caturl
    # utils.kodilog(tags)
    tags = {
        'Rainy day': 'tags/109/1/date', 'Anchor Tanhua': 'tags/132/1/date', 'WC': 'tags/75/1/date', 'Loli': 'tags/67/1/date',
        'Poor milk': 'tags/63/1/date', 'More than 4 hours': 'tags/60/1/date', 'Black wire': 'tags/15/1/date', 'Slap directly': 'tags/43/1/date',
        'Search officer': 'tags/73/1/date', 'Gym': 'tags/107/1/date', 'Slut': 'tags/26/1/date', 'Garter socks': 'tags/76/1/date',
        'Creampie': 'tags/2/1/date', 'prison': 'tags/44/1/date', 'Debut/retirement': 'tags/52/1/date', 'Stolen camera': 'tags/58/1/date',
        'Training': 'tags/17/1/date', 'Swimming pool': 'tags/100/1/date', '3P group sex': 'tags/10/1/date', 'Housekeeper': 'tags/110/1/date',
        'Hypnosis': 'tags/66/1/date', 'kiss': 'tags/29/1/date', 'school': 'tags/42/1/date', 'OL': 'tags/55/1/date', 'Exposed': 'tags/79/1/date',
        'tram': 'tags/96/1/date', 'White tiger': 'tags/102/1/date', 'short hair': 'tags/24/1/date', 'within Temptation': 'tags/25/1/date',
        'Tied up': 'tags/53/1/date', 'Urinate': 'tags/78/1/date', 'virginity': 'tags/37/1/date', 'Giant man': 'tags/84/1/date',
        'Cheating': 'tags/4/1/date', 'Cosplay': 'tags/88/1/date', 'Uncoded liberation': 'tags/93/1/date', 'Idiot': 'tags/111/1/date',
        '3P': 'tags/46/1/date', 'library': 'tags/65/1/date', 'Jingdong Pictures': 'tags/125/1/date', 'Couples': 'tags/101/1/date',
        'Peach Media': 'tags/129/1/date', 'Black person': 'tags/105/1/date', 'Shredded pork': 'tags/120/1/date', 'Convenience Store': 'tags/116/1/date',
        'Sneak shots': 'tags/59/1/date', 'Abuse': 'tags/19/1/date', 'nurse': 'tags/74/1/date', 'Undead': 'tags/99/1/date',
        'Thanks offering': 'tags/86/1/date', 'Chinese subtitle': 'tags/27/1/date', 'Knee socks': 'tags/70/1/date', 'revenge': 'tags/92/1/date',
        'Beautiful legs': 'tags/20/1/date', 'Variety Show': 'tags/115/1/date', 'Mature': 'tags/5/1/date', 'Gang rape': 'tags/22/1/date',
        'teacher': 'tags/23/1/date', 'Uniforms': 'tags/49/1/date', 'Maiden': 'tags/12/1/date', 'Role plot': 'tags/0/1/date',
        'Fishing net': 'tags/47/1/date', 'massage': 'tags/40/1/date', 'software': 'tags/56/1/date', 'Cramps': 'tags/62/1/date',
        'Breast milk': 'tags/114/1/date', 'Fugitive': 'tags/94/1/date', 'Royal Chinese': 'tags/124/1/date', 'Long body': 'tags/54/1/date',
        'Footjob': 'tags/89/1/date', 'Abuse and rape': 'tags/8/1/date', 'Bukkake': 'tags/32/1/date', 'Crow media': 'tags/130/1/date',
        'oral sex': 'tags/39/1/date', 'Big breasts': 'tags/1/1/date', 'SWAG': 'tags/122/1/date', 'Husband is currently committing': 'tags/30/1/date',
        'Tit fuck': 'tags/14/1/date', 'Torture': 'tags/45/1/date', 'Lebo Media': 'tags/128/1/date', 'Bunny girl': 'tags/87/1/date',
        'Pao Ji': 'tags/83/1/date', 'Anchor': 'tags/98/1/date', 'virgin': 'tags/104/1/date', 'Ugly man': 'tags/91/1/date', 'Doctors': 'tags/95/1/date',
        'Time stops': 'tags/118/1/date', 'Deepthroat': 'tags/41/1/date', 'idol': 'tags/85/1/date', 'HongKongDoll': 'tags/133/1/date',
        'cheongsam': 'tags/113/1/date', 'Boyfriend perspective': 'tags/36/1/date', 'Wedding dress': 'tags/119/1/date', 'Bathing area': 'tags/81/1/date',
        'Nondescript': 'tags/6/1/date', 'flight attendant': 'tags/112/1/date', 'Lesbian pleasure': 'tags/71/1/date', 'Squirting': 'tags/18/1/date',
        'Anal sex': 'tags/48/1/date', 'car': 'tags/90/1/date', 'Glasses girl': 'tags/34/1/date', 'NTR': 'tags/28/1/date', 'Video': 'tags/72/1/date',
        'Age difference': 'tags/31/1/date', 'Custom girl': 'tags/82/1/date', 'Jelly Media': 'tags/123/1/date', 'private teacher': 'tags/106/1/date',
        'Stockings beautiful legs': 'tags/11/1/date', 'Master slave training': 'tags/7/1/date', 'Maid': 'tags/97/1/date', 'spa': 'tags/38/1/date',
        'Instantly insert': 'tags/64/1/date', 'rape': 'tags/21/1/date', 'Ten times a day': 'tags/69/1/date', 'kimono': 'tags/80/1/date',
        'Mijiri': 'tags/51/1/date', 'Multiple P': 'tags/33/1/date', 'Homemade selfie': 'tags/131/1/date', 'Madou Media': 'tags/121/1/date',
        'Animal ears': 'tags/108/1/date', 'Tattoos': 'tags/117/1/date', 'crapulence': 'tags/77/1/date', 'Water': 'tags/50/1/date',
        'Love potion': 'tags/57/1/date', 'Star Infinite Media': 'tags/127/1/date', 'Stockings': 'tags/13/1/date', 'Magic Mirror': 'tags/61/1/date',
        'Mouth burst': 'tags/16/1/date', 'wife': 'tags/3/1/date', 'Male M': 'tags/103/1/date', 'Team manager': 'tags/68/1/date',
        'Uniform temptation': 'tags/9/1/date', 'Tianmei Media': 'tags/126/1/date', 'Sportswear': 'tags/35/1/date', 'Molena': 'tags/136/1/date',
        'FC2PPV': 'tags/135/1/date'
    }
    for name in sorted(tags.keys(), key=lambda x: x[0].lower()):
        site.add_dir(name, site.url + tags[name], 'List', '')
    utils.eod()


@site.register()
def GotoPage(url, np, lp):
    dialog = xbmcgui.Dialog()
    pg = dialog.numeric(0, 'Enter Page number')
    if pg:
        if 'page=' in url:
            url = url.replace('page={}'.format(np), 'page={}'.format(pg))
        elif '/{}/date'.format(np) in url:
            url = url.replace('/{}/date'.format(np), '/{}/date'.format(pg))
        if int(lp) > 0 and int(pg) > int(lp):
            utils.notify(msg='Out of range!')
            return
        contexturl = (utils.addon_sys + "?mode=avple.List&url=" + urllib_parse.quote_plus(url))
        xbmc.executebuiltin('Container.Update(' + contexturl + ')')


@site.register()
def Search(url, keyword=None):
    if not keyword:
        site.search_dir(url, 'Search')
    else:
        url = "{0}{1}".format(url, keyword.replace(' ', '%20'))
        List(url)


@site.register()
def Playvid(url, name, download=None):
    vp = utils.VideoPlayer(name, download)
    vp.progress.update(25, "[CR]Loading video page[CR]")
    html = utils.getHtml(url, site.url)
    # jdata = re.compile(r'application/json">([^<]+)', re.DOTALL | re.IGNORECASE).findall(html)[0]
    # jdata = json.loads(jdata).get("props").get("pageProps")
    # vidurl = 'https://{0}/file/avple-images/{1}'.format(random.choice(CDN), jdata.get('instance').get('play'))
    vidurl = re.compile(r"source\s*=\s*'([^']+)", re.DOTALL | re.IGNORECASE).findall(html)[0]
    vidurl += '|Referer={0}&Origin={1}&verifypeer=false'.format(site.url, site.url[:-1])
    vp.play_from_direct_link(vidurl)
