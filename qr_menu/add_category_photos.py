"""
Kategori Banner Fotoğrafı İndirici
Kullanım: python add_category_photos.py
app.py ile aynı klasörde çalıştır.
"""

import os
import time
import requests
from PIL import Image
from io import BytesIO

from app import app, db, Tenant, Kategori

SLUG = "test-restoran"
UPLOAD_BASE = os.path.join("static", "uploads", SLUG, "kategoriler")

# Kategori banner'ları — geniş format (800x400)
CATEGORY_PHOTOS = {
    "Çorbalar":              "https://images.pexels.com/photos/539451/pexels-photo-539451.jpeg?auto=compress&cs=tinysrgb&w=800&h=400&fit=crop",
    "Mezeler":               "https://images.pexels.com/photos/1640777/pexels-photo-1640777.jpeg?auto=compress&cs=tinysrgb&w=800&h=400&fit=crop",
    "Izgara & Kebaplar":     "https://images.pexels.com/photos/1105325/pexels-photo-1105325.jpeg?auto=compress&cs=tinysrgb&w=800&h=400&fit=crop",
    "Pideler":               "https://images.pexels.com/photos/4109111/pexels-photo-4109111.jpeg?auto=compress&cs=tinysrgb&w=800&h=400&fit=crop",
    "Salatalar":             "https://images.pexels.com/photos/1213710/pexels-photo-1213710.jpeg?auto=compress&cs=tinysrgb&w=800&h=400&fit=crop",
    "Ana Yemekler":          "https://images.pexels.com/photos/675951/pexels-photo-675951.jpeg?auto=compress&cs=tinysrgb&w=800&h=400&fit=crop",
    "Pilavlar & Makarnalar": "https://images.pexels.com/photos/723198/pexels-photo-723198.jpeg?auto=compress&cs=tinysrgb&w=800&h=400&fit=crop",
    "Tatlılar":              "https://images.pexels.com/photos/6941010/pexels-photo-6941010.jpeg?auto=compress&cs=tinysrgb&w=800&h=400&fit=crop",
    "Sıcak İçecekler":      "https://images.pexels.com/photos/312418/pexels-photo-312418.jpeg?auto=compress&cs=tinysrgb&w=800&h=400&fit=crop",
    "Soğuk İçecekler":      "https://images.pexels.com/photos/1638280/pexels-photo-1638280.jpeg?auto=compress&cs=tinysrgb&w=800&h=400&fit=crop",
    "SPECİAL PİZZA":        "https://images.pexels.com/photos/1146760/pexels-photo-1146760.jpeg?auto=compress&cs=tinysrgb&w=800&h=400&fit=crop",
}

FALLBACK = "https://images.pexels.com/photos/1640777/pexels-photo-1640777.jpeg?auto=compress&cs=tinysrgb&w=800&h=400&fit=crop"


def download_photo(url, save_path):
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        r = requests.get(url, timeout=20, headers=headers)
        if r.status_code == 200 and len(r.content) > 3000:
            img = Image.open(BytesIO(r.content)).convert("RGB")
            img = img.resize((800, 400), Image.LANCZOS)
            img.save(save_path, "JPEG", quality=85, optimize=True)
            return True
    except Exception as e:
        print(f"hata:{e}", end=" ")
    return False


def run():
    os.makedirs(UPLOAD_BASE, exist_ok=True)

    with app.app_context():
        tenant = Tenant.query.filter_by(slug=SLUG).first()
        if not tenant:
            print(f"Restoran bulunamadi: {SLUG}")
            return

        kategoriler = Kategori.query.filter_by(tenant_id=tenant.id).all()
        total = len(kategoriler)
        print(f"\n🖼️  {total} kategori için banner indiriliyor...\n")

        success = skip = fail = 0

        for i, kat in enumerate(kategoriler, 1):
            # Zaten varsa atla
            if kat.banner:
                path = os.path.join(UPLOAD_BASE, kat.banner)
                if os.path.exists(path):
                    print(f"[{i:2}/{total}] ⏭  {kat.isim} (zaten var)")
                    skip += 1
                    continue

            url = CATEGORY_PHOTOS.get(kat.isim, FALLBACK)
            filename = f"kat_banner_{kat.id}.jpg"
            save_path = os.path.join(UPLOAD_BASE, filename)

            print(f"[{i:2}/{total}] ⬇  {kat.isim}...", end=" ", flush=True)
            if download_photo(url, save_path):
                kat.banner = filename
                # resim de set et (thumbnail için)
                if not kat.resim:
                    kat.resim = filename
                db.session.commit()
                print("✅")
                success += 1
            else:
                print("❌")
                fail += 1
            time.sleep(0.15)

        print(f"\n🎉 {success} banner indirildi, {skip} atlandı, {fail} hata.")


if __name__ == "__main__":
    run()
