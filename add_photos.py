"""
Ürün Fotoğrafı Otomatik İndirici v2 - Pexels CDN
Kullanım: python add_photos.py
app.py ile aynı klasörde çalıştır.
"""

import argparse
import os
import time
import requests
from PIL import Image
from io import BytesIO

from app import app, db, Tenant, Urun

SLUG = "test"

# Pexels CDN — ücretsiz, API key gerektirmez, stabil URL'ler
FOOD_PHOTOS = {
    "Mercimek Çorbası":     "https://images.pexels.com/photos/539451/pexels-photo-539451.jpeg?auto=compress&cs=tinysrgb&w=600&h=600&fit=crop",
    "Ezogelin Çorbası":     "https://images.pexels.com/photos/1731535/pexels-photo-1731535.jpeg?auto=compress&cs=tinysrgb&w=600&h=600&fit=crop",
    "İşkembe Çorbası":      "https://images.pexels.com/photos/1734278/pexels-photo-1734278.jpeg?auto=compress&cs=tinysrgb&w=600&h=600&fit=crop",
    "Tarhana Çorbası":      "https://images.pexels.com/photos/2116094/pexels-photo-2116094.jpeg?auto=compress&cs=tinysrgb&w=600&h=600&fit=crop",
    "Domates Çorbası":      "https://images.pexels.com/photos/1703272/pexels-photo-1703272.jpeg?auto=compress&cs=tinysrgb&w=600&h=600&fit=crop",
    "Yayla Çorbası":        "https://images.pexels.com/photos/1435706/pexels-photo-1435706.jpeg?auto=compress&cs=tinysrgb&w=600&h=600&fit=crop",
    "Paça Çorbası":         "https://images.pexels.com/photos/6605214/pexels-photo-6605214.jpeg?auto=compress&cs=tinysrgb&w=600&h=600&fit=crop",
    "Tavuk Suyu Çorba":    "https://images.pexels.com/photos/3184192/pexels-photo-3184192.jpeg?auto=compress&cs=tinysrgb&w=600&h=600&fit=crop",
    "Düğün Çorbası":       "https://images.pexels.com/photos/2641886/pexels-photo-2641886.jpeg?auto=compress&cs=tinysrgb&w=600&h=600&fit=crop",
    "Pırasa Çorbası":      "https://images.pexels.com/photos/1095550/pexels-photo-1095550.jpeg?auto=compress&cs=tinysrgb&w=600&h=600&fit=crop",
    "Humus":                "https://images.pexels.com/photos/1640777/pexels-photo-1640777.jpeg?auto=compress&cs=tinysrgb&w=600&h=600&fit=crop",
    "Haydari":              "https://images.pexels.com/photos/4331490/pexels-photo-4331490.jpeg?auto=compress&cs=tinysrgb&w=600&h=600&fit=crop",
    "Patlıcan Ezmesi":      "https://images.pexels.com/photos/5737254/pexels-photo-5737254.jpeg?auto=compress&cs=tinysrgb&w=600&h=600&fit=crop",
    "Acılı Ezme":           "https://images.pexels.com/photos/4518645/pexels-photo-4518645.jpeg?auto=compress&cs=tinysrgb&w=600&h=600&fit=crop",
    "Cacık":               "https://images.pexels.com/photos/5966431/pexels-photo-5966431.jpeg?auto=compress&cs=tinysrgb&w=600&h=600&fit=crop",
    "Sigara Böreği":        "https://images.pexels.com/photos/6107787/pexels-photo-6107787.jpeg?auto=compress&cs=tinysrgb&w=600&h=600&fit=crop",
    "Dolma":               "https://images.pexels.com/photos/5410400/pexels-photo-5410400.jpeg?auto=compress&cs=tinysrgb&w=600&h=600&fit=crop",
    "Tarama":              "https://images.pexels.com/photos/3655916/pexels-photo-3655916.jpeg?auto=compress&cs=tinysrgb&w=600&h=600&fit=crop",
    "Kısır":               "https://images.pexels.com/photos/1640772/pexels-photo-1640772.jpeg?auto=compress&cs=tinysrgb&w=600&h=600&fit=crop",
    "Yoğurtlu Patlıcan":   "https://images.pexels.com/photos/5737247/pexels-photo-5737247.jpeg?auto=compress&cs=tinysrgb&w=600&h=600&fit=crop",
    "Adana Kebap":          "https://images.pexels.com/photos/8887012/pexels-photo-8887012.jpeg?auto=compress&cs=tinysrgb&w=600&h=600&fit=crop",
    "Urfa Kebap":           "https://images.pexels.com/photos/410648/pexels-photo-410648.jpeg?auto=compress&cs=tinysrgb&w=600&h=600&fit=crop",
    "Kuzu Şiş":            "https://images.pexels.com/photos/1251198/pexels-photo-1251198.jpeg?auto=compress&cs=tinysrgb&w=600&h=600&fit=crop",
    "Tavuk Şiş":           "https://images.pexels.com/photos/2338407/pexels-photo-2338407.jpeg?auto=compress&cs=tinysrgb&w=600&h=600&fit=crop",
    "Karışık Izgara":      "https://images.pexels.com/photos/1105325/pexels-photo-1105325.jpeg?auto=compress&cs=tinysrgb&w=600&h=600&fit=crop",
    "Köfte":               "https://images.pexels.com/photos/6210747/pexels-photo-6210747.jpeg?auto=compress&cs=tinysrgb&w=600&h=600&fit=crop",
    "Beyti Kebap":         "https://images.pexels.com/photos/7394819/pexels-photo-7394819.jpeg?auto=compress&cs=tinysrgb&w=600&h=600&fit=crop",
    "Kanat Izgara":        "https://images.pexels.com/photos/60616/fried-chicken-chicken-fried-crunchy-60616.jpeg?auto=compress&cs=tinysrgb&w=600&h=600&fit=crop",
    "Patlıcanlı Kebap":    "https://images.pexels.com/photos/6107786/pexels-photo-6107786.jpeg?auto=compress&cs=tinysrgb&w=600&h=600&fit=crop",
    "İskender":            "https://images.pexels.com/photos/5836384/pexels-photo-5836384.jpeg?auto=compress&cs=tinysrgb&w=600&h=600&fit=crop",
    "Kaşarlı Pide":        "https://images.pexels.com/photos/4109111/pexels-photo-4109111.jpeg?auto=compress&cs=tinysrgb&w=600&h=600&fit=crop",
    "Kıymalı Pide":        "https://images.pexels.com/photos/5409010/pexels-photo-5409010.jpeg?auto=compress&cs=tinysrgb&w=600&h=600&fit=crop",
    "Sucuklu Pide":        "https://images.pexels.com/photos/6942024/pexels-photo-6942024.jpeg?auto=compress&cs=tinysrgb&w=600&h=600&fit=crop",
    "Kuşbaşılı Pide":      "https://images.pexels.com/photos/1146760/pexels-photo-1146760.jpeg?auto=compress&cs=tinysrgb&w=600&h=600&fit=crop",
    "Yumurtalı Pide":      "https://images.pexels.com/photos/4518623/pexels-photo-4518623.jpeg?auto=compress&cs=tinysrgb&w=600&h=600&fit=crop",
    "Peynirli Ispanaklı Pide": "https://images.pexels.com/photos/6107782/pexels-photo-6107782.jpeg?auto=compress&cs=tinysrgb&w=600&h=600&fit=crop",
    "Kavurmalı Pide":      "https://images.pexels.com/photos/2233729/pexels-photo-2233729.jpeg?auto=compress&cs=tinysrgb&w=600&h=600&fit=crop",
    "Karışık Pide":        "https://images.pexels.com/photos/4109117/pexels-photo-4109117.jpeg?auto=compress&cs=tinysrgb&w=600&h=600&fit=crop",
    "Lahmacun":            "https://images.pexels.com/photos/7423752/pexels-photo-7423752.jpeg?auto=compress&cs=tinysrgb&w=600&h=600&fit=crop",
    "Mantarlı Pide":       "https://images.pexels.com/photos/1640773/pexels-photo-1640773.jpeg?auto=compress&cs=tinysrgb&w=600&h=600&fit=crop",
    "Çoban Salata":        "https://images.pexels.com/photos/1213710/pexels-photo-1213710.jpeg?auto=compress&cs=tinysrgb&w=600&h=600&fit=crop",
    "Roka Salatası":       "https://images.pexels.com/photos/2097090/pexels-photo-2097090.jpeg?auto=compress&cs=tinysrgb&w=600&h=600&fit=crop",
    "Mevsim Salatası":     "https://images.pexels.com/photos/1199562/pexels-photo-1199562.jpeg?auto=compress&cs=tinysrgb&w=600&h=600&fit=crop",
    "Gavurdağı Salatası":  "https://images.pexels.com/photos/3722214/pexels-photo-3722214.jpeg?auto=compress&cs=tinysrgb&w=600&h=600&fit=crop",
    "Piyaz":               "https://images.pexels.com/photos/5950433/pexels-photo-5950433.jpeg?auto=compress&cs=tinysrgb&w=600&h=600&fit=crop",
    "Semizotu Salatası":   "https://images.pexels.com/photos/1640774/pexels-photo-1640774.jpeg?auto=compress&cs=tinysrgb&w=600&h=600&fit=crop",
    "Tahinli Patlıcan":    "https://images.pexels.com/photos/5737254/pexels-photo-5737254.jpeg?auto=compress&cs=tinysrgb&w=600&h=600&fit=crop",
    "Mercimek Salatası":   "https://images.pexels.com/photos/1640775/pexels-photo-1640775.jpeg?auto=compress&cs=tinysrgb&w=600&h=600&fit=crop",
    "Hellim Salatası":     "https://images.pexels.com/photos/2116094/pexels-photo-2116094.jpeg?auto=compress&cs=tinysrgb&w=600&h=600&fit=crop",
    "Tabule":              "https://images.pexels.com/photos/1640776/pexels-photo-1640776.jpeg?auto=compress&cs=tinysrgb&w=600&h=600&fit=crop",
    "Kuzu Tandır":         "https://images.pexels.com/photos/675951/pexels-photo-675951.jpeg?auto=compress&cs=tinysrgb&w=600&h=600&fit=crop",
    "İmam Bayıldı":        "https://images.pexels.com/photos/5737247/pexels-photo-5737247.jpeg?auto=compress&cs=tinysrgb&w=600&h=600&fit=crop",
    "Hünkârbeğendi":       "https://images.pexels.com/photos/8887012/pexels-photo-8887012.jpeg?auto=compress&cs=tinysrgb&w=600&h=600&fit=crop",
    "Karnıyarık":          "https://images.pexels.com/photos/6107789/pexels-photo-6107789.jpeg?auto=compress&cs=tinysrgb&w=600&h=600&fit=crop",
    "Etli Güveç":          "https://images.pexels.com/photos/2641886/pexels-photo-2641886.jpeg?auto=compress&cs=tinysrgb&w=600&h=600&fit=crop",
    "Mantı":              "https://images.pexels.com/photos/6107784/pexels-photo-6107784.jpeg?auto=compress&cs=tinysrgb&w=600&h=600&fit=crop",
    "Etli Yaprak Sarma":   "https://images.pexels.com/photos/5410400/pexels-photo-5410400.jpeg?auto=compress&cs=tinysrgb&w=600&h=600&fit=crop",
    "Terbiyeli Köfte":     "https://images.pexels.com/photos/6210747/pexels-photo-6210747.jpeg?auto=compress&cs=tinysrgb&w=600&h=600&fit=crop",
    "Fırın Tavuk":         "https://images.pexels.com/photos/2338407/pexels-photo-2338407.jpeg?auto=compress&cs=tinysrgb&w=600&h=600&fit=crop",
    "Ali Nazik":           "https://images.pexels.com/photos/5836384/pexels-photo-5836384.jpeg?auto=compress&cs=tinysrgb&w=600&h=600&fit=crop",
    "Türk Pilavı":         "https://images.pexels.com/photos/723198/pexels-photo-723198.jpeg?auto=compress&cs=tinysrgb&w=600&h=600&fit=crop",
    "Bulgur Pilavı":       "https://images.pexels.com/photos/1640772/pexels-photo-1640772.jpeg?auto=compress&cs=tinysrgb&w=600&h=600&fit=crop",
    "İç Pilav":            "https://images.pexels.com/photos/1640773/pexels-photo-1640773.jpeg?auto=compress&cs=tinysrgb&w=600&h=600&fit=crop",
    "Nohutlu Pilav":       "https://images.pexels.com/photos/5950433/pexels-photo-5950433.jpeg?auto=compress&cs=tinysrgb&w=600&h=600&fit=crop",
    "Erişte":             "https://images.pexels.com/photos/3184192/pexels-photo-3184192.jpeg?auto=compress&cs=tinysrgb&w=600&h=600&fit=crop",
    "Mücver":             "https://images.pexels.com/photos/6107787/pexels-photo-6107787.jpeg?auto=compress&cs=tinysrgb&w=600&h=600&fit=crop",
    "Kuru Fasulye":       "https://images.pexels.com/photos/1731535/pexels-photo-1731535.jpeg?auto=compress&cs=tinysrgb&w=600&h=600&fit=crop",
    "Mercimekli Bulgur":  "https://images.pexels.com/photos/1640775/pexels-photo-1640775.jpeg?auto=compress&cs=tinysrgb&w=600&h=600&fit=crop",
    "Etli Nohut":         "https://images.pexels.com/photos/2116094/pexels-photo-2116094.jpeg?auto=compress&cs=tinysrgb&w=600&h=600&fit=crop",
    "Kaygana":            "https://images.pexels.com/photos/4518623/pexels-photo-4518623.jpeg?auto=compress&cs=tinysrgb&w=600&h=600&fit=crop",
    "Baklava":             "https://images.pexels.com/photos/6941010/pexels-photo-6941010.jpeg?auto=compress&cs=tinysrgb&w=600&h=600&fit=crop",
    "Künefe":              "https://images.pexels.com/photos/6107782/pexels-photo-6107782.jpeg?auto=compress&cs=tinysrgb&w=600&h=600&fit=crop",
    "Sütlaç":             "https://images.pexels.com/photos/3026804/pexels-photo-3026804.jpeg?auto=compress&cs=tinysrgb&w=600&h=600&fit=crop",
    "Kazandibi":          "https://images.pexels.com/photos/3026808/pexels-photo-3026808.jpeg?auto=compress&cs=tinysrgb&w=600&h=600&fit=crop",
    "Revani":             "https://images.pexels.com/photos/1126359/pexels-photo-1126359.jpeg?auto=compress&cs=tinysrgb&w=600&h=600&fit=crop",
    "Muhallebi":          "https://images.pexels.com/photos/3026804/pexels-photo-3026804.jpeg?auto=compress&cs=tinysrgb&w=600&h=600&fit=crop",
    "Helva":              "https://images.pexels.com/photos/6941010/pexels-photo-6941010.jpeg?auto=compress&cs=tinysrgb&w=600&h=600&fit=crop",
    "Lokma":              "https://images.pexels.com/photos/4518645/pexels-photo-4518645.jpeg?auto=compress&cs=tinysrgb&w=600&h=600&fit=crop",
    "Aşure":             "https://images.pexels.com/photos/3722214/pexels-photo-3722214.jpeg?auto=compress&cs=tinysrgb&w=600&h=600&fit=crop",
    "Dondurma":           "https://images.pexels.com/photos/1352281/pexels-photo-1352281.jpeg?auto=compress&cs=tinysrgb&w=600&h=600&fit=crop",
    "Türk Kahvesi":        "https://images.pexels.com/photos/312418/pexels-photo-312418.jpeg?auto=compress&cs=tinysrgb&w=600&h=600&fit=crop",
    "Çay":                "https://images.pexels.com/photos/1638280/pexels-photo-1638280.jpeg?auto=compress&cs=tinysrgb&w=600&h=600&fit=crop",
    "Sütlü Kahve":        "https://images.pexels.com/photos/350478/pexels-photo-350478.jpeg?auto=compress&cs=tinysrgb&w=600&h=600&fit=crop",
    "Salep":              "https://images.pexels.com/photos/1187317/pexels-photo-1187317.jpeg?auto=compress&cs=tinysrgb&w=600&h=600&fit=crop",
    "Ihlamur":            "https://images.pexels.com/photos/1638280/pexels-photo-1638280.jpeg?auto=compress&cs=tinysrgb&w=600&h=600&fit=crop",
    "Nane Limon":         "https://images.pexels.com/photos/1435706/pexels-photo-1435706.jpeg?auto=compress&cs=tinysrgb&w=600&h=600&fit=crop",
    "Türk Mırra":         "https://images.pexels.com/photos/312418/pexels-photo-312418.jpeg?auto=compress&cs=tinysrgb&w=600&h=600&fit=crop",
    "Zencefilli Çay":     "https://images.pexels.com/photos/1187317/pexels-photo-1187317.jpeg?auto=compress&cs=tinysrgb&w=600&h=600&fit=crop",
    "Menengiç Kahvesi":   "https://images.pexels.com/photos/350478/pexels-photo-350478.jpeg?auto=compress&cs=tinysrgb&w=600&h=600&fit=crop",
    "Osmanlı Şerbeti":   "https://images.pexels.com/photos/1638280/pexels-photo-1638280.jpeg?auto=compress&cs=tinysrgb&w=600&h=600&fit=crop",
    "Ayran":              "https://images.pexels.com/photos/5966431/pexels-photo-5966431.jpeg?auto=compress&cs=tinysrgb&w=600&h=600&fit=crop",
    "Şalgam Suyu":        "https://images.pexels.com/photos/4518645/pexels-photo-4518645.jpeg?auto=compress&cs=tinysrgb&w=600&h=600&fit=crop",
    "Limonata":           "https://images.pexels.com/photos/1435706/pexels-photo-1435706.jpeg?auto=compress&cs=tinysrgb&w=600&h=600&fit=crop",
    "Portakal Suyu":      "https://images.pexels.com/photos/2109099/pexels-photo-2109099.jpeg?auto=compress&cs=tinysrgb&w=600&h=600&fit=crop",
    "Vişne Suyu":         "https://images.pexels.com/photos/1353361/pexels-photo-1353361.jpeg?auto=compress&cs=tinysrgb&w=600&h=600&fit=crop",
    "Su":                 "https://images.pexels.com/photos/327090/pexels-photo-327090.jpeg?auto=compress&cs=tinysrgb&w=600&h=600&fit=crop",
    "Soda":              "https://images.pexels.com/photos/50593/coca-cola-cold-drink-soft-drink-50593.jpeg?auto=compress&cs=tinysrgb&w=600&h=600&fit=crop",
    "Kola":              "https://images.pexels.com/photos/50593/coca-cola-cold-drink-soft-drink-50593.jpeg?auto=compress&cs=tinysrgb&w=600&h=600&fit=crop",
    "Şıra":              "https://images.pexels.com/photos/1353361/pexels-photo-1353361.jpeg?auto=compress&cs=tinysrgb&w=600&h=600&fit=crop",
    "Tamarind Şerbeti":  "https://images.pexels.com/photos/2109099/pexels-photo-2109099.jpeg?auto=compress&cs=tinysrgb&w=600&h=600&fit=crop",
    "SPECİAL PİZZA":     "https://images.pexels.com/photos/1146760/pexels-photo-1146760.jpeg?auto=compress&cs=tinysrgb&w=600&h=600&fit=crop",
}

FALLBACK = "https://images.pexels.com/photos/1640777/pexels-photo-1640777.jpeg?auto=compress&cs=tinysrgb&w=600&h=600&fit=crop"


def download_photo(url, save_path):
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        r = requests.get(url, timeout=20, headers=headers)
        if r.status_code == 200 and len(r.content) > 3000:
            img = Image.open(BytesIO(r.content)).convert("RGB")
            img = img.resize((600, 600), Image.LANCZOS)
            img.save(save_path, "JPEG", quality=85, optimize=True)
            return True
    except Exception as e:
        print(f"hata:{e}", end=" ")
    return False


def run(slug=SLUG, force=False):
    upload_base = os.path.join("static", "uploads", slug, "urunler")
    os.makedirs(upload_base, exist_ok=True)

    with app.app_context():
        tenant = Tenant.query.filter_by(slug=slug).first()
        if not tenant:
            print(f"Restoran bulunamadi: {slug}")
            print("Mevcut:", [t.slug for t in Tenant.query.all()])
            return

        urunler = Urun.query.filter_by(tenant_id=tenant.id).order_by(Urun.sira, Urun.id).all()
        total = len(urunler)
        print(f"\n📸 {total} urun icin fotograf indiriliyor ({slug})...\n")

        success = skip = fail = 0

        for i, urun in enumerate(urunler, 1):
            filename = f"urun_{urun.id}.jpg"
            save_path = os.path.join(upload_base, filename)
            if not force and urun.resim and os.path.exists(os.path.join(upload_base, urun.resim)):
                print(f"[{i:3}/{total}] ⏭  {urun.isim}")
                skip += 1
                continue

            url = FOOD_PHOTOS.get(urun.isim, FALLBACK)
            print(f"[{i:3}/{total}] ⬇  {urun.isim}...", end=" ", flush=True)
            if download_photo(url, save_path):
                urun.resim = filename
                db.session.commit()
                print("✅")
                success += 1
            else:
                print("❌")
                fail += 1
            time.sleep(0.12)

        print(f"\n🎉 {success} indirildi, {skip} atlandı, {fail} hata.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--slug", default=SLUG)
    parser.add_argument("--force", action="store_true", help="Mevcut gorselleri yeniden indir")
    args = parser.parse_args()
    run(slug=args.slug, force=args.force)
