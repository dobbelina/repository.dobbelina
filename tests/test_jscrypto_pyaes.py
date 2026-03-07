import pytest
import base64
import os
import six
from resources.lib.jscrypto import jscrypto, pyaes, pkcs7

def test_pkcs7_padding():
    encoder = pkcs7.PKCS7Encoder()
    text = b"Hello World"
    padded = encoder.encode(text)
    assert len(padded) % 16 == 0
    decoded = encoder.decode(padded)
    assert decoded == text

def test_evpkdf():
    passwd = b"password"
    salt = b"saltsalt"
    result = jscrypto.evpKDF(passwd, salt, key_size=8, iv_size=4)
    assert "key" in result
    assert "iv" in result
    assert len(result["key"]) == 32
    assert len(result["iv"]) == 16

def test_jscrypto_encode_decode():
    plaintext = "This is a secret message"
    passphrase = "super-secret-password"
    
    # Test encode
    encrypted = jscrypto.encode(plaintext, passphrase)
    assert isinstance(encrypted, bytes)
    
    # Test decode
    decrypted = jscrypto.decode(encrypted, passphrase)
    assert decrypted == plaintext

def test_jscrypto_decode_with_salt():
    plaintext = "Another secret"
    passphrase = "password123"
    salt = b"12345678"
    
    # Manually construct a raw ciphertext (no Salted__ header) to test explicit salt
    data = jscrypto.evpKDF(passphrase.encode(), salt)
    decryptor = pyaes.new(data["key"], pyaes.MODE_CBC, IV=data["iv"])
    padded_plaintext = pkcs7.PKCS7Encoder().encode(plaintext)
    enctext = decryptor.encrypt(padded_plaintext)
    ciphertext = base64.b64encode(enctext)
    
    # Decode with explicit salt
    decrypted = jscrypto.decode(ciphertext, passphrase, salt=salt)
    assert decrypted == plaintext

def test_pyaes_invalid_key_size():
    with pytest.raises(ValueError, match="Key length must be 16, 24 or 32 bytes"):
        pyaes.AES(b"too-short")

def test_pyaes_ecb_mode():
    key = b"16bytekey1234567"
    cipher = pyaes.new(key, pyaes.MODE_ECB)
    plaintext = b"16 bytes exactly"
    
    encrypted = cipher.encrypt(plaintext)
    assert len(encrypted) == 16
    assert encrypted != plaintext
    
    decrypted = cipher.decrypt(encrypted)
    assert decrypted == plaintext

def test_pyaes_ecb_invalid_length():
    key = b"16bytekey1234567"
    cipher = pyaes.new(key, pyaes.MODE_ECB)
    with pytest.raises(ValueError, match="Plaintext length must be multiple of 16"):
        cipher.encrypt(b"too short")
    with pytest.raises(ValueError, match="Plaintext length must be multiple of 16"):
        cipher.decrypt(b"too short")

def test_pyaes_cbc_mode():
    key = b"16bytekey1234567"
    iv = b"16byteiv12345678"
    cipher = pyaes.new(key, pyaes.MODE_CBC, IV=iv)
    plaintext = b"16 bytes exactly" * 2
    
    encrypted = cipher.encrypt(plaintext)
    assert len(encrypted) == 32
    assert encrypted != plaintext
    
    # Reset cipher for decryption (or create new one with same IV)
    cipher_dec = pyaes.new(key, pyaes.MODE_CBC, IV=iv)
    decrypted = cipher_dec.decrypt(encrypted)
    assert decrypted == plaintext

def test_pyaes_cbc_no_iv():
    key = b"16bytekey1234567"
    with pytest.raises(ValueError, match="CBC mode needs an IV value!"):
        pyaes.new(key, pyaes.MODE_CBC)

def test_pyaes_cbc_invalid_length():
    key = b"16bytekey1234567"
    iv = b"16byteiv12345678"
    cipher = pyaes.new(key, pyaes.MODE_CBC, IV=iv)
    with pytest.raises(ValueError, match="Plaintext length must be multiple of 16"):
        cipher.encrypt(b"too short")
    with pytest.raises(ValueError, match="Ciphertext length must be multiple of 16"):
        cipher.decrypt(b"too short")

def test_pyaes_invalid_mode():
    key = b"16bytekey1234567"
    with pytest.raises(NotImplementedError):
        pyaes.new(key, mode=999)

def test_pyaes_different_key_sizes():
    # 24-byte key (AES-192)
    key24 = b"24bytekey123456789012345"
    cipher24 = pyaes.new(key24, pyaes.MODE_ECB)
    plaintext = b"16 bytes exactly"
    assert cipher24.decrypt(cipher24.encrypt(plaintext)) == plaintext
    
    # 32-byte key (AES-256)
    key32 = b"32bytekey12345678901234567890123"
    cipher32 = pyaes.new(key32, pyaes.MODE_ECB)
    assert cipher32.decrypt(cipher32.encrypt(plaintext)) == plaintext

def test_galois_multiply():
    assert pyaes.galois_multiply(0, 0) == 0
    assert pyaes.galois_multiply(1, 1) == 1
    assert pyaes.galois_multiply(0x57, 0x13) == 0xfe # Example from AES spec

def test_pkcs7_corrupt_padding():
    encoder = pkcs7.PKCS7Encoder()
    # Padded block where the last byte says the padding is 20 bytes (larger than block size 16)
    corrupt_padded = b"Hello World" + b"\x14" * 5 
    with pytest.raises(ValueError, match="Input is not padded or padding is corrupt"):
        encoder.decode(corrupt_padded)

def test_evpkdf_iterations():
    passwd = b"password"
    salt = b"saltsalt"
    # Test with iterations > 1 to hit the iteration branch
    result = jscrypto.evpKDF(passwd, salt, key_size=8, iv_size=4, iterations=3)
    assert len(result["key"]) == 32
    assert len(result["iv"]) == 16
