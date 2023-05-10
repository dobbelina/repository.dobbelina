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
import xbmc
import xbmcgui
import random
import base64
from resources.lib import utils
from resources.lib.adultsite import AdultSite
from six.moves import urllib_parse

addon = utils.addon
site = AdultSite("beeg", "[COLOR hotpink]Beeg[/COLOR]", "https://beeg.com/", "beeg.png", "beeg")


@site.register(default_mode=True)
def BGMain():
    site.add_dir('[COLOR hotpink]Categories[/COLOR]', 'https://store.externulls.com/tag/facts/tags?get_original=true&slug=index', 'BGCat', site.img_cat)
    BGList('https://store.externulls.com/facts/tag?id=27173&limit=48&offset=0', 1)
    utils.eod()


@site.register()
def BGList(url, page=1):
    listjson = utils.getHtml(url, site.url)
    jdata = json.loads(listjson)

    for video in jdata:
        tag = ''
        slug = ''
        fc_facts = video["fc_facts"]
        for t in video["tags"]:
            if t["is_owner"]:
                tag = t["tg_name"]
                slug = t["tg_slug"]
        tag = tag if utils.PY3 else tag.encode('utf8')
        name = video["file"]["stuff"]["sf_name"] if "sf_name" in video["file"]["stuff"] else tag
        name = name if utils.PY3 else name.encode('utf8')
        name = '{} - {}'.format(tag, name)
        story = video["file"]["stuff"]["sf_story"] if "sf_story" in video["file"]["stuff"] else ''
        story = story if utils.PY3 else story.encode('utf8')
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

        thumb = str(random.choice(fc_facts[0]["fc_thumbs"]))
        videodump = json.dumps(video)
        videopage = base64.b64encode(videodump.encode())
        # videopage = 'https://store.externulls.com/facts/file/' + str(video["fc_file_id"])
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

        if len(fc_facts) == 1 and "fc_start" in fc_facts[0] and "fc_end" in fc_facts[0]:
            if not fc_facts[0]["fc_start"] is None and not fc_facts[0]["fc_end"] is None:
                min_start, sec_start = divmod(fc_facts[0]["fc_start"], 60)
                min_end, sec_end = divmod(fc_facts[0]["fc_end"], 60)
                parts = '[COLOR blue] ({:d}:{:02d} - {:d}:{:02d})[/COLOR]'.format(min_start, sec_start, min_end, sec_end)

        name += parts

        cm_related = (utils.addon_sys + "?mode=" + str('beeg.ContextRelated') + "&slug=" + urllib_parse.quote_plus(slug))
        if tag:
            cm = [('[COLOR violet]Tag [COLOR orange][{}][/COLOR]'.format(tag), 'RunPlugin(' + cm_related + ')')]
        else:
            cm = ''

        site.add_download_link(name, videopage, 'BGPlayvid', img, plot, contextm=cm, duration=duration, quality=quality)
    if len(jdata) == 48:
        if not page:
            page = 1
        npage = url.split('offset=')[0] + 'offset=' + str(page * 48)
        cm_page = (utils.addon_sys + "?mode=beeg.GotoPage" + "&url=" + urllib_parse.quote_plus(npage) + "&np=" + str(page))
        cm = [('[COLOR violet]Goto Page #[/COLOR]', 'RunPlugin(' + cm_page + ')')]
        site.add_dir('Next Page ({})'.format(str(page + 1)), npage, 'BGList', site.img_next, page=page + 1, contextm=cm)
    utils.eod()


@site.register()
def GotoPage(url, np):
    dialog = xbmcgui.Dialog()
    pg = dialog.numeric(0, 'Enter Page number')
    if pg:
        url = url.replace('offset={}'.format(int(np) * 48), 'offset={}'.format(int(pg) * 48))
        contexturl = (utils.addon_sys + "?mode=" + "beeg.BGList&url=" + urllib_parse.quote_plus(url) + "&page=" + str(pg))
        xbmc.executebuiltin('Container.Update(' + contexturl + ')')


@site.register()
def ContextRelated(slug):
    url = 'https://store.externulls.com/facts/tag?slug={}&get_original=true&limit=48&offset=0'.format(slug)
    contexturl = (utils.addon_sys
                  + "?mode=" + str('beeg.BGList')
                  + "&url=" + urllib_parse.quote_plus(url))
    xbmc.executebuiltin('Container.Update(' + contexturl + ')')


@site.register()
def BGPlayvid(url, name, download=None):
    playall = True if utils.addon.getSetting("paradisehill") == "true" else False
    vp = utils.VideoPlayer(name, download)
    vp.progress.update(25, "[CR]Loading video page[CR]")
    # listjson = utils.getHtml(url, site.url)
    # jdata = json.loads(listjson)
    listjson = base64.b64decode(url)
    jdata = json.loads(listjson.decode())

    fc_facts = jdata["fc_facts"]
    if len(fc_facts) == 1:
        if "hls_resources" in jdata["file"]:
            videos = jdata["file"]["hls_resources"]
        else:
            videos = jdata["fc_facts"][0]["hls_resources"]
        playall = False
    else:
        links = {}
        for i, fc_fact in enumerate(sorted(fc_facts, key=lambda x: x["fc_start"])):
            start = fc_fact["fc_start"]
            end = fc_fact["fc_end"]
            m, s = divmod(start, 60)
            stxt = '{:d}:{:02d}'.format(m, s)
            m, s = divmod(end, 60)
            etxt = '{:d}:{:02d}'.format(m, s)
            part = ' part {} ({} - {})'.format(str(i + 1), stxt, etxt)
            links[part] = fc_fact["hls_resources"]
        if len(links) < 2:
            playall = False
        if not playall:
            videos = utils.selector('Select part:', links)
    if not playall:
        if videos:
            videos = {key.replace('fl_cdn_', ''): videos[key] for key in videos.keys()}
            if 'multi' in videos.keys():
                maxres = videos['multi'].split('x')[-1].split(':')[0]
                if maxres in videos.keys():
                    del videos['multi']
                elif maxres.isdigit():
                    videos[maxres] = videos.pop('multi')
            key = utils.prefquality(videos, sort_by=lambda x: int(x), reverse=True)
            if key:
                vp.progress.update(75, "[CR]Loading video page[CR]")
                videourl = 'https://video.beeg.com/' + key + '|Referer={}'.format(site.url)
                vp.play_from_direct_link(videourl)

    if playall:
        if links:
            iconimage = xbmc.getInfoImage("ListItem.Thumb")
            pl = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
            pl.clear()
            for video in links:
                vp.progress.update(75, "[CR]Adding part to playlist[CR]")
                videos = links[video]
                videos = {key.replace('fl_cdn_', ''): videos[key] for key in videos.keys()}
                if 'multi' in videos.keys():
                    maxres = videos['multi'].split('x')[-1].split(':')[0]
                    if maxres in videos.keys():
                        del videos['multi']
                    elif maxres.isdigit():
                        videos[maxres] = videos.pop('multi')
                key = utils.prefquality(videos, sort_by=lambda x: int(x), reverse=True)
                newname = name + video
                listitem = xbmcgui.ListItem(newname)
                listitem.setArt({'thumb': iconimage, 'icon': "DefaultVideo.png", 'poster': iconimage})
                if utils.KODIVER > 19.8:
                    vtag = listitem.getVideoInfoTag()
                    vtag.setTitle(newname)
                    vtag.setGenres(['Porn'])
                else:
                    listitem.setInfo('video', {'Title': newname, 'Genre': 'Porn'})
                listitem.setProperty("IsPlayable", "true")
                videourl = 'https://video.beeg.com/' + key + '|Referer={}'.format(site.url)
                pl.add(videourl, listitem)
                listitem = ''
            xbmc.Player().play(pl)


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
