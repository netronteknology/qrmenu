"""
10 kategori x 10 urun — tum yasal alanlar dolu demo menu.
Kullanim: python seed_legal_full_menu.py
          python seed_legal_full_menu.py --slug test
"""

import argparse
import os
import random

from PIL import Image, ImageDraw, ImageFont

from app import app, db, Tenant, Kategori, Urun, STANDARD_ALLERGENS
from seed_data import DATA

SLUG = 'test'
ALLERGEN_NAMES = [a[0] for a in STANDARD_ALLERGENS]
PORTIONS = ['180g', '250g', '300g', '350g', '400g', '1 Porsiyon', '1.5 Porsiyon', '330ml', '500ml', '200g']
MEAT_ORIGINS = [
    '%100 Dana Eti',
    '%70 Dana, %30 Kuzu Eti',
    '%100 Kuzu Eti',
    '%60 Dana, %40 Kuzu Eti',
    '%100 Tavuk Eti',
]
MEAT_CATEGORIES = {'Izgara & Kebaplar', 'Pideler', 'Ana Yemekler', 'Pilavlar & Makarnalar'}


def make_image(path, title, subtitle, size=(900, 600), seed=0):
    random.seed(seed)
    bg1 = (random.randint(30, 100), random.randint(30, 100), random.randint(30, 100))
    bg2 = (random.randint(130, 200), random.randint(90, 180), random.randint(70, 150))
    img = Image.new('RGB', size, bg1)
    draw = ImageDraw.Draw(img)
    w, h = size
    for y in range(h):
        t = y / max(h - 1, 1)
        r = int(bg1[0] * (1 - t) + bg2[0] * t)
        g = int(bg1[1] * (1 - t) + bg2[1] * t)
        b = int(bg1[2] * (1 - t) + bg2[2] * t)
        draw.line([(0, y), (w, y)], fill=(r, g, b))
    font = ImageFont.load_default()
    draw.rectangle((24, h - 160, w - 24, h - 24), fill=(20, 20, 20))
    draw.text((38, h - 138), title[:48], fill=(255, 243, 221), font=font)
    draw.text((38, h - 110), subtitle[:70], fill=(245, 245, 245), font=font)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    img.save(path, 'JPEG', quality=88)


def pick_allergens(cat_idx, prod_idx):
    start = (cat_idx * 3 + prod_idx) % len(ALLERGEN_NAMES)
    count = 3 + (prod_idx % 4)
    picked = []
    for i in range(count):
        picked.append(ALLERGEN_NAMES[(start + i * 2) % len(ALLERGEN_NAMES)])
    return list(dict.fromkeys(picked))


def enrich_product(urun, u_data, cat_name, cat_idx, prod_idx):
    allergens = pick_allergens(cat_idx, prod_idx)
    calorie = 180 + cat_idx * 35 + prod_idx * 22
    portion = PORTIONS[(cat_idx + prod_idx) % len(PORTIONS)]
    meat_origin = None
    if cat_name in MEAT_CATEGORIES:
        meat_origin = MEAT_ORIGINS[(cat_idx + prod_idx) % len(MEAT_ORIGINS)]
    alcohol = cat_name in ('Soğuk İçecekler', 'Tatlılar') and prod_idx in (2, 5, 8)

    urun.calorie = calorie
    urun.kalori = calorie
    urun.portion_weight = portion
    urun.meat_origin = meat_origin
    urun.allergens = allergens
    urun.alerjen_notu = ', '.join(allergens)
    urun.alerjen_notu_en = urun.alerjen_notu
    urun.contains_alcohol = alcohol
    urun.servis_suresi_dk = 8 + (prod_idx % 12)
    urun.durum = True
    urun.one_cikan = prod_idx < 3
    urun.badge_yeni = u_data.get('badge_yeni', False) or prod_idx in (0, 4, 9)
    urun.badge_populer = u_data.get('badge_populer', False) or prod_idx in (1, 5, 7)
    urun.badge_acili = u_data.get('badge_acili', False) or prod_idx in (2, 6)
    if not urun.badge_acili:
        urun.aci_seviyesi = 1 + prod_idx % 3


def run(slug=SLUG, reset=True):
    with app.app_context():
        tenant = Tenant.query.filter_by(slug=slug).first()
        if not tenant:
            print(f'Restoran bulunamadi: {slug}')
            print('Mevcut:', [t.slug for t in Tenant.query.all()])
            return

        if reset:
            Urun.query.filter_by(tenant_id=tenant.id).delete()
            Kategori.query.filter_by(tenant_id=tenant.id).delete()
            db.session.commit()
            print(f'Mevcut kategori/urunler temizlendi: {slug}')

        tenant.service_fee_percentage = 10
        tenant.kdv_dahil = True

        base = os.path.join('static', 'uploads', slug)
        cat_dir = os.path.join(base, 'kategoriler')
        urun_dir = os.path.join(base, 'urunler')
        os.makedirs(cat_dir, exist_ok=True)
        os.makedirs(urun_dir, exist_ok=True)

        added_kat = added_urun = 0

        for kat_data in DATA:
            cat_idx = kat_data['sira'] - 1
            kat = Kategori(
                tenant_id=tenant.id,
                isim=kat_data['isim'],
                isim_en=kat_data['isim_en'],
                sira=kat_data['sira'],
                durum=True,
            )
            db.session.add(kat)
            db.session.flush()
            added_kat += 1

            cat_img = f'cat_{kat.id}.jpg'
            make_image(os.path.join(cat_dir, cat_img), kat.isim, kat.isim_en, size=(1200, 560), seed=kat.id * 13)
            kat.banner = cat_img
            kat.resim = cat_img

            for i, u in enumerate(kat_data['urunler']):
                urun = Urun(
                    tenant_id=tenant.id,
                    kategori_id=kat.id,
                    isim=u['isim'],
                    isim_en=u.get('isim_en', ''),
                    fiyat=u.get('fiyat', 0),
                    aciklama=u.get('aciklama', ''),
                    aciklama_en=u.get('aciklama_en', ''),
                    badge_yeni=u.get('badge_yeni', False),
                    badge_populer=u.get('badge_populer', False),
                    badge_acili=u.get('badge_acili', False),
                    aci_seviyesi=u.get('aci_seviyesi', 2),
                    sira=i,
                )
                enrich_product(urun, u, kat_data['isim'], cat_idx, i)
                db.session.add(urun)
                db.session.flush()

                img_name = f'urun_{urun.id}.jpg'
                make_image(os.path.join(urun_dir, img_name), urun.isim, f'{urun.calorie} kcal', size=(900, 900), seed=urun.id * 7)
                urun.resim = img_name
                added_urun += 1

        db.session.commit()
        print(f'Tamamlandi: {slug}')
        print(f'  {added_kat} kategori, {added_urun} urun')
        print(f'  Servis ucreti: %{tenant.service_fee_percentage}')
        print(f'  Menu: /r/{slug}/')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--slug', default=SLUG)
    parser.add_argument('--no-reset', action='store_true')
    args = parser.parse_args()
    run(slug=args.slug, reset=not args.no_reset)
