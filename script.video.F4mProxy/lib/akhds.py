import base64
from struct import unpack, pack
import sys
import io
import os
import time
import itertools
import urllib2,urllib
import traceback
import urlparse
import posixpath
import re
import hmac
import hashlib
import binascii 
import zlib
from hashlib import sha256, sha1,md5,sha512
import cookielib
import array
import socket
#from multiprocessing.connection import Client
from subprocess import Popen, PIPE
import subprocess
import struct
import pickle
import xbmc
import binascii


USEDec=0
initDone=False


def init():
#    global initDone, androidClient,USEDec,popenProcess,authkey,portNumber
#    if initDone: return
    initDone=True

try:
    from Crypto.Cipher import AES

    USEDec=1 ## 1==crypto 2==local, local pycrypto
    print 'using pycrypt wooot woot'
except:
    print 'pycrypt not available trying other options'
    print traceback.print_exc()
    USEDec=3 ## 1==crypto 2==local, local pycrypto
    #check if its android
    if xbmc.getCondVisibility('System.Platform.Android'):
        try:
            import androidsslPy
            AES=androidsslPy._load_crypto_libcrypto()
            USEDec=2 ## android
            print 'using android ssllib woot woot'
        except: 
            print traceback.print_exc()
            print 'android copy not available'    
            from f4mUtils import python_aes
            print 'using slow decryption'  
    else:
        print 'using slow decryption'  
        from f4mUtils import python_aes


value_unsafe = '%+&;#'
VALUE_SAFE = ''.join(chr(c) for c in range(33, 127)
    if chr(c) not in value_unsafe)


def tagDecrypt(data,key):
    enc_data=data#binascii.unhexlify(enc_data)
    enc_key=key#binascii.unhexlify(enc_key)

#    print 'DataIn',binascii.hexlify(data)
#    print 'KeyIn',binascii.hexlify(key)
    

    keydatalen=0
    if 'key_' in enc_data[0:300]: #quick check?? need to find better way to predict offsets
        keydatalen=enc_data[0:300].find(chr(0),13+16)-(13+16)+1
       
       
#    print 'keydatalen',keydatalen       
    stage_4a_finaldataIndex=13+16+1+keydatalen  #?? dynamic calc req
    enc_data_index=stage_4a_finaldataIndex+32+40

    stage_4a_finaldata=enc_data[stage_4a_finaldataIndex:stage_4a_finaldataIndex+32]
    globalivIndex=13
    global_iv=enc_data[globalivIndex:globalivIndex+16]
#    print 'global  iv',binascii.hexlify(global_iv)

    stage_4a_data=enc_key+global_iv

#    print len (stage_4a_data)

    #??static data
    stage_4a_key=binascii.unhexlify("3b27bdc9e00fd5995d60a1ee0aa057a9f1416ed085b21762110f1c2204ddf80ec8caab003070fd43baafdde27aeb3194ece5c1adff406a51185eb5dd7300c058")
#    stage_4a_key=key#fixed


#    print 'stage_4a_key',binascii.hexlify(stage_4a_key),len(stage_4a_key)
#    print 'data',binascii.hexlify(stage_4a_data) ,len(stage_4a_data)

    stage_4a_key2 = hmac.new(stage_4a_key,stage_4a_data , sha1).digest()

    #stage_4a_key2+=chr(0)*12
#    print 'first HMAC ',binascii.hexlify(stage_4a_key2) ,len(stage_4a_key2)



    #??static data
    stage_4a_data2=binascii.unhexlify("d1ba6371c56ce6b498f1718228b0aa112f24a47bcad757a1d0b3f4c2b8bd637cb8080d9c8e7855b36a85722a60552a6c00")

#    print 'stage_4a_data2',binascii.hexlify(stage_4a_data2),len(stage_4a_data2)
    
    
    auth = hmac.new(stage_4a_key2,stage_4a_data2 , sha1).digest()
    stage_4a_finalkey=auth[:16]

     
#    print stage_4a_finalkey, repr(stage_4a_finalkey), len(stage_4a_finalkey)
#    print binascii.hexlify(stage_4a_finalkey)
#    print 'first end HMAC >>>>>>>>>>>>>>>>>>>>>>>>>'
#    print 'final data',binascii.hexlify(stage_4a_finaldata)
#    print 'final iv',binascii.hexlify(global_iv)
#    print 'final key',binascii.hexlify(stage_4a_finalkey)





    #import  pyaes   
#    de =AES.new(stage_4a_finalkey, AES.MODE_CBC, global_iv)
#    # pyaes.new(stage_4a_finalkey, pyaes.MODE_CBC, IV=global_iv)



    de=getDecrypter(stage_4a_finalkey,global_iv )
    cc=global_iv
    decresp=decryptData(de,stage_4a_finaldata,cc)
    stage_4a_finaloutput=decresp[:20]


    enc_size=stage_4a_finaloutput[:4]
    enc_size=int(struct.unpack('>I',enc_size)[0])
#    print stage_4a_finaloutput
    stage_4a_finaloutput=stage_4a_finaloutput[4:4+16]
#    print 'final',binascii.hexlify(stage_4a_finaloutput)

    stage_4_key=stage_4a_key
    stage_5_key = hmac.new(stage_4_key,stage_4a_finaloutput , sha1).digest()

#    print 'stage_4_hmac ',binascii.hexlify(stage_5_key)


    #??static data
    stage_5_data=binascii.unhexlify("d1ba6371c56ce6b498f1718228b0aa112f24a47bcad757a1d0b3f4c2b8bd637cb8080d9c8e7855b36a85722a60552a6c01")
    
#    print 'stage_5_data',binascii.hexlify(stage_5_data),len(stage_5_data)
    
    stage_5_hmac = hmac.new(stage_5_key,stage_5_data , sha1).digest()

#    print 'stage_5_hmac ',binascii.hexlify(stage_5_hmac), len(stage_5_hmac)

    stage_5_hmac=stage_5_hmac[:16]

#    print 'stage_5_hmac trmimed ',binascii.hexlify(stage_5_hmac), len(stage_5_hmac)

#    de =AES.new(stage_5_hmac, AES.MODE_CBC, global_iv)
#    #de = pyaes.new(stage_5_hmac, pyaes.MODE_CBC, IV=global_iv)
    de2=getDecrypter(stage_5_hmac,global_iv )
    enc_data_todec=""
    if enc_size>0:
        enc_data_todec=enc_data[enc_data_index:enc_data_index+enc_size]
    unEncdata=enc_data[enc_data_index+enc_size:]

    decData=""
    if len(enc_data_todec)>0:
#        print 'enc_data_todec',binascii.hexlify(enc_data_todec), len(enc_data_todec)
        #enc_data_remaining
        decData=decryptData(de2,enc_data_todec,global_iv)
        
    decData+=unEncdata
    if 1==2 and len(decData)<300:
        print 'enc data received',binascii.hexlify(enc_data_todec), len(enc_data_todec)
        print 'iv received',binascii.hexlify(global_iv), len(global_iv)
        print 'key received',binascii.hexlify(stage_5_hmac), len(stage_5_hmac)
        print 'data received',binascii.hexlify(data), len(data)
        print 'final return',binascii.hexlify(decData), len(decData)
    return decData

## function to create the cbc decrypter object
def getDecrypter(key,iv):
    global USEDec
    if USEDec==1:
        enc =AES.new(key, AES.MODE_CBC, iv)
    elif USEDec==3:
        ivb=array.array('B',iv)
        keyb= array.array('B',key)
        enc=python_aes.new(keyb, 2, ivb)
    else:
        enc =androidsslPy._load_crypto_libcrypto()
        enc = enc(key, iv)
    return  enc       

## function to create the cbc decrypter    
def decryptData(d,encdata,iv):
#    print 'start'
    global USEDec
    if USEDec==1 or USEDec==2:
        data =d.decrypt(encdata)
#        print binascii.hexlify(data)
    elif USEDec==3:
        chunkb=array.array('B',encdata)
        data = d.decrypt(chunkb)
        data="".join(map(chr, data))
#    print 'end'
    return  data       
    
def cleanup():
    try:
        if USEDec==2:
            print 'doing android cleanup'
            #AndroidCrypto.teardown()
            #print 'android cleanup'
    except:
        pass


#enc_data="0c0000000055e975370000ffff2cc98372afe2d8418ed47c36b7cc5b2c2f7a2f5353315f31403330393730312f6b65795f415142534c5a684350767738787a64313656564965484f47567a36764c727a37436d47644f55675a47443571563350684647637a344333727372583955473372333732625030592b00017147a7c17c3fb29ba210dd6fbb542d689ee6c1578635b7545358a260ddb808ac00000000000000000000000000000000000000003f106033e78c4842f66e12489d7d0ec974cb4780a912366394fe3eb1eaa6f1f9f7de4ed81d3ec642fe9c42c7887962b4d62f9969bbe8e1102a3bedf6f1f19fcab6f073d36801000428f96bc8"
#byte[] arrOutput = { 0x0C, 0x00, 0x00, 0x00, 0x00, 0x55, 0xEA, 0x65, 0x7E, 0x00, 0x00, 0xFF, 0xFF, 0xE9, 0x86, 0x40, 0x1A, 0x2B, 0xDB, 0x60, 0x36, 0xEC, 0x24, 0xB3, 0x47, 0xA3, 0xF4, 0x91, 0x40, 0x2F, 0x7A, 0x2F, 0x41, 0x45, 0x54, 0x4E, 0x2D, 0x48, 0x69, 0x73, 0x74, 0x6F, 0x72, 0x79, 0x5F, 0x56, 0x4D, 0x53, 0x2F, 0x42, 0x52, 0x41, 0x4E, 0x44, 0x5F, 0x54, 0x48, 0x43, 0x5F, 0x4F, 0x43, 0x48, 0x41, 0x5F, 0x31, 0x37, 0x36, 0x38, 0x34, 0x37, 0x5F, 0x53, 0x46, 0x4D, 0x5F, 0x30, 0x30, 0x30, 0x5F, 0x32, 0x39, 0x39, 0x37, 0x5F, 0x31, 0x35, 0x5F, 0x32, 0x30, 0x31, 0x35, 0x30, 0x39, 0x30, 0x31, 0x5F, 0x30, 0x30, 0x5F, 0x53, 0x33, 0x5F, 0x2C, 0x34, 0x2C, 0x31, 0x38, 0x2C, 0x31, 0x33, 0x2C, 0x31, 0x30, 0x2C, 0x37, 0x2C, 0x32, 0x2C, 0x31, 0x2C, 0x30, 0x30, 0x2E, 0x6D, 0x70, 0x34, 0x2E, 0x63, 0x73, 0x6D, 0x69, 0x6C, 0x2F, 0x6B, 0x65, 0x79, 0x5F, 0x41, 0x51, 0x42, 0x63, 0x41, 0x54, 0x31, 0x51, 0x50, 0x68, 0x69, 0x44, 0x6B, 0x33, 0x35, 0x6C, 0x36, 0x6C, 0x56, 0x39, 0x56, 0x62, 0x54, 0x7A, 0x35, 0x56, 0x4C, 0x32, 0x31, 0x56, 0x61, 0x71, 0x76, 0x4F, 0x41, 0x38, 0x42, 0x79, 0x79, 0x32, 0x47, 0x31, 0x35, 0x68, 0x4C, 0x4D, 0x34, 0x65, 0x58, 0x48, 0x63, 0x54, 0x6D, 0x67, 0x70, 0x67, 0x7A, 0x67, 0x43, 0x5A, 0x34, 0x77, 0x44, 0x50, 0x55, 0x62, 0x6A, 0x48, 0x44, 0x5A, 0x31, 0x6E, 0x00, 0x01, 0xEF, 0x4E, 0x24, 0x89, 0x4B, 0x22, 0x08, 0x93, 0xDD, 0xD2, 0x9D, 0xA3, 0xD6, 0xBA, 0x3A, 0xB4, 0x98, 0x57, 0x84, 0x80, 0x7E, 0xD9, 0xA7, 0xA4, 0x49, 0x85, 0xCF, 0xA2, 0xAD, 0x4B, 0x22, 0xD9, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x48, 0x38, 0x73, 0xD0, 0xAB, 0x9F, 0xB7, 0x4C, 0x81, 0xEE, 0xCD, 0xD2, 0xB7, 0x87, 0xE2, 0x98, 0x96, 0xE8, 0x8A, 0x98, 0xC6, 0x4E, 0x79, 0xC9, 0x53, 0x3C, 0x8F, 0xDA, 0xDE, 0xEE, 0xF7, 0x84, 0x16, 0xC8, 0x4F, 0x75, 0xB4, 0x7B, 0x7C, 0xF8, 0x61, 0xA7, 0x2B, 0x54, 0xF3, 0x06, 0xD5, 0x3F, 0xEE, 0xDF, 0xF2, 0xD1, 0x60, 0x8F, 0x18, 0x32, 0x58, 0x01, 0x00, 0x05, 0x68, 0xE9, 0x33, 0x2C, 0x80, 0x00, 0x00, 0x01, 0x53, 0x0A, 0x00, 0x00, 0x6D, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x0C, 0x00, 0x00, 0x00, 0x00, 0x55, 0xEA, 0x65, 0x7E, 0x00, 0x00, 0xFF, 0xFB, 0xE9, 0x86, 0x40, 0x1A, 0x2B, 0xDB, 0x60, 0x36, 0xEC, 0x24, 0xB3, 0x47, 0xA3, 0xF4, 0x91, 0x40, 0x01, 0x7B, 0x4C, 0x44, 0x02, 0x0B, 0xD1, 0xBD, 0x24, 0xD1, 0x15, 0x35, 0xAA, 0x24, 0x67, 0x1B, 0x89, 0xA7, 0x70, 0xB7, 0xF6, 0xF5, 0x62, 0x1E, 0xCB, 0xDA, 0x7B, 0x44, 0x77, 0x29, 0xF0, 0x42, 0x30, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0xCE, 0x2E, 0x6C, 0x71, 0x3B, 0x79, 0x1D, 0x96, 0x0C, 0x49, 0x83, 0x94, 0x9A, 0xD0, 0x25, 0x0D, 0x3B, 0xD2, 0x68, 0xB7, 0xAF, 0x00, 0x11, 0x90, 0x56, 0xE5, 0x00, 0x00, 0x00, 0x00, 0x78, 0x0B, 0x00, 0x6D, 0xE3, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x0C, 0x00, 0x00, 0x00, 0x00, 0x55, 0xEA, 0x65, 0x7E, 0x00, 0x00, 0xFF, 0xFB, 0xE9, 0x86, 0x40, 0x1A, 0x2B, 0xDB, 0x60, 0x36, 0xEC, 0x24, 0xB3, 0x47, 0xA3, 0xF4 };
#enc_data=binascii.unhexlify(enc_data)
#enc_key="93ac1d5925eadd38f61fee4c321cc843"
#enc_key=binascii.unhexlify(enc_key)
    
#print 'final data',binascii.hexlify(tagDecrypt(enc_data,enc_key)    )