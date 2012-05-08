import base64
import hashlib
import random

def gen_key():
    return base64.b64encode(hashlib.sha224(str(random.getrandbits(256)))\
            .hexdigest(),random.choice(['rA','aZ','gQ','hH','hG','aR','DD'])) \
            .rstrip('==')

print gen_key()
