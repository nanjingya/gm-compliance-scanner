# 国密合规示例 - 使用SM2/SM3/SM4
from gmssl import sm2, sm3, sm4

def encrypt_data(data, key):
    crypt = sm4.CryptSM4()
    crypt.set_key(key, sm4.SM4_ENCRYPT)
    return crypt.crypt_ecb(data)

def hash_password(pwd):
    return sm3.sm3_hash(list(pwd.encode()))

def sign_document(doc, private_key, public_key):
    crypt = sm2.CryptSM2(public_key=public_key, private_key=private_key)
    return crypt.sign_with_sm3(doc)
