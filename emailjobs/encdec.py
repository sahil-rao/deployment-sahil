#!/usr/bin/python

from Crypto import Random
from Crypto.Cipher import AES
import hashlib

def generate_key(password, salt, iterations):
    assert iterations > 0
    key = password + salt
    for i in range(iterations):
        key = hashlib.sha256(key).digest()  
    with open('key1.pem', 'wb') as fo:
        fo.write(key)
    return key

def pad(s):
    return s + b"\0" * (AES.block_size - len(s) % AES.block_size)

def encrypt(message, key, key_size=256):
    message = pad(message)
    iv = Random.new().read(AES.block_size)
    cipher = AES.new(key, AES.MODE_CBC, iv)
    return key + iv + cipher.encrypt(message)

def decrypt(ciphertext):
    key = ciphertext[:32]
    iv = ciphertext[32:32 + AES.block_size]
    cipher = AES.new(key, AES.MODE_CBC, iv)
    plaintext = cipher.decrypt(ciphertext[AES.block_size+32:])
    return plaintext.rstrip(b"\0")

def encrypt_file(file_name, key):
    with open(file_name, 'rb') as fo:
        plaintext = fo.read()
    enc = encrypt(plaintext, key)
    with open(file_name + ".enc", 'wb') as fo:
        fo.write(enc)

def decrypt_file(file_name):
    with open(file_name, 'rb') as fo:
        ciphertext = fo.read()
    dec = decrypt(ciphertext)
    with open(file_name[:-4], 'wb') as fo:
        fo.write(dec)


#key = 'E5E9FA1BA31ECD1AE84F75CAAA474F3A663F05F412028F81DA65D26EE56424B2'.decode("hex")
#encrypt_file('sender.txt', key)
decrypt_file('sender.txt.enc')
#generate_key('xplainio', 'CE176DBCC59C9100'.decode("hex"), 16)