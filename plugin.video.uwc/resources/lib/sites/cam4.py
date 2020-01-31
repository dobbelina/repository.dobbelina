'''
    Ultimate Whitecream
    Copyright (C) 2016 Whitecream

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
import os
import sys
import sqlite3
import urllib
import json

import xbmc
import xbmcplugin
import xbmcgui
from resources.lib import utils

languages = json.loads(' {"aa":"Afar","ab":"Abkhazian","af":"Afrikaans","am":"Amharic","ar":"Arabic","as":"Assamese","ay":"Aymara","az":"Azerbaijani","ba":"Bashkir","be":"Byelorussian","bg":"Bulgarian","bh":"Bihari","bi":"Bislama","bn":"Bengali","bo":"Tibetan","br":"Breton","ca":"Catalan","co":"Corsican","cs":"Czech","cy":"Welch","da":"Danish","de":"German","dz":"Bhutani","el":"Greek","en":"English","eo":"Esperanto","es":"Spanish","et":"Estonian","eu":"Basque","fa":"Persian","fi":"Finnish","fj":"Fiji","fo":"Faeroese","fr":"French","fy":"Frisian","ga":"Irish","gd":"Scots Gaelic","gl":"Galician","gn":"Guarani","gu":"Gujarati","ha":"Hausa","hi":"Hindi","he":"Hebrew","hr":"Croatian","hu":"Hungarian","hy":"Armenian","ia":"Interlingua","id":"Indonesian","ie":"Interlingue","ik":"Inupiak","in":"former Indonesian","is":"Icelandic","it":"Italian","iu":"Inuktitut (Eskimo)","iw":"former Hebrew","ja":"Japanese","ji":"former Yiddish","jw":"Javanese","ka":"Georgian","kk":"Kazakh","kl":"Greenlandic","km":"Cambodian","kn":"Kannada","ko":"Korean","ks":"Kashmiri","ku":"Kurdish","ky":"Kirghiz","la":"Latin","ln":"Lingala","lo":"Laothian","lt":"Lithuanian","lv":"Latvian, Lettish","mg":"Malagasy","mi":"Maori","mk":"Macedonian","ml":"Malayalam","mn":"Mongolian","mo":"Moldavian","mr":"Marathi","ms":"Malay","mt":"Maltese","my":"Burmese","na":"Nauru","ne":"Nepali","nl":"Dutch","no":"Norwegian","oc":"Occitan","om":"(Afan) Oromo","or":"Oriya","pa":"Punjabi","pl":"Polish","ps":"Pashto, Pushto","pt":"Portuguese","qu":"Quechua","rm":"Rhaeto-Romance","rn":"Kirundi","ro":"Romanian","ru":"Russian","rw":"Kinyarwanda","sa":"Sanskrit","sd":"Sindhi","sg":"Sangro","sh":"Serbo-Croatian","si":"Singhalese","sk":"Slovak","sl":"Slovenian","sm":"Samoan","sn":"Shona","so":"Somali","sq":"Albanian","sr":"Serbian","ss":"Siswati","st":"Sesotho","su":"Sudanese","sv":"Swedish","sw":"Swahili","ta":"Tamil","te":"Tegulu","tg":"Tajik","th":"Thai","ti":"Tigrinya","tk":"Turkmen","tl":"Tagalog","tn":"Setswana","to":"Tonga","tr":"Turkish","ts":"Tsonga","tt":"Tatar","tw":"Twi","ug":"Uigur","uk":"Ukrainian","ur":"Urdu","uz":"Uzbek","vi":"Vietnamese","vo":"Volapuk","wo":"Wolof","xh":"Xhosa","yi":"Yiddish","yo":"Yoruba","za":"Zhuang","zh":"Chinese","zu":"Zulu"}')

countries = json.loads('{"af":"Afghanistan","al":"Albania","dz":"Algeria","as":"American Samoa","ad":"Andorra","ao":"Angola","ai":"Anguilla","ag":"Antigua & Barbuda","ar":"Argentina","am":"Armenia","aw":"Aruba","au":"Australia","at":"Austria","az":"Azerbaijan","bs":"Bahamas","bh":"Bahrain","bd":"Bangladesh","bb":"Barbados","by":"Belarus","be":"Belgium","bz":"Belize","bj":"Benin","bm":"Bermuda","bt":"Bhutan","bo":"Bolivia","ba":"Bosnia & Herzegovina","bw":"Botswana","bv":"Bouvet Island","br":"Brazil","bn":"Brunei Darussalam","bg":"Bulgaria","bf":"Burkina Faso","bi":"Burundi","kh":"Cambodia","cm":"Cameroon","ca":"Canada","cv":"Cape Verde","ky":"Cayman Islands","cf":"Central African Republic","td":"Chad","cl":"Chile","cn":"China","co":"Colombia","km":"Comoros","cg":"Congo","cd":"Congo, the Democratic Republic of the","ck":"Cook Islands","cr":"Costa Rica","ci":"Cote D\'Ivoire","hr":"Croatia","cu":"Cuba","cw":"Curacao","cy":"Cyprus","cz":"Czech Republic","dk":"Denmark","dj":"Djibouti","dm":"Dominica","do":"Dominican Republic","ec":"Ecuador","eg":"Egypt","sv":"El Salvador","gq":"Equatorial Guinea","er":"Eritrea","ee":"Estonia","et":"Ethiopia","fk":"Falkland Islands (Malvinas)","fo":"Faroe Islands","fj":"Fiji","fi":"Finland","fr":"France","gf":"French Guiana","pf":"French Polynesia","ga":"Gabon","gm":"Gambia","ge":"Georgia","de":"Germany","gh":"Ghana","gi":"Gibraltar","gr":"Greece","gl":"Greenland","gd":"Grenada","gp":"Guadeloupe","gu":"Guam","gt":"Guatemala","gn":"Guinea","gw":"Guinea-Bissau","gy":"Guyana","ht":"Haiti","va":"Holy See (Vatican City)","hn":"Honduras","hk":"Hong Kong","hu":"Hungary","is":"Iceland","in":"India","id":"Indonesia","ir":"Iran","iq":"Iraq","ie":"Ireland","il":"Israel","it":"Italy","jm":"Jamaica","jp":"Japan","je":"Jersey","jo":"Jordan","kz":"Kazakhstan","ke":"Kenya","ki":"Kiribati","kp":"Korea, Democratic People\'s Republic of","kr":"Korea, Republic of","kw":"Kuwait","kg":"Kyrgyzstan","la":"Lao","lv":"Latvia","lb":"Lebanon","ls":"Lesotho","lr":"Liberia","ly":"Libyan Arab Jamahiriya","li":"Liechtenstein","lt":"Lithuania","lu":"Luxembourg","mo":"Macao","mk":"Macedonia","mg":"Madagascar","mw":"Malawi","my":"Malaysia","mv":"Maldives","ml":"Mali","mt":"Malta","mh":"Marshall Islands","mq":"Martinique","mr":"Mauritania","mu":"Mauritius","mx":"Mexico","fm":"Micronesia","md":"Moldova","mc":"Monaco","mn":"Mongolia","me":"Montenegro","ms":"Montserrat","ma":"Morocco","mz":"Mozambique","mm":"Myanmar","na":"Namibia","nr":"Nauru","np":"Nepal","nl":"Netherlands","an":"Netherlands Antilles","nc":"New Caledonia","nz":"New Zealand","ni":"Nicaragua","ne":"Niger","ng":"Nigeria","nu":"Niue","nf":"Norfolk Island","mp":"Northern Mariana Islands","no":"Norway","om":"Oman","pk":"Pakistan","pw":"Palau","ps":"Palestine","pa":"Panama","pg":"Papua New Guinea","py":"Paraguay","pe":"Peru","ph":"Philippines","pn":"Pitcairn","pl":"Poland","pt":"Portugal","pr":"Puerto Rico","qa":"Qatar","re":"Reunion","ro":"Romania","ru":"Russian Federation","rw":"Rwanda","bl":"Saint Barths","sh":"Saint Helena","kn":"Saint Kitts and Nevis","lc":"Saint Lucia","pm":"Saint Pierre & Miquelon","vc":"Saint Vincent & the Grenadines","ws":"Samoa","sm":"San Marino","st":"Sao Tome & Principe","sa":"Saudi Arabia","sn":"Senegal","rs":"Serbia","sc":"Seychelles","sl":"Sierra Leone","sg":"Singapore","sk":"Slovakia","si":"Slovenia","sb":"Solomon Islands","so":"Somalia","za":"South Africa","es":"Spain","lk":"Sri Lanka","sd":"Sudan","sr":"Suriname","sj":"Svalbard & Jan Mayen","sz":"Swaziland","se":"Sweden","ch":"Switzerland","sy":"Syrian Arab Republic","tw":"Taiwan","tj":"Tajikistan","tz":"Tanzania","th":"Thailand","tl":"Timor-Leste","tg":"Togo","tk":"Tokelau","to":"Tonga","tt":"Trinidad & Tobago","tn":"Tunisia","tr":"Turkey","tm":"Turkmenistan","tc":"Turks & Caicos","tv":"Tuvalu","ug":"Uganda","ua":"Ukraine","ae":"United Arab Emirates","gb":"United Kingdom","us":"United States","um":"United States Minor Outlying Islands","uy":"Uruguay","uz":"Uzbekistan","vu":"Vanuatu","ve":"Venezuela","vn":"Viet Nam","vg":"Virgin Islands, British","vi":"Virgin Islands, U.S.","wf":"Wallis & Futuna","eh":"Western Sahara","ye":"Yemen","zm":"Zambia","zw":"Zimbabwe"}')

mobileagent = {'User-Agent': 'Mozilla/5.0 (Linux; U; Android 2.2; en-us; Droid Build/FRG22D) AppleWebKit/533.1 (KHTML, like Gecko) Version/4.0 Mobile Safari/533.1'}


@utils.url_dispatcher.register('280')
def Main():
    utils.addDir('[COLOR red]Refresh Cam4 images[/COLOR]','',283,'',Folder=False)
    utils.addDir('[COLOR hotpink]Featured[/COLOR]','https://www.cam4.com/directoryCams?directoryJson=true&online=true&url=true&page=1&orderBy=VIDEO_QUALITY&resultsPerPage=60',281,'',1)
    utils.addDir('[COLOR hotpink]Females[/COLOR]','https://www.cam4.com/directoryCams?directoryJson=true&online=true&url=true&gender=female&broadcastType=female_group&broadcastType=solo&broadcastType=male_female_group&page=1&orderBy=VIDEO_QUALITY&resultsPerPage=60',281,'',1)
    utils.addDir('[COLOR hotpink]Couples[/COLOR]','https://www.cam4.com/directoryCams?directoryJson=true&online=true&url=true&broadcastType=male_group&broadcastType=female_group&broadcastType=male_female_group&page=1&orderBy=VIDEO_QUALITY&resultsPerPage=60',281,'',1)
    utils.addDir('[COLOR hotpink]Males[/COLOR]','https://www.cam4.com/directoryCams?directoryJson=true&online=true&url=true&gender=male&broadcastType=male_group&broadcastType=solo&broadcastType=male_female_group&page=1&orderBy=VIDEO_QUALITY&resultsPerPage=60',281,'',1)
    utils.addDir('[COLOR hotpink]Transsexual[/COLOR]','https://www.cam4.com/directoryCams?directoryJson=true&online=true&url=true&gender=shemale&page=1&orderBy=VIDEO_QUALITY&resultsPerPage=60',281,'',1)
    xbmcplugin.endOfDirectory(utils.addon_handle)


@utils.url_dispatcher.register('283')
def clean_database(showdialog=True):
    conn = sqlite3.connect(xbmc.translatePath("special://database/Textures13.db"))
    try:
        with conn:
            list = conn.execute("SELECT id, cachedurl FROM texture WHERE url LIKE '%%%s%%';" % ".cam4s.com")
            for row in list:
                conn.execute("DELETE FROM sizes WHERE idtexture LIKE '%s';" % row[0])
                try: os.remove(xbmc.translatePath("special://thumbnails/" + row[1]))
                except: pass
            conn.execute("DELETE FROM texture WHERE url LIKE '%%%s%%';" % ".cam4s.com")
            if showdialog:
                utils.notify('Finished','Cam4 images cleared')
    except:
        pass


@utils.url_dispatcher.register('281', ['url'], ['page'])
def List(url, page=1):
    if utils.addon.getSetting("chaturbate") == "true":
        clean_database(False)
    try:
        data = utils.getHtml(url)
    except:
        return None
    model_list = json.loads(data)
    for model in model_list['users']:
        lang = ""
        for language in model['languages']:
            if lang != "":
                lang  = lang + ", "
            lang = lang + languages[language]

        info = "\n\n[B]Age:[/B] " + str(model['age']) + "\n[B]Gender:[/B] " + model['gender'].title() + "\n[B]Orientation:[/B] " + model['sexPreference'].title() + "\n\n[B]Country:[/B] " + countries[model['countryCode']] + "\n[B]Language:[/B] " + lang + "\n\n[B]Broadcast type:[/B] " + model['broadcastType'].title() + "\n[B]Broadcast time:[/B] " + str(model['broadcastTime']) + "\n[B]Viewers:[/B] " + str(model['viewers']) + "\n\n[B]Source:[/B] " + model['source'].title() + " (" + str(model['resolution']) + ")" + "\n\n[B]Room topic:[/B] " + model['statusMessage'].title()

        utils.addDownLink(model['username'], model['hlsPreviewUrl'], 282, model['snapshotImageLink'], info, noDownload=True)
    if len(model_list['users'])== 60:
            npage = page + 1        
            url = url.replace('&page='+str(page),'&page='+str(npage))
            utils.addDir('Next Page ('+str(npage)+')', url, 281, '', npage)        
    xbmcplugin.endOfDirectory(utils.addon_handle)


@utils.url_dispatcher.register('282', ['url', 'name'])
def Playvid(url, name):
    info = ''
    listhtml = utils.getHtml('https://www.cam4.com/' + name)
    listhtml = listhtml.replace('><','> <')
    match = re.compile(r'<span class="desc">(.+?)</span>.*?(class="field.+?>(.+?)</|</li>)', re.DOTALL | re.IGNORECASE).findall(listhtml)
    for desc, dummy, field in match:
        info = info + "[B]" + desc + "[/B] " + field + "\n"
    videourl = url
    iconimage = xbmc.getInfoImage("ListItem.Thumb")
    listitem = xbmcgui.ListItem(name, iconImage="DefaultVideo.png", thumbnailImage=iconimage)
    listitem.setInfo('video', {'Title': name, 'Genre': 'Porn', 'Plot': info})
    listitem.setProperty("IsPlayable","true")
    if int(sys.argv[1]) == -1:
       pl = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
       pl.clear()
       pl.add(videourl, listitem)
       xbmc.Player().play(pl)
    else:
       listitem.setPath(str(videourl))
       xbmcplugin.setResolvedUrl(utils.addon_handle, True, listitem)
