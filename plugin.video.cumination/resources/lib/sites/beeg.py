'''
    Cumination
    Copyright (C) 2015 Whitecream
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

import json
from resources.lib import utils
from resources.lib.adultsite import AdultSite
import random

addon = utils.addon
site = AdultSite("beeg", "[COLOR hotpink]Beeg[/COLOR]", "https://beeg.com/", "beeg.png", "beeg")


@site.register(default_mode=True)
def BGMain():
    site.add_dir('[COLOR hotpink]Categories[/COLOR]', 'https://store.externulls.com/tags/top', 'BGCat', site.img_cat)
    BGList('https://store.externulls.com/facts/index?limit=48&offset=0', 1)
    utils.eod()


@site.register()
def BGList(url, page=1):
    listjson = utils.getHtml(url, site.url)
    jdata = json.loads(listjson)

    for video in jdata:
        tag = video["tags"][0]["tg_name"] if video["tags"] else ''
        name = video["file"]["stuff"]["sf_name"] if "sf_name" in video["file"]["stuff"] else tag
        name = name if utils.PY3 else name.encode('utf8')
        story = video["file"]["stuff"]["sf_story"] if "sf_story" in video["file"]["stuff"] else ''
        if "fl_duration" in video["file"]:
            m, s = divmod(video["file"]["fl_duration"], 60)
            duration = '{:d}:{:02d}'.format(m, s)
        else:
            duration = ''

        h = video["file"]["fl_height"]
        w = video["file"]["fl_width"]
        quality = str(h) + 'p' if "fl_height" in video["file"] else ''
        th_size = '480x' + str((480 * h) // w)
        plot = tag + ' - ' + name + '[CR]' + story

        fc_facts = video["fc_facts"]
        thumb = str(random.choice(fc_facts[0]["fc_thumbs"]))
        videopage = 'https://store.externulls.com/facts/file/' + str(video["fc_file_id"])
        if "set_id" in video["file"]:
            img = 'https://thumbs-015.externulls.com/sets/{0}/thumbs/{0}-{1}.jpg?size={2}'.format(str(video["file"]["set_id"]).zfill(5), thumb.zfill(4), th_size)
        else:
            img = 'https://thumbs-015.externulls.com/videos/{0}/{1}.jpg?size={2}'.format(str(video["fc_file_id"]), thumb, th_size)
        parts = ''
        if len(fc_facts) > 1:
            parts = '[COLOR blue] ({} parts)[/COLOR]'.format(len(fc_facts))
            for fc_fact in fc_facts:
                if "fc_start" not in fc_fact:
                    parts = ''
        name += parts
        site.add_download_link(name, videopage, 'BGPlayvid', img, plot, duration=duration, quality=quality)
    if len(jdata) == 48:
        if not page:
            page = 1
        npage = url.split('offset=')[0] + 'offset=' + str(page * 48)
        site.add_dir('Next Page ({})'.format(str(page + 1)), npage, 'BGList', site.img_next, page=page + 1)
    utils.eod()


@site.register()
def BGPlayvid(url, name, download=None):
    vp = utils.VideoPlayer(name, download)
    vp.progress.update(25, "[CR]Loading video page[CR]")
    listjson = utils.getHtml(url, site.url)
    jdata = json.loads(listjson)

    if "resources" in jdata["file"]:
        videos = jdata["file"]["resources"]
    else:
        links = {}
        for i, fc_fact in enumerate(jdata["fc_facts"]):
            start = fc_fact["fc_start"]
            end = fc_fact["fc_end"]
            m, s = divmod(start, 60)
            stxt = '{:d}:{:02d}'.format(m, s)
            m, s = divmod(end, 60)
            etxt = '{:d}:{:02d}'.format(m, s)
            part = ' part {} ({} - {})'.format(str(i + 1), stxt, etxt)
            links[part] = fc_fact["resources"]
        videos = utils.selector('Select part:', links)
    videos = {key.replace('fl_cdn_', ''): videos[key] for key in videos.keys()}
    key = utils.prefquality(videos, sort_by=lambda x: int(x), reverse=True)
    if key:
        vp.progress.update(75, "[CR]Loading video page[CR]")
        videourl = 'https://video.beeg.com/' + key + '|Referer={}'.format(site.url)
        vp.play_from_direct_link(videourl)


@site.register()
def BGCat(url):
    listjson = utils.getHtml(url, site.url)
    jdata = json.loads(listjson)
    # for cat in jdata:
    for cat in sorted(jdata, key=lambda x: x["tg_name"]):
        name = cat["tg_name"]
        slug = cat["tg_slug"]
        thumbs = random.choice(cat["thumbs"]) if "thumbs" in cat else ''
        img = 'https://thumbs-015.externulls.com/tags/{}/to.jpg?size=480x480'.format(thumbs) if thumbs else ''
        caturl = 'https://store.externulls.com/facts/tag?slug={}&limit=48&offset=0'.format(slug)
        site.add_dir(name, caturl, 'BGList', img)
    utils.eod()
