import os
import sys
from app import app, db, BuilderGrup, BuilderSecenek, Tenant

def add_builder_examples():
    with app.app_context():
        # Test tenant'ını bul
        tenant = Tenant.query.filter_by(slug='test').first()
        if not tenant:
            print("Test tenant bulunamadı!")
            return

        print(f"Tenant: {tenant.restoran_adi} (ID: {tenant.id})")

        # Örnek Builder Grupları
        builder_gruplar = [
            {
                'ad': 'Boy',
                'ad_en': 'Size',
                'secenekler': [
                    {'ad': 'Küçük', 'ad_en': 'Small', 'fiyat_farki': 0, 'varsayilan': True},
                    {'ad': 'Orta', 'ad_en': 'Medium', 'fiyat_farki': 15, 'varsayilan': False},
                    {'ad': 'Büyük', 'ad_en': 'Large', 'fiyat_farki': 25, 'varsayilan': False},
                ]
            },
            {
                'ad': 'Protein',
                'ad_en': 'Protein',
                'secenekler': [
                    {'ad': 'Tavuk', 'ad_en': 'Chicken', 'fiyat_farki': 0, 'varsayilan': True},
                    {'ad': 'Kırmızı Et', 'ad_en': 'Beef', 'fiyat_farki': 20, 'varsayilan': False},
                    {'ad': 'Kajun Tavuk', 'ad_en': 'Cajun Chicken', 'fiyat_farki': 15, 'varsayilan': False},
                    {'ad': 'Izgara Somon', 'ad_en': 'Grilled Salmon', 'fiyat_farki': 35, 'varsayilan': False},
                ]
            },
            {
                'ad': 'Garnitür',
                'ad_en': 'Garnish',
                'secenekler': [
                    {'ad': 'Pirinç', 'ad_en': 'Rice', 'fiyat_farki': 0, 'varsayilan': True},
                    {'ad': 'Bulgur', 'ad_en': 'Bulgur', 'fiyat_farki': 5, 'varsayilan': False},
                    {'ad': 'Makarna', 'ad_en': 'Pasta', 'fiyat_farki': 5, 'varsayilan': False},
                    {'ad': 'Patates Kızartması', 'ad_en': 'French Fries', 'fiyat_farki': 10, 'varsayilan': False},
                ]
            },
            {
                'ad': 'Ekstra Malzeme',
                'ad_en': 'Extra Toppings',
                'secenekler': [
                    {'ad': 'Ekstra Peynir', 'ad_en': 'Extra Cheese', 'fiyat_farki': 10, 'varsayilan': False},
                    {'ad': 'Ekstra Sos', 'ad_en': 'Extra Sauce', 'fiyat_farki': 5, 'varsayilan': False},
                    {'ad': 'Avokado', 'ad_en': 'Avocado', 'fiyat_farki': 15, 'varsayilan': False},
                    {'ad': 'Yumurta', 'ad_en': 'Egg', 'fiyat_farki': 8, 'varsayilan': False},
                ]
            },
            {
                'ad': 'Sos',
                'ad_en': 'Sauce',
                'secenekler': [
                    {'ad': 'Barbekü', 'ad_en': 'BBQ', 'fiyat_farki': 0, 'varsayilan': True},
                    {'ad': 'Acı Sos', 'ad_en': 'Hot Sauce', 'fiyat_farki': 0, 'varsayilan': False},
                    {'ad': 'Ranch', 'ad_en': 'Ranch', 'fiyat_farki': 0, 'varsayilan': False},
                    {'ad': 'Sarımsaklı Yoğurt', 'ad_en': 'Garlic Yogurt', 'fiyat_farki': 5, 'varsayilan': False},
                ]
            }
        ]

        # Mevcut builder gruplarını temizle (test için)
        BuilderSecenek.query.filter(BuilderSecenek.grup_id.in_(
            db.session.query(BuilderGrup.id).filter_by(tenant_id=tenant.id)
        )).delete(synchronize_session=False)
        BuilderGrup.query.filter_by(tenant_id=tenant.id).delete(synchronize_session=False)
        db.session.commit()

        # Yeni builder grupları ekle
        for grup_data in builder_gruplar:
            grup = BuilderGrup(
                tenant_id=tenant.id,
                ad=grup_data['ad'],
                ad_en=grup_data['ad_en'],
                zorunlu=False,
                coklu_secim=False,
                sira=0,
                durum=True
            )
            db.session.add(grup)
            db.session.flush()  # ID'yi almak için

            for sec_data in grup_data['secenekler']:
                secenek = BuilderSecenek(
                    grup_id=grup.id,
                    ad=sec_data['ad'],
                    ad_en=sec_data['ad_en'],
                    fiyat_farki=sec_data['fiyat_farki'],
                    resim='',
                    varsayilan=sec_data['varsayilan'],
                    sira=0,
                    durum=True
                )
                db.session.add(secenek)

            print(f"Grup eklendi: {grup.ad} ({len(grup_data['secenekler'])} seçenek)")

        db.session.commit()
        print("\n✅ Builder grupları ve seçenekleri başarıyla eklendi!")

if __name__ == '__main__':
    add_builder_examples()
