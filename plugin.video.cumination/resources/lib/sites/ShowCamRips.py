'''
     Cumination
    Copyright (C) 2015 Whitecream

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

# -*- coding: utf-8 -*-

import re
import html
import base64
import os
import time
import io

from six.moves import urllib_parse
from resources.lib import utils
from resources.lib.basics import tempDir
from resources.lib.adultsite import AdultSite

# Constantes
SITE_URL = 'https://www.showcamrips.com/'
FALLBACK_THUMB = 'https://img.showcamrips.com/images/no-image.jpg'

site = AdultSite(
    'showcamrips',
    '[COLOR hotpink]ShowCamRips[/COLOR]',
    SITE_URL,
    'showcamrips.png',
    'showcamrips'
)


def _get_html_with_retry(url, referer=None, max_retries=3):
    """
    Récupère le HTML avec retry et gestion des timeouts.
    Utilise _getHtml pour les requêtes complexes (search, referer) et getHtml pour les simples.
    """
    time.sleep(1.5)  # Anti-ban delay
    
    hdr = utils.base_hdrs.copy()
    if referer:
        hdr['Referer'] = referer
    
    for attempt in range(max_retries):
        try:
            if 'search.php' in url or referer:
                listhtml = utils._getHtml(url, referer or SITE_URL, headers=hdr)
            else:
                listhtml = utils.getHtml(url)
            
            if listhtml and len(listhtml) > 500:
                return listhtml
                
        except Exception as e:
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)  # Backoff exponentiel
    
    return None


def _thumbnail_file(img_data_b64, video_id):
    """
    Gère la création et la mise en cache des fichiers d'aperçu.
    Décode le base64, détecte le format, convertit en JPG pour Kodi.
    
    Args:
        img_data_b64: String base64 (avec ou sans header data:image)
        video_id: ID unique de la vidéo pour le nom de fichier
    
    Returns:
        Chemin vers le fichier image local ou URL fallback
    """
    if not img_data_b64 or not video_id:
        return FALLBACK_THUMB
    
    # Nettoyage du base64 (enlever header si présent)
    if ',' in img_data_b64:
        img_data_b64 = img_data_b64.split(',', 1)[1]
    
    # Vérification cache existant
    jpg_path = os.path.join(tempDir, 'scr_{}.jpg'.format(video_id))
    if os.path.exists(jpg_path):
        return jpg_path
    
    webp_path = os.path.join(tempDir, 'scr_{}.webp'.format(video_id))
    if os.path.exists(webp_path):
        return webp_path
    
    png_path = os.path.join(tempDir, 'scr_{}.png'.format(video_id))
    if os.path.exists(png_path):
        return png_path
    
    # Décodage base64
    try:
        # Padding si nécessaire
        padding_needed = 4 - len(img_data_b64) % 4
        if padding_needed != 4:
            img_data_b64 += '=' * padding_needed
        
        img_data = base64.b64decode(img_data_b64)
        
        if not img_data:
            return FALLBACK_THUMB
        
        # Détection du format par magic bytes
        img_format = None
        file_ext = 'jpg'
        
        if img_data[:4] == b'RIFF':
            img_format = 'WEBP'
            file_ext = 'webp'
        elif img_data[:4] == b'\x89PNG':
            img_format = 'PNG'
            file_ext = 'png'
        elif img_data[:2] == b'\xff\xd8':
            img_format = 'JPEG'
            file_ext = 'jpg'
        
        # Écriture du fichier temporaire
        temp_path = os.path.join(tempDir, 'scr_{}.{}'.format(video_id, file_ext))
        
        with open(temp_path, 'wb') as f:
            f.write(img_data)
        
        # Conversion WebP/PNG vers JPG pour compatibilité Kodi
        if img_format in ['WEBP', 'PNG'] and file_ext != 'jpg':
            try:
                from PIL import Image
                img = Image.open(temp_path)
                if img.mode in ('RGBA', 'LA', 'P'):
                    img = img.convert('RGB')
                jpg_path = os.path.join(tempDir, 'scr_{}.jpg'.format(video_id))
                img.save(jpg_path, 'JPEG', quality=90)
                os.remove(temp_path)  # Nettoyage du fichier original
                return jpg_path
            except ImportError:
                # PIL non disponible, utiliser le fichier original
                return temp_path
            except Exception:
                return temp_path
        
        return temp_path
        
    except Exception:
        return FALLBACK_THUMB


def _extract_img_url(img_attr, video_id):
    """
    Extrait et résout l'URL de l'aperçu depuis un attribut img.
    Gère les formats: data:image/base64, URL absolue, URL relative.
    """
    if not img_attr:
        return site.image
    
    img_attr = img_attr.strip()
    
    # Format data:image/base64
    if img_attr.startswith('data:image'):
        return _thumbnail_file(img_attr, video_id)
    
    # URL absolue
    if img_attr.startswith('http'):
        return img_attr
    
    # URL relative
    if img_attr.startswith('/'):
        return 'https://www.showcamrips.com' + img_attr
    
    # Fallback
    return site.image


def _detect_model_redirect(html_content):
    """
    Détecte si une recherche redirige vers une page modèle unique.
    Retourne l'URL du modèle si trouvé, None sinon.
    """
    if not html_content:
        return None
    
    # Pattern: lien vers /model/en/xxx dans les résultats de recherche
    model_match = re.search(
        r'href=["\'](https?://www\.showcamrips\.com/model/en/([^/"\']+))/?["\']',
        html_content,
        re.I
    )
    
    if model_match:
        model_url = model_match.group(1)
        if not model_url.endswith('/'):
            model_url += '/'
        return model_url
    
    return None


def _extract_videos(listhtml):
    """
    Extrait les vidéos du HTML avec plusieurs patterns de fallback.
    Retourne une liste de tuples (videopage, slug, video_id, title, img_url)
    """
    matches = []
    
    # Pattern 1: Structure standard avec data-id et data-tn/src
    pattern1 = re.compile(
        r'<a[^>]*href=["\']((?:https?://www\.showcamrips\.com)?/show-cam-sex-movies/([^/"\']+))["\']'
        r'[^>]*data-id=["\'](\d+)["\'][^>]*title=["\']([^"\']+)["\'][^>]*>'
        r'.*?<img[^>]*(?:data-tn|src)=["\']([^"\']+)["\']',
        re.IGNORECASE | re.DOTALL
    )
    matches = pattern1.findall(listhtml)
    
    if matches:
        return [
            (
                'https://www.showcamrips.com' + m[0] if m[0].startswith('/') else m[0],
                m[1],
                m[2],
                utils.cleantext(html.unescape(m[3])).strip(),
                _extract_img_url(m[4], m[2])
            )
            for m in matches
        ]
    
    # Pattern 2: Structure liste avec li (recherche)
    pattern2 = re.compile(
        r'<li[^>]*id=["\']li\d+["\'][^>]*>.*?'
        r'<a[^>]*href=["\']((?:https?://www\.showcamrips\.com)?/show-cam-sex-movies/([^/"\']+))["\']'
        r'[^>]*data-id=["\'](\d+)["\'][^>]*>.*?'
        r'<h3[^>]*class=["\']title["\'][^>]*>(.*?)</h3>.*?'
        r'<img[^>]*(?:data-tn|src)=["\']([^"\']+)["\'].*?</li>',
        re.IGNORECASE | re.DOTALL
    )
    matches = pattern2.findall(listhtml)
    
    if matches:
        return [
            (
                'https://www.showcamrips.com' + m[0] if m[0].startswith('/') else m[0],
                m[1],
                m[2],
                utils.cleantext(html.unescape(m[3])).strip(),
                _extract_img_url(m[4], m[2])
            )
            for m in matches
        ]
    
    # Pattern 3: Sans image (fallback)
    pattern3 = re.compile(
        r'<li[^>]*id=["\']li\d+["\'][^>]*>.*?'
        r'<a[^>]*href=["\']((?:https?://www\.showcamrips\.com)?/show-cam-sex-movies/([^/"\']+))["\']'
        r'[^>]*data-id=["\'](\d+)["\'][^>]*>.*?'
        r'<h3[^>]*class=["\']title["\'][^>]*>(.*?)</h3>.*?</li>',
        re.IGNORECASE | re.DOTALL
    )
    matches = pattern3.findall(listhtml)
    
    if matches:
        return [
            (
                'https://www.showcamrips.com' + m[0] if m[0].startswith('/') else m[0],
                m[1],
                m[2],
                utils.cleantext(html.unescape(m[3])).strip(),
                site.image  # Pas d'image disponible
            )
            for m in matches
        ]
    
    return []


def _get_next_page_url(listhtml, url, is_model_page, is_search, current_page):
    """
    Extrait l'URL de la page suivante selon le type de page.
    Retourne l'URL ou None si pas de page suivante.
    """
    # Pour les pages modèle: construction manuelle
    if is_model_page:
        base_url = re.sub(r'/\d+-pg/?$', '/', url)
        if not base_url.endswith('/'):
            base_url += '/'
        next_url = '{}{}-pg/'.format(base_url, current_page + 1)
        return next_url
    
    # Pour la recherche: extraction du lien page 2
    if is_search:
        page2_match = re.search(
            r'href=["\']([^"\']*search\.php[^"\']*page=\d+[^"\']*)["\']',
            listhtml,
            re.I
        )
        if page2_match:
            next_url = html.unescape(page2_match.group(1))
            if next_url.startswith('/'):
                next_url = 'https://www.showcamrips.com' + next_url
            return next_url
        return None
    
    # Pour les autres pages: lien "Next"
    next_match = re.search(
        r'<a[^>]*href=["\']([^"\']*?(?:\d+-pg|page=\d+)[^"\']*)["\'][^>]*>(?:Next|&gt;|»|→)',
        listhtml,
        re.I
    )
    if next_match:
        next_url = html.unescape(next_match.group(1))
        if next_url.startswith('/'):
            next_url = 'https://www.showcamrips.com' + next_url
        elif not next_url.startswith('http'):
            next_url = urllib_parse.urljoin(url, next_url)
        return next_url
    
    return None


@site.register(default_mode=True)
def Main():
    """Menu principal"""
    site.add_dir('[COLOR hotpink]Search[/COLOR]', site.url, 'showcamrips.Search', site.img_search)
    site.add_dir('[COLOR hotpink]Categories[/COLOR]', site.url, 'showcamrips.Categories', site.img_cat)
    site.add_dir('[COLOR hotpink]Models[/COLOR]', SITE_URL + 'cat/en/allmodels/', 'showcamrips.Models', site.img_models)
    List(site.url)


@site.register()
def List(url):
    """Liste les vidéos avec gestion avancée de la pagination et des aperçus"""
    if not url:
        url = site.url
    
    # Détection du type de page
    is_model_page = '/model/en/' in url
    is_search = 'search.php' in url
    
    # Extraction page courante pour modèles
    current_page = 1
    if is_model_page:
        pg_match = re.search(r'/(\d+)-pg/?$', url)
        if pg_match:
            current_page = int(pg_match.group(1))
    
    # Récupération du HTML
    referer = SITE_URL if is_search else None
    listhtml = _get_html_with_retry(url, referer)
    
    if not listhtml:
        utils.notify('ShowCamRips', 'Error loading page')
        utils.eod()
        return
    
    # Détection redirection recherche -> modèle (ta logique améliorée préservée)
    model_redirect = _detect_model_redirect(listhtml) if is_search else None
    if model_redirect and is_search:
        is_model_page = True
        is_search = False
        current_page = 1
    
    # Extraction des vidéos
    videos = _extract_videos(listhtml)
    
    if not videos:
        utils.notify('ShowCamRips', 'No videos found')
        utils.eod()
        return
    
    # Affichage des vidéos
    for videopage, slug, video_id, title, img_url in videos:
        site.add_download_link(title, videopage, 'showcamrips.Playvid', img_url, title)
    
    # Pagination
    base_url = model_redirect if model_redirect else url
    next_url = _get_next_page_url(listhtml, base_url, is_model_page, is_search, current_page)
    
    if next_url and next_url != url:
        page_num = current_page + 1 if is_model_page else '...'
        site.add_dir('Next Page ({})'.format(page_num), next_url, 'showcamrips.List', site.img_next)
    
    utils.eod()


@site.register()
def Categories(url):
    """Liste les catégories"""
    listhtml = utils.getHtml(url or site.url)
    
    pattern = r'href=["\'](https?://www\.showcamrips\.com/cat/en/([^/"\']+))/?["\'][^>]*>([^<]+)</a>'
    matches = re.findall(pattern, listhtml, re.I)
    
    if not matches:
        utils.notify('ShowCamRips', 'No categories found')
        utils.eod()
        return
    
    seen = set()
    for cat_url, cat_id, name in matches:
        if cat_id == 'allmodels' or cat_url in seen:
            continue
        seen.add(cat_url)
        name = utils.cleantext(html.unescape(name)).strip()
        if name and len(name) > 1:
            site.add_dir(name, cat_url + '/', 'showcamrips.List', site.img_cat)
    
    utils.eod()


@site.register()
def Models(url):
    """Liste les modèles avec pagination"""
    if not url:
        url = SITE_URL + 'cat/en/allmodels/'
    
    listhtml = utils.getHtml(url)
    
    pattern = r'href=["\'](https?://www\.showcamrips\.com/model/en/([^/"\']+))/?["\'][^>]*>([^<]+)</a>'
    matches = re.findall(pattern, listhtml, re.I)
    
    if not matches:
        utils.notify('ShowCamRips', 'No models found')
        utils.eod()
        return
    
    seen = set()
    for model_url, model_id, name in matches:
        if model_url in seen:
            continue
        seen.add(model_url)
        name = utils.cleantext(html.unescape(name)).strip()
        if name:
            site.add_dir(name, model_url + '/', 'showcamrips.List', site.img_models)
    
    # Pagination modèles
    if len(matches) >= 20:
        pg_match = re.search(r'/(\d+)-pg/?$', url)
        current_page = int(pg_match.group(1)) if pg_match else 1
        
        base_url = re.sub(r'/\d+-pg/?$', '/', url)
        if not base_url.endswith('/'):
            base_url += '/'
        next_url = '{}{}-pg/'.format(base_url, current_page + 1)
        
        site.add_dir('Next Page ({})'.format(current_page + 1), next_url, 'showcamrips.Models', site.img_next)
    
    utils.eod()


@site.register()
def Search(url, keyword=None):
    """Gestion de la recherche avec ta logique améliorée préservée"""
    if not keyword:
        site.search_dir(url, 'showcamrips.Search')
        return
    
    search_url = SITE_URL + "search.php?Src={}&lg=en".format(urllib_parse.quote_plus(keyword))
    List(search_url)


@site.register()
def Playvid(url, name, download=None):
    """Lecture vidéo avec extraction multi-niveaux du stream"""
    vp = utils.VideoPlayer(name, download)
    vp.progress.update(25, "[CR]Loading video page[CR]")
    
    listhtml = utils.getHtml(url, site.url)
    
    # Extraction iframe loading_video.php
    iframe = re.search(r'<iframe[^>]*src=["\']([^"\']*loading_video\.php\?[^"\']+)', listhtml, re.I)
    
    if not iframe:
        vp.progress.close()
        utils.notify('ShowCamRips', 'Video not found')
        return
    
    player_url = urllib_parse.urljoin(SITE_URL, html.unescape(iframe.group(1)))
    vp.progress.update(50, "[CR]Loading player[CR]")
    
    player_html = utils.getHtml(player_url, url)
    
    # Détection redirection vers play.php
    play_match = re.search(
        r'window\.location\.href\s*=\s*[\'"](play\.php\?[^\'"]+)[\'"]',
        player_html,
        re.I
    )
    if play_match:
        real_play_url = urllib_parse.urljoin(SITE_URL, html.unescape(play_match.group(1)))
        player_html = utils.getHtml(real_play_url, player_url)
        player_url = real_play_url
    
    # Extraction URL vidéo (multi-patterns)
    video_url = None
    
    # Pattern video src
    video_match = re.search(r'<video[^>]*src=["\']([^"\']+)["\']', player_html, re.I)
    if video_match:
        video_url = video_match.group(1)
    
    # Pattern source src
    if not video_url:
        video_match = re.search(r'<source[^>]*src=["\']([^"\']+)["\']', player_html, re.I)
        if video_match:
            video_url = video_match.group(1)
    
    # Pattern direct mp4
    if not video_url:
        video_match = re.search(r'(https?://[^\s"\'<>]+\.mp4[^\s"\'<>]*)', player_html, re.I)
        if video_match:
            video_url = video_match.group(1)
    
    if not video_url:
        vp.progress.close()
        utils.notify('ShowCamRips', 'Stream not found')
        return
    
    video_url = html.unescape(video_url)
    vp.progress.update(75, "[CR]Found stream[CR]")
    
    vp.play_from_direct_link(video_url + '|referer=' + player_url)
    vp.progress.close()