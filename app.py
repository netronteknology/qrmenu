import os, uuid, json, qrcode, socket, openpyxl, requests as http_req
import boto3
from datetime import datetime, timedelta
from io import BytesIO
from PIL import Image, ImageDraw, ImageFilter
from functools import wraps
from flask import (Flask, render_template, request, redirect,
                   url_for, session, flash, send_file, abort, jsonify)
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text, inspect
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-change-in-prod')

# Canlıda Supabase PostgreSQL, local'de SQLite
_db_url = os.environ.get('DATABASE_URL', 'sqlite:///saas.db')
if _db_url.startswith('postgres://'):
    _db_url = _db_url.replace('postgres://', 'postgresql://', 1)
app.config['SQLALCHEMY_DATABASE_URI'] = _db_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER']                  = 'static/uploads'
app.config['MAX_CONTENT_LENGTH']             = 16 * 1024 * 1024

ALLOWED_EXT = {'png', 'jpg', 'jpeg', 'webp', 'gif'}
SUPPORTED_LANGS = {'tr', 'en', 'ar', 'de', 'fr', 'ru', 'zh', 'it'}
STANDARD_ALLERGENS = [
    ('Gluten', '🌾 Gluten'),
    ('Süt/Laktoz', '🥛 Süt/Laktoz'),
    ('Yumurta', '🥚 Yumurta'),
    ('Balık', '🐟 Balık'),
    ('Yer Fıstığı', '🥜 Yer Fıstığı'),
    ('Sert Kabuklu Meyveler', '🌰 Sert Kabuklu Meyveler'),
    ('Kabuklular', '🦐 Kabuklular'),
    ('Soya', '🫘 Soya'),
    ('Kereviz', '🌿 Kereviz'),
    ('Hardal', '🟡 Hardal'),
    ('Susam', '🌱 Susam'),
    ('Sülfitler', '⚗️ Sülfitler'),
    ('Acı Bakla', '🫛 Acı Bakla'),
    ('Yumuşakçalar', '🐚 Yumuşakçalar'),
]
db = SQLAlchemy(app)

# Cloudflare R2 ayarları (canlıda env variable, local'de boş kalır)
R2_ACCESS_KEY  = os.environ.get('R2_ACCESS_KEY')
R2_SECRET_KEY  = os.environ.get('R2_SECRET_KEY')
R2_ENDPOINT    = os.environ.get('R2_ENDPOINT')
R2_BUCKET      = os.environ.get('R2_BUCKET_NAME', 'qrmenu')
R2_PUBLIC_URL  = os.environ.get('R2_PUBLIC_URL', '')

# Jinja2 global: şablonlarda {{ now() }} kullanımı için
def _now(): return datetime.now()
app.jinja_env.globals['now'] = _now

# Dinamik veri yönetimi için yardımcı fonksiyonlar
def get_menu_data(tenant_slug):
    """Merkezi menü verisi yapısı - tüm dillerdeki verileri içerir"""
    from flask import current_app
    
    # Tenant bilgileri
    tenant = Tenant.query.filter_by(slug=tenant_slug).first()
    if not tenant:
        return {}
    
    # Kategorileri ve ürünleri getir
    kategoriler = Kategori.query.filter_by(tenant_id=tenant.id, durum=True).order_by(Kategori.sira).all()
    
    menu_data = {
        'tenant': {
            'id': tenant.id,
            'slug': tenant.slug,
            'restoran_adi': tenant.restoran_adi,
            'restoran_adi_en': tenant.restoran_adi_en or tenant.restoran_adi,
            'logo': tenant.logo,
            'banner': tenant.banner,
            'whatsapp': tenant.whatsapp,
            'instagram': tenant.instagram,
            'konum_url': tenant.konum_url,
            'wifi_sifresi': tenant.wifi_sifresi,
            'splash_text': tenant.splash_text,
            'acilis_saati': tenant.acilis_saati,
            'kapanis_saati': tenant.kapanis_saati,
            'tema': tenant.tema,
            'son_fiyat_guncelleme': tenant.son_fiyat_guncelleme
        },
        'categories': [],
        'products': []
    }
    
    # Kategorileri ekle
    for kat in kategoriler:
        urunler = Urun.query.filter_by(kategori_id=kat.id, durum=True).order_by(Urun.sira).all()
        
        category_data = {
            'id': kat.id,
            'isim': kat.isim,
            'isim_en': kat.isim_en or kat.isim,  # Fallback: TR
            'resim': kat.resim,
            'banner': kat.banner,
            'products': []
        }
        
        # Ürünleri ekle
        for urun in urunler:
            product_data = {
                'id': urun.id,
                'kategori_id': urun.kategori_id,
                'isim': urun.isim,
                'isim_en': urun.isim_en or urun.isim,  # Fallback: TR
                'fiyat': urun.fiyat,
                'aciklama': urun.aciklama,
                'aciklama_en': urun.aciklama_en or urun.aciklama,  # Fallback: TR
                'resim': urun.resim,
                'one_cikan': urun.one_cikan,
                'badge_yeni': urun.badge_yeni,
                'badge_populer': urun.badge_populer,
                'badge_acili': urun.badge_acili,
                'aci_seviyesi': urun.aci_seviyesi,
                'alerjen_notu': urun.alerjen_notu,
                'alerjen_notu_en': urun.alerjen_notu_en or urun.alerjen_notu,  # Fallback: TR
                'calorie': urun.calorie,
                'portion_weight': urun.portion_weight,
                'meat_origin': urun.meat_origin,
                'allergens': normalize_allergens(urun.allergens or urun.alerjen_notu),
                'contains_alcohol': urun.contains_alcohol,
                'goruntuleme': urun.goruntuleme,
                'sira': urun.sira
            }
            category_data['products'].append(product_data)
        
        menu_data['categories'].append(category_data)
        menu_data['products'].extend(category_data['products'])
    
    return menu_data

def get_translation(text_dict, lang='tr'):
    """Otomatik çeviri fonksiyonu - fallback sistemi ile"""
    if not isinstance(text_dict, dict):
        return text_dict
    
    # Dil önceliği: istenen dil > İngilizce > Türkçe (varsayılan)
    priority_order = [lang, 'en', 'tr']
    
    for lang_code in priority_order:
        if lang_code in text_dict and text_dict[lang_code] and text_dict[lang_code].strip():
            return text_dict[lang_code]
    
    # Hiçbir dilde metin yoksa boş string dön
    return ""

# Jinja2 template filtreleri
@app.template_filter('translate')
def translate_filter(text_dict, lang='tr'):
    return get_translation(text_dict, lang)

@app.template_filter('format_price')
def format_price_filter(price):
    return f"{price:.2f} TL"


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
#  MODELLER
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

class Tenant(db.Model):
    id              = db.Column(db.Integer, primary_key=True)
    slug            = db.Column(db.String(60), unique=True, nullable=False)
    restoran_adi    = db.Column(db.String(120), default='Yeni Restoran')
    restoran_adi_en = db.Column(db.String(120), default='')
    logo            = db.Column(db.String(255), default='')
    banner          = db.Column(db.String(255), default='')
    whatsapp        = db.Column(db.String(60),  default='')
    instagram       = db.Column(db.String(160), default='')
    konum_url       = db.Column(db.String(255), default='')
    wifi_sifresi    = db.Column(db.String(100), default='')
    splash_text     = db.Column(db.String(200), default='Lezzet menümüze hoş geldiniz')
    aktif           = db.Column(db.Boolean, default=True)
    paket           = db.Column(db.String(20), default='temel')
    created_at      = db.Column(db.DateTime, default=db.func.now())
    view_count      = db.Column(db.Integer, default=0)
    lisans_bitis    = db.Column(db.DateTime, nullable=True)
    restoran_kodu   = db.Column(db.String(20), unique=True, nullable=True)  # QRM-0001
    musteri_id      = db.Column(db.Integer, db.ForeignKey('musteri.id'), nullable=True)
    referrer_id     = db.Column(db.Integer, nullable=True)
    tema            = db.Column(db.String(20), default='amber')
    menu_gorunum    = db.Column(db.String(10), default='liste')  # liste / grid
    menu_modu       = db.Column(db.String(10), default='klasik')  # klasik / builder
    white_mod       = db.Column(db.Boolean, default=False)  # True = beyaz tema
    aktif_diller    = db.Column(db.String(60), default='tr,en')  # virgülle ayrılmış: tr,en,it,ru vs.
    kdv_dahil       = db.Column(db.Boolean, default=True)  # "Fiyatlara KDV dahildir" notu
    acilis_saati    = db.Column(db.String(5), default='10:00')
    kapanis_saati   = db.Column(db.String(5), default='23:30')
    son_fiyat_guncelleme = db.Column(db.DateTime, nullable=True)
    service_fee_percentage = db.Column(db.Float, default=0)
    # Lisans (tenant seviyesinde)
    lisans_tipi     = db.Column(db.String(20), default='yillik')
    odeme_tipi      = db.Column(db.String(20), default='nakit')
    ucret           = db.Column(db.Float, default=0)
    odendi_mi       = db.Column(db.Boolean, default=False)
    sozlesme_tarihi = db.Column(db.DateTime, nullable=True)
    son_iletisim    = db.Column(db.DateTime, nullable=True)
    iletisim_notu   = db.Column(db.Text, default='')
    kategoriler     = db.relationship('Kategori',  backref='tenant', lazy=True, cascade='all, delete-orphan')
    urunler         = db.relationship('Urun',       backref='tenant', lazy=True, cascade='all, delete-orphan')
    qrcodes         = db.relationship('QRCodeItem', backref='tenant', lazy=True, cascade='all, delete-orphan')
    kullanicilar    = db.relationship('Kullanici',  backref='tenant', lazy=True, cascade='all, delete-orphan')


class Kullanici(db.Model):
    id            = db.Column(db.Integer, primary_key=True)
    tenant_id     = db.Column(db.Integer, db.ForeignKey('tenant.id'), nullable=False)
    username      = db.Column(db.String(60), nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    is_superuser  = db.Column(db.Boolean, default=False)
    __table_args__ = (db.UniqueConstraint('tenant_id', 'username'),)

    def set_password(self, pw):  self.password_hash = generate_password_hash(pw)
    def check_password(self, pw): return check_password_hash(self.password_hash, pw)


class SuperAdmin(db.Model):
    id            = db.Column(db.Integer, primary_key=True)
    username      = db.Column(db.String(60), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)

    def set_password(self, pw):  self.password_hash = generate_password_hash(pw)
    def check_password(self, pw): return check_password_hash(self.password_hash, pw)


class Kategori(db.Model):
    id        = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenant.id'), nullable=False)
    isim      = db.Column(db.String(80), nullable=False)
    isim_en   = db.Column(db.String(80), default='')
    aciklama  = db.Column(db.String(255), default='')
    aciklama_en = db.Column(db.String(255), default='')
    ikon      = db.Column(db.String(50), default='')
    resim     = db.Column(db.String(255), default='')
    banner    = db.Column(db.String(255), default='')
    durum     = db.Column(db.Boolean, default=True)
    sira      = db.Column(db.Integer, default=0)
    urunler   = db.relationship('Urun', backref='kategori', lazy=True, cascade='all, delete-orphan')


class Urun(db.Model):
    id              = db.Column(db.Integer, primary_key=True)
    tenant_id       = db.Column(db.Integer, db.ForeignKey('tenant.id'),   nullable=False)
    kategori_id     = db.Column(db.Integer, db.ForeignKey('kategori.id'), nullable=False)
    isim            = db.Column(db.String(120), nullable=False)
    isim_en         = db.Column(db.String(120), default='')
    isim_ru         = db.Column(db.String(120), default='')
    isim_it         = db.Column(db.String(120), default='')
    isim_de         = db.Column(db.String(120), default='')
    isim_fr         = db.Column(db.String(120), default='')
    fiyat           = db.Column(db.Float, default=0)
    aciklama        = db.Column(db.Text, default='')
    aciklama_en     = db.Column(db.Text, default='')
    aciklama_ru     = db.Column(db.Text, default='')
    aciklama_it     = db.Column(db.Text, default='')
    aciklama_de     = db.Column(db.Text, default='')
    aciklama_fr     = db.Column(db.Text, default='')
    resim           = db.Column(db.String(255), default='')
    durum           = db.Column(db.Boolean, default=True)
    one_cikan       = db.Column(db.Boolean, default=False)
    badge_yeni      = db.Column(db.Boolean, default=False)
    badge_populer   = db.Column(db.Boolean, default=False)
    badge_acili     = db.Column(db.Boolean, default=False)
    aci_seviyesi    = db.Column(db.Integer, default=2)
    alerjen_notu    = db.Column(db.String(255), default='')
    alerjen_notu_en = db.Column(db.String(255), default='')
    kalori          = db.Column(db.Integer, default=0)
    servis_suresi_dk= db.Column(db.Integer, default=0)
    calorie         = db.Column(db.Integer, nullable=True)
    portion_weight  = db.Column(db.String(80), nullable=True)
    meat_origin     = db.Column(db.String(255), nullable=True)
    allergens       = db.Column(db.JSON, nullable=True, default=list)
    contains_alcohol = db.Column(db.Boolean, default=False)
    goruntuleme     = db.Column(db.Integer, default=0)
    sira            = db.Column(db.Integer, default=0)
    urun_tipi       = db.Column(db.String(10), default='standart')  # standart / builder


class QRCodeItem(db.Model):
    id          = db.Column(db.Integer, primary_key=True)
    tenant_id   = db.Column(db.Integer, db.ForeignKey('tenant.id'), nullable=False)
    isim        = db.Column(db.String(100), nullable=False)
    hedef_url   = db.Column(db.String(255), nullable=False)
    dosya       = db.Column(db.String(255), nullable=False)
    kilitli     = db.Column(db.Boolean, default=True)
    silme_hazir = db.Column(db.Boolean, default=False)
    renk_on     = db.Column(db.String(20), default='#000000')
    renk_arka   = db.Column(db.String(20), default='#ffffff')
    logo_var    = db.Column(db.Boolean, default=False)


class Musteri(db.Model):
    id            = db.Column(db.Integer, primary_key=True)
    # Kimlik
    musteri_kodu  = db.Column(db.String(20), unique=True, nullable=False)  # MUS-0001
    referans_kodu = db.Column(db.String(20), unique=True, nullable=True)
    ad_soyad      = db.Column(db.String(120), nullable=False)
    telefon       = db.Column(db.String(30),  default='')
    email         = db.Column(db.String(120), default='')
    tc_vkn        = db.Column(db.String(20),  default='')
    sehir         = db.Column(db.String(60),  default='')
    ilce          = db.Column(db.String(60),  default='')
    notlar        = db.Column(db.Text,        default='')
    created_at    = db.Column(db.DateTime,    default=db.func.now())
    # Restoranlar bu müşteriye backref ile baÄŸlı
    restoranlar   = db.relationship('Tenant', backref='musteri', lazy=True)


# ═══════════════════════════════════════════════════════════════
#  BUILDER SİPARİS MODÜLÜ MODELLERİ
# ═══════════════════════════════════════════════════════════════

class BuilderGrup(db.Model):
    """Builder ürünleri için seçenek grupları (Boy, Protein, Garnitür vb.)"""
    id            = db.Column(db.Integer, primary_key=True)
    tenant_id     = db.Column(db.Integer, db.ForeignKey('tenant.id'), nullable=False)
    urun_id       = db.Column(db.Integer, db.ForeignKey('urun.id'), nullable=True)  # null = tüm ürünler için
    isim          = db.Column(db.String(80), nullable=False)
    isim_en       = db.Column(db.String(80), default='')
    aciklama      = db.Column(db.String(255), default='')
    ikon          = db.Column(db.String(50), default='')
    sira          = db.Column(db.Integer, default=0)
    zorunlu       = db.Column(db.Boolean, default=False)
    min_secim     = db.Column(db.Integer, default=0)
    max_secim     = db.Column(db.Integer, default=1)
    secim_tipi    = db.Column(db.String(10), default='radio')  # radio / checkbox / dropdown
    Gorsel_goster = db.Column(db.Boolean, default=False)
    fiyat_goster  = db.Column(db.Boolean, default=True)
    durum         = db.Column(db.Boolean, default=True)
    secenekler    = db.relationship('BuilderSecenek', backref='grup', lazy=True, cascade='all, delete-orphan')


class BuilderSecenek(db.Model):
    """Builder grupları için seçenekler (Kajun Tavuk, Domates vb.)"""
    id            = db.Column(db.Integer, primary_key=True)
    grup_id       = db.Column(db.Integer, db.ForeignKey('builder_grup.id'), nullable=False)
    ad            = db.Column(db.String(80), nullable=False)
    ad_en         = db.Column(db.String(80), default='')
    fiyat_farki   = db.Column(db.Float, default=0)
    resim         = db.Column(db.String(255), default='')
    varsayilan    = db.Column(db.Boolean, default=False)
    sira          = db.Column(db.Integer, default=0)
    durum         = db.Column(db.Boolean, default=True)


class Siparis(db.Model):
    """Müşteri siparişleri"""
    id            = db.Column(db.Integer, primary_key=True)
    tenant_id     = db.Column(db.Integer, db.ForeignKey('tenant.id'), nullable=False)
    masa_no       = db.Column(db.String(20), default='')
    musteri_adi   = db.Column(db.String(120), default='')
    siparis_notu  = db.Column(db.Text, default='')
    toplam_fiyat  = db.Column(db.Float, default=0)
    durum         = db.Column(db.String(20), default='bekliyor')  # bekliyor / hazirlaniyor / hazir / teslim_edildi / iptal
    created_at    = db.Column(db.DateTime, default=db.func.now())
    updated_at    = db.Column(db.DateTime, default=db.func.now(), onupdate=db.func.now())
    detaylar      = db.relationship('SiparisDetay', backref='siparis', lazy=True, cascade='all, delete-orphan')


class SiparisDetay(db.Model):
    """Sipariş detayları (seçilen ürünler ve seçenekler)"""
    id            = db.Column(db.Integer, primary_key=True)
    siparis_id    = db.Column(db.Integer, db.ForeignKey('siparis.id'), nullable=False)
    urun_id       = db.Column(db.Integer, db.ForeignKey('urun.id'), nullable=False)
    urun_adi      = db.Column(db.String(120), nullable=False)
    urun_fiyati   = db.Column(db.Float, default=0)
    miktar        = db.Column(db.Integer, default=1)
    secenekler    = db.Column(db.JSON, default=list)  # [{"secenek_adi": "Kajun", "grup_adi": "Protein", "fiyat": 15}]
    detay_toplam  = db.Column(db.Float, default=0)


class Yazici(db.Model):
    """ESC/POS yazıcıları için yönetim"""
    id            = db.Column(db.Integer, primary_key=True)
    tenant_id     = db.Column(db.Integer, db.ForeignKey('tenant.id'), nullable=False)
    yazici_adi    = db.Column(db.String(80), nullable=False)
    ip_adresi     = db.Column(db.String(50), default='')
    port          = db.Column(db.Integer, default=9100)
    kagit_genisligi = db.Column(db.Integer, default=58)  # 58 / 80
    otomatik_yazdir = db.Column(db.Boolean, default=True)
    durum         = db.Column(db.Boolean, default=True)
    created_at    = db.Column(db.DateTime, default=db.func.now())


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
#  YARDIMCILAR
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
def upload_dir(slug, sub=''):
    path = os.path.join(app.config['UPLOAD_FOLDER'], slug, sub) if sub \
           else os.path.join(app.config['UPLOAD_FOLDER'], slug)
    os.makedirs(path, exist_ok=True)
    return path


def allowed(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXT


def save_img(file, slug, sub):
    if not file or not file.filename:
        return None
    if not allowed(file.filename):
        return None
    ext  = secure_filename(file.filename).rsplit('.', 1)[1].lower()
    name = f'{uuid.uuid4().hex}.{ext}'

    # Canlı ortam: Cloudflare R2'ye yükle
    if R2_ACCESS_KEY and R2_SECRET_KEY and R2_ENDPOINT:
        try:
            s3 = boto3.client('s3',
                aws_access_key_id=R2_ACCESS_KEY,
                aws_secret_access_key=R2_SECRET_KEY,
                endpoint_url=R2_ENDPOINT)
            key = f'{slug}/{sub}/{name}'.strip('/')
            s3.upload_fileobj(file, R2_BUCKET, key,
                ExtraArgs={'ContentType': file.content_type or 'image/jpeg'})
            return f'{R2_PUBLIC_URL.rstrip("/")}/{key}'
        except Exception as e:
            print(f'R2 upload hatası: {e}')
            return None

    # Local geliştirme: static/uploads klasörüne kaydet
    file.save(os.path.join(upload_dir(slug, sub), name))
    return name


def musteri_kodu_uret():
    son = Musteri.query.order_by(Musteri.id.desc()).first()
    num = (son.id + 1) if son else 1
    return f'MUS-{num:04d}'

def restoran_kodu_uret():
    son = Tenant.query.order_by(Tenant.id.desc()).first()
    num = (son.id + 1) if son else 1
    return f'QRM-{num:04d}'

def referans_kodu_uret(mid):
    return f'REF-{mid:04d}'

def clean(v, d=''):  return (v or d).strip()
def parse_price(v):
    try:    return float(str(v).replace(',', '.').strip())
    except: return None

def get_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80)); ip = s.getsockname()[0]; s.close(); return ip
    except: return '127.0.0.1'

def ok(m):  flash(m, 'success')
def err(m): flash(m, 'error')


def normalize_time(v, fallback):
    raw = clean(v, fallback)
    parts = raw.split(':')
    if len(parts) != 2:
        return fallback
    try:
        hh = max(0, min(23, int(parts[0])))
        mm = max(0, min(59, int(parts[1])))
    except ValueError:
        return fallback
    return f'{hh:02d}:{mm:02d}'


def stamp_price_update(tenant):
    tenant.son_fiyat_guncelleme = datetime.now()


def parse_calorie(value):
    raw = clean(value)
    if not raw:
        return None
    try:
        n = int(raw)
        return n if n > 0 else None
    except (TypeError, ValueError):
        return None


def normalize_allergens(value):
    if not value:
        return []
    if isinstance(value, list):
        return [clean(a) for a in value if clean(a)]
    if isinstance(value, str):
        raw = value.strip()
        if not raw:
            return []
        if raw.startswith('['):
            try:
                parsed = json.loads(raw)
                if isinstance(parsed, list):
                    return [clean(a) for a in parsed if clean(a)]
            except (TypeError, ValueError, json.JSONDecodeError):
                pass
        return [a.strip() for a in raw.split(',') if a.strip()]
    return []


def parse_allergens_from_form():
    seen, items = set(), []
    for raw in request.form.getlist('allergens'):
        val = clean(raw)
        if val and val not in seen:
            seen.add(val)
            items.append(val)
    return items


def apply_legal_product_fields(urun):
    urun.calorie = parse_calorie(request.form.get('calorie'))
    urun.portion_weight = clean(request.form.get('portion_weight')) or None
    urun.meat_origin = clean(request.form.get('meat_origin')) or None
    urun.contains_alcohol = bool(request.form.get('contains_alcohol'))
    allergens = parse_allergens_from_form()
    urun.allergens = allergens
    urun.alerjen_notu = ', '.join(allergens)
    urun.alerjen_notu_en = urun.alerjen_notu


def ensure_schema():
    column_sql = {
        'tenant': {
            'referrer_id': 'referrer_id INTEGER',
            'acilis_saati': "acilis_saati VARCHAR(5) DEFAULT '10:00'",
            'kapanis_saati': "kapanis_saati VARCHAR(5) DEFAULT '23:30'",
            'son_fiyat_guncelleme': 'son_fiyat_guncelleme DATETIME',
            'service_fee_percentage': 'service_fee_percentage FLOAT DEFAULT 0',
            'menu_gorunum': "menu_gorunum VARCHAR(10) DEFAULT 'liste'",
            'menu_modu': "menu_modu VARCHAR(10) DEFAULT 'klasik'",
            'white_mod': 'white_mod BOOLEAN DEFAULT 0',
            'wifi_sifresi': "wifi_sifresi VARCHAR(100) DEFAULT ''",
        },
        'musteri': {
            'referans_kodu': 'referans_kodu VARCHAR(20)',
        },
        'urun': {
            'aci_seviyesi': 'aci_seviyesi INTEGER DEFAULT 2',
            'goruntuleme': 'goruntuleme INTEGER DEFAULT 0',
            'alerjen_notu': "alerjen_notu VARCHAR(255) DEFAULT ''",
            'alerjen_notu_en': "alerjen_notu_en VARCHAR(255) DEFAULT ''",
            'kalori': 'kalori INTEGER DEFAULT 0',
            'servis_suresi_dk': 'servis_suresi_dk INTEGER DEFAULT 0',
            'calorie': 'calorie INTEGER',
            'portion_weight': 'portion_weight VARCHAR(80)',
            'meat_origin': 'meat_origin VARCHAR(255)',
            'allergens': "allergens TEXT DEFAULT '[]'",
            'contains_alcohol': 'contains_alcohol BOOLEAN DEFAULT 0',
            'urun_tipi': "urun_tipi VARCHAR(10) DEFAULT 'standart'",
        },
        'kategori': {
            'aciklama': "aciklama VARCHAR(255) DEFAULT ''",
            'aciklama_en': "aciklama_en VARCHAR(255) DEFAULT ''",
            'ikon': "ikon VARCHAR(50) DEFAULT ''",
        },
    }

    inspector = inspect(db.engine)

    for table_name, columns in column_sql.items():
        mevcut = {row["name"] for row in inspector.get_columns(table_name)}
        for column_name, ddl in columns.items():
            if column_name not in mevcut:
                db.session.execute(text(f'ALTER TABLE {table_name} ADD COLUMN {ddl}'))

    db.session.execute(text("UPDATE tenant SET acilis_saati = '10:00' WHERE acilis_saati IS NULL OR acilis_saati = ''"))
    db.session.execute(text("UPDATE tenant SET kapanis_saati = '23:30' WHERE kapanis_saati IS NULL OR kapanis_saati = ''"))
    
    # Yeni tabloları oluştur (varsa hata vermez)
    db.create_all()
    db.session.execute(text("UPDATE tenant SET service_fee_percentage = 0 WHERE service_fee_percentage IS NULL"))
    db.session.execute(text("UPDATE urun SET contains_alcohol = FALSE WHERE contains_alcohol IS NULL"))
    db.session.execute(text("UPDATE urun SET calorie = kalori WHERE calorie IS NULL AND kalori > 0"))
    db.session.commit()

    for urun in Urun.query.all():
        changed = False
        if urun.allergens is None:
            urun.allergens = []
            changed = True
        if not urun.allergens and urun.alerjen_notu:
            parsed = [a.strip() for a in urun.alerjen_notu.split(',') if a.strip()]
            if parsed:
                urun.allergens = parsed
                changed = True
        if changed:
            db.session.add(urun)
    db.session.commit()


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
#  VERÄ°TABANI BAÅLATMA
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
with app.app_context():
    db.create_all()
    ensure_schema()
    if not SuperAdmin.query.first():
        sa = SuperAdmin(username='superadmin')
        sa.set_password('superadmin123')
        db.session.add(sa)
        db.session.commit()
    changed = False
    for musteri in Musteri.query.order_by(Musteri.id).all():
        if not musteri.referans_kodu:
            musteri.referans_kodu = referans_kodu_uret(musteri.id)
            changed = True
    if changed:
        db.session.commit()


# â”€â”€ Dekoratörler â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
def sa_required(f):
    @wraps(f)
    def w(*a, **kw):
        if not session.get('sa_id'):
            return redirect(url_for('sa_login'))
        return f(*a, **kw)
    return w


def login_required(f):
    @wraps(f)
    def w(*a, **kw):
        slug   = kw.get('slug')
        tenant = Tenant.query.filter_by(slug=slug, aktif=True).first_or_404()
        uid    = session.get(f't_{slug}')
        if not uid:
            return redirect(url_for('t_login', slug=slug))
        user = Kullanici.query.filter_by(id=uid, tenant_id=tenant.id).first()
        if not user:
            session.pop(f't_{slug}', None)
            return redirect(url_for('t_login', slug=slug))
        return f(*a, **kw, tenant=tenant, me=user)
    return w


@app.context_processor
def ctx():
    sid = session.get('sa_id')
    return {'sa': SuperAdmin.query.get(sid) if sid else None}


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
#  QR ÜRETİCİ
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
def make_qr(url, fg='#000000', bg='#ffffff', logo=None):
    def h(c):
        c = c.lstrip('#')
        return tuple(int(c[i:i+2], 16) for i in (0, 2, 4))

    qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_H, box_size=14, border=3)
    qr.add_data(url); qr.make(fit=True)
    img = qr.make_image(fill_color=h(fg), back_color=h(bg)).convert('RGBA')

    if logo and os.path.exists(logo):
        qw, qh = img.size
        area   = int(min(qw, qh) * 0.22)
        pad    = int(area * 0.18)
        csz    = area + pad * 2

        sh = Image.new('RGBA', (csz+8, csz+8), (0,0,0,0))
        ImageDraw.Draw(sh).ellipse((4,4,csz+4,csz+4), fill=(0,0,0,60))
        sh = sh.filter(ImageFilter.GaussianBlur(4))

        ci = Image.new('RGBA', (csz, csz), (0,0,0,0))
        ImageDraw.Draw(ci).ellipse((0,0,csz-1,csz-1), fill=(255,255,255,255))

        lo = Image.open(logo).convert('RGBA').resize((area, area), Image.LANCZOS)
        mk = Image.new('L', (area, area), 0)
        ImageDraw.Draw(mk).ellipse((0,0,area,area), fill=255)
        lr = Image.new('RGBA', (area, area), (0,0,0,0))
        lr.paste(lo, (0,0), mk); ci.paste(lr, (pad,pad), lr)

        px, py = (qw-csz)//2, (qh-csz)//2
        img.paste(sh, (px-4, py-4), sh)
        img.paste(ci, (px, py), ci)
    return img


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
#  SÜPER ADMİN
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
@app.route('/')
def root(): return redirect(url_for('sa_login'))


@app.route('/superadmin/login', methods=['GET','POST'])
def sa_login():
    if request.method == 'POST':
        sa = SuperAdmin.query.filter_by(username=clean(request.form.get('username'))).first()
        if sa and sa.check_password(request.form.get('password','')):
            session['sa_id'] = sa.id
            return redirect(url_for('sa_panel'))
        err('Hatalı giriş.')
    return render_template('superadmin/login.html')


@app.route('/superadmin/logout')
def sa_logout():
    session.pop('sa_id', None)
    return redirect(url_for('sa_login'))


@app.route('/superadmin/sifre-degistir', methods=['POST'])
@sa_required
def sa_sifre_degistir():
    sa = SuperAdmin.query.get(session['sa_id'])
    eski  = request.form.get('eski_sifre', '')
    yeni  = request.form.get('yeni_sifre', '')
    yeni2 = request.form.get('yeni_sifre2', '')
    if not sa.check_password(eski):
        flash('Mevcut şifre yanlış.', 'error')
    elif len(yeni) < 8:
        flash('Yeni şifre en az 8 karakter olmalı.', 'error')
    elif yeni != yeni2:
        flash('Şifreler eşleşmiyor.', 'error')
    else:
        sa.set_password(yeni)
        db.session.commit()
        flash('Şifre başarıyla değiştirildi.', 'success')
    return redirect(url_for('sa_panel') + '#tab-ayarlar')


@app.route('/superadmin')
@sa_required
def sa_panel():
    now = datetime.now()
    tenants  = Tenant.query.order_by(Tenant.id.desc()).all()
    musteriler = Musteri.query.order_by(Musteri.id.desc()).all()

    for t in tenants:
        if t.lisans_bitis and t.lisans_bitis < now and t.aktif:
            t.aktif = False
    db.session.commit()

    yaklasan      = [t for t in tenants if t.lisans_bitis and now < t.lisans_bitis < now + timedelta(days=30)]
    suresi_dolmus = [t for t in tenants if t.lisans_bitis and t.lisans_bitis < now]

    # Kasa takibi istatistikleri
    tahsil_edilen = sum(t.ucret or 0 for t in tenants if t.odendi_mi)
    bekleyen_tutar = sum(t.ucret or 0 for t in tenants if not t.odendi_mi)
    odeme_nakit = sum(t.ucret or 0 for t in tenants if t.odeme_tipi == 'nakit' and t.odendi_mi)
    odeme_havale = sum(t.ucret or 0 for t in tenants if t.odeme_tipi == 'havale' and t.odendi_mi)
    odeme_kredi = sum(t.ucret or 0 for t in tenants if t.odeme_tipi == 'kredi' and t.odendi_mi)

    stats = dict(
        toplam_musteri=len(musteriler),
        toplam=len(tenants),
        aktif=sum(1 for t in tenants if t.aktif),
        pro=sum(1 for t in tenants if t.paket=='pro'),
        kurumsal=sum(1 for t in tenants if t.paket=='kurumsal'),
        deneme=sum(1 for t in tenants if t.paket=='deneme'),
        toplam_gorunum=sum(t.view_count or 0 for t in tenants),
        toplam_gelir=sum(t.ucret or 0 for t in tenants),
        tahsil_edilen=tahsil_edilen,
        bekleyen_tutar=bekleyen_tutar,
        odeme_nakit=odeme_nakit,
        odeme_havale=odeme_havale,
        odeme_kredi=odeme_kredi,
        yaklasan_lisans=len(yaklasan),
        suresi_dolmus=len(suresi_dolmus),
        odeme_bekleyen=sum(1 for t in tenants if not t.odendi_mi),
    )

    def shift_month(base, delta):
        month_index = base.month - 1 + delta
        year = base.year + month_index // 12
        month = month_index % 12 + 1
        return datetime(year, month, 1)

    ay_adlari = ['Oca', 'Sub', 'Mar', 'Nis', 'May', 'Haz', 'Tem', 'Agu', 'Eyl', 'Eki', 'Kas', 'Ara']
    month_slots = [shift_month(datetime(now.year, now.month, 1), offset) for offset in range(-5, 1)]
    gelir_haritasi = {slot.strftime('%Y-%m'): 0 for slot in month_slots}
    for tenant in tenants:
        gelir_tarihi = tenant.sozlesme_tarihi or tenant.created_at
        if not gelir_tarihi:
            continue
        key = gelir_tarihi.strftime('%Y-%m')
        if key in gelir_haritasi:
            gelir_haritasi[key] += tenant.ucret or 0
    chart_labels = [ay_adlari[slot.month - 1] for slot in month_slots]
    chart_values = [round(gelir_haritasi[slot.strftime('%Y-%m')], 2) for slot in month_slots]
    chart_max = max(chart_values) if any(chart_values) else 1

    odeme_bekleyenler = sorted(
        [t for t in tenants if not t.odendi_mi],
        key=lambda t: (t.lisans_bitis or datetime.max, t.restoran_adi.lower())
    )[:8]

    top_referrers = []
    for musteri in musteriler:
        referred = [t for t in tenants if t.referrer_id == musteri.id]
        if referred:
            top_referrers.append({
                'musteri': musteri,
                'count': len(referred),
                'gelir': sum(t.ucret or 0 for t in referred),
            })
    top_referrers.sort(key=lambda item: (-item['count'], -item['gelir'], item['musteri'].ad_soyad.lower()))

    return render_template('superadmin/dashboard.html',
        tenants=tenants, musteriler=musteriler, stats=stats,
        yaklasan=yaklasan, suresi_dolmus=suresi_dolmus, now=now,
        chart_labels=chart_labels, chart_values=chart_values, chart_max=chart_max,
        odeme_bekleyenler=odeme_bekleyenler, top_referrers=top_referrers[:8])


@app.route('/superadmin/ekle', methods=['POST'])
@sa_required
def sa_ekle():
    slug  = clean(request.form.get('slug','')).lower().replace(' ','-')
    isim  = clean(request.form.get('restoran_adi','Yeni Restoran'))
    pw    = request.form.get('password','admin123')
    paket = request.form.get('paket','temel')

    if not slug:
        err('Slug zorunludur.'); return redirect(url_for('sa_panel'))
    if Tenant.query.filter_by(slug=slug).first():
        err(f'"{slug}" zaten kullanımda.'); return redirect(url_for('sa_panel'))

    t = Tenant(slug=slug, restoran_adi=isim, paket=paket)
    db.session.add(t); db.session.flush()

    u = Kullanici(tenant_id=t.id, username='admin', is_superuser=True)
    u.set_password(pw); db.session.add(u)
    db.session.commit()

    for sub in ['kategoriler','urunler','qrcodes','ayarlar']:
        upload_dir(slug, sub)

    ok(f'"{isim}" oluşturuldu â€” URL: /r/{slug}/  |  Åifre: {pw}')
    return redirect(url_for('sa_panel'))


@app.route('/superadmin/durum/<int:tid>')
@sa_required
def sa_durum(tid):
    t = Tenant.query.get_or_404(tid)
    t.aktif = not t.aktif; db.session.commit()
    ok('Durum güncellendi.'); return redirect(url_for('sa_panel'))


@app.route('/superadmin/sil/<int:tid>', methods=['POST'])
@sa_required
def sa_sil(tid):
    t = Tenant.query.get_or_404(tid)
    db.session.delete(t); db.session.commit()
    ok(f'"{t.restoran_adi}" silindi.'); return redirect(url_for('sa_panel'))


@app.route('/superadmin/paket/<int:tid>', methods=['POST'])
@sa_required
def sa_paket(tid):
    t = Tenant.query.get_or_404(tid)
    t.paket = request.form.get('paket','temel'); db.session.commit()
    ok('Paket güncellendi.'); return redirect(url_for('sa_panel'))


@app.route('/superadmin/musteri_ata/<int:tid>', methods=['POST'])
@sa_required
def sa_musteri_ata(tid):
    t = Tenant.query.get_or_404(tid)
    mid = request.form.get('musteri_id', '').strip()
    if mid:
        m = Musteri.query.get(int(mid))
        if m:
            t.musteri_id = m.id
            ok(f'"{t.restoran_adi}" → {m.ad_soyad} olarak atandı.')
        else:
            err('Müşteri bulunamadı.')
    else:
        t.musteri_id = None
        ok(f'"{t.restoran_adi}" müşterisi kaldırıldı.')
    db.session.commit()
    return redirect(url_for('sa_panel') + '#restoranlar')


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
#  MÜŞTERİ MENÜSÜ (herkese açık)
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
@app.route('/r/<slug>/')
def menu(slug):
    tenant = Tenant.query.filter_by(slug=slug, aktif=True).first_or_404()
    tenant.view_count = (tenant.view_count or 0) + 1
    db.session.commit()

    session_key = f'lang_{slug}'
    cookie_key = f'menu_lang_{slug}'
    selected_lang = request.args.get('lang') or session.get(session_key) or request.cookies.get(cookie_key) or 'tr'
    if selected_lang not in SUPPORTED_LANGS:
        selected_lang = 'tr'
    session[session_key] = selected_lang
    
    # Dinamik menü verisi yapısını kullan
    menu_data = get_menu_data(slug)
    
    # Öne çıkan ürünleri filtrele
    one_cikanlar = [p for p in menu_data['products'] if p['one_cikan']]
    
    return render_template('menu/index.html', 
                         tenant=tenant, 
                         menu_data=menu_data,
                         one_cikan_urunler=one_cikanlar,
                         selected_lang=selected_lang)


@app.route('/r/<slug>/set-language', methods=['POST'])
def set_language(slug):
    tenant = Tenant.query.filter_by(slug=slug, aktif=True).first_or_404()
    payload = request.get_json(silent=True) or {}
    lang = (payload.get('lang') or request.form.get('lang') or '').strip().lower()
    if lang not in SUPPORTED_LANGS:
        return jsonify({'ok': False, 'error': 'unsupported_language'}), 400

    session_key = f'lang_{slug}'
    cookie_key = f'menu_lang_{slug}'
    session[session_key] = lang
    resp = jsonify({'ok': True, 'lang': lang, 'tenant': tenant.slug})
    resp.set_cookie(cookie_key, lang, max_age=60 * 60 * 24 * 180, samesite='Lax')
    return resp


@app.route('/r/<slug>/urun_goruntule/<int:uid>', methods=['POST'])
def urun_goruntule(slug, uid):
    tenant = Tenant.query.filter_by(slug=slug, aktif=True).first_or_404()
    urun = Urun.query.filter_by(id=uid, tenant_id=tenant.id).first()
    if urun:
        urun.goruntuleme = (urun.goruntuleme or 0) + 1
        db.session.commit()
    return '', 204


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
#  TENANT LOGIN/LOGOUT
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
@app.route('/r/<slug>/admin/login', methods=['GET','POST'])
def t_login(slug):
    tenant = Tenant.query.filter_by(slug=slug, aktif=True).first_or_404()
    if request.method == 'POST':
        u = Kullanici.query.filter_by(
            tenant_id=tenant.id, username=clean(request.form.get('username'))).first()
        if u and u.check_password(request.form.get('password','')):
            session[f't_{slug}'] = u.id
            ok('Giriş başarılı.')
            return redirect(url_for('t_admin', slug=slug))
        err('Hatalı giriş.')
    return render_template('tenant/login.html', tenant=tenant)


@app.route('/r/<slug>/admin/logout')
def t_logout(slug):
    session.pop(f't_{slug}', None)
    return redirect(url_for('t_login', slug=slug))


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
#  TENANT ADMÄ°N PANELÄ°
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
@app.route('/r/<slug>/admin')
@login_required
def t_admin(slug, tenant, me):
    kats  = Kategori.query.filter_by(tenant_id=tenant.id)\
                          .order_by(Kategori.sira, Kategori.id.desc()).all()
    uruns = Urun.query.filter_by(tenant_id=tenant.id).order_by(Urun.sira, Urun.id.desc()).all()
    users = Kullanici.query.filter_by(tenant_id=tenant.id).all()
    qrs   = QRCodeItem.query.filter_by(tenant_id=tenant.id).order_by(QRCodeItem.id.desc()).all()
    port  = request.host.split(':')[1] if ':' in request.host else '5000'
    local = f'http://{get_ip()}:{port}/r/{slug}/'
    return render_template('tenant/admin.html',
        tenant=tenant, me=me,
        kategoriler=kats, urunler=uruns,
        kullanicilar=users, qrcodes=qrs, local_url=local,
        standard_allergens=STANDARD_ALLERGENS)


# â”€â”€ Ayarlar â”€â”€
@app.route('/r/<slug>/admin/ayarlar', methods=['POST'])
@login_required
def t_ayarlar(slug, tenant, me):
    tenant.restoran_adi    = clean(request.form.get('restoran_adi'), tenant.restoran_adi)
    tenant.restoran_adi_en = clean(request.form.get('restoran_adi_en'))
    tenant.whatsapp        = clean(request.form.get('whatsapp'))
    tenant.instagram       = clean(request.form.get('instagram'))
    tenant.konum_url       = clean(request.form.get('konum_url'))
    tenant.wifi_sifresi    = clean(request.form.get('wifi_sifresi'))
    tenant.splash_text     = clean(request.form.get('splash_text'), tenant.splash_text)
    tenant.acilis_saati    = normalize_time(request.form.get('acilis_saati'), tenant.acilis_saati or '10:00')
    tenant.kapanis_saati   = normalize_time(request.form.get('kapanis_saati'), tenant.kapanis_saati or '23:30')
    tema = request.form.get('tema', '').strip()
    if tema in ('amber', 'zeytin', 'gece'):
        tenant.tema = tema
    tenant.white_mod    = bool(request.form.get('white_mod'))
    menu_mod = request.form.get('menu_modu', 'klasik')
    tenant.menu_modu = menu_mod if menu_mod in ('klasik', 'builder') else 'klasik'
    gorunum = request.form.get('menu_gorunum', 'liste')
    tenant.menu_gorunum = gorunum if gorunum in ('liste', 'grid') else 'liste'
    tenant.kdv_dahil = bool(request.form.get('kdv_dahil'))
    try:
        tenant.service_fee_percentage = max(0.0, float(request.form.get('service_fee_percentage') or 0))
    except (TypeError, ValueError):
        tenant.service_fee_percentage = 0
    # Aktif diller
    secili = request.form.getlist('aktif_diller')
    if 'tr' not in secili:
        secili.insert(0, 'tr')  # Türkçe her zaman aktif
    tenant.aktif_diller = ','.join(s for s in secili if s in SUPPORTED_LANGS)
    logo   = save_img(request.files.get('logo'),   slug, 'ayarlar')
    banner = save_img(request.files.get('banner'), slug, 'ayarlar')
    if logo:   tenant.logo   = logo
    if banner: tenant.banner = banner
    db.session.commit(); ok('Ayarlar kaydedildi.')
    return redirect(url_for('t_admin', slug=slug) + '#ayarlar')


# â”€â”€ Kategoriler â”€â”€
@app.route('/r/<slug>/admin/kat_ekle', methods=['POST'])
@login_required
def t_kat_ekle(slug, tenant, me):
    isim = clean(request.form.get('isim'))
    if not isim:
        err('Ad zorunludur.')
    elif Kategori.query.filter_by(tenant_id=tenant.id, isim=isim).first():
        err('Bu isim zaten var.')
    else:
        resim  = save_img(request.files.get('resim'),  slug, 'kategoriler')
        banner = save_img(request.files.get('banner'), slug, 'kategoriler')
        db.session.add(Kategori(tenant_id=tenant.id, isim=isim,
            isim_en=clean(request.form.get('isim_en'), isim),
            resim=resim or '', banner=banner or '', durum=True))
        db.session.commit(); ok('Kategori eklendi.')
    return redirect(url_for('t_admin', slug=slug) + '#kategoriler')


@app.route('/r/<slug>/admin/kat_duzenle/<int:kid>', methods=['POST'])
@login_required
def t_kat_duzenle(slug, tenant, me, kid):
    k = Kategori.query.filter_by(id=kid, tenant_id=tenant.id).first_or_404()
    k.isim = clean(request.form.get('isim'), k.isim)
    k.isim_en = clean(request.form.get('isim_en'))
    yeni        = save_img(request.files.get('resim'),  slug, 'kategoriler')
    yeni_banner = save_img(request.files.get('banner'), slug, 'kategoriler')
    if yeni:        k.resim  = yeni
    if yeni_banner: k.banner = yeni_banner
    db.session.commit(); ok('Güncellendi.')
    return redirect(url_for('t_admin', slug=slug) + '#kategoriler')


@app.route('/r/<slug>/admin/kat_durum/<int:kid>')
@login_required
def t_kat_durum(slug, tenant, me, kid):
    k = Kategori.query.filter_by(id=kid, tenant_id=tenant.id).first_or_404()
    k.durum = not k.durum; db.session.commit(); ok('Güncellendi.')
    return redirect(url_for('t_admin', slug=slug) + '#kategoriler')


@app.route('/r/<slug>/admin/kat_sil/<int:kid>')
@login_required
def t_kat_sil(slug, tenant, me, kid):
    k = Kategori.query.filter_by(id=kid, tenant_id=tenant.id).first_or_404()
    db.session.delete(k); db.session.commit(); ok('Silindi.')
    return redirect(url_for('t_admin', slug=slug) + '#kategoriler')


# â”€â”€ Ürünler â”€â”€


# ── AI Çeviri Route ──────────────────────────────────────
@app.route('/r/<slug>/admin/ai_cevir', methods=['POST'])
@login_required
def t_ai_cevir(slug, tenant, me):
    import json, re
    from flask import jsonify
    data        = request.get_json(silent=True) or {}
    isim        = (data.get('isim') or '').strip()
    aciklama    = (data.get('aciklama') or '').strip()
    diller      = [d for d in (data.get('diller') or []) if d != 'tr']

    if not isim or not diller:
        return jsonify({'error': 'Eksik veri'}), 400

    lang_names = {
        'en': 'English', 'ru': 'Russian', 'it': 'Italian',
        'de': 'German',  'fr': 'French',  'ar': 'Arabic', 'zh': 'Chinese'
    }
    target_list = ', '.join(f"{d} ({lang_names[d]})" for d in diller if d in lang_names)

    prompt = (
        f"You are a restaurant menu translator. Detect the language of the product name and translate to: {target_list}.\n"
        f"Product name: \"{isim}\"\n"
        + (f"Description: \"{aciklama}\"\n" if aciklama else '')
        + "Rules:\n"
        "- If the name is already English (like Pizza, Burger, Cola), still provide all requested translations\n"
        "- Keep brand names as-is (Coca-Cola, Sprite etc)\n"
        "- Make translations sound natural and appetizing\n"
        "- If description is empty, set aciklama to empty string\n"
        "Respond ONLY with valid JSON, no extra text:\n"
        '{"en":{"isim":"...","aciklama":"..."},"ru":{"isim":"...","aciklama":"..."}}'
    )

    api_key = os.environ.get('ANTHROPIC_API_KEY', '')
    if not api_key:
        return jsonify({'error': 'ANTHROPIC_API_KEY eksik. .env dosyasına ekleyin.'}), 500

    try:
        resp = http_req.post(
            'https://api.anthropic.com/v1/messages',
            headers={
                'x-api-key': api_key,
                'anthropic-version': '2023-06-01',
                'content-type': 'application/json',
            },
            json={
                'model': 'claude-haiku-4-5-20251001',
                'max_tokens': 800,
                'messages': [{'role': 'user', 'content': prompt}]
            },
            timeout=25
        )
        resp.raise_for_status()
        raw  = resp.json()['content'][0]['text']
        m    = re.search(r'\{[\s\S]*\}', raw)
        if not m:
            return jsonify({'error': 'Geçersiz yanıt'}), 500
        return jsonify(json.loads(m.group()))
    except Exception as e:
        return jsonify({'error': str(e)}), 500
# ─────────────────────────────────────────────────────────

@app.route('/r/<slug>/admin/urun_ekle', methods=['POST'])
@login_required
def t_urun_ekle(slug, tenant, me):
    isim  = clean(request.form.get('isim'))
    fiyat = parse_price(request.form.get('fiyat'))
    kid   = request.form.get('kategori_id')
    if not isim or fiyat is None or not kid:
        err('Zorunlu alanları doldur.')
        return redirect(url_for('t_admin', slug=slug) + '#urunler')
    kat = Kategori.query.filter_by(id=int(kid), tenant_id=tenant.id).first()
    if not kat:
        err('Geçersiz kategori.')
        return redirect(url_for('t_admin', slug=slug) + '#urunler')
    resim = save_img(request.files.get('resim'), slug, 'urunler')
    urun_tip = request.form.get('urun_tipi', 'standart')
    urun = Urun(
        tenant_id=tenant.id, kategori_id=kat.id,
        isim=isim,
        isim_en=clean(request.form.get('isim_en'), isim),
        isim_ru=clean(request.form.get('isim_ru')),
        isim_it=clean(request.form.get('isim_it')),
        isim_de=clean(request.form.get('isim_de')),
        isim_fr=clean(request.form.get('isim_fr')),
        fiyat=fiyat,
        aciklama=clean(request.form.get('aciklama')),
        aciklama_en=clean(request.form.get('aciklama_en')),
        aciklama_ru=clean(request.form.get('aciklama_ru')),
        aciklama_it=clean(request.form.get('aciklama_it')),
        aciklama_de=clean(request.form.get('aciklama_de')),
        aciklama_fr=clean(request.form.get('aciklama_fr')),
        resim=resim or '', durum=True,
        one_cikan=bool(request.form.get('one_cikan')),
        badge_yeni=bool(request.form.get('badge_yeni')),
        badge_populer=bool(request.form.get('badge_populer')),
        badge_acili=bool(request.form.get('badge_acili')),
        aci_seviyesi=int(request.form.get('aci_seviyesi') or 2),
        urun_tipi=urun_tip if urun_tip in ('standart', 'builder') else 'standart',
    )
    apply_legal_product_fields(urun)
    db.session.add(urun)
    stamp_price_update(tenant)
    db.session.commit(); ok('Ürün eklendi.')
    return redirect(url_for('t_admin', slug=slug) + '#urunler')


@app.route('/r/<slug>/admin/urun_duzenle/<int:uid>', methods=['POST'])
@login_required
def t_urun_duzenle(slug, tenant, me, uid):
    u = Urun.query.filter_by(id=uid, tenant_id=tenant.id).first_or_404()
    fiyat = parse_price(request.form.get('fiyat'))
    kid   = request.form.get('kategori_id')
    onceki_fiyat = u.fiyat
    u.isim        = clean(request.form.get('isim'), u.isim)
    u.isim_en     = clean(request.form.get('isim_en'))
    u.isim_ru     = clean(request.form.get('isim_ru'))
    u.isim_it     = clean(request.form.get('isim_it'))
    u.isim_de     = clean(request.form.get('isim_de'))
    u.isim_fr     = clean(request.form.get('isim_fr'))
    u.aciklama    = clean(request.form.get('aciklama'))
    u.aciklama_en = clean(request.form.get('aciklama_en'))
    u.aciklama_ru = clean(request.form.get('aciklama_ru'))
    u.aciklama_it = clean(request.form.get('aciklama_it'))
    u.aciklama_de = clean(request.form.get('aciklama_de'))
    u.aciklama_fr = clean(request.form.get('aciklama_fr'))
    urun_tip = request.form.get('urun_tipi', 'standart')
    u.urun_tipi = urun_tip if urun_tip in ('standart', 'builder') else 'standart'
    u.one_cikan   = bool(request.form.get('one_cikan'))
    u.badge_yeni  = bool(request.form.get('badge_yeni'))
    u.badge_populer = bool(request.form.get('badge_populer'))
    u.badge_acili   = bool(request.form.get('badge_acili'))
    u.aci_seviyesi   = int(request.form.get('aci_seviyesi') or 2)
    apply_legal_product_fields(u)
    fiyat_degisti = False
    if fiyat is not None:
        u.fiyat = fiyat
        fiyat_degisti = onceki_fiyat != fiyat
    if kid:
        k = Kategori.query.filter_by(id=int(kid), tenant_id=tenant.id).first()
        if k: u.kategori_id = k.id
    yeni = save_img(request.files.get('resim'), slug, 'urunler')
    if yeni: u.resim = yeni
    if fiyat_degisti:
        stamp_price_update(tenant)
    db.session.commit(); ok('Güncellendi.')
    return redirect(url_for('t_admin', slug=slug) + '#urunler')


@app.route('/r/<slug>/admin/urun_durum/<int:uid>')
@login_required
def t_urun_durum(slug, tenant, me, uid):
    u = Urun.query.filter_by(id=uid, tenant_id=tenant.id).first_or_404()
    u.durum = not u.durum; db.session.commit(); ok('Güncellendi.')
    return redirect(url_for('t_admin', slug=slug) + '#urunler')


@app.route('/r/<slug>/admin/urun_one/<int:uid>')
@login_required
def t_urun_one(slug, tenant, me, uid):
    u = Urun.query.filter_by(id=uid, tenant_id=tenant.id).first_or_404()
    u.one_cikan = not u.one_cikan; db.session.commit(); ok('Güncellendi.')
    return redirect(url_for('t_admin', slug=slug) + '#urunler')


@app.route('/r/<slug>/admin/urun_sil/<int:uid>')
@login_required
def t_urun_sil(slug, tenant, me, uid):
    u = Urun.query.filter_by(id=uid, tenant_id=tenant.id).first_or_404()
    db.session.delete(u); db.session.commit(); ok('Silindi.')
    return redirect(url_for('t_admin', slug=slug) + '#urunler')


@app.route('/r/<slug>/admin/gorsel_indir', methods=['POST'])
@login_required
def t_gorsel_indir(slug, tenant, me):
    from food_photos import sync_restaurant_photos
    stats = sync_restaurant_photos(tenant, db, force=True)
    ok(f"{stats['products_ok']} urun + {stats['categories_ok']} kategori gorseli indirildi.")
    if stats['products_fail'] or stats['categories_fail']:
        err(f"{stats['products_fail']} urun, {stats['categories_fail']} kategori indirilemedi.")
    return redirect(url_for('t_admin', slug=slug) + '#urunler')


# â”€â”€ Excel Aktarım â”€â”€
@app.route('/r/<slug>/admin/excel_sablon')
@login_required
def t_excel_sablon(slug, tenant, me):
    wb = openpyxl.Workbook(); ws = wb.active; ws.title = 'Urunler'
    ws.append(['Kategori Adı','Ürün Adı (TR)','Ürün Adı (EN)',
               'Fiyat','Açıklama (TR)','Açıklama (EN)',
               'Öne Çıkan(1/0)','Yeni(1/0)','Popüler(1/0)','Acılı(1/0)'])
    ws.append(['Pizzalar','Margarita','Margherita','120','Klasik pizza','Classic pizza','0','1','0','0'])
    for col in ws.columns:
        ws.column_dimensions[col[0].column_letter].width = 22
    buf = BytesIO(); wb.save(buf); buf.seek(0)
    return send_file(buf, download_name='urun_sablon.xlsx', as_attachment=True,
                     mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')


@app.route('/r/<slug>/admin/excel_yukle', methods=['POST'])
@login_required
def t_excel_yukle(slug, tenant, me):
    from flask import jsonify
    f = request.files.get('excel_file')
    if not f or not f.filename.endswith(('.xlsx','.xls')):
        return jsonify({'ok': False, 'mesaj': 'Geçerli bir .xlsx dosyası seç.', 'hatalar': []})
    try:
        wb = openpyxl.load_workbook(f, data_only=True); ws = wb.active
    except Exception:
        return jsonify({'ok': False, 'mesaj': 'Dosya okunamadı.', 'hatalar': []})

    eklenen, hatalar = 0, []
    for rn, row in enumerate(ws.iter_rows(min_row=2, values_only=True), 2):
        if not any(row): continue
        try:
            kat_isim = str(row[0] or '').strip()
            isim     = str(row[1] or '').strip()
            if not kat_isim or not isim:
                hatalar.append(f'Satır {rn}: Kategori/ürün adı boş.'); continue
            fiyat = parse_price(row[3])
            if fiyat is None:
                hatalar.append(f'Satır {rn}: Geçersiz fiyat.'); continue
            kat = Kategori.query.filter_by(tenant_id=tenant.id, isim=kat_isim).first()
            if not kat:
                kat = Kategori(tenant_id=tenant.id, isim=kat_isim, isim_en='', resim='', durum=True)
                db.session.add(kat); db.session.flush()
            db.session.add(Urun(
                tenant_id=tenant.id, kategori_id=kat.id,
                isim=isim, isim_en=str(row[2] or isim).strip(),
                fiyat=fiyat,
                aciklama=str(row[4] or '').strip(),
                aciklama_en=str(row[5] or '').strip(),
                resim='', durum=True,
                one_cikan=str(row[6] or '0').strip()=='1',
                badge_yeni=str(row[7] or '0').strip()=='1',
                badge_populer=str(row[8] or '0').strip()=='1',
                badge_acili=str(row[9] or '0').strip()=='1',
                aci_seviyesi=int(row[10]) if len(row) > 10 and str(row[10]).strip().isdigit() else 2,
            ))
            eklenen += 1
        except Exception as e:
            hatalar.append(f'Satır {rn}: {e}')
    if eklenen:
        stamp_price_update(tenant)
    db.session.commit()

    if eklenen and not hatalar:
        return jsonify({'ok': True, 'mesaj': f'{eklenen} ürün başarıyla aktarıldı!', 'hatalar': []})
    elif eklenen and hatalar:
        return jsonify({'ok': True, 'mesaj': f'{eklenen} ürün aktarıldı, bazı satırlarda hata var.', 'hatalar': hatalar[:10]})
    else:
        return jsonify({'ok': False, 'mesaj': 'Hiç ürün aktarılamadı.', 'hatalar': hatalar[:10]})


# â”€â”€ Kullanıcılar â”€â”€
@app.route('/r/<slug>/admin/kullanici_ekle', methods=['POST'])
@login_required
def t_kullanici_ekle(slug, tenant, me):
    if not me.is_superuser:
        err('Yetkisiz.'); return redirect(url_for('t_admin', slug=slug) + '#kullanicilar')
    uname = clean(request.form.get('username'))
    pw    = request.form.get('password','')
    if not uname or not pw:
        err('Ad ve şifre zorunlu.')
    elif Kullanici.query.filter_by(tenant_id=tenant.id, username=uname).first():
        err('Bu kullanıcı adı var.')
    else:
        u = Kullanici(tenant_id=tenant.id, username=uname,
                      is_superuser=bool(request.form.get('is_superuser')))
        u.set_password(pw); db.session.add(u); db.session.commit(); ok('Kullanıcı eklendi.')
    return redirect(url_for('t_admin', slug=slug) + '#kullanicilar')


@app.route('/r/<slug>/admin/kullanici_sil/<int:kid>')
@login_required
def t_kullanici_sil(slug, tenant, me, kid):
    if not me.is_superuser:
        err('Yetkisiz.'); return redirect(url_for('t_admin', slug=slug) + '#kullanicilar')
    u = Kullanici.query.filter_by(id=kid, tenant_id=tenant.id).first_or_404()
    if u.id == me.id:
        err('Kendinizi silemezsiniz.')
    else:
        db.session.delete(u); db.session.commit(); ok('Silindi.')
    return redirect(url_for('t_admin', slug=slug) + '#kullanicilar')


@app.route('/r/<slug>/admin/sifre/<int:kid>', methods=['POST'])
@login_required
def t_sifre(slug, tenant, me, kid):
    u = Kullanici.query.filter_by(id=kid, tenant_id=tenant.id).first_or_404()
    if not me.is_superuser and u.id != me.id:
        err('Yetkisiz.'); return redirect(url_for('t_admin', slug=slug) + '#kullanicilar')
    pw = request.form.get('new_password','')
    if not pw: err('Åifre boş olamaz.')
    else: u.set_password(pw); db.session.commit(); ok('Åifre güncellendi.')
    return redirect(url_for('t_admin', slug=slug) + '#kullanicilar')


# â”€â”€ QR Kodlar â”€â”€
@app.route('/r/<slug>/admin/qr_olustur', methods=['POST'])
@login_required
def t_qr_olustur(slug, tenant, me):
    isim  = clean(request.form.get('isim'), 'Menü QR')
    url   = clean(request.form.get('hedef_url'), f'{request.host_url}r/{slug}/')
    fg    = clean(request.form.get('renk_on'),   '#000000')
    bg    = clean(request.form.get('renk_arka'), '#ffffff')
    logo_p = None
    if request.form.get('logo_ekle') and tenant.logo:
        for sub in ('ayarlar','kategoriler'):
            c = os.path.join(app.config['UPLOAD_FOLDER'], slug, sub, tenant.logo)
            if os.path.exists(c): logo_p = c; break
    fname = f'{uuid.uuid4().hex}.png'
    path  = os.path.join(upload_dir(slug, 'qrcodes'), fname)
    make_qr(url, fg, bg, logo_p).save(path)
    db.session.add(QRCodeItem(
        tenant_id=tenant.id, isim=isim, hedef_url=url, dosya=fname,
        kilitli=True, silme_hazir=False, renk_on=fg, renk_arka=bg,
        logo_var=(logo_p is not None)))
    db.session.commit(); ok('QR oluşturuldu.')
    return redirect(url_for('t_admin', slug=slug) + '#qrcodes')


@app.route('/r/<slug>/admin/qr_kilit/<int:qid>')
@login_required
def t_qr_kilit(slug, tenant, me, qid):
    q = QRCodeItem.query.filter_by(id=qid, tenant_id=tenant.id).first_or_404()
    q.kilitli = not q.kilitli
    if q.kilitli: q.silme_hazir = False
    db.session.commit(); ok('Kilit güncellendi.')
    return redirect(url_for('t_admin', slug=slug) + '#qrcodes')


@app.route('/r/<slug>/admin/qr_hazirla/<int:qid>')
@login_required
def t_qr_hazirla(slug, tenant, me, qid):
    q = QRCodeItem.query.filter_by(id=qid, tenant_id=tenant.id).first_or_404()
    if q.kilitli: err('Önce kilidi aç.')
    else: q.silme_hazir = True; db.session.commit(); ok('Adım 1 aktif.')
    return redirect(url_for('t_admin', slug=slug) + '#qrcodes')


@app.route('/r/<slug>/admin/qr_iptal/<int:qid>')
@login_required
def t_qr_iptal(slug, tenant, me, qid):
    q = QRCodeItem.query.filter_by(id=qid, tenant_id=tenant.id).first_or_404()
    q.silme_hazir = False; db.session.commit(); ok('Ä°ptal edildi.')
    return redirect(url_for('t_admin', slug=slug) + '#qrcodes')


@app.route('/r/<slug>/admin/qr_sil/<int:qid>')
@login_required
def t_qr_sil(slug, tenant, me, qid):
    q = QRCodeItem.query.filter_by(id=qid, tenant_id=tenant.id).first_or_404()
    if not q.kilitli and q.silme_hazir:
        fp = os.path.join(upload_dir(slug, 'qrcodes'), q.dosya)
        if os.path.exists(fp): os.remove(fp)
        db.session.delete(q); db.session.commit(); ok('QR silindi.')
    else: err('Koşullar saÄŸlanmadı.')
    return redirect(url_for('t_admin', slug=slug) + '#qrcodes')


@app.route('/r/<slug>/admin/qr_yedek')
@login_required
def t_qr_yedek(slug, tenant, me):
    import zipfile

    qrs = QRCodeItem.query.filter_by(tenant_id=tenant.id).order_by(QRCodeItem.id.asc()).all()
    payload = {
        'version': 1,
        'type': 'qr_backup',
        'tenant_slug': tenant.slug,
        'tenant_name': tenant.restoran_adi,
        'exported_at': datetime.utcnow().isoformat() + 'Z',
        'qrcodes': [
            {
                'id': q.id,
                'isim': q.isim,
                'hedef_url': q.hedef_url,
                'dosya': q.dosya,
                'kilitli': q.kilitli,
                'silme_hazir': q.silme_hazir,
                'renk_on': q.renk_on,
                'renk_arka': q.renk_arka,
                'logo_var': q.logo_var,
            }
            for q in qrs
        ],
    }

    buf = BytesIO()
    with zipfile.ZipFile(buf, 'w', compression=zipfile.ZIP_DEFLATED) as z:
        z.writestr('qr_backup.json', json.dumps(payload, ensure_ascii=False, indent=2))
        base_dir = upload_dir(slug, 'qrcodes')
        for q in qrs:
            fp = os.path.join(base_dir, q.dosya)
            if os.path.exists(fp):
                z.write(fp, arcname=f'qrcodes/{q.dosya}')

    buf.seek(0)
    fname = f'qr_yedek_{slug}_{datetime.utcnow().strftime("%Y%m%d_%H%M%S")}.zip'
    return send_file(buf, as_attachment=True, download_name=fname, mimetype='application/zip')


@app.route('/r/<slug>/admin/qr_yukle', methods=['POST'])
@login_required
def t_qr_yukle(slug, tenant, me):
    import zipfile

    def _bool(v, default=False):
        if v is None:
            return default
        if isinstance(v, bool):
            return v
        if isinstance(v, (int, float)):
            return bool(v)
        s = str(v).strip().lower()
        if s in ('1', 'true', 'yes', 'on', 'evet'):
            return True
        if s in ('0', 'false', 'no', 'off', ''):
            return False
        return default

    file = request.files.get('backup_file')
    if not file or not file.filename.lower().endswith('.zip'):
        err('Geçerli bir QR yedeği (.zip) seç.')
        return redirect(url_for('t_admin', slug=slug) + '#qrcodes')

    restore_mode = request.form.get('restore_mode', 'replace')
    try:
        zf = zipfile.ZipFile(file.stream)
        names = set(zf.namelist())
        if 'qr_backup.json' not in names:
            raise ValueError('qr_backup.json bulunamadı.')
        payload = json.loads(zf.read('qr_backup.json').decode('utf-8'))
        if payload.get('type') != 'qr_backup':
            raise ValueError('Yedek türü QR değil.')
    except Exception as e:
        err(f'Yedek okunamadı: {e}')
        return redirect(url_for('t_admin', slug=slug) + '#qrcodes')

    base_dir = upload_dir(slug, 'qrcodes')
    os.makedirs(base_dir, exist_ok=True)

    if restore_mode == 'replace':
        for old in QRCodeItem.query.filter_by(tenant_id=tenant.id).all():
            try:
                os.remove(os.path.join(base_dir, old.dosya))
            except OSError:
                pass
            db.session.delete(old)
        db.session.commit()

    imported = 0
    skipped = 0
    for item in payload.get('qrcodes', []):
        src_name = item.get('dosya') or f'{uuid.uuid4().hex}.png'
        arc_name = f'qrcodes/{src_name}'
        if arc_name not in names:
            skipped += 1
            continue

        target_name = src_name
        if restore_mode != 'replace':
            root, ext = os.path.splitext(target_name)
            idx = 1
            while os.path.exists(os.path.join(base_dir, target_name)):
                target_name = f'{root}_{idx}{ext or ".png"}'
                idx += 1

        with open(os.path.join(base_dir, target_name), 'wb') as out:
            out.write(zf.read(arc_name))

        db.session.add(QRCodeItem(
            tenant_id=tenant.id,
            isim=item.get('isim') or 'QR',
            hedef_url=item.get('hedef_url') or f'{request.host_url}r/{slug}/',
            dosya=target_name,
            kilitli=_bool(item.get('kilitli'), True),
            silme_hazir=_bool(item.get('silme_hazir'), False),
            renk_on=item.get('renk_on') or '#000000',
            renk_arka=item.get('renk_arka') or '#ffffff',
            logo_var=_bool(item.get('logo_var'), False),
        ))
        imported += 1

    db.session.commit()
    ok(f'{imported} QR kod içe aktarıldı. {skipped} öğe atlandı.')
    return redirect(url_for('t_admin', slug=slug) + '#qrcodes')


@app.route('/superadmin/sifre/<int:tid>', methods=['POST'])
@sa_required
def sa_sifre(tid):
    t = Tenant.query.get_or_404(tid)
    pw = request.form.get('new_password', '').strip()
    if not pw:
        err('Åifre boş olamaz.')
        return redirect(url_for('sa_panel'))
    u = Kullanici.query.filter_by(tenant_id=t.id, is_superuser=True).first()
    if not u:
        err('Admin kullanıcı bulunamadı.')
        return redirect(url_for('sa_panel'))
    u.set_password(pw)
    db.session.commit()
    ok(f'"{t.restoran_adi}" admin şifresi güncellendi.')
    return redirect(url_for('sa_panel'))


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
#  MÜŞTERİ YÖNETİMİ
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•


@app.route('/superadmin/musteri_ekle', methods=['POST'])
@sa_required
def sa_musteri_ekle():
    ad = (request.form.get('ad_soyad') or '').strip()
    if not ad:
        err('Ad Soyad zorunludur.'); return redirect(url_for('sa_panel'))
    kod = musteri_kodu_uret()
    m = Musteri(
        musteri_kodu = kod,
        ad_soyad     = ad,
        telefon      = (request.form.get('telefon') or '').strip(),
        email        = (request.form.get('email') or '').strip(),
        tc_vkn       = (request.form.get('tc_vkn') or '').strip(),
        sehir        = (request.form.get('sehir') or '').strip(),
        ilce         = (request.form.get('ilce') or '').strip(),
        notlar       = (request.form.get('notlar') or '').strip(),
    )
    db.session.add(m)
    db.session.commit()
    m.referans_kodu = referans_kodu_uret(m.id)
    db.session.commit()
    ok(f'Müşteri "{ad}" oluşturuldu. Kod: {kod}')
    return redirect(url_for('sa_panel'))


@app.route('/superadmin/musteri_duzenle/<int:mid>', methods=['POST'])
@sa_required
def sa_musteri_duzenle(mid):
    m = Musteri.query.get_or_404(mid)
    m.ad_soyad = (request.form.get('ad_soyad') or m.ad_soyad).strip()
    m.telefon  = (request.form.get('telefon') or '').strip()
    m.email    = (request.form.get('email') or '').strip()
    m.tc_vkn   = (request.form.get('tc_vkn') or '').strip()
    m.sehir    = (request.form.get('sehir') or '').strip()
    m.ilce     = (request.form.get('ilce') or '').strip()
    m.notlar   = (request.form.get('notlar') or '').strip()
    db.session.commit()
    ok('Müşteri güncellendi.')
    return redirect(url_for('sa_panel'))


@app.route('/superadmin/musteri_sil/<int:mid>', methods=['POST'])
@sa_required
def sa_musteri_sil(mid):
    m = Musteri.query.get_or_404(mid)
    for t in m.restoranlar:
        t.musteri_id = None
    db.session.delete(m)
    db.session.commit()
    ok('Müşteri silindi.')
    return redirect(url_for('sa_panel'))


@app.route('/superadmin/lisans_ata/<int:mid>', methods=['POST'])
@sa_required
def sa_lisans_ata(mid):
    m    = Musteri.query.get_or_404(mid)
    slug = (request.form.get('slug') or '').lower().strip().replace(' ', '-')
    isim = (request.form.get('restoran_adi') or m.ad_soyad).strip()
    pw   = request.form.get('password', 'admin123')
    paket = request.form.get('paket', 'temel')
    sure  = int(request.form.get('sure', 12) or 12)
    ucret = float(request.form.get('ucret', 0) or 0)
    odeme = request.form.get('odeme_tipi', 'nakit')
    odendi = bool(request.form.get('odendi_mi'))
    referans_kodu = clean(request.form.get('referans_kodu')).upper()

    if not slug:
        err('Slug zorunludur.'); return redirect(url_for('sa_panel'))
    if Tenant.query.filter_by(slug=slug).first():
        err(f'"{slug}" zaten kullanımda.'); return redirect(url_for('sa_panel'))

    bas   = datetime.now()
    bitis = bas + timedelta(days=14) if paket == 'deneme' else bas + timedelta(days=30 * sure)
    kod   = restoran_kodu_uret()
    referrer = Musteri.query.filter_by(referans_kodu=referans_kodu).first() if referans_kodu else None

    t = Tenant(
        slug=slug, restoran_adi=isim, paket=paket,
        aktif=True, musteri_id=m.id,
        restoran_kodu=kod,
        lisans_bitis=bitis,
        lisans_tipi=request.form.get('lisans_tipi', 'yillik'),
        ucret=0 if paket == 'deneme' else ucret,
        odeme_tipi=odeme,
        odendi_mi=odendi if paket != 'deneme' else False,
        sozlesme_tarihi=bas,
        referrer_id=referrer.id if referrer and referrer.id != m.id else None,
    )
    db.session.add(t); db.session.flush()

    u = Kullanici(tenant_id=t.id, username='admin', is_superuser=True)
    u.set_password(pw)
    db.session.add(u)
    db.session.commit()

    for sub in ['kategoriler', 'urunler', 'qrcodes', 'ayarlar']:
        upload_dir(slug, sub)

    sure_mesaji = '14 günlük deneme' if paket == 'deneme' else f'{sure} ay lisans'
    ok(f'Restoran "{isim}" oluşturuldu. Kod: {kod} | {sure_mesaji} | /r/{slug}/')
    return redirect(url_for('sa_panel'))


@app.route('/superadmin/lisans_yenile/<int:tid>', methods=['POST'])
@sa_required
def sa_lisans_yenile(tid):
    t    = Tenant.query.get_or_404(tid)
    sure = int(request.form.get('sure', 12) or 12)
    bas  = t.lisans_bitis if t.lisans_bitis and t.lisans_bitis > datetime.now() else datetime.now()
    t.lisans_bitis = bas + timedelta(days=30 * sure)
    t.aktif = True
    db.session.commit()
    ok(f'{t.restoran_adi} lisansı {sure} ay uzatıldı.')
    return redirect(url_for('sa_panel'))


@app.route('/superadmin/musteri_export')
@sa_required
def sa_musteri_export():
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = 'Musteriler'
    ws.append([
        'Musteri Kodu', 'Referans Kodu', 'Ad Soyad', 'Telefon', 'E-posta',
        'Sehir', 'Ilce', 'Restoran Sayisi', 'Toplam Gelir', 'Son Iletisim'
    ])

    musteriler = Musteri.query.order_by(Musteri.created_at.desc(), Musteri.id.desc()).all()
    for musteri in musteriler:
        restoranlar = Tenant.query.filter_by(musteri_id=musteri.id).all()
        son_iletisimler = [t.son_iletisim for t in restoranlar if t.son_iletisim]
        son_iletisim = max(son_iletisimler).strftime('%d.%m.%Y %H:%M') if son_iletisimler else ''
        ws.append([
            musteri.musteri_kodu,
            musteri.referans_kodu or referans_kodu_uret(musteri.id),
            musteri.ad_soyad,
            musteri.telefon,
            musteri.email,
            musteri.sehir,
            musteri.ilce,
            len(restoranlar),
            round(sum(t.ucret or 0 for t in restoranlar), 2),
            son_iletisim,
        ])

    for col in ws.columns:
        width = max(len(str(cell.value or '')) for cell in col[:20]) + 4
        ws.column_dimensions[col[0].column_letter].width = min(max(width, 14), 28)

    buf = BytesIO()
    wb.save(buf)
    buf.seek(0)
    return send_file(
        buf,
        download_name=f'musteriler_{datetime.now().strftime("%Y%m%d_%H%M")}.xlsx',
        as_attachment=True,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )


@app.route('/superadmin/referans_export')
@sa_required
def sa_referans_export():
    """Referans sistemi Excel export"""
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = 'Referanslar'
    ws.append(['Musteri Kodu', 'Ad Soyad', 'Referans Kodu', 'Yonlendirme Sayisi', 'Gelir (TL)'])
    musteriler = Musteri.query.order_by(Musteri.id).all()
    for m in musteriler:
        referred = Tenant.query.filter_by(referrer_id=m.id).all()
        gelir = sum(t.ucret or 0 for t in referred)
        ws.append([
            m.musteri_kodu,
            m.ad_soyad,
            m.referans_kodu or '',
            len(referred),
            round(gelir, 2),
        ])
    buf = BytesIO()
    wb.save(buf); buf.seek(0)
    return send_file(buf,
        download_name=f'referanslar_{datetime.now().strftime("%Y%m%d_%H%M")}.xlsx',
        as_attachment=True,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )


@app.route('/superadmin/iletisim/<int:tid>', methods=['POST'])
@sa_required
def sa_iletisim(tid):
    from datetime import datetime
    t = Tenant.query.get_or_404(tid)
    t.iletisim_notu = (request.form.get('iletisim_notu') or '').strip()
    t.son_iletisim  = datetime.now()
    db.session.commit()
    ok('Ä°letişim notu güncellendi.')
    return redirect(url_for('sa_panel'))



# â”€â”€ Resim Kaldır â”€â”€
@app.route('/r/<slug>/admin/kat_resim_sil/<int:kid>/<tip>')
@login_required
def t_kat_resim_sil(slug, tenant, me, kid, tip):
    from flask import jsonify
    k = Kategori.query.filter_by(id=kid, tenant_id=tenant.id).first_or_404()
    if tip == 'resim':
        if k.resim:
            try: os.remove(os.path.join(upload_dir(slug, 'kategoriler'), k.resim))
            except: pass
        k.resim = ''
    elif tip == 'banner':
        if k.banner:
            try: os.remove(os.path.join(upload_dir(slug, 'kategoriler'), k.banner))
            except: pass
        k.banner = ''
    db.session.commit()
    return jsonify({'ok': True})


@app.route('/r/<slug>/admin/urun_resim_sil/<int:uid>')
@login_required
def t_urun_resim_sil(slug, tenant, me, uid):
    from flask import jsonify
    u = Urun.query.filter_by(id=uid, tenant_id=tenant.id).first_or_404()
    if u.resim:
        try: os.remove(os.path.join(upload_dir(slug, 'urunler'), u.resim))
        except: pass
    u.resim = ''
    db.session.commit()
    return jsonify({'ok': True})


# â”€â”€ Sıralama â”€â”€
@app.route('/r/<slug>/admin/kat_sirala', methods=['POST'])
@login_required
def t_kat_sirala(slug, tenant, me):
    from flask import jsonify
    ids = request.json.get('ids', [])
    for i, kid in enumerate(ids):
        k = Kategori.query.filter_by(id=kid, tenant_id=tenant.id).first()
        if k: k.sira = i
    db.session.commit()
    return jsonify({'ok': True})


@app.route('/r/<slug>/admin/urun_sirala', methods=['POST'])
@login_required
def t_urun_sirala(slug, tenant, me):
    from flask import jsonify
    ids = request.json.get('ids', [])
    for i, uid in enumerate(ids):
        u = Urun.query.filter_by(id=uid, tenant_id=tenant.id).first()
        if u: u.sira = i
    db.session.commit()
    return jsonify({'ok': True})


@app.route('/r/<slug>/admin/hizli_fiyat/<int:uid>', methods=['POST'])
@login_required
def t_hizli_fiyat(slug, tenant, me, uid):
    from flask import jsonify
    u = Urun.query.filter_by(id=uid, tenant_id=tenant.id).first_or_404()
    fiyat = parse_price(request.form.get('fiyat'))
    if fiyat is None or fiyat < 0:
        return jsonify({'ok': False, 'mesaj': 'Geçersiz fiyat.'})
    u.fiyat = fiyat
    stamp_price_update(tenant)
    db.session.commit()
    return jsonify({'ok': True, 'fiyat': fiyat})


@app.route('/r/<slug>/admin/fiyat_pdf')
@login_required
def t_fiyat_pdf(slug, tenant, me):
    """Yasal fiyat listesi PDF'i (Fiyat Etiketi YönetmeliÄŸi'ne uygun)"""
    from io import BytesIO
    from datetime import datetime
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.pdfgen import canvas
        from reportlab.lib.units import cm
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
    except ImportError:
        return 'PDF kütüphanesi eksik. Terminalde çalıştırın: pip install reportlab', 500

    # Türkçe karakter desteÄŸi için font
    import os as _os
    font_paths = [
        'C:/Windows/Fonts/arial.ttf',
        'C:/Windows/Fonts/calibri.ttf',
        '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
        '/Library/Fonts/Arial.ttf',
    ]
    font_name = 'Helvetica'
    font_bold = 'Helvetica-Bold'
    for fp in font_paths:
        if _os.path.exists(fp):
            try:
                pdfmetrics.registerFont(TTFont('TR', fp))
                font_name = 'TR'
                # Bold variant
                bold_path = fp.replace('.ttf', 'bd.ttf').replace('arial', 'arialbd')
                if _os.path.exists(bold_path):
                    pdfmetrics.registerFont(TTFont('TR-Bold', bold_path))
                    font_bold = 'TR-Bold'
                else:
                    font_bold = 'TR'
                break
            except: pass

    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    margin = 2 * cm

    # Başlık
    y = height - margin
    p.setFont(font_bold, 18)
    p.drawCentredString(width/2, y, tenant.restoran_adi or 'Restoran')
    y -= 0.7 * cm
    p.setFont(font_name, 10)
    p.setFillColorRGB(0.4, 0.4, 0.4)
    p.drawCentredString(width/2, y, 'FIYAT LISTESI')
    y -= 0.5 * cm
    p.setFont(font_name, 8)
    p.drawCentredString(width/2, y, f'Guncel Tarih: {datetime.now().strftime("%d.%m.%Y %H:%M")}')
    y -= 0.4 * cm

    # Yasal not
    p.setFont(font_name, 7)
    p.setFillColorRGB(0.6, 0.6, 0.6)
    p.drawCentredString(width/2, y, 'Fiyat Etiketi Yonetmeligi (R.G. 11.10.2025/33044) kapsaminda hazirlanmistir.')
    y -= 0.8 * cm

    # Çizgi
    p.setStrokeColorRGB(0.85, 0.85, 0.85)
    p.line(margin, y, width - margin, y)
    y -= 0.7 * cm

    # Kategoriler
    p.setFillColorRGB(0, 0, 0)
    kategoriler = Kategori.query.filter_by(tenant_id=tenant.id, durum=True).order_by(Kategori.sira, Kategori.id).all()

    for kat in kategoriler:
        urunler = [u for u in kat.urunler if u.durum]
        if not urunler:
            continue

        # Yeni sayfa kontrol
        if y < margin + 4*cm:
            p.showPage()
            y = height - margin

        # Kategori başlıÄŸı
        p.setFillColorRGB(0.95, 0.61, 0.07)
        p.rect(margin, y - 0.3*cm, width - 2*margin, 0.7*cm, fill=1, stroke=0)
        p.setFillColorRGB(1, 1, 1)
        p.setFont(font_bold, 11)
        p.drawString(margin + 0.3*cm, y - 0.05*cm, kat.isim.upper())
        y -= 1.2 * cm

        # Ürünler
        p.setFillColorRGB(0, 0, 0)
        for u in urunler:
            if y < margin + 1*cm:
                p.showPage()
                y = height - margin

            p.setFont(font_bold, 10)
            p.drawString(margin + 0.3*cm, y, u.isim)
            p.setFont(font_bold, 10)
            fiyat_str = f"{u.fiyat:,.2f} TL".replace(",", ".")
            p.drawRightString(width - margin - 0.3*cm, y, fiyat_str)

            if u.aciklama:
                y -= 0.45 * cm
                p.setFont(font_name, 8)
                p.setFillColorRGB(0.5, 0.5, 0.5)
                aciklama = u.aciklama[:120] + ('...' if len(u.aciklama) > 120 else '')
                p.drawString(margin + 0.3*cm, y, aciklama)
                p.setFillColorRGB(0, 0, 0)

            y -= 0.55 * cm

        y -= 0.4 * cm

    # Alt bilgi - sayfa sonuna
    p.setFont(font_name, 8)
    p.setFillColorRGB(0.5, 0.5, 0.5)
    if tenant.kdv_dahil:
        p.drawCentredString(width/2, margin/2, '* Fiyatlara KDV dahildir.')

    p.save()
    buffer.seek(0)

    from flask import send_file
    return send_file(
        buffer,
        as_attachment=True,
        download_name=f'{slug}_fiyat_listesi_{datetime.now().strftime("%Y%m%d")}.pdf',
        mimetype='application/pdf'
    )


# API Endpoints for Admin Data Integration
@app.route('/api/tenant/<slug>')
def api_tenant(slug):
    """Get tenant information for mobile app"""
    tenant = Tenant.query.filter_by(slug=slug, aktif=True).first_or_404()
    return jsonify({
        'restoran_adi': tenant.restoran_adi,
        'restoran_adi_en': tenant.restoran_adi_en or tenant.restoran_adi,
        'splash_text': tenant.splash_text,
        'acilis_saati': tenant.acilis_saati,
        'kapanis_saati': tenant.kapanis_saati,
        'whatsapp': tenant.whatsapp,
        'instagram': tenant.instagram,
        'konum_url': tenant.konum_url,
        'logo': tenant.logo,
        'tema': tenant.tema,
        'kdv_dahil': tenant.kdv_dahil,
        'son_fiyat_guncelleme': tenant.son_fiyat_guncelleme.isoformat() if tenant.son_fiyat_guncelleme else None
    })

@app.route('/api/categories/<slug>')
def api_categories(slug):
    """Get categories for mobile app"""
    tenant = Tenant.query.filter_by(slug=slug, aktif=True).first_or_404()
    categories = Kategori.query.filter_by(tenant_id=tenant.id, durum=True).order_by(Kategori.sira, Kategori.id).all()
    
    result = []
    for cat in categories:
        result.append({
            'id': cat.id,
            'isim': cat.isim,
            'isim_en': cat.isim_en or cat.isim,
            'resim': cat.resim,
            'banner': cat.banner,
            'sira': cat.sira,
            'urunler': len([u for u in cat.urunler if u.durum])
        })
    
    return jsonify(result)

@app.route('/api/products/<slug>')
def api_products(slug):
    """Get products for mobile app"""
    tenant = Tenant.query.filter_by(slug=slug, aktif=True).first_or_404()
    products = Urun.query.filter_by(tenant_id=tenant.id, durum=True).order_by(Urun.sira, Urun.id).all()
    
    result = []
    for prod in products:
        result.append({
            'id': prod.id,
            'kategori_id': prod.kategori_id,
            'isim': prod.isim,
            'isim_en': prod.isim_en or prod.isim,
            'fiyat': prod.fiyat,
            'aciklama': prod.aciklama,
            'aciklama_en': prod.aciklama_en or prod.aciklama,
            'resim': prod.resim,
            'one_cikan': prod.one_cikan,
            'badge_yeni': prod.badge_yeni,
            'badge_populer': prod.badge_populer,
            'badge_acili': prod.badge_acili,
            'aci_seviyesi': prod.aci_seviyesi,
            'alerjen_notu': prod.alerjen_notu,
            'alerjen_notu_en': prod.alerjen_notu_en or prod.alerjen_notu,
            'sira': prod.sira
        })
    
    return jsonify(result)

@app.route('/api/featured/<slug>')
def api_featured(slug):
    """Get featured products for mobile app"""
    tenant = Tenant.query.filter_by(slug=slug, aktif=True).first_or_404()
    products = Urun.query.filter_by(tenant_id=tenant.id, durum=True, one_cikan=True).order_by(Urun.sira, Urun.id).all()
    
    result = []
    for prod in products:
        result.append({
            'id': prod.id,
            'kategori_id': prod.kategori_id,
            'isim': prod.isim,
            'isim_en': prod.isim_en or prod.isim,
            'fiyat': prod.fiyat,
            'resim': prod.resim,
            'badge_yeni': prod.badge_yeni,
            'badge_populer': prod.badge_populer,
            'badge_acili': prod.badge_acili
        })
    
    return jsonify(result)


if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=5000)
