'''
    Cumination
    Copyright (C) 2020 Cumination
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


convertdict = {23: 'xtheatre.XTVideo',
               52: 'porntrex.PTPlayvid',
               62: 'porn00.Playvid',
               72: 'pornhive.PHVideo',
               82: 'beeg.BGPlayvid',
               92: 'bubbaporn.TPPlayvid',
               102: 'poldertube.NLPLAYVID',
               112: 'cambro.Playvid',
               132: 'xvideospanish.Playvid',
               142: 'pelisxporno.Playvid',
               152: 'hqporner.HQPLAY',
               172: 'streamxxx.Playvid',
               192: 'vipporns.Playvid',
               212: 'cumlouder.Playvid',
               222: 'chaturbate.Playvid',
               242: 'justporn.Playvid',
               252: 'paradisehill.Playvid',
               282: 'cam4.Playvid',
               292: 'porndig.Playvid',
               302: 'absoluporn.Playvid',
               322: 'anybunny.Playvid',
               342: 'txxx.Playvid',
               372: 'freeomovie.Playvid',
               382: 'txxx.Playvid',
               392: 'pornhub.Playvid',
               402: 'mrsexe.Playvid',
               412: 'xxxstreams.Playvid',
               422: 'xxxsorg.Playvid',
               442: 'spankbang.Playvid',
               462: 'hentaihaven.Playvid',
               478: 'camsoda.Playvid',
               482: 'naked.Playvid',
               492: 'amateurcool.Playvid',
               502: 'vporn.Playvid',
               507: 'xhamster.Playvid',
               518: 'streamate.Playvid',
               524: 'bongacams.Playvid',
               532: 'herexxx.Playvid',
               612: 'daftsex.Playvid',
               662: 'animeid.animeidhentai_play',
               672: 'datoporn.datoporn_play',
               682: 'pornvibe.pornvibe_play',
               692: 'porngo.Play',
               742: 'freepornstreams.Playvid',
               752: 'xmoviesforyou.Playvid',
               762: 'viralvideosporno.Playvid',
               772: 'xozilla.Playvid',
               782: 'speedporn.Playvid',
               922: 'hentaidude.hentaidude_play',
               932: 'cpv.Playvid',
               812: 'netflixporno.Playvid'}


def convertfav(backupdata):
    favorites = backupdata["data"]
    favoritesnew = []

    for favorite in favorites:
        if favorite['mode'] in convertdict:
            if favorite['mode'] == 518:
                favorite['url'] = '{0}$${1}'.format(favorite['name'], favorite['url'])
            if favorite['mode'] in (342, 382):
                url = favorite['url'].split('/')
                favorite['url'] = '/'.join([url[x] for x in [0, 1, 2, 4]])
            if favorite['mode'] == 282:
                favorite['url'] = 'https://www.cam4.com/' + favorite['name']
            favorite['mode'] = convertdict[favorite['mode']]
            favoritesnew.append(favorite)

    backupdata['data'] = favoritesnew
    return backupdata
