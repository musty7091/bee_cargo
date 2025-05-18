﻿# app/__init__.py
import os
from flask import Flask, current_app, session, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_mail import Mail # Flask-Mail importu
from config import Config
from werkzeug.security import generate_password_hash, check_password_hash
from decimal import Decimal
from datetime import datetime

# Eklenti nesnelerini global olarak tanımla
db = SQLAlchemy()
migrate = Migrate()
mail = Mail() # Mail nesnesi burada global olarak tanımlanıyor

def create_app(config_class=Config):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(config_class)

    if not app.config.get('SECRET_KEY'):
        raise ValueError("Uygulama için bir SECRET_KEY ayarlanmalıdır! Lütfen config.py dosyasını kontrol edin.")

    try:
        os.makedirs(app.instance_path, exist_ok=True) # 'instance' klasörünü oluştur (varsa hata vermez)
    except OSError:
        pass 

    # Eklentileri uygulamaya bağla
    db.init_app(app)
    migrate.init_app(app, db)
    mail.init_app(app) # Mail burada uygulamaya bağlanıyor

    # Context processor'ı tanımla
    @app.context_processor
    def utility_processor():
        # Bildirimler modelini fonksiyon içinde import et (döngüsel import riskini azaltır)
        from .models import Bildirimler 
        unread_notifications = []
        unread_count = 0
        view_all_notifications_url = None
        user_type = None # Hangi tip kullanıcı için bildirim alındığını belirlemek için

        try:
            if 'admin_id' in session:
                user_id = session.get('admin_id')
                user_type = 'admin'
                unread_notifications = Bildirimler.query.filter_by(admin_id=user_id, okundu_mu=False).order_by(Bildirimler.olusturulma_tarihi.desc()).limit(5).all()
                unread_count = Bildirimler.query.filter_by(admin_id=user_id, okundu_mu=False).count()
            elif 'isletme_id' in session:
                user_id = session.get('isletme_id')
                user_type = 'isletme'
                unread_notifications = Bildirimler.query.filter_by(isletme_id=user_id, okundu_mu=False).order_by(Bildirimler.olusturulma_tarihi.desc()).limit(5).all()
                unread_count = Bildirimler.query.filter_by(isletme_id=user_id, okundu_mu=False).count()
            elif 'kurye_id' in session: 
                user_id = session.get('kurye_id')
                user_type = 'kurye'
                # Kuryeler için Bildirimler modelinde kurye_id alanı olmalı ve sorgu ona göre yapılmalı.
                unread_notifications = Bildirimler.query.filter_by(kurye_id=user_id, okundu_mu=False).order_by(Bildirimler.olusturulma_tarihi.desc()).limit(5).all()
                unread_count = Bildirimler.query.filter_by(kurye_id=user_id, okundu_mu=False).count()

            if user_type: # Sadece giriş yapmış bir kullanıcı tipi varsa link oluştur
                 view_all_notifications_url = url_for('bp_common.view_all_notifications')

        except Exception as e:
            if app.debug: 
                current_app.logger.error(f"Bildirim context processor hatası: {e}", exc_info=True)
            
        return dict(
            now=datetime.now, # datetime.now objesini şablona gönder
            unread_notifications=unread_notifications,
            unread_notification_count=unread_count,
            view_all_notifications_url=view_all_notifications_url
        )

    # CLI komutlarını ve Blueprint'leri uygulama bağlamı içinde kaydet
    with app.app_context():
        from . import models # Modelleri burada import etmek daha güvenli

        @app.cli.command("create-tables")
        def create_tables_command():
            """Veritabanı tablolarını oluşturur veya günceller."""
            db.create_all()
            print("Veritabanı tabloları başarıyla oluşturuldu (veya zaten mevcuttu).")

        @app.cli.command("init-data")
        def init_data_command():
            """Başlangıç verilerini (admin, ayarlar, örnek kurye) ekler/günceller."""
            print("Başlangıç verileri kontrol ediliyor/ekleniyor...")
            
            # Ayar Ekleme
            ayar_kargo_ucreti_adi = 'sabit_kargo_hizmet_bedeli'
            # models prefix'i eklendi
            sabit_kargo_ayari = models.Ayarlar.query.filter_by(ayar_adi=ayar_kargo_ucreti_adi).first()
            if not sabit_kargo_ayari:
                yeni_ayar_kargo = models.Ayarlar( # models prefix'i eklendi
                    ayar_adi=ayar_kargo_ucreti_adi,
                    ayar_degeri='100.00', 
                    aciklama='Kargo başına işletmeden alınacak standart hizmet bedeli (TL).'
                )
                db.session.add(yeni_ayar_kargo)
                print(f"- Varsayılan '{ayar_kargo_ucreti_adi}' ayarı (100.00 TL) eklendi.")
            else:
                print(f"- '{ayar_kargo_ucreti_adi}' ayarı zaten mevcut: {sabit_kargo_ayari.ayar_degeri} TL.")

            # Admin Ekleme/Güncelleme
            admin_kullanici_adi_str = os.environ.get('ADMIN_USER', 'admin')
            admin_sifre_str = os.environ.get('ADMIN_PASS', '1234') 
            admin_email_str = os.environ.get('ADMIN_EMAIL', 'admin@example.com')
            # models prefix'i eklendi
            admin_kullanicisi = models.AdminKullanicilar.query.filter_by(kullanici_adi=admin_kullanici_adi_str).first()
            
            if not admin_kullanicisi:
                hashed_sifre = generate_password_hash(admin_sifre_str)
                yeni_admin = models.AdminKullanicilar( # models prefix'i eklendi
                    kullanici_adi=admin_kullanici_adi_str,
                    sifre_hash=hashed_sifre,
                    email=admin_email_str
                )
                db.session.add(yeni_admin)
                print(f"- '{admin_kullanici_adi_str}' adlı admin kullanıcısı '{admin_sifre_str}' şifresiyle oluşturuldu.")
            else:
                if not check_password_hash(admin_kullanicisi.sifre_hash, admin_sifre_str):
                    admin_kullanicisi.sifre_hash = generate_password_hash(admin_sifre_str)
                    print(f"- '{admin_kullanici_adi_str}' adlı admin kullanıcısının şifresi '{admin_sifre_str}' olarak güncellendi.")
                else:
                    print(f"- '{admin_kullanici_adi_str}' adlı admin kullanıcısı zaten mevcut ve şifresi güncel.")

            # Örnek Kurye Ekleme (Test için)
            kurye_kullanici_adi_str = os.environ.get('COURIER_USER', 'kurye1')
            kurye_sifre_str = os.environ.get('COURIER_PASS', 'kurye1sifre') 
            kurye_ad_soyad_str = os.environ.get('COURIER_NAME', 'Ali Kurye')
            kurye_telefon_str = os.environ.get('COURIER_PHONE', '05001234567') 

            # models prefix'i eklendi
            kurye_kullanicisi_db = models.Kuryeler.query.filter_by(kullanici_adi=kurye_kullanici_adi_str).first()
            if not kurye_kullanicisi_db:
                yeni_kurye_obj = models.Kuryeler( # models prefix'i eklendi
                    kullanici_adi=kurye_kullanici_adi_str,
                    ad_soyad=kurye_ad_soyad_str,
                    telefon=kurye_telefon_str, 
                    email=f"{kurye_kullanici_adi_str}@example.com" 
                )
                yeni_kurye_obj.set_password(kurye_sifre_str) 
                db.session.add(yeni_kurye_obj)
                print(f"- '{kurye_kullanici_adi_str}' adlı kurye '{kurye_sifre_str}' şifresiyle oluşturuldu.")
            else:
                print(f"- '{kurye_kullanici_adi_str}' adlı kurye zaten mevcut.")
            
            try:
                db.session.commit()
                print("Başlangıç verileri başarıyla eklendi/güncellendi.")
            except Exception as e:
                db.session.rollback()
                print(f"Başlangıç verileri kaydedilirken hata oluştu: {str(e)}")
                if app.debug:
                    current_app.logger.error(f"init-data commit hatası: {e}", exc_info=True)

        # Blueprint'leri en son import et ve kaydet (uygulama bağlamı içinde)
        # Bu importlar, utils.py gibi dosyaları tetikleyebilir ve mail nesnesinin
        # global olarak tanımlanmış ve init_app ile bağlanmış olmasını gerektirir.
        from .routes_admin import bp_admin 
        app.register_blueprint(bp_admin)
        
        from .routes_business import bp_business
        app.register_blueprint(bp_business)
        
        from .routes_common import bp_common
        app.register_blueprint(bp_common)
        
        from .routes_courier import bp_courier 
        app.register_blueprint(bp_courier)    

    return app
