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
import socket

from resources.lib import utils
from six.moves import urllib_error, urllib_parse
from resources.lib.adultsite import AdultSite

site = AdultSite('stripchat', '[COLOR hotpink]stripchat.com[/COLOR]', 'http://stripchat.com/', 'stripchat.jpg', 'stripchat', True)


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
    altUrl = 'https://stripchat.com/api/external/v4/widget/?limit=1&modelsList='
    original_url = url  # Backup from listing
    model_ref = 'https://stripchat.com/{0}'.format(name)
    probe_headers = {'User-Agent': utils.USER_AGENT,
                     'Origin': 'https://stripchat.com',
                     'Referer': model_ref}

    def _decode_stripchat_url(raw_value):
        if not raw_value:
            return None
        if isinstance(raw_value, bytes):
            value = raw_value.decode('utf-8', errors='ignore')
        else:
            value = str(raw_value)
        try:
            value = value.encode('utf-8').decode('unicode_escape')
        except Exception:
            pass
        value = value.replace('\\/', '/')
        value = value.replace('&amp;', '&')
        value = value.replace('\\u0026', '&')
        value = value.replace('\\u003F', '?')
        value = value.replace('\\u003D', '=')
        return value.strip()

    candidate_urls = []

    def _add_candidate(kind, raw_value):
        normalized = _decode_stripchat_url(raw_value)
        if not normalized or not normalized.startswith('http'):
            return None
        if any(normalized == existing for _, existing in candidate_urls):
            return normalized
        candidate_urls.append((kind, normalized))
        return normalized

    def _probe_candidate(test_url):
        try:
            utils._getHtml(test_url, site.url, headers=probe_headers, error='raise')
            return True, None, None
        except urllib_error.HTTPError as http_err:
            return False, 'http_error', 'HTTP {}'.format(http_err.code)
        except urllib_error.URLError as url_err:
            reason = getattr(url_err, 'reason', None)
            if isinstance(reason, socket.gaierror):
                return False, 'dns_failure', str(reason)
            return False, 'url_error', str(url_err)
        except Exception as gen_err:
            return False, 'general_error', str(gen_err)

    def _select_candidate():
        last_result = None
        for kind, candidate_url in candidate_urls:
            success, err_type, err_msg = _probe_candidate(candidate_url)
            if success:
                return {'kind': kind, 'url': candidate_url, 'status': 'ok'}
            if err_type == 'dns_failure':
                utils.kodilog(
                    "Stripchat: DNS lookup failed for {} candidate ({}). Will still attempt playback.".format(
                        kind, err_msg))
                return {'kind': kind, 'url': candidate_url, 'status': 'dns_warning'}
            utils.kodilog("Stripchat: {} candidate rejected during probe ({})".format(kind.capitalize(), err_msg))
            last_result = {'kind': kind, 'url': candidate_url, 'status': err_type or 'failed', 'error': err_msg}
        return last_result or {'kind': 'listing', 'url': original_url, 'status': 'fallback'}

    def _extract_stream_url_from_page():
        try:
            page_html = utils._getHtml(model_ref, site.url, headers={'User-Agent': utils.USER_AGENT}, error='return')
        except Exception as page_err:
            utils.kodilog("Stripchat: Error loading model page for fallback: {}".format(str(page_err)))
            return None
        if not page_html:
            return None
        patterns = [
            r'"hlsUrl"\s*:\s*"([^"]+?\.m3u8[^"]*)"',
            r'"streamUrl"\s*:\s*"([^"]+?\.m3u8[^"]*)"',
            r'https:\\/\\/edge-[^"\\]+?\.m3u8[^"\\]*',
            r'https://edge-[^"\\]+?\.m3u8[^"\\]*',
        ]
        matches = []
        seen = set()
        for pattern in patterns:
            for match in re.findall(pattern, page_html, re.IGNORECASE):
                candidate = _decode_stripchat_url(match)
                if not candidate or not candidate.startswith('http'):
                    continue
                if candidate in seen:
                    continue
                seen.add(candidate)
                matches.append(candidate)
        if not matches:
            return None
        matches.sort(key=lambda u: (0 if 'master' in u or '_source' in u else 1, -len(u)))
        selected = matches[0]
        utils.kodilog("Stripchat: Extracted stream URL from page fallback: {}".format(selected[:80]))
        return selected

    api_primary = None
    try:
        utils.kodilog("Stripchat: Fetching stream URL from external widget API")
        response = utils._getHtml(altUrl + name, error='raise')
        data = json.loads(response)["models"][0]
        stream_data = data.get('stream') or {}
        api_primary = _add_candidate('api', stream_data.get('url') or stream_data.get('hlsUrl') or stream_data.get('hls_url'))
        if api_primary:
            utils.kodilog("Stripchat: Got stream URL from external API: {}".format(api_primary[:80]))
        else:
            utils.kodilog("Stripchat: External API returned no stream URL, using listing URL")
        variant_map = stream_data.get('streams') or {}
        if isinstance(variant_map, dict):
            for key in ('source', '1080p', '720p', '480p', '360p'):
                variant_url = variant_map.get(key) or variant_map.get(key.upper())
                normalized_variant = _add_candidate('api', variant_url)
                if normalized_variant and normalized_variant != api_primary:
                    utils.kodilog("Stripchat: Added API variant {}: {}".format(key, normalized_variant[:80]))
    except Exception as e:
        utils.kodilog("Stripchat: Error fetching from external API (will use listing URL): {}".format(str(e)))

    selection = _select_candidate()

    if selection['kind'] == 'listing':
        page_fallback = _extract_stream_url_from_page()
        if page_fallback and not any(url == page_fallback for _, url in candidate_urls):
            _add_candidate('page', page_fallback)
            selection = _select_candidate()

    url = selection['url']
    selected_base_url = url
    if selection['kind'] != 'api':
        utils.kodilog("Stripchat: Using {} URL for playback".format(selection['kind']))

    vp.progress.update(60, "[CR]Selecting best quality[CR]")

    # Prepare headers (for IA and for probing master)
    ua = urllib_parse.quote(utils.USER_AGENT, safe='')
    origin_enc = urllib_parse.quote('https://stripchat.com', safe='')
    referer_enc = urllib_parse.quote(model_ref, safe='')
    ia_headers = 'User-Agent={0}&Origin={1}&Referer={2}'.format(ua, origin_enc, referer_enc)

    # Choose quality based on setting
    force_best = utils.addon.getSetting('stripchat_best') == 'true'
    if force_best:
        try:
            master_headers = {'User-Agent': utils.USER_AGENT,
                              'Origin': 'https://stripchat.com',
                              'Referer': model_ref}
            master_url = url
            master_txt = None
            mvar = re.search(r'_(\d+)p\.m3u8$', url)
            if mvar:
                candidate = re.sub(r'_(\d+)p\.m3u8$', '.m3u8', url)
                try:
                    master_txt = utils._getHtml(candidate, site.url, headers=master_headers, error='raise')
                    master_url = candidate
                    utils.kodilog("Stripchat: Using probed master manifest: {}".format(master_url))
                except Exception:
                    master_txt = None
            if master_txt is None:
                try:
                    master_txt = utils._getHtml(master_url, site.url, headers=master_headers, error='raise')
                except Exception:
                    master_txt = None

            if master_txt:
                best_pixels = -1
                best_avc_pixels = -1
                lines = master_txt.splitlines()
                best_avc_url = None
                best_any_url = None
                for i, line in enumerate(lines):
                    if line.startswith('#EXT-X-STREAM-INF:'):
                        info = line
                        if i + 1 < len(lines):
                            vurl = lines[i + 1].strip()
                            abs_vurl = urllib_parse.urljoin(master_url, vurl)
                            if 'NAME="source"' in info or 'NAME=source' in info:
                                url = abs_vurl
                                utils.kodilog("Stripchat: Selected variant by NAME=source")
                                break
                            m = re.search(r'RESOLUTION=(\d+)x(\d+)', info)
                            pixels = -1
                            if m:
                                w, h = int(m.group(1)), int(m.group(2))
                                pixels = w * h
                            is_avc = 'CODECS="avc1' in info or 'codecs="avc1' in info
                            if is_avc and pixels > best_avc_pixels:
                                best_avc_pixels = pixels
                                best_avc_url = abs_vurl
                            if pixels > best_pixels:
                                best_pixels = pixels
                                best_any_url = abs_vurl
                else:
                    if best_avc_url:
                        url = best_avc_url
                        utils.kodilog("Stripchat: Selected AVC variant")
                    elif best_any_url:
                        url = best_any_url
                        utils.kodilog("Stripchat: Selected highest-res variant")
        except Exception:
            pass

    try:
        utils._getHtml(url, site.url, headers=probe_headers, error='raise')
    except urllib_error.HTTPError as http_err:
        utils.kodilog("Stripchat: Probe HTTP error {} for {} (reverting to base URL)".format(http_err.code, url))
        url = selected_base_url
    except urllib_error.URLError as url_err:
        reason = getattr(url_err, 'reason', None)
        if isinstance(reason, socket.gaierror):
            utils.kodilog("Stripchat: DNS lookup failed during final probe ({}). Will attempt playback anyway.".format(reason))
        else:
            utils.kodilog("Stripchat: Probe failed for {} ({}). Reverting to base URL".format(url, url_err))
            url = selected_base_url
    except Exception as gen_err:
        utils.kodilog("Stripchat: Probe exception for {} ({}). Reverting to base URL".format(url, gen_err))
        url = selected_base_url

    vp.progress.update(85, "[CR]Found Stream[CR]")
    vp = utils.VideoPlayer(name, IA_check='IA')
    vp.play_from_direct_link(url + '|' + ia_headers)


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
