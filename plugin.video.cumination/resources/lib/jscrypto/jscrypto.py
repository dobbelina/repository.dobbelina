import hashlib
import base64
import six
from . import pyaes
from .pkcs7 import PKCS7Encoder
import os


def evpKDF(
        passwd,
        salt,
        key_size=8,
        iv_size=4,
        iterations=1,
        hash_algorithm="md5"):
    target_key_size = key_size + iv_size
    derived_bytes = six.ensure_binary("")
    number_of_derived_words = 0
    block = None
    hasher = hashlib.new(hash_algorithm)
    while number_of_derived_words < target_key_size:
        if block is not None:
            hasher.update(block)

        hasher.update(passwd)
        hasher.update(salt)
        block = hasher.digest()
        hasher = hashlib.new(hash_algorithm)

        for i in range(1, iterations):
            hasher.update(block)
            block = hasher.digest()
            hasher = hashlib.new(hash_algorithm)

        derived_bytes += block[0: min(len(block), (target_key_size - number_of_derived_words) * 4)]

        number_of_derived_words += len(block) / 4

    return {
        "key": derived_bytes[0: key_size * 4],
        "iv": derived_bytes[key_size * 4:]
    }


def encode(plaintext, passphrase, saltsize=8):
    salt = os.urandom(saltsize)
    data = evpKDF(six.ensure_binary(passphrase), salt)
    decryptor = pyaes.new(data['key'], pyaes.MODE_CBC, IV=data['iv'])
    plaintext = PKCS7Encoder().encode(plaintext)
    enctext = decryptor.encrypt(plaintext)
    return base64.b64encode("Salted__" + salt + enctext)

# ''if salt is provided, it should be string
# ciphertext is base64 and passphrase is string


def decode(ciphertext, passphrase, salt=None):
    ciphertext = base64.b64decode(ciphertext)
    if not salt:
        salt = ciphertext[8:16]
        ciphertext = ciphertext[16:]
    data = evpKDF(six.ensure_binary(passphrase), salt)
    decryptor = pyaes.new(data['key'], pyaes.MODE_CBC, IV=data['iv'])
    d = decryptor.decrypt(ciphertext)
    return PKCS7Encoder().decode(d.decode())
