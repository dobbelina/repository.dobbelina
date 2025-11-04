'''
    Cumination
    Copyright (C) 2017 Whitecream, hdgdl, Team Cumination
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

import os
import sqlite3
import json
import re

from resources.lib import utils
from six.moves import urllib_parse
from resources.lib.adultsite import AdultSite

site = AdultSite('stripchat', '[COLOR hotpink]stripchat.com[/COLOR]', 'https://stripchat.com/', 'stripchat.jpg', 'stripchat', True)


@site.register(default_mode=True)
def Main():
    female = utils.addon.getSetting("chatfemale") == "true"
    male = utils.addon.getSetting("chatmale") == "true"
    couple = utils.addon.getSetting("chatcouple") == "true"
    trans = utils.addon.getSetting("chattrans") == "true"
    site.add_dir('[COLOR red]Refresh Stripchat images[/COLOR]', '', 'clean_database', '', Folder=False)

    bu = "https://stripchat.com/api/front/models?limit=80&parentTag=autoTagNew&sortBy=trending&offset=0&primaryTag="
    # site.add_dir('[COLOR hotpink]HD[/COLOR]', '{0}hd&broadcastHD=true'.format(bu), 'List', '', '')
    if female:
        site.add_dir('[COLOR hotpink]Female HD[/COLOR]', '{0}girls&broadcastHD=true'.format(bu), 'List', '', '')
        site.add_dir('[COLOR hotpink]Female[/COLOR]', '{0}girls'.format(bu), 'List', '', '')
    if couple:
        site.add_dir('[COLOR hotpink]Couples HD[/COLOR]', '{0}couples&broadcastHD=true'.format(bu), 'List', '', '')
        site.add_dir('[COLOR hotpink]Couples[/COLOR]', '{0}couples'.format(bu), 'List', '', '')
    if male:
        site.add_dir('[COLOR hotpink]Male HD[/COLOR]', '{0}men&broadcastHD=true'.format(bu), 'List', '', '')
        site.add_dir('[COLOR hotpink]Male[/COLOR]', '{0}men'.format(bu), 'List', '', '')
    if trans:
        site.add_dir('[COLOR hotpink]Transsexual HD[/COLOR]', '{0}trans&broadcastHD=true'.format(bu), 'List', '', '')
        site.add_dir('[COLOR hotpink]Transsexual[/COLOR]', '{0}trans'.format(bu), 'List', '', '')
    utils.eod()


@site.register()
def List(url, page=1):
    if utils.addon.getSetting("chaturbate") == "true":
        clean_database(False)

    # utils._getHtml will automatically use FlareSolverr if Cloudflare is detected
    try:
        utils.kodilog("Stripchat: Fetching model list from API")
        response = utils._getHtml(url)
        if not response:
            utils.kodilog("Stripchat: Empty response from API")
            utils.notify('Error', 'Could not load Stripchat models')
            return None
        data = json.loads(response)
        model_list = data["models"]
        utils.kodilog("Stripchat: Successfully loaded {} models".format(len(model_list)))
    except Exception as e:
        utils.kodilog("Stripchat: Error loading model list: {}".format(str(e)))
        utils.notify('Error', 'Could not load Stripchat models')
        return None

    for model in model_list:
        name = utils.cleanhtml(model['username'])
        videourl = model['hlsPlaylist']
        # fanart = model.get('') if utils.addon.getSetting('posterfanart') == 'true' else None
        fanart = model.get('previewUrlThumbSmall')
        img = 'https://img.strpst.com/thumbs/{0}/{1}_webp'.format(model.get('snapshotTimestamp'), model.get('id'))
        # img = img.replace('{0}/previews'.format(model.get('snapshotServer')), 'thumbs') + '_webp'
        subject = model.get('groupShowTopic')
        if subject:
            subject += '[CR]'
        if model.get('country'):
            subject += '[COLOR deeppink]Location: [/COLOR]{0}[CR]'.format(utils.get_country(model.get('country')))
        if model.get('languages'):
            langs = [utils.get_language(x) for x in model.get('languages')]
            subject += '[COLOR deeppink]Languages: [/COLOR]{0}[CR]'.format(', '.join(langs))
        if model.get('broadcastGender'):
            subject += '[COLOR deeppink]Gender: [/COLOR]{0}[CR]'.format(model.get('broadcastGender'))
        if model.get('viewersCount'):
            subject += '[COLOR deeppink]Watching: [/COLOR]{0}[CR][CR]'.format(model.get('viewersCount'))
        if model.get('tags'):
            subject += '[COLOR deeppink]#[/COLOR]'
            tags = [t for t in model.get('tags') if 'tag' not in t.lower()]
            subject += '[COLOR deeppink] #[/COLOR]'.join(tags)
        site.add_download_link(name, videourl, 'Playvid', img, subject, noDownload=True, fanart=fanart)

    total_items = data.get('filteredCount', 0)
    nextp = (page * 80) < total_items
    if nextp:
        next = (page * 80) + 1
        lastpg = -1 * (-total_items // 80)
        page += 1
        nurl = re.sub(r'offset=\d+', 'offset={0}'.format(next), url)
        site.add_dir('Next Page.. (Currently in Page {0} of {1})'.format(page - 1, lastpg), nurl, 'List', site.img_next, page)

    utils.eod()


@site.register(clean_mode=True)
def clean_database(showdialog=True):
    conn = sqlite3.connect(utils.TRANSLATEPATH("special://database/Textures13.db"))
    try:
        with conn:
            list = conn.execute("SELECT id, cachedurl FROM texture WHERE url LIKE ?;", ('%' + ".strpst.com" + '%',))
            for row in list:
                conn.execute("DELETE FROM sizes WHERE idtexture = ?;", (row[0],))
                try:
                    os.remove(utils.TRANSLATEPATH("special://thumbnails/" + row[1]))
                except:
                    pass
            conn.execute("DELETE FROM texture WHERE url LIKE ?;", ('%' + ".strpst.com" + '%',))
            if showdialog:
                utils.notify('Finished', 'Stripchat images cleared')
    except:
        pass


@site.register()
def Playvid(url, name):
    vp = utils.VideoPlayer(name, IA_check='IA')
    vp.progress.update(25, "[CR]Loading video page[CR]")

    def _load_model_details(model_name):
        headers = {
            'User-Agent': utils.USER_AGENT,
            'Accept': 'application/json, text/plain, */*',
            'Origin': 'https://stripchat.com',
            'Referer': 'https://stripchat.com/{0}'.format(model_name)
        }
        endpoints = [
            'https://stripchat.com/api/external/v4/widget/?limit=1&modelsList={0}',
            'https://stripchat.com/api/front/models?limit=1&modelsList={0}&offset=0'
        ]
        for endpoint in endpoints:
            try:
                response = utils._getHtml(endpoint.format(model_name), site.url, headers=headers)
                payload = json.loads(response)
                models = payload.get('models') if isinstance(payload, dict) else None
                if models:
                    return models[0]
            except Exception:
                continue
        return None

    def _pick_stream(model_data, fallback_url):
        candidates = []
        stream_info = model_data.get('stream') if model_data else None
        if isinstance(stream_info, dict):
            # Explicit urls map (new API structure)
            urls_map = stream_info.get('urls') or stream_info.get('files') or {}
            hls_map = urls_map.get('hls') if isinstance(urls_map, dict) else {}
            if isinstance(hls_map, dict):
                for quality, data in hls_map.items():
                    quality_label = str(quality).lower()
                    if isinstance(data, dict):
                        for key in ('absolute', 'https', 'url', 'src'):
                            stream_url = data.get(key)
                            if isinstance(stream_url, str) and stream_url.startswith('http'):
                                candidates.append((quality_label, stream_url))
                                break
                    elif isinstance(data, str) and data.startswith('http'):
                        candidates.append((quality_label, data))
            # Some responses keep direct URL on stream['url']
            stream_url = stream_info.get('url')
            if isinstance(stream_url, str) and stream_url.startswith('http'):
                candidates.append(('direct', stream_url))
        # Legacy field on model root
        if model_data and isinstance(model_data.get('hlsPlaylist'), str):
            candidates.append(('playlist', model_data['hlsPlaylist']))
        if isinstance(fallback_url, str) and fallback_url.startswith('http'):
            candidates.append(('fallback', fallback_url))
        if not candidates:
            return None

        def quality_score(label):
            if not label:
                return -1
            label = label.lower()
            if 'source' in label:
                return 10000
            match = re.search(r'(\d{3,4})p', label)
            if match:
                try:
                    return int(match.group(1))
                except ValueError:
                    return -1
            return 0

        force_best = utils.addon.getSetting('stripchat_best') == 'true'
        # sort candidates: highest score first, keep stable order otherwise
        candidates_sorted = sorted(candidates, key=lambda item: quality_score(item[0]), reverse=True)
        selected_url = candidates_sorted[0][1]

        if force_best:
            top_label = candidates_sorted[0][0]
            # If highest ranked is not "source", probe master playlist for any better variant
            if 'source' not in top_label:
                try:
                    master_headers = {
                        'User-Agent': utils.USER_AGENT,
                        'Origin': 'https://stripchat.com',
                        'Referer': 'https://stripchat.com/{0}'.format(name)
                    }
                    master_txt = utils._getHtml(selected_url, site.url, headers=master_headers)
                    best_pixels = -1
                    best_url = None
                    lines = master_txt.splitlines()
                    for i, line in enumerate(lines):
                        if line.startswith('#EXT-X-STREAM-INF:') and i + 1 < len(lines):
                            info = line
                            next_url = lines[i + 1].strip()
                            if not next_url:
                                continue
                            stream_variant = urllib_parse.urljoin(selected_url, next_url)
                            if 'NAME="source"' in info or 'NAME=source' in info:
                                best_url = stream_variant
                                best_pixels = 10**9
                                break
                            match = re.search(r'RESOLUTION=(\d+)x(\d+)', info)
                            if match:
                                pixels = int(match.group(1)) * int(match.group(2))
                                if pixels > best_pixels:
                                    best_pixels = pixels
                                    best_url = stream_variant
                    if best_url:
                        selected_url = best_url
                except Exception:
                    pass

        return selected_url

    model_data = _load_model_details(name)
    stream_url = _pick_stream(model_data, url)
    if not stream_url:
        vp.progress.close()
        utils.notify('Stripchat', 'Unable to locate stream URL')
        return

    stream_url = re.sub(r'_\d+p\.', '.', stream_url)
    vp.progress.update(85, "[CR]Found Stream[CR]")

    ua = urllib_parse.quote(utils.USER_AGENT, safe='')
    origin_enc = urllib_parse.quote('https://stripchat.com', safe='')
    referer_enc = urllib_parse.quote('https://stripchat.com/{0}'.format(name), safe='')
    accept_enc = urllib_parse.quote('application/x-mpegURL', safe='')
    accept_lang = urllib_parse.quote('en-US,en;q=0.9', safe='')
    ia_headers = 'User-Agent={0}&Origin={1}&Referer={2}&Accept={3}&Accept-Language={4}'.format(
        ua, origin_enc, referer_enc, accept_enc, accept_lang)

    vp.play_from_direct_link(stream_url + '|' + ia_headers)


@site.register()
def List2(url):
    site.add_download_link('[COLOR red][B]Refresh[/B][/COLOR]', url, 'utils.refresh', '', '', noDownload=True)
    if utils.addon.getSetting("online_only") == "true":
        url = url + '/?online_only=1'
        site.add_download_link('[COLOR red][B]Show all models[/B][/COLOR]', url, 'online', '', '', noDownload=True)
    else:
        site.add_download_link('[COLOR red][B]Show only models online[/B][/COLOR]', url, 'online', '', '', noDownload=True)

    if utils.addon.getSetting("chaturbate") == "true":
        clean_database(False)

    headers = {'X-Requested-With': 'XMLHttpRequest'}
    data = utils._getHtml(url, site.url, headers=headers)
    match = re.compile('class="top_ranks(.+?)class="title_h3', re.I | re.M | re.S).findall(data)
    if not match:
        match = re.compile('class="top_others(.+?)class="title_h3', re.I | re.M | re.S).findall(data)
    match = re.compile('class="top_thumb".+?href="([^"]+)".+?src="([^"]+)".+?class="mn_lc">(.+?)</span>', re.I | re.M | re.S).findall(match[0])
    for url, img, name in match:
        if 'profile' in url:
            name = '[COLOR hotpink][Offline][/COLOR] ' + name
            url = "  "
        site.add_download_link(name, url[1:], 'Playvid', 'https:' + img, '')
    utils.eod()


@site.register()
def List3(url):
    site.add_download_link('[COLOR red][B]Refresh[/B][/COLOR]', url, 'utils.refresh', '', '', noDownload=True)
    if utils.addon.getSetting("online_only") == "true":
        url = url + '/?online_only=1'
        site.add_download_link('[COLOR red][B]Show all models[/B][/COLOR]', url, 'online', '', '', noDownload=True)
    else:
        site.add_download_link('[COLOR red][B]Show only models online[/B][/COLOR]', url, 'online', '', '', noDownload=True)

    if utils.addon.getSetting("chaturbate") == "true":
        clean_database(False)

    headers = {'X-Requested-With': 'XMLHttpRequest'}
    data = utils._getHtml(url, site.url, headers=headers)
    match = re.compile('class="top_ranks(.+?)trs_actions', re.I | re.M | re.S).findall(data)
    match = re.compile('class="top_thumb".+?href="([^"]+)".+?src="([^"]+)".+?class="mn_lc">(.+?)</span>', re.I | re.M | re.S).findall(match[0])
    for url, img, name in match:
        if 'profile' in url:
            name = '[COLOR hotpink][Offline][/COLOR] ' + name
            url = "  "
        site.add_download_link(name, url[1:], 'Playvid', 'https:' + img, '')
    utils.eod()


@site.register()
def online(url):
    if utils.addon.getSetting("online_only") == "true":
        utils.addon.setSetting("online_only", "false")
    else:
        utils.addon.setSetting("online_only", "true")
    utils.refresh()
