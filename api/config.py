from cryptography.fernet import Fernet

#setup the encrpytion - ripped from stack overflow lol
with open('./.env', 'r') as f:
    key = f.read()
    key.encode()

cipher_suite = Fernet(key) #setting up the cipher with the key