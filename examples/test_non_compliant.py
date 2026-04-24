# 这是一个测试用的示例文件，包含非国密算法使用（用于演示扫描效果）
from Crypto.Cipher import AES
from Crypto.PublicKey import RSA
import hashlib

def encrypt_data(data, key):
    cipher = AES.new(key, AES.MODE_CBC)
    return cipher.encrypt(data)

def hash_password(pwd):
    return hashlib.md5(pwd.encode()).hexdigest()

def sign_document(doc, private_key):
    key = RSA.import_key(private_key)
    # RSA签名
    from Crypto.Signature import pkcs1_15
    from Crypto.Hash import SHA256
    h = SHA256.new(doc)
    return pkcs1_15.new(key).sign(h)
