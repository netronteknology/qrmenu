"""
20 kategori x 20 ürün demo kataloğu + hazır görsel üretici.
Kullanım:
  python seed_large_catalog.py
  python seed_large_catalog.py --slug test-restoran
"""

import argparse
import os
import random
import re
from PIL import Image, ImageDraw, ImageFont

from app import app, db, Tenant, Kategori, Urun


CATEGORY_NAMES = [
    ("Corbalar", "Soups"),
    ("Mezeler", "Appetizers"),
    ("Izgara ve Kebaplar", "Grills and Kebabs"),
    ("Ana Yemekler", "Main Courses"),
    ("Pilav ve Makarna", "Rice and Pasta"),
    ("Tatlilar", "Desserts"),
    ("Sicak Icecekler", "Hot Drinks"),
    ("Soguk Icecekler", "Cold Drinks"),
    ("Salatalar", "Salads"),
    ("Vegan Secenekler", "Vegan Options"),
    ("Deniz Urunleri", "Seafood"),
    ("Firindan Lezzetler", "From the Oven"),
    ("Sandvic ve Burger", "Sandwiches and Burgers"),
    ("Atistirmaliklar", "Snacks"),
    ("Kahvaltiliklar", "Breakfast"),
    ("Cocuk Menusu", "Kids Menu"),
    ("Chef Onerileri", "Chef Specials"),
    ("Gunun Corbasi", "Soup of the Day"),
    ("Soslar ve Ekstralar", "Sauces and Extras"),
    ("Ozel Lezzetler", "Signature Dishes"),
]


def slugify(value: str) -> str:
    value = value.lower().strip()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-") or "item"


def make_image(path: str, title: str, subtitle: str, size=(900, 600), seed=0):
    random.seed(seed)
    bg1 = (random.randint(20, 90), random.randint(20, 90), random.randint(20, 90))
    bg2 = (random.randint(120, 190), random.randint(80, 170), random.randint(60, 140))

    img = Image.new("RGB", size, bg1)
    draw = ImageDraw.Draw(img)

    w, h = size
    for y in range(h):
        t = y / max(h - 1, 1)
        r = int(bg1[0] * (1 - t) + bg2[0] * t)
        g = int(bg1[1] * (1 - t) + bg2[1] * t)
        b = int(bg1[2] * (1 - t) + bg2[2] * t)
        draw.line([(0, y), (w, y)], fill=(r, g, b))

    font = ImageFont.load_default()
    draw.rectangle((24, h - 160, w - 24, h - 24), fill=(0, 0, 0, 120))
    draw.text((38, h - 138), title[:48], fill=(255, 243, 221), font=font)
    draw.text((38, h - 110), subtitle[:70], fill=(245, 245, 245), font=font)
    img.save(path, "JPEG", quality=88)


def ensure_demo_catalog(tenant: Tenant):
    base = os.path.join("static", "uploads", tenant.slug)
    cat_dir = os.path.join(base, "kategoriler")
    product_dir = os.path.join(base, "urunler")
    os.makedirs(cat_dir, exist_ok=True)
    os.makedirs(product_dir, exist_ok=True)

    total_products = 0
    for idx, (cat_tr, cat_en) in enumerate(CATEGORY_NAMES, start=1):
        kat = Kategori.query.filter_by(tenant_id=tenant.id, isim=cat_tr).first()
        if not kat:
            kat = Kategori(
                tenant_id=tenant.id,
                isim=cat_tr,
                isim_en=cat_en,
                aciklama=f"{cat_tr} kategorisinin secili urunleri",
                aciklama_en=f"Featured selections for {cat_en}",
                ikon="fa-utensils",
                sira=idx,
                durum=True,
            )
            db.session.add(kat)
            db.session.flush()

        cat_img_name = f"cat_{kat.id}.jpg"
        cat_img_path = os.path.join(cat_dir, cat_img_name)
        if not os.path.exists(cat_img_path):
            make_image(cat_img_path, kat.isim, kat.isim_en, size=(1200, 560), seed=kat.id * 17)
        kat.banner = cat_img_name
        kat.resim = cat_img_name

        for pidx in range(1, 21):
            p_tr = f"{cat_tr} Urun {pidx}"
            p_en = f"{cat_en} Item {pidx}"
            urun = Urun.query.filter_by(tenant_id=tenant.id, isim=p_tr).first()
            if not urun:
                urun = Urun(
                    tenant_id=tenant.id,
                    kategori_id=kat.id,
                    isim=p_tr,
                    isim_en=p_en,
                    fiyat=round(90 + (idx * 7) + (pidx * 3.5), 2),
                    aciklama=f"{kat.isim} icin ozel hazirlanan lezzetli urun {pidx}.",
                    aciklama_en=f"Tasty {cat_en.lower()} special item {pidx}.",
                    alerjen_notu="",
                    alerjen_notu_en="",
                    kalori=220 + (pidx * 12),
                    servis_suresi_dk=8 + (pidx % 6),
                    badge_yeni=(pidx % 7 == 0),
                    badge_populer=(pidx % 5 == 0),
                    badge_acili=(pidx % 9 == 0),
                    aci_seviyesi=2 + (pidx % 3),
                    one_cikan=(pidx <= 3),
                    durum=True,
                    sira=pidx,
                )
                db.session.add(urun)
                db.session.flush()

            img_name = f"urun_{urun.id}.jpg"
            img_path = os.path.join(product_dir, img_name)
            if not os.path.exists(img_path):
                make_image(img_path, urun.isim, urun.isim_en, size=(900, 900), seed=urun.id * 11)
            urun.resim = img_name
            urun.kategori_id = kat.id
            urun.durum = True
            urun.sira = pidx
            total_products += 1

    db.session.commit()
    return len(CATEGORY_NAMES), total_products


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--slug", help="Hedef restoran slug")
    args = parser.parse_args()

    with app.app_context():
        tenant = None
        if args.slug:
            tenant = Tenant.query.filter_by(slug=args.slug).first()
        if not tenant:
            tenant = Tenant.query.filter_by(aktif=True).order_by(Tenant.id.asc()).first()
        if not tenant:
            print("Aktif restoran bulunamadi.")
            return

        cat_count, product_count = ensure_demo_catalog(tenant)
        print(f"Tamamlandi: {tenant.slug} icin {cat_count} kategori ve {product_count} urun hazirlandi.")


if __name__ == "__main__":
    main()
