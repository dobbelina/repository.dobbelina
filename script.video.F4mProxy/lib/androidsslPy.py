#! /usr/bin/python

from __future__ import with_statement

# ignobleepub.pyw, version 3.5
# modified by shani and adapted it for android

__license__ = 'GPL v3'

import sys
import os



class IGNOBLEError(Exception):
    pass

def _load_crypto_libcrypto():
    from ctypes import CDLL, POINTER, c_void_p, c_char_p, c_int, c_long, \
        Structure, c_ulong, create_string_buffer, cast
    from ctypes.util import find_library
    import ctypes


    libcrypto = ctypes.cdll.LoadLibrary("libcrypto.so")
    AES_MAXNR = 14

    c_char_pp = POINTER(c_char_p)
    c_int_p = POINTER(c_int)

    class AES_KEY(Structure):
        _fields_ = [('rd_key', c_long * (4 * (AES_MAXNR + 1))),
                    ('rounds', c_int)]
    AES_KEY_p = POINTER(AES_KEY)

    def F(restype, name, argtypes):
        func = getattr(libcrypto, name)
        func.restype = restype
        func.argtypes = argtypes
        return func

    AES_cbc_encrypt = F(None, 'AES_cbc_encrypt',
                        [c_char_p, c_char_p, c_ulong, AES_KEY_p, c_char_p,
                         c_int])
    AES_set_decrypt_key = F(c_int, 'AES_set_decrypt_key',
                            [c_char_p, c_int, AES_KEY_p])
    AES_cbc_encrypt = F(None, 'AES_cbc_encrypt',
                        [c_char_p, c_char_p, c_ulong, AES_KEY_p, c_char_p,
                         c_int])

    class AES(object):
        def __init__(self,userkey,iv):
            self._blocksize = len(userkey)
            self.iv=iv
            if (self._blocksize != 16) and (self._blocksize != 24) and (self._blocksize != 32) :
                raise IGNOBLEError('AES improper key used')
                return
            key = self._key = AES_KEY()
            rv = AES_set_decrypt_key(userkey, len(userkey) * 8, key)
            if rv < 0:
                raise IGNOBLEError('Failed to initialize AES key')

        def decrypt(self, data):
            out = create_string_buffer(len(data))
            ivcopy = create_string_buffer(self.iv)
            rv = AES_cbc_encrypt(data, out, len(data), self._key, ivcopy , 0)
            if rv == 0:
                raise IGNOBLEError('AES decryption failed')
            return out.raw

    return AES