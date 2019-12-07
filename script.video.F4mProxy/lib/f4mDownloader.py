# -*- coding: utf-8 -*-
import xml.etree.ElementTree as etree
import base64
from struct import unpack, pack
import sys
import io
import os
import time
import itertools
import xbmcaddon
import xbmc
import urllib2,urllib
import traceback
import urlparse
import posixpath
import re
import hmac
import hashlib
import binascii 
import zlib
from hashlib import sha256
import cookielib
import akhds

#import youtube_dl
#from youtube_dl.utils import *

try:
    addon_id = 'plugin.video.f4mTester' # yes its a wrong one but due to settings getting reset
    selfAddon = xbmcaddon.Addon(id=addon_id)
except:
    addon_id = 'script.video.F4mProxy' # yes its a wrong one but due to settings getting reset
    selfAddon = xbmcaddon.Addon(id=addon_id)
    
    
__addonname__   = selfAddon.getAddonInfo('name')
__icon__        = selfAddon.getAddonInfo('icon')
downloadPath   = xbmc.translatePath(selfAddon.getAddonInfo('profile'))#selfAddon["profile"])
F4Mversion=''
#from Crypto.Cipher import AES

value_unsafe = '%+&;#'
VALUE_SAFE = ''.join(chr(c) for c in range(33, 127)
    if chr(c) not in value_unsafe)
def urlencode_param(value):
    """Minimal URL encoding for query parameter"""
    return urllib.quote_plus(value, safe=VALUE_SAFE)
        
class FlvReader(io.BytesIO):
    """
    Reader for Flv files
    The file format is documented in https://www.adobe.com/devnet/f4v.html
    """

    # Utility functions for reading numbers and strings
    def read_unsigned_long_long(self):
        return unpack('!Q', self.read(8))[0]
    def read_unsigned_int(self):
        return unpack('!I', self.read(4))[0]
    def read_unsigned_char(self):
        return unpack('!B', self.read(1))[0]
    def read_string(self):
        res = b''
        while True:
            char = self.read(1)
            if char == b'\x00':
                break
            res+=char
        return res

    def read_box_info(self):
        """
        Read a box and return the info as a tuple: (box_size, box_type, box_data)
        """
        real_size = size = self.read_unsigned_int()
        box_type = self.read(4)
        header_end = 8
        if size == 1:
            real_size = self.read_unsigned_long_long()
            header_end = 16
        return real_size, box_type, self.read(real_size-header_end)

    def read_asrt(self, debug=False):
        version = self.read_unsigned_char()
        self.read(3) # flags
        quality_entry_count = self.read_unsigned_char()
        quality_modifiers = []
        for i in range(quality_entry_count):
            quality_modifier = self.read_string()
            quality_modifiers.append(quality_modifier)
        segment_run_count = self.read_unsigned_int()
        segments = []
        #print 'segment_run_count',segment_run_count
        for i in range(segment_run_count):
            first_segment = self.read_unsigned_int()
            fragments_per_segment = self.read_unsigned_int()
            segments.append((first_segment, fragments_per_segment))
        #print 'segments',segments
        return {'version': version,
                'quality_segment_modifiers': quality_modifiers,
                'segment_run': segments,
                }

    def read_afrt(self, debug=False):
        version = self.read_unsigned_char()
        self.read(3) # flags
        time_scale = self.read_unsigned_int()
        quality_entry_count = self.read_unsigned_char()
        quality_entries = []
        for i in range(quality_entry_count):
            mod = self.read_string()
            quality_entries.append(mod)
        fragments_count = self.read_unsigned_int()
        #print 'fragments_count',fragments_count
        fragments = []
        for i in range(fragments_count):
            first = self.read_unsigned_int()
            first_ts = self.read_unsigned_long_long()
            duration = self.read_unsigned_int()
            if duration == 0:
                discontinuity_indicator = self.read_unsigned_char()
            else:
                discontinuity_indicator = None
            fragments.append({'first': first,
                              'ts': first_ts,
                              'duration': duration,
                              'discontinuity_indicator': discontinuity_indicator,
                              })
        #print 'fragments',fragments
        return {'version': version,
                'time_scale': time_scale,
                'fragments': fragments,
                'quality_entries': quality_entries,
                }

    def read_abst(self, debug=False):
        version = self.read_unsigned_char()
        self.read(3) # flags
        bootstrap_info_version = self.read_unsigned_int()
        streamType=self.read_unsigned_char()#self.read(1) # Profile,Live,Update,Reserved
        islive=False
        if (streamType & 0x20) >> 5:
            islive=True
        print 'LIVE',streamType,islive
        time_scale = self.read_unsigned_int()
        current_media_time = self.read_unsigned_long_long()
        smpteTimeCodeOffset = self.read_unsigned_long_long()
        movie_identifier = self.read_string()
        server_count = self.read_unsigned_char()
        servers = []
        for i in range(server_count):
            server = self.read_string()
            servers.append(server)
        quality_count = self.read_unsigned_char()
        qualities = []
        for i in range(server_count):
            quality = self.read_string()
            qualities.append(server)
        drm_data = self.read_string()
        metadata = self.read_string()
        segments_count = self.read_unsigned_char()
        #print 'segments_count11',segments_count
        segments = []
        for i in range(segments_count):
            box_size, box_type, box_data = self.read_box_info()
            assert box_type == b'asrt'
            segment = FlvReader(box_data).read_asrt()
            segments.append(segment)
        fragments_run_count = self.read_unsigned_char()
        #print 'fragments_run_count11',fragments_run_count
        fragments = []
        for i in range(fragments_run_count):
            # This info is only useful for the player, it doesn't give more info 
            # for the download process
            box_size, box_type, box_data = self.read_box_info()
            assert box_type == b'afrt'
            fragments.append(FlvReader(box_data).read_afrt())
    
        return {'segments': segments,
                'movie_identifier': movie_identifier,
                'drm_data': drm_data,
                'fragments': fragments,
                },islive

    def read_bootstrap_info(self):
        """
        Read the bootstrap information from the stream,
        returns a dict with the following keys:
        segments: A list of dicts with the following keys
            segment_run: A list of (first_segment, fragments_per_segment) tuples
        """
        total_size, box_type, box_data = self.read_box_info()
        assert box_type == b'abst'
        return FlvReader(box_data).read_abst()

def read_bootstrap_info(bootstrap_bytes):
    return FlvReader(bootstrap_bytes).read_bootstrap_info()

def build_fragments_list(boot_info, startFromFregment=None, live=True):
    """ Return a list of (segment, fragment) for each fragment in the video """
    res = []
    segment_run_table = boot_info['segments'][0]
    print 'segment_run_table',segment_run_table
    # I've only found videos with one segment
    #if len(segment_run_table['segment_run'])>1:
    #    segment_run_table['segment_run']=segment_run_table['segment_run'][-2:] #pick latest

    
    frag_start = boot_info['fragments'][0]['fragments']
    #print boot_info['fragments']
 
 
    
#    sum(j for i, j in segment_run_table['segment_run'])
    
    first_frag_number=frag_start[0]['first']
    last_frag_number=frag_start[-1]['first']
    if last_frag_number==0:
        last_frag_number=frag_start[-2]['first']
    endfragment=0
    segment_to_start=None
    for current in range (len(segment_run_table['segment_run'])):
        seg,fregCount=segment_run_table['segment_run'][current]
        #print 'segmcount',seg,fregCount
        if (not live):
            frag_end=last_frag_number
        else:
            frag_end=first_frag_number+fregCount-1
            if fregCount>10000:
                frag_end=last_frag_number
        #if frag_end

            
        
        segment_run_table['segment_run'][current]=(seg,fregCount,first_frag_number,frag_end)
        if (not startFromFregment==None) and startFromFregment>=first_frag_number and startFromFregment<=frag_end:
            segment_to_start=current
        first_frag_number+=fregCount
#    print 'current status',segment_run_table['segment_run']
    #if we have no index then take the last segment
    if segment_to_start==None:
        segment_to_start=len(segment_run_table['segment_run'])-1
        #if len(segment_run_table['segment_run'])>2:
        #    segment_to_start=len(segment_run_table['segment_run'])-2;
        if live:
            startFromFregment=segment_run_table['segment_run'][-1][3]
#            if len(boot_info['fragments'][0]['fragments'])>1: #go bit back
#               startFromFregment= boot_info['fragments'][0]['fragments'][-1]['first']

        else:
            startFromFregment= boot_info['fragments'][0]['fragments'][0]['first'] #start from begining
            
        #if len(boot_info['fragments'][0]['fragments'])>2: #go little bit back
        #    startFromFregment= boot_info['fragments'][0]['fragments'][-2]['first']
    #print 'startFromFregment',startFromFregment,boot_info,len(boot_info['fragments'][0]['fragments'])
    #print 'segment_to_start',segment_to_start
    for currentIndex in range (segment_to_start,len(segment_run_table['segment_run'])):
        currentSegment=segment_run_table['segment_run'][currentIndex]
        #print 'currentSegment',currentSegment
        (seg,fregCount,frag_start,frag_end)=currentSegment
        #print 'startFromFregment',startFromFregment, 
        if (not startFromFregment==None) and startFromFregment>=frag_start and startFromFregment<=frag_end:
            frag_start=startFromFregment
        #print 'frag_start',frag_start,frag_end
        for currentFreg in range(frag_start,frag_end+1):
             res.append((seg,currentFreg ))
#    print 'fragmentlist',res,boot_info
    return res

    
    #totalFrags=sum(j for i, j in segment_run_table['segment_run'])
    #lastSegment=segment_run_table['segment_run'][-1]
    #lastSegmentStart= lastSegment[0]
    #lastSegmentFragCount = lastSegment[1]
    #print 'totalFrags',totalFrags
    
    #first_frag_number = frag_start[0]['first']
    #startFragOfLastSegment= first_frag_number +totalFrags - lastSegmentFragCount
    
    #for (i, frag_number) in zip(range(1, lastSegmentFragCount+1), itertools.count(startFragOfLastSegment)):
    #    res.append((lastSegmentStart,frag_number )) #this was i, i am using first segement start
    #return res
    
    #segment_run_entry = segment_run_table['segment_run'][0]
    #print 'segment_run_entry',segment_run_entry,segment_run_table
    #n_frags = segment_run_entry[1]
    #startingPoint = segment_run_entry[0]
    #fragment_run_entry_table = boot_info['fragments'][0]['fragments']
    #frag_entry_index = 0
    #first_frag_number = fragment_run_entry_table[0]['first']

    #first_frag_number=(startingPoint*n_frags) -(n_frags)+1
    #print 'THENUMBERS',startingPoint,n_frags,first_frag_number
    #for (i, frag_number) in zip(range(1, n_frags+1), itertools.count(first_frag_number)):
    #    res.append((startingPoint,frag_number )) #this was i, i am using first segement start
    #return res

def join(base,url):
    join = urlparse.urljoin(base,url)
    url = urlparse.urlparse(join)
    path = posixpath.normpath(url[2])
    return urlparse.urlunparse(
        (url.scheme,url.netloc,path,url.params,url.query,url.fragment)
        )
        
def _add_ns(prop):
    #print 'F4Mversion',F4Mversion
    return '{http://ns.adobe.com/f4m/%s}%s' %(F4Mversion, prop)


#class ReallyQuietDownloader(youtube_dl.FileDownloader):
#    def to_screen(sef, *args, **kargs):
#        pass

class F4MDownloader():
    """
    A downloader for f4m manifests or AdobeHDS.
    """
    outputfile =''
    clientHeader=None
    cookieJar=cookielib.LWPCookieJar()

    def __init__(self):
        self.init_done=False
        
    def getUrl(self,url, ischunkDownloading=False):
        try:
            post=None
            print 'url',url
            
            #openner = urllib2.build_opener(urllib2.HTTPHandler, urllib2.HTTPSHandler)
            cookie_handler = urllib2.HTTPCookieProcessor(self.cookieJar)
            openner = urllib2.build_opener(cookie_handler, urllib2.HTTPBasicAuthHandler(), urllib2.HTTPHandler())

            if post:
                req = urllib2.Request(url, post)
            else:
                req = urllib2.Request(url)
            
            ua_header=False
            if self.clientHeader:
                for n,v in self.clientHeader:
                    req.add_header(n,v)
                    if n=='User-Agent':
                        ua_header=True

            if not ua_header:
                req.add_header('User-Agent','Mozilla/5.0 (Windows NT 6.1; Win64; x64; Trident/7.0; rv:11.0) like Gecko')
            #response = urllib2.urlopen(req)
            if self.proxy and (  (not ischunkDownloading) or self.use_proxy_for_chunks ):
                req.set_proxy(self.proxy, 'http')
            response = openner.open(req)
            data=response.read()

            return data

        except:
            print 'Error in getUrl'
            traceback.print_exc()
            return None
            
    def _write_flv_header2(self, stream):
        """Writes the FLV header and the metadata to stream"""
        # FLV header
        stream.write(b'FLV\x01')
        stream.write(b'\x01')
        stream.write(b'\x00\x00\x00\x09')
        # FLV File body
        stream.write(b'\x00\x00\x00\x09')

        
    def _write_flv_header(self, stream, metadata):
        """Writes the FLV header and the metadata to stream"""
        # FLV header
        stream.write(b'FLV\x01')
        stream.write(b'\x05')
        stream.write(b'\x00\x00\x00\x09')
        # FLV File body
        stream.write(b'\x00\x00\x00\x00')
        # FLVTAG
        if metadata:
            stream.write(b'\x12') # Script data
            stream.write(pack('!L',len(metadata))[1:]) # Size of the metadata with 3 bytes
            stream.write(b'\x00\x00\x00\x00\x00\x00\x00')
            stream.write(metadata)
        # All this magic numbers have been extracted from the output file
        # produced by AdobeHDS.php (https://github.com/K-S-V/Scripts)
            stream.write(b'\x00\x00\x01\x73')

    def init(self, out_stream, url, proxy=None,use_proxy_for_chunks=True,g_stopEvent=None, maxbitrate=0, auth='',swf=None):
        try:
            self.init_done=False
            self.total_frags=0
            self.init_url=url
            self.clientHeader=None
            self.status='init'
            self.proxy = proxy
            self.auth=auth
            #self.auth="pvtoken=exp%3D9999999999%7Eacl%3D%252f%252a%7Edata%3DZXhwPTE0MDYzMDMxMTV+YWNsPSUyZip+ZGF0YT1wdmMsc35obWFjPWQxODA5MWVkYTQ4NDI3NjFjODhjOWQwY2QxNTk3YTI0MWQwOWYwNWI1N2ZmMDE0ZjcxN2QyMTVjZTJkNmJjMDQ%3D%2196e4sdLWrezE46RaCBzzP43/LEM5en2KujAosbeDimQ%3D%7Ehmac%3DACF8A1E4467676C9BCE2721CA5EFF840BD6ED1780046954039373A3B0D942ADC&hdntl=exp=1406303115~acl=%2f*~data=hdntl~hmac=4ab96fa533fd7c40204e487bfc7befaf31dd1f49c27eb1f610673fed9ff97a5f&als=0,2,0,0,0,NaN,0,0,0,37,f,52293145.57,52293155.9,t,s,GARWLHLMHNGA,2.11.3,37&hdcore=2.11.3" 
            if self.auth ==None or self.auth =='None' :
                self.auth=''
            if self.proxy and len(self.proxy)==0:
                self.proxy=None
            self.use_proxy_for_chunks=use_proxy_for_chunks
            self.out_stream=out_stream
            self.g_stopEvent=g_stopEvent
            self.maxbitrate=maxbitrate
            if '|' in url:
                sp = url.split('|')
                url = sp[0]
                self.clientHeader = sp[1]
                self.clientHeader= urlparse.parse_qsl(self.clientHeader)
                
                print 'header recieved now url and headers are',url, self.clientHeader 
            self.status='init done'
            self.url=url
            self.swf=swf
            #self.downloadInternal(  url)
            return self.preDownoload()
            
            #os.remove(self.outputfile)
        except: 
            traceback.print_exc()
            self.status='finished'
        return False
     
    def preDownoload(self):
        global F4Mversion
        try:
            self.seqNumber=0
            self.live=False #todo find if its Live or not
            man_url = self.url
            url=self.url
            print 'Downloading f4m manifest'
            manifest = self.getUrl(man_url)#.read()
            if not manifest:
                return False
            print len(manifest)
            try:
                print manifest
            except: pass
            self.status='manifest done'
            #self.report_destination(filename)
            #dl = ReallyQuietDownloader(self.ydl, {'continuedl': True, 'quiet': True, 'noprogress':True})
            version_fine="xmlns=\".*?\/([0-9].*?)\""
            F4Mversion =re.findall(version_fine, manifest)[0]
            #print F4Mversion,_add_ns('media')
            auth_patt='<pv-2.0>(.*?)<'

            auth_obj =re.findall(auth_patt, manifest)
            self.auth20=''
            if auth_obj and len(auth_obj)>0:
                self.auth20=auth_obj[0] #not doing anything for time being
            print 'auth got from xml',self.auth,self.auth20
            #quick for one example where the xml was wrong.
            if '\"bootstrapInfoId' in manifest:
                manifest=manifest.replace('\"bootstrapInfoId','\" bootstrapInfoId')

            doc = etree.fromstring(manifest)
            print doc
            
            # Added the-one 05082014
            # START
            # Check if manifest defines a baseURL tag
            baseURL_tag = doc.find(_add_ns('baseURL'))
            if baseURL_tag != None:
                man_url = baseURL_tag.text
                url = man_url
                self.url = url
                print 'base url defined as: %s' % man_url
            # END
            
            try:
                #formats = [(int(f.attrib.get('bitrate', -1)),f) for f in doc.findall(_add_ns('media'))]
                formats=[]
                for f in doc.findall(_add_ns('media')):
                    vtype=f.attrib.get('type', '')
                    if f.attrib.get('type', '')=='video' or vtype=='' :
                        formats.append([int(f.attrib.get('bitrate', -1)),f])
                print 'format works',formats
            except:
                formats=[(int(0),f) for f in doc.findall(_add_ns('media'))]
            #print 'formats',formats
            
            
            formats = sorted(formats, key=lambda f: f[0])
            if self.maxbitrate==0:
                rate, media = formats[-1]
            elif self.maxbitrate==-1:
                rate, media = formats[0]
            else: #find bitrate
                brselected=None
                rate, media=None,None
                for r, m in formats:
                    if r<=self.maxbitrate:
                        rate, media=r,m
                    else:
                        break
                
                if media==None:
                    rate, media = formats[-1]
                
            
            dest_stream =  self.out_stream
            print 'rate selected',rate
            self.metadata=None
            try:
                self.metadata = base64.b64decode(media.find(_add_ns('metadata')).text)
                print 'metadata stream read done'#,media.find(_add_ns('metadata')).text

                #self._write_flv_header(dest_stream, metadata)
                #dest_stream.flush()
            except: pass
        
            # Modified the-one 05082014
            # START
            # url and href can be used interchangeably
            # so if url attribute is not present
            # check for href attribute
            try:
                mediaUrl=media.attrib['url']
            except:
                mediaUrl=media.attrib['href']
            # END
            
            # Added the-one 05082014
            # START
            # if media url/href points to another f4m file
            if '.f4m' in mediaUrl:
                sub_f4m_url = join(man_url,mediaUrl)
                print 'media points to another f4m file: %s' % sub_f4m_url
                
                print 'Downloading f4m sub manifest'
                sub_manifest = self.getUrl(sub_f4m_url)#.read()
                if not sub_manifest:
                    return False
                print len(sub_manifest)
                try:
                    print sub_manifest
                except: pass
                self.status='sub manifest done'
                F4Mversion =re.findall(version_fine, sub_manifest)[0]
                doc = etree.fromstring(sub_manifest)
                print doc
                media = doc.find(_add_ns('media'))
                if media == None:
                    return False
                    
                try:
                    self.metadata = base64.b64decode(media.find(_add_ns('metadata')).text)
                    print 'metadata stream read done'
                except: pass
                
                try:
                    mediaUrl=media.attrib['url']
                except:
                    mediaUrl=media.attrib['href']
            # END
            
            
            try:
                bootStrapID = media.attrib['bootstrapInfoId']
            except: bootStrapID='xx'
            #print 'mediaUrl',mediaUrl
            base_url = join(man_url,mediaUrl)#compat_urlparse.urljoin(man_url,media.attrib['url'])
            keybase_url=join(man_url,'key_')
            if mediaUrl.endswith('/') and not base_url.endswith('/'):
                    base_url += '/'

            self.base_url=base_url
            self.keybase_url=keybase_url
            bsArray=doc.findall(_add_ns('bootstrapInfo'))
            print 'bootStrapID',bootStrapID
            #bootStrapID='bootstrap_450'
            bootstrap=self.getBootStrapWithId(bsArray,bootStrapID)
            if bootstrap==None: #if not available then find any!
                print 'bootStrapID NOT Found'
                bootstrap=doc.findall(_add_ns('bootstrapInfo'))[0]
            else:
                print 'found bootstrap with id',bootstrap
            #print 'bootstrap',bootstrap
            

            bootstrapURL1=''
            try:
                bootstrapURL1=bootstrap.attrib['url']
            except: pass

            bootstrapURL=''
            bootstrapData=None
            queryString=None

            if bootstrapURL1=='':
                bootstrapData=base64.b64decode(doc.findall(_add_ns('bootstrapInfo'))[0].text)
                #
            else:
                from urlparse import urlparse
                queryString = urlparse(url).query
                print 'queryString11',queryString
                if len(queryString)==0: queryString=None
                
                if queryString==None or '?'  in bootstrap.attrib['url']:
                   
                    bootstrapURL = join(man_url,bootstrap.attrib['url'])# take out querystring for later
                    queryString = urlparse(bootstrapURL).query
                    print 'queryString override',queryString
                    if len(queryString)==0: 
                        queryString=None
                        if len(self.auth)>0:
                            bootstrapURL+='?'+self.auth
                            queryString=self.auth#self._pv_params('',self.auth20)#not in use
                        elif len(self.auth20)>0:
                            
                            queryString=self._pv_params(self.swf,self.auth20)
                            bootstrapURL+='?'+queryString
                else:
                    print 'queryString!!',queryString
                    bootstrapURL = join(man_url,bootstrap.attrib['url'])+'?'+queryString
                    if len(self.auth)>0:
                        authval=self.auth#self._pv_params('',self.auth20)#not in use
                        bootstrapURL = join(man_url,bootstrap.attrib['url'])+'?'+authval
                        queryString=authval
                    elif len(self.auth20)>0:
                        authval=self._pv_params(self.swf,self.auth20)#requires swf param
                        bootstrapURL = join(man_url,bootstrap.attrib['url'])+'?'+authval
                        queryString=authval
                        
            print 'bootstrapURL',bootstrapURL
            if queryString==None:
                queryString=''
            self.bootstrapURL=bootstrapURL
            self.queryString=queryString
            self.bootstrap, self.boot_info, self.fragments_list,self.total_frags=self.readBootStrapInfo(bootstrapURL,bootstrapData)
            self.init_done=True
            return True
        except:
            traceback.print_exc()
        return False

    def readAKKey(self, data):
        messageKeyExists=False
        key=""
        firstByte=ord(data[0])
        pos=1
        returnIV=None
        if firstByte==12: #version12
            pos+=4+4+2+1;
#            print 'indeedddd',firstByte
#            print 'data',repr(data)
            messageByte=ord(data[pos])
            pos+=1
            messageKeyExists=(messageByte & 4) > 0;
            messageIV=(messageByte & 2) > 0;
            if messageIV:
               pos+=16
#               print 'IV exists'
            if messageKeyExists:
#                print 'Message Key exists!!!'
                returnIV=data[pos-16:pos]
                d = str(data[pos]);
                pos+=1
                key = d;
                while(d != '\x00'):
                    d = str(data[pos]);
                    pos+=1
                    if d != '\x00':
                        key+= d;
        else:
            print 'SOMETHING WRONG.... got other than 12'
            print 1/0#shouldn't come where
        return messageKeyExists, key,pos,returnIV
    def getFrames(self,box_data, remainingdata):
        frames=[]
        KeepProcessing = False;
        currentStep= 0;
        tagLen = 0;
        if(box_data):
            if remainingdata and len(remainingdata)>0:
                box_data=remainingdata+box_data
                remainingdata=None
           
        lookForTagStart = 0;
        KeepProcessing = True;
        while(KeepProcessing and lookForTagStart<len(box_data)):
            currentStep = ord(box_data[lookForTagStart]);
            tagLen = ord(box_data[lookForTagStart + 1]) << 16 | ord(box_data[lookForTagStart + 2]) << 8 | ord(box_data[lookForTagStart + 3]) & 255;

                                
            nextTag = lookForTagStart + 11 + tagLen + 4
            if (nextTag > len(box_data) and currentStep > 0):
                remainingdata = [];
                remainingdata=box_data[lookForTagStart:]
                KeepProcessing = False;
          
            elif (currentStep > 0):
                chunk = []
                chunk=box_data[lookForTagStart:lookForTagStart+tagLen + 11 + 4]
                frames.append((1,chunk))
           
            elif (currentStep == 0):
                KeepProcessing = False;
            #if nextTag==len(box_data):
            #    KeepProcessing=False
           
            #print nextTag, len(box_data)
            lookForTagStart = nextTag;
        return frames,remainingdata
    
#    #def AES(self,key):
#        return Rijndael(key, keySize=16, blockSize=16, padding=padWithPadLen())

#    def AES_CBC(self,key):
#        return CBC(blockCipherInstance=AES(key))
        
    def addBytesToOutput(self,prefix,data,post,segmentid,buffer):
        dataLen=0
        if data and len(data)>0:
            dataLen=len(data)
            #print 'Incomming',repr(prefix)
            prefix=list(prefix)
            prefix[3]=chr(dataLen & 255)
            prefix[2]=chr(dataLen >> 8 & 255);
            prefix[1]=chr(dataLen >> 16 & 255);
            #print repr(prefix)
            prefix=''.join(prefix)
            #print repr(prefix)
        #print len(prefix) 
        finalArray=prefix
        if data and len(data)>0:
            finalArray+=data
        if post and len(post):
            finalArray+=post
#        with open("c:\\temp\\myfile.mp4", 'a+b') as output:
#            output.write(finalArray)
        lenReturned=len(finalArray)
        buffer.write(finalArray)
        buffer.flush()
        return lenReturned
        
    def keep_sending_video(self,dest_stream, segmentToStart=None, totalSegmentToSend=0):
        try:
            self.status='download Starting'            
            self.downloadInternal(self.url,dest_stream,segmentToStart,totalSegmentToSend)
        except: 
            traceback.print_exc()
        try:
            akhds.cleanup()                                    
        except:pass
        self.status='finished'
            
    def downloadInternal(self,url,dest_stream ,segmentToStart=None,totalSegmentToSend=0):
        global F4Mversion
        try:
            #dest_stream =  self.out_stream
            queryString=self.queryString
            print 'segmentToStart',segmentToStart
            if self.live or segmentToStart==0 or segmentToStart==None:
                print 'writing metadata'#,len(self.metadata)
                self._write_flv_header(dest_stream, self.metadata)
                dest_stream.flush()
            #elif segmentToStart>0 and not self.live:
            #    self._write_flv_header2(dest_stream)
            #    dest_stream.flush()
            
            url=self.url
  
            bootstrap, boot_info, fragments_list,total_frags=(self.bootstrap, self.boot_info, self.fragments_list,self.total_frags)
            print  boot_info, fragments_list,total_frags
            self.status='bootstrap done'


            self.status='file created'
            self.downloaded_bytes = 0
            self.bytes_in_disk = 0
            self.frag_counter = 0
            start = time.time()


            frags_filenames = []
            self.seqNumber=0
            if segmentToStart and  not self.live :
                self.seqNumber=segmentToStart
                if   self.seqNumber>=total_frags:
                    self.seqNumber=total_frags-1
            #for (seg_i, frag_i) in fragments_list:
            #for seqNumber in range(0,len(fragments_list)):
            self.segmentAvailable=0
            frameSent=0
            keyValue=""
            keyData=None
            firstPacket=True
            remainingFrameData=None
            decrypter=None
            errors=0
            file=0
            lastIV=None
            AKSession=None
            
            while True:
            
                #if not self.live:
                #    _write_flv_header2
                try:    
                    if self.g_stopEvent.isSet():
                        return
                except: pass
                seg_i, frag_i=fragments_list[self.seqNumber]
                self.seqNumber+=1
                frameSent+=1
                name = u'Seg%d-Frag%d' % (seg_i, frag_i)
                #print 'base_url',base_url,name
                if AKSession:
                    name+=AKSession
                url = self.base_url + name

                if queryString and '?' not in url:
                    url+='?'+queryString
                elif '?' in self.base_url:
                    url = self.base_url.split('?')[0] + name+'?'+self.base_url.split('?')[1]
                #print(url),base_url,name
                #frag_filename = u'%s-%s' % (tmpfilename, name)
                #success = dl._do_download(frag_filename, {'url': url})
                print 'downloading....',url
                success=False
                urlTry=0
                while not success and urlTry<5:
                    success = self.getUrl(url,True)
                    if not success: xbmc.sleep(300)
                    urlTry+=1
                print 'downloaded',not success==None,url
                if not success:
                    return False
                #with open(frag_filename, 'rb') as down:
                
                if 1==1:
                    down_data = success#down.read()
                    reader = FlvReader(down_data)
                    while True:
                        _, box_type, box_data = reader.read_box_info()
                        print  'box_type',box_type,len(box_data)
                        #if box_type == b'afra':
                        #    dest_stream.write(box_data)
                        #    dest_stream.flush()
                        #    break
                            
                        if box_type == b'mdat':
                            isDrm=True if ord(box_data[0])&1 else False
                            boxlength=len(box_data)
                            seglen=0
                            file+=1
#                            if file>6: print 1/0
                            skip=False
                            doDecrypt=False
#                            print 'first byte',repr(box_data[0]),'kk'
                            
                            isAkamaiEncrypted=True if ord(box_data[0])==11 or ord(box_data[0])==10  else False
                            if isAkamaiEncrypted:
#                                print 'Total MDAT count',len(box_data), len(box_data)%16

                                _loc8_ = ord(box_data[1]) << 16 | ord(box_data[2]) << 8 | ord(box_data[3]) & 255;
                                _loc9_ = box_data[11:11+_loc8_]
#                                print 'this is encrypted',len(_loc9_),_loc8_,repr(box_data[1:70])
                                keyExists,Key,dataread,lastIV=self.readAKKey(_loc9_)
                                if keyExists:
#                                    print 'key exists and its len is ',_loc8_,repr(Key)
                                    doDecrypt=True
                                    keyValueNew=Key.split('key_')[1]
#                                    print 'previous key is'+keyValue,'new key is',keyValueNew
                                    if keyValue=="":
                                        keyValue="_"+keyValueNew
                                        AKSession=keyValue
                                        keyurl = self.keybase_url +keyValueNew
                                        
                                        if queryString and '?' not in keyurl:
                                            keyurl+='?'+queryString+'&guid=CHRLRCMRHGUD'
                                        print 'the key url is ',keyurl,'thanks'
                                        keyData=self.getUrl(keyurl,False)
                                        skip=False
                                        firstPacket=True
                                        
                                    elif not keyValue=="_"+keyValueNew:
                                        keyValue="_"+keyValueNew#take new key
                                        AKSession=keyValue
                                        keyurl = self.keybase_url +keyValueNew
                                        if queryString and '?' not in keyurl:
                                            keyurl+='?'+queryString+'&guid=CHRLRCMRHGUD'
                                        keyData=self.getUrl(keyurl,False)
                                        firstPacket=True
                                        #todo decryptit! and put it in box_data
                            #print 'before skip'
                            if skip:
                                break;
                            if keyData:
#                                print 'key data is',repr(keyData),len(keyData)
                                #do decrypt here. frame by frame
                                #now generate frames
                                #put remaining in remaining
                                #for each frame decrypt and write and flush
                                try:
                                    frames=[]
#                                    print 'before frames data', repr(box_data[0:70])
                                    frames,remainingFrameData=self.getFrames(box_data,remainingFrameData)
#                                    print 'after frames data first frame', repr(frames[0][0:70])
                                    #print 'frames',frames
                                    cleanup=False

                                    for frame in frames:
                                        
                                        data=frame[1]                                            
                                        datalen=ord(data[1]) << 16 | ord(data[2]) << 8 | ord(data[3]) & 255;
                                        preFrame=len(data)
                                        #print 'samp>',len(data),datalen,ord(data[0]) ,'<samp'
                                        if firstPacket:
                                            firstPacket=False
#                                            data=data[0:datalen]
                                            #print 'first>',len(data),ord(data[0]),datalen,'<first'
#                                        else:
                                        if 1==1:
                                            #if not not key frame then decrypt else
                                            firstByte=ord(data[0])
                                            frameHeader=data[:11]
                                            framePad=data[11 + datalen:11 + datalen+4];



                                            if firstByte==10 or firstByte==11:

                                                if firstByte==10: 
                                                    frameHeader = list(frameHeader)
                                                    frameHeader[0]=chr(8)
                                                    frameHeader=''.join(frameHeader)
                                                    
                                                if firstByte==11: 
                                                    frameHeader = list(frameHeader)
                                                    frameHeader[0]=chr(9)
                                                    frameHeader=''.join(frameHeader)
                                                data=data[11:11+datalen]
                                                #print 'sub>',len(data),firstByte,datalen,datalen%16,len(data)%16 ,'<sub'
                                                keyExistsNew,KeyNew,dataread,ignoreIV=self.readAKKey(data)
#                                                print 'dataread',dataread,keyExistsNew,KeyNew,ignoreIV

                                                try:    
                                                    akhds.init()
                                                    data=akhds.tagDecrypt(data,keyData)
                                                    

                                                except:
                                                    print 'decryption error'
                                                    errors+=1
                                                    traceback.print_exc()
                                                    if errors>10: print 1/0
                                                    
                                                    
#                                                print 'pre return size %d, %d %d'%(len(frameHeader),len(data), len(framePad))
                                                seglen1=self.addBytesToOutput(frameHeader,data,framePad,1,dest_stream)
                                                seglen+=seglen1
#                                                print 'pre frame %d, after %d'%(preFrame,seglen1)
                                            else:
                                                print 'hmm no 10 or 11?'
#                                                print 'pre return size %d, %d %d'%(len(frameHeader),len(data), len(framePad))
                                                seglen1=self.addBytesToOutput(frameHeader,None,None,1,dest_stream)
                                                seglen+=seglen1
#                                                print 'pre frame %d, after %d'%(preFrame,seglen1)
                                            #est_stream.write(data)
                                            #dest_stream.flush()
                                            #dest_stream.write(self.decryptData(data,keyData))
                                            #dest_stream.flush() 
                                except:
                                    print traceback.print_exc()
                                    self.g_stopEvent.set()     
                                    

                            else:
                                dest_stream.write(box_data)
                                dest_stream.flush()
                            print 'box length is %d and seg total is %d'%(boxlength,seglen)
                            break                            
                            # Using the following code may fix some videos, but 
                            # only in mplayer, VLC won't play the sound.
                            # mdat_reader = FlvReader(box_data)
                            # media_type = mdat_reader.read_unsigned_char()
                            # while True:
                            #     if mdat_reader.read_unsigned_char() == media_type:
                            #         if mdat_reader.read_unsigned_char() == 0x00:
                            #             break
                            # dest_stream.write(pack('!B', media_type))
                            # dest_stream.write(b'\x00')
                            # dest_stream.write(mdat_reader.read())
                            # break
                self.status='play'
                if self.seqNumber==len(fragments_list) or (totalSegmentToSend>0 and frameSent==totalSegmentToSend):
                    if not self.live:
                        break
                    self.seqNumber=0
                    #todo if the url not available then get manifest and get the data again
                    total_frags=None
                    try:
                        bootstrap, boot_info, fragments_list,total_frags=self.readBootStrapInfo(self.bootstrapURL,None,updateMode=True,lastSegment=seg_i, lastFragement=frag_i)
                    except: 
                        traceback.print_exc()
                        pass
                    if total_frags==None:
                        break

            del self.downloaded_bytes
            del self.frag_counter
        except:
            traceback.print_exc()
            return
    def getBootStrapWithId (self,BSarray, id):
        try:
            for bs in BSarray:
                print 'compare val is ',bs.attrib['id'], 'id', id
                if bs.attrib['id']==id:
                    print 'gotcha'
                    return bs
        except: pass
        return None
    
    def readBootStrapInfo(self,bootstrapUrl,bootStrapData, updateMode=False, lastFragement=None,lastSegment=None):

        try:
            retries=0
            while retries<=10:

                try:    
                    if self.g_stopEvent.isSet():
                        print 'event is set. returning'
                        return
                except: pass

                if bootStrapData==None:
                    bootStrapData =self.getUrl(bootstrapUrl)

                if bootStrapData==None:
                    retries+=1
                    continue
                #print 'bootstrapData',len(bootStrapData)
                bootstrap = bootStrapData#base64.b64decode(bootStrapData)#doc.findall(_add_ns('bootstrapInfo'))[0].text)
                #print 'boot stream read done'
                boot_info,self.live = read_bootstrap_info(bootstrap)
                #print 'boot_info  read done',boot_info
                newFragement=None
                if not lastFragement==None:
                    newFragement=lastFragement+1
                fragments_list = build_fragments_list(boot_info,newFragement,self.live)
                total_frags = len(fragments_list)
                #print 'fragments_list',fragments_list, newFragement
                #print lastSegment
                if updateMode and (len(fragments_list)==0 or (  newFragement and newFragement>fragments_list[0][1])):
                    #todo check lastFragement to see if we got valid data
                    print 'retrying......'
                    bootStrapData=None
                    retries+=1
                    xbmc.sleep(2000)
                    continue
                return bootstrap, boot_info, fragments_list,total_frags
        except:
            traceback.print_exc()
    

        

    
    def _pv_params(self, pvswf, pv):
        """Returns any parameters needed for Akamai HD player verification.

        Algorithm originally documented by KSV, source:
        http://stream-recorder.com/forum/showpost.php?p=43761&postcount=13
        """
        #return pv;
        #pv="ZXhwPTE0NDAxNTUyODJ+YWNsPSUyZip+ZGF0YT1wdmMsc35obWFjPWMyZjk4MmVjZjFjODQyM2IzZDkxMzExMjNmY2ExN2U4Y2UwMjU4NWFhODg3MWFjYzM5YmI0MmVlNTYxYzM5ODc="
#        pv="ZXhwPTE0NDAzMjc3ODF+YWNsPSUyZip+ZGF0YT1wdmMsc35obWFjPTYyYTE2MzU2MTNjZTI4ZWI2MTg0MmRjYjFlZTZlYTYwYTA5NWUzZDczNTQ5MTQ1ZDVkNTc0M2M2Njk5MDJjNjY="
#        pv="ZXhwPTE0Mzk2MDgzMTl+YWNsPSUyZip+ZGF0YT1wdmMsc35obWFjPTExYTJiNzQ4NjQyYmY1M2VlNzk5MzhhNTMzNjc1MTAzZjk2NWViOGVhODY4MzUwODkwZGM1MjVmNjI3ODM4MzQ="
            
        try:
            data, hdntl = pv.split(";")
        except ValueError:
            data = pv
            hdntl = ""
        print 'DATA IS',data
        print 'hdntl IS',hdntl
        if data=="": return hdntl
        first_stage_msg=binascii.unhexlify('056377146640142763057567157640125041016376130175171220177717044510157134116364123221072012122137150351003442036164015632157517073355151142067436113220106435137171174171127530157325044270025004')
        
        first_stage_key=data

        hash_data=""
        if pvswf is None:
            print 'swf required for pv2 decryption'
            pvswf=""

        if pvswf.startswith('http'):
            import hashlib            
            h=hashlib.md5()
            h.update(pvswf)
            hashkey=""+str(h.hexdigest())
            existinghash=str(selfAddon.getSetting(hashkey))
            #print 'existinghash',hashkey
            #print 'existinghashval',existinghash
            if len(existinghash)==0:
                swf = self.getUrl(pvswf,False)
                hash = hashlib.sha256()
                hash.update(self.swfdecompress(swf))
                hash = base64.b64encode(hash.digest()).decode("ascii")
                #print hashkey,hash
                selfAddon.setSetting(hashkey, str(hash))
                #print 'getting back',str(selfAddon.getSetting(hashkey))
            else:
                hash=existinghash
                
            
        else:
            hash=pvswf # the incoming is the hash!
            
        print 'hash',hash
          
#        shouldhash="AFe6zmDCNudrcFNyePaAzAn/KRT5ES99ql4SNqldM2I="      
#        if shouldhash==hash:
#            print '**************HASH MATCH ********************'
#        else:
#            print '********* NOOOOOOOOOOOOOOOOOOOOTTTTTTTTTTTTTTTTT**********'
            
            
        second_stage_key = hmac.new(first_stage_key,first_stage_msg , sha256).digest()
#        second_stage_data=hash_data  #
        second_stage_data=base64.b64decode( hash)
        buffer="106,45,165,20,106,45,165,20,38,45,165,87,11,98,228,14,107,89,233,25,101,36,223,76,97,28,175,18,23,86,164,6,1,56,157,64,123,58,186,100,54,34,184,14,3,44,164,20,106,6,222,84,122,45,165,20,106,28,196,84,122,111,183,84,122,45,165,20,106,45,165,20,106,45,165,20,106,45,165,20,106,45,165,20,106,45,165,20,106,45,165,20,106,45,165,20" 
        buffer=buffer.split(',');
        second_stage_data+=chr(int(buffer[len(second_stage_data)]))
#        print len(second_stage_data),repr(second_stage_data)

        third_stage_key= hmac.new(second_stage_key, second_stage_data, sha256).digest()
        

        #hash=shouldhash
        msg = "exp=9999999999~acl=%2f%2a~data={0}!{1}".format(data, hash)
        
        auth = hmac.new(third_stage_key, msg.encode("ascii"), sha256)
        pvtoken = "{0}~hmac={1}".format(msg, auth.hexdigest())

        # The "hdntl" parameter can be accepted as a cookie or passed in the
        # query string, but the "pvtoken" parameter can only be in the query
        # string
        print 'pvtoken',pvtoken
        
        params=urllib.urlencode({'pvtoken':pvtoken})+'&'+hdntl+'&hdcore=2.11.3'
        params=params.replace('%2B','+')
        params=params.replace('%2F','/')
        print params
        return params
        
    def swfdecompress(self,data):
        if data[:3] == b"CWS":
            data = b"F" + data[1:8] + zlib.decompress(data[8:])

        return data

        
        