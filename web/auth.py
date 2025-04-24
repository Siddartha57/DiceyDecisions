from flask_bcrypt import Bcrypt
from web import app
bcrypt = Bcrypt(app)

def hash(password):
    return bcrypt.generate_password_hash(password).decode('utf-8')

def verify(plain_text,hash_text):
    return bcrypt.check_password_hash(plain_text,hash_text)