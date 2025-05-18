# config.py
import os
import secrets

basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or secrets.token_hex(16)
    
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'instance', 'kargo_sistemi.db')
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # --- E-posta Ayarları ---
    MAIL_SERVER = os.environ.get('MAIL_SERVER') or 'smtp.gmail.com'
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 587)
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'true').lower() in ['true', 'on', '1']
    MAIL_USE_SSL = os.environ.get('MAIL_USE_SSL', 'false').lower() in ['true', 'on', '1']
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME') or 'beecargocyprus@gmail.com'
    # Uygulama şifresi aşağıya eklendi (boşluksuz)
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD') or 'ldownvzpkmolxdcm' # GÜNCELLENDİ
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER_NAME', 'BeeCargo'), os.environ.get('MAIL_DEFAULT_SENDER_EMAIL', 'beecargocyprus@gmail.com')
    # ------------------------

    SITE_NAME = os.environ.get('SITE_NAME') or 'BeeCargo'
