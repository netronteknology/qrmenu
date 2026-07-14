"""
Türk Mutfağı Seed Script
Kullanım: python seed_data.py
app.py ile aynı klasörde çalıştır.
"""

from app import app, db, Tenant, Kategori, Urun

SLUG = 'test-restoran'  # Hangi restorana eklenecek

DATA = [
    {
        'isim': 'Çorbalar',
        'isim_en': 'Soups',
        'sira': 1,
        'urunler': [
            dict(isim='Mercimek Çorbası',    isim_en='Red Lentil Soup',     fiyat=120, aciklama='Geleneksel kırmızı mercimek çorbası, limon ve pul biberle.',        aciklama_en='Traditional red lentil soup served with lemon and chili flakes.',  badge_populer=True),
            dict(isim='Ezogelin Çorbası',    isim_en='Ezogelin Soup',       fiyat=130, aciklama='Pirinç, mercimek ve domatesle hazırlanan köy usulü çorba.',         aciklama_en='Village-style soup with rice, lentils and tomato.'),
            dict(isim='İşkembe Çorbası',     isim_en='Tripe Soup',          fiyat=160, aciklama='Geleneksel işkembe çorbası, sarımsaklı sirke ile.',                 aciklama_en='Classic tripe soup with garlic vinegar.',                          alerjen_notu='Süt ürünü içerir'),
            dict(isim='Tarhana Çorbası',     isim_en='Tarhana Soup',        fiyat=120, aciklama='Ev yapımı tarhana ile pişirilmiş geleneksel Anadolu çorbası.',      aciklama_en='Traditional Anatolian soup made with homemade tarhana.',           badge_yeni=True),
            dict(isim='Domates Çorbası',     isim_en='Tomato Soup',         fiyat=110, aciklama='Taze domates püresi, fesleğen ve krema ile.',                       aciklama_en='Fresh tomato purée with basil and cream.',                         alerjen_notu='Süt ürünü içerir'),
            dict(isim='Yayla Çorbası',       isim_en='Yogurt Soup',         fiyat=125, aciklama='Yoğurt, pirinç ve nane ile hazırlanan hafif ve besleyici çorba.',   aciklama_en='Light and nourishing soup with yogurt, rice and mint.',            alerjen_notu='Süt ürünü, gluten içerir'),
            dict(isim='Paça Çorbası',        isim_en='Lamb Trotter Soup',   fiyat=180, aciklama='Kuzu paçasından hazırlanan geleneksel sabah çorbası.',              aciklama_en='Traditional morning soup from lamb trotters.'),
            dict(isim='Tavuk Suyu Çorba',   isim_en='Chicken Broth Soup',  fiyat=130, aciklama='Doğal tavuk suyu ile pişirilmiş, şehriyeli çorba.',                aciklama_en='Natural chicken broth soup with vermicelli.',                      alerjen_notu='Gluten içerir'),
            dict(isim='Düğün Çorbası',      isim_en='Wedding Soup',        fiyat=150, aciklama='Kuzu eti, yoğurt ve yumurta ile hazırlanan şenlik çorbası.',        aciklama_en='Festive soup with lamb, yogurt and egg.',                          alerjen_notu='Yumurta, süt ürünü içerir'),
            dict(isim='Pırasa Çorbası',     isim_en='Leek Soup',           fiyat=115, aciklama='Pırasa ve patates ile hazırlanan hafif sebze çorbası.',             aciklama_en='Light vegetable soup with leek and potato.'),
        ]
    },
    {
        'isim': 'Mezeler',
        'isim_en': 'Appetizers',
        'sira': 2,
        'urunler': [
            dict(isim='Humus',               isim_en='Hummus',              fiyat=95,  aciklama='Nohut ezmesi, zeytinyağı ve tahin ile.',                           aciklama_en='Chickpea dip with olive oil and tahini.',                          alerjen_notu='Susam içerir', badge_populer=True),
            dict(isim='Haydari',             isim_en='Haydari',             fiyat=90,  aciklama='Süzme yoğurt, sarımsak, dereotu ve nane.',                         aciklama_en='Strained yogurt with garlic, dill and mint.',                      alerjen_notu='Süt ürünü içerir'),
            dict(isim='Patlıcan Ezmesi',     isim_en='Eggplant Dip',        fiyat=95,  aciklama='Közlenmiş patlıcan, sarımsak ve limonla hazırlanan meze.',         aciklama_en='Roasted eggplant dip with garlic and lemon.'),
            dict(isim='Acılı Ezme',          isim_en='Spicy Paste',         fiyat=80,  aciklama='Domates, biber ve maydanozla hazırlanan acılı salata.',            aciklama_en='Spicy tomato, pepper and parsley salad.',                          badge_acili=True, aci_seviyesi=3),
            dict(isim='Cacık',              isim_en='Cacik',               fiyat=85,  aciklama='Yoğurt, salatalık ve sarımsak; serinletici Türk mezesi.',           aciklama_en='Yogurt with cucumber and garlic; refreshing Turkish dip.',         alerjen_notu='Süt ürünü içerir'),
            dict(isim='Sigara Böreği',       isim_en='Cheese Rolls',        fiyat=110, aciklama='Beyaz peynir ve maydanozla doldurulmuş çıtır yufka rulleri.',      aciklama_en='Crispy phyllo rolls filled with white cheese and parsley.',        alerjen_notu='Gluten, süt ürünü içerir'),
            dict(isim='Dolma',              isim_en='Stuffed Grape Leaves', fiyat=120, aciklama='Zeytinyağında pişirilmiş asma yaprağı sarması.',                   aciklama_en='Grape leaves stuffed with rice and spices in olive oil.'),
            dict(isim='Tarama',             isim_en='Tarama',              fiyat=105, aciklama='Balık yumurtası ezmesi, limon ve zeytinyağı ile.',                  aciklama_en='Fish roe dip with lemon and olive oil.',                           alerjen_notu='Balık içerir'),
            dict(isim='Kısır',              isim_en='Bulgur Salad',        fiyat=90,  aciklama='İnce bulgur, domates sosu, maydanoz ve limon ile.',                aciklama_en='Fine bulgur with tomato paste, parsley and lemon.',               alerjen_notu='Gluten içerir'),
            dict(isim='Yoğurtlu Patlıcan',  isim_en='Eggplant with Yogurt', fiyat=100, aciklama='Kızarmış patlıcan üzerine sarımsaklı yoğurt ve domates sosu.',   aciklama_en='Fried eggplant with garlic yogurt and tomato sauce.',              alerjen_notu='Süt ürünü içerir'),
        ]
    },
    {
        'isim': 'Izgara & Kebaplar',
        'isim_en': 'Grills & Kebabs',
        'sira': 3,
        'urunler': [
            dict(isim='Adana Kebap',         isim_en='Adana Kebab',         fiyat=320, aciklama='Acı biber ile yoğrulmuş kıyma kebabı, lavaş ve soğan salatası ile.',  aciklama_en='Spicy minced meat kebab with lavash and onion salad.',  badge_acili=True, aci_seviyesi=3, badge_populer=True),
            dict(isim='Urfa Kebap',          isim_en='Urfa Kebab',          fiyat=310, aciklama='Hafif acılı, yumuşak kıyma kebabı.',                                  aciklama_en='Mildly spiced, tender minced meat kebab.',              badge_acili=True, aci_seviyesi=2),
            dict(isim='Kuzu Şiş',           isim_en='Lamb Shish',          fiyat=380, aciklama='Marine edilmiş kuzu but eti, mangal ateşinde pişirilmiş.',            aciklama_en='Marinated lamb leg, grilled over charcoal.'),
            dict(isim='Tavuk Şiş',          isim_en='Chicken Shish',       fiyat=260, aciklama='Baharatlı tavuk göğsü şiş, közlenmiş sebzelerle.',                   aciklama_en='Spiced chicken breast skewer with grilled vegetables.'),
            dict(isim='Karışık Izgara',     isim_en='Mixed Grill',         fiyat=450, aciklama='Adana, tavuk şiş, köfte ve kuzu pirzola; tam bir şölen tabağı.',     aciklama_en='Adana, chicken skewer, köfte and lamb chops; a feast plate.', badge_populer=True),
            dict(isim='Köfte',              isim_en='Turkish Meatballs',   fiyat=280, aciklama='El yapımı ızgara köfte, domates sosu ve patates ile.',               aciklama_en='Handmade grilled meatballs with tomato sauce and potatoes.'),
            dict(isim='Beyti Kebap',        isim_en='Beyti Kebab',         fiyat=350, aciklama='Sarılı kıyma kebabı, domates sosu ve yoğurt ile.',                   aciklama_en='Rolled minced kebab with tomato sauce and yogurt.',      alerjen_notu='Süt ürünü içerir'),
            dict(isim='Kanat Izgara',       isim_en='Grilled Wings',       fiyat=230, aciklama='Baharatlı tavuk kanadı, yoğurt sos ile servis edilir.',              aciklama_en='Spiced chicken wings served with yogurt sauce.',         alerjen_notu='Süt ürünü içerir'),
            dict(isim='Patlıcanlı Kebap',   isim_en='Eggplant Kebab',      fiyat=340, aciklama='Közlenmiş patlıcan üzerine kıyma kebabı ve domates sosu.',          aciklama_en='Minced kebab over roasted eggplant and tomato sauce.'),
            dict(isim='İskender',           isim_en='Iskender Kebab',      fiyat=370, aciklama='Döner et, yoğurt, domates sosu ve tereyağı ile efsanevi Bursa lezzeti.', aciklama_en='Döner meat with yogurt, tomato sauce and butter.', alerjen_notu='Süt ürünü, gluten içerir', badge_populer=True),
        ]
    },
    {
        'isim': 'Pideler',
        'isim_en': 'Pide',
        'sira': 4,
        'urunler': [
            dict(isim='Kaşarlı Pide',       isim_en='Cheese Pide',         fiyat=200, aciklama='Bol kaşar peyniri ile pişirilmiş çıtır Türk pidesi.',              aciklama_en='Crispy Turkish pide with plenty of kashar cheese.',      alerjen_notu='Gluten, süt ürünü içerir', badge_populer=True),
            dict(isim='Kıymalı Pide',       isim_en='Minced Meat Pide',    fiyat=230, aciklama='Kıyma, soğan ve baharatlarla doldurulmuş Türk pidesi.',            aciklama_en='Turkish pide with minced meat, onion and spices.',        alerjen_notu='Gluten içerir'),
            dict(isim='Sucuklu Pide',       isim_en='Sujuk Pide',          fiyat=230, aciklama='Acılı sucuk ve kaşar ile çıtır pide.',                             aciklama_en='Crispy pide with spicy sujuk and kashar cheese.',         alerjen_notu='Gluten, süt ürünü içerir', badge_acili=True, aci_seviyesi=2),
            dict(isim='Kuşbaşılı Pide',    isim_en='Cubed Meat Pide',     fiyat=260, aciklama='İnce doğranmış kuzu eti ve biber ile hazırlanan pide.',            aciklama_en='Pide with finely diced lamb and peppers.',                alerjen_notu='Gluten içerir'),
            dict(isim='Yumurtalı Pide',    isim_en='Egg Pide',            fiyat=180, aciklama='Taze yumurta ve kaşar peyniri ile pişirilmiş besleyici pide.',     aciklama_en='Nourishing pide baked with fresh egg and kashar.',        alerjen_notu='Gluten, yumurta, süt ürünü içerir'),
            dict(isim='Peynirli Ispanaklı Pide', isim_en='Spinach Cheese Pide', fiyat=210, aciklama='Taze ıspanak ve beyaz peynir kombinasyonu.',               aciklama_en='Fresh spinach and white cheese combination.',             alerjen_notu='Gluten, süt ürünü içerir'),
            dict(isim='Kavurmalı Pide',    isim_en='Kavurma Pide',        fiyat=270, aciklama='Yağda kavrulan et parçaları ile dolu, lezzetli pide.',             aciklama_en='Pide filled with meat sautéed in its own fat.',          alerjen_notu='Gluten içerir'),
            dict(isim='Karışık Pide',      isim_en='Mixed Pide',          fiyat=250, aciklama='Kıyma, kaşar ve sucuk üçlüsü ile dolu pide.',                     aciklama_en='Pide with minced meat, kashar and sujuk trio.',          alerjen_notu='Gluten, süt ürünü içerir'),
            dict(isim='Lahmacun',          isim_en='Lahmacun',            fiyat=90,  aciklama='İnce hamur üzerine baharatlı kıyma; maydanoz ve limonla.',         aciklama_en='Thin flatbread with spiced minced meat, parsley and lemon.', alerjen_notu='Gluten içerir', badge_populer=True),
            dict(isim='Mantarlı Pide',     isim_en='Mushroom Pide',       fiyat=210, aciklama='Kültür mantarı ve kaşar peyniri ile hafif vejetaryen pide.',       aciklama_en='Light vegetarian pide with mushrooms and kashar.',        alerjen_notu='Gluten, süt ürünü içerir', badge_yeni=True),
        ]
    },
    {
        'isim': 'Salatalar',
        'isim_en': 'Salads',
        'sira': 5,
        'urunler': [
            dict(isim='Çoban Salata',       isim_en='Shepherd Salad',      fiyat=100, aciklama='Domates, salatalık, soğan, maydanoz ve zeytinyağı.',              aciklama_en='Tomato, cucumber, onion, parsley and olive oil.',         badge_populer=True),
            dict(isim='Roka Salatası',      isim_en='Arugula Salad',       fiyat=120, aciklama='Taze roka, parmesan ve limon sosu ile.',                          aciklama_en='Fresh arugula, parmesan and lemon dressing.',             alerjen_notu='Süt ürünü içerir'),
            dict(isim='Mevsim Salatası',    isim_en='Season Salad',        fiyat=110, aciklama='Günün taze sebzeleriyle hazırlanan hafif salata.',                aciklama_en='Light salad with fresh seasonal vegetables.'),
            dict(isim='Gavurdağı Salatası', isim_en='Gavurdagi Salad',     fiyat=115, aciklama='Ceviz, nar ekşisi, domates ve soğan ile.',                        aciklama_en='With walnuts, pomegranate molasses, tomato and onion.',   alerjen_notu='Kuruyemiş içerir'),
            dict(isim='Piyaz',             isim_en='Bean Salad',           fiyat=95,  aciklama='Haşlanmış fasulye, yumurta, soğan ve zeytinyağı ile.',           aciklama_en='Boiled beans with egg, onion and olive oil.',             alerjen_notu='Yumurta içerir'),
            dict(isim='Semizotu Salatası', isim_en='Purslane Salad',       fiyat=105, aciklama='Semizotu, yoğurt ve sarımsakla hazırlanan geleneksel salata.',    aciklama_en='Traditional salad with purslane, yogurt and garlic.',     alerjen_notu='Süt ürünü içerir'),
            dict(isim='Tahinli Patlıcan',  isim_en='Eggplant Tahini Salad', fiyat=120, aciklama='Közlenmiş patlıcan, tahin ve limonla.',                         aciklama_en='Roasted eggplant with tahini and lemon.',                 alerjen_notu='Susam içerir'),
            dict(isim='Mercimek Salatası', isim_en='Lentil Salad',         fiyat=100, aciklama='Yeşil mercimek, soğan ve nar ekşili sos.',                        aciklama_en='Green lentil salad with onion and pomegranate dressing.'),
            dict(isim='Hellim Salatası',   isim_en='Halloumi Salad',       fiyat=140, aciklama='Izgara hellim, roka ve kiraz domates ile.',                       aciklama_en='Grilled halloumi with arugula and cherry tomatoes.',      alerjen_notu='Süt ürünü içerir', badge_yeni=True),
            dict(isim='Tabule',            isim_en='Tabbouleh',            fiyat=110, aciklama='İnce bulgur, bol maydanoz, domates ve limon suyu.',               aciklama_en='Fine bulgur with lots of parsley, tomato and lemon juice.', alerjen_notu='Gluten içerir'),
        ]
    },
    {
        'isim': 'Ana Yemekler',
        'isim_en': 'Main Courses',
        'sira': 6,
        'urunler': [
            dict(isim='Kuzu Tandır',        isim_en='Lamb Tandoor',        fiyat=480, aciklama='Saatlerce pişirilmiş, kemikten düşen kuzu tandır.',               aciklama_en='Slow-cooked, fall-off-the-bone lamb tandoor.',            badge_populer=True),
            dict(isim='İmam Bayıldı',       isim_en='Imam Bayildi',        fiyat=200, aciklama='Zeytinyağlı patlıcan, soğan, sarımsak ve domates ile.',          aciklama_en='Eggplant with olive oil, onion, garlic and tomato.'),
            dict(isim='Hünkârbeğendi',      isim_en='Hunkar Begendi',      fiyat=360, aciklama='Patlıcan ezmesi üzerine kuzu eti yahnisi.',                       aciklama_en='Lamb stew over creamy eggplant purée.',                  alerjen_notu='Süt ürünü içerir'),
            dict(isim='Karnıyarık',         isim_en='Karniyarik',          fiyat=220, aciklama='Kıymalı iç harcıyla doldurulmuş fırın patlıcan.',                aciklama_en='Baked eggplant stuffed with minced meat filling.'),
            dict(isim='Etli Güveç',         isim_en='Meat Stew',           fiyat=340, aciklama='Kuzu eti, sebze ve baharat ile güveç tenceresi.',                 aciklama_en='Lamb, vegetables and spices slow-cooked in clay pot.'),
            dict(isim='Mantı',             isim_en='Turkish Dumplings',   fiyat=220, aciklama='El açması mantı, yoğurt ve tereyağlı sos ile.',                   aciklama_en='Handmade dumplings with yogurt and buttery sauce.',       alerjen_notu='Gluten, süt ürünü, yumurta içerir', badge_populer=True),
            dict(isim='Etli Yaprak Sarma',  isim_en='Stuffed Vine Leaves', fiyat=260, aciklama='Pirinçli kıyma ile doldurulmuş taze asma yaprağı.',              aciklama_en='Fresh vine leaves stuffed with minced meat and rice.'),
            dict(isim='Terbiyeli Köfte',    isim_en='Meatball in Sauce',   fiyat=270, aciklama='Yumurta ve limonlu sos içinde pişirilmiş köfte.',                aciklama_en='Meatballs cooked in egg and lemon sauce.',               alerjen_notu='Yumurta, gluten içerir'),
            dict(isim='Fırın Tavuk',        isim_en='Roast Chicken',       fiyat=290, aciklama='Baharatlı marine edilmiş bütün tavuk, fırında.',                  aciklama_en='Spice-marinated whole chicken, oven-roasted.'),
            dict(isim='Ali Nazik',          isim_en='Ali Nazik',           fiyat=350, aciklama='Közlenmiş patlıcan ve yoğurt üzerine kuzu eti kavurması.',        aciklama_en='Lamb sauté over roasted eggplant and yogurt.',           alerjen_notu='Süt ürünü içerir'),
        ]
    },
    {
        'isim': 'Pilavlar & Makarnalar',
        'isim_en': 'Rice & Pasta',
        'sira': 7,
        'urunler': [
            dict(isim='Türk Pilavı',        isim_en='Turkish Rice Pilaf',  fiyat=80,  aciklama='Tereyağlı, şehriyeli pirinç pilavı.',                            aciklama_en='Buttery rice pilaf with vermicelli.',                    alerjen_notu='Gluten, süt ürünü içerir'),
            dict(isim='Bulgur Pilavı',      isim_en='Bulgur Pilaf',        fiyat=75,  aciklama='Domates salçalı, tereyağlı bulgur pilavı.',                      aciklama_en='Bulgur pilaf with tomato paste and butter.',             alerjen_notu='Gluten, süt ürünü içerir'),
            dict(isim='İç Pilav',           isim_en='Jeweled Rice',        fiyat=120, aciklama='Kuş üzümü, fıstık ve biberiyeli özel iç pilav.',                 aciklama_en='Special rice with currants, pine nuts and rosemary.',    alerjen_notu='Kuruyemiş içerir'),
            dict(isim='Nohutlu Pilav',      isim_en='Chickpea Rice',       fiyat=95,  aciklama='Haşlanmış nohut ile pişirilmiş doyurucu pilav.',                 aciklama_en='Filling rice cooked with boiled chickpeas.'),
            dict(isim='Erişte',            isim_en='Turkish Noodles',     fiyat=130, aciklama='Ev yapımı erişte, tereyağı ve kaşar peyniri ile.',               aciklama_en='Homemade noodles with butter and kashar cheese.',        alerjen_notu='Gluten, süt ürünü, yumurta içerir'),
            dict(isim='Mücver',            isim_en='Zucchini Fritters',   fiyat=120, aciklama='Kabak rendesi, beyaz peynir ve dereotlu mücver.',                 aciklama_en='Zucchini fritters with white cheese and dill.',          alerjen_notu='Gluten, yumurta, süt ürünü içerir'),
            dict(isim='Kuru Fasulye',      isim_en='White Bean Stew',     fiyat=130, aciklama='Domates salçalı, pastırmalı kuru fasulye; pilav ile.',           aciklama_en='White bean stew with tomato and pastırma; with rice.'),
            dict(isim='Mercimekli Bulgur', isim_en='Lentil Bulgur',       fiyat=110, aciklama='Yeşil mercimek ve kavrulmuş soğanla pişirilmiş bulgur.',          aciklama_en='Bulgur cooked with green lentils and caramelized onion.', alerjen_notu='Gluten içerir'),
            dict(isim='Etli Nohut',        isim_en='Chickpea with Meat',  fiyat=190, aciklama='Kuzu etli nohut yahnisi, pilav ile servis edilir.',              aciklama_en='Lamb and chickpea stew, served with rice.'),
            dict(isim='Kaygana',           isim_en='Turkish Omelette',    fiyat=100, aciklama='Yumurta, un ve sütle hazırlanan geleneksel Karadeniz omlet.',    aciklama_en='Traditional Black Sea omelette with egg, flour and milk.', alerjen_notu='Gluten, yumurta, süt ürünü içerir', badge_yeni=True),
        ]
    },
    {
        'isim': 'Tatlılar',
        'isim_en': 'Desserts',
        'sira': 8,
        'urunler': [
            dict(isim='Baklava',            isim_en='Baklava',             fiyat=160, aciklama='Antep fıstıklı, bol şerbetli geleneksel Türk baklavası.',        aciklama_en='Traditional Turkish baklava with pistachio and syrup.',  alerjen_notu='Gluten, kuruyemiş, süt ürünü içerir', badge_populer=True),
            dict(isim='Künefe',             isim_en='Kunefe',              fiyat=180, aciklama='Peynirli tel kadayıf, şerbet ve antep fıstığı ile.',             aciklama_en='Cheese-filled shredded pastry with syrup and pistachio.', alerjen_notu='Gluten, süt ürünü, kuruyemiş içerir', badge_populer=True),
            dict(isim='Sütlaç',            isim_en='Rice Pudding',        fiyat=90,  aciklama='Fırında üzeri kızartılmış Türk muhallebisi.',                    aciklama_en='Oven-baked Turkish rice pudding.',                       alerjen_notu='Süt ürünü, gluten içerir'),
            dict(isim='Kazandibi',         isim_en='Kazandibi',           fiyat=95,  aciklama='Dibinde karamelize kabuk olan geleneksel Türk tatlısı.',         aciklama_en='Traditional Turkish pudding with caramelized bottom.',    alerjen_notu='Süt ürünü içerir'),
            dict(isim='Revani',            isim_en='Revani',              fiyat=110, aciklama='İrmik ve hindistancevizli şerbetli kek.',                         aciklama_en='Semolina cake soaked in syrup with coconut.',            alerjen_notu='Gluten, yumurta içerir'),
            dict(isim='Muhallebi',         isim_en='Muhallebi',           fiyat=85,  aciklama='Gül suyu ile aromalandırılmış sütlü tatlı.',                      aciklama_en='Milk dessert flavoured with rose water.',                alerjen_notu='Süt ürünü içerir'),
            dict(isim='Helva',             isim_en='Halva',               fiyat=80,  aciklama='Tereyağı, un ve şeker ile hazırlanan geleneksel Türk helvası.',  aciklama_en='Traditional Turkish halva with butter, flour and sugar.', alerjen_notu='Gluten, süt ürünü içerir'),
            dict(isim='Lokma',             isim_en='Lokma',               fiyat=70,  aciklama='Kızarmış hamur topları, şerbet ile.',                            aciklama_en='Fried dough balls drizzled with syrup.',                 alerjen_notu='Gluten içerir'),
            dict(isim='Aşure',            isim_en='Ashure',              fiyat=75,  aciklama='Buğday, kuru meyve ve kuruyemiş ile hazırlanan Nuh\'un gemisi.', aciklama_en='Noah\'s pudding with wheat, dried fruits and nuts.',      alerjen_notu='Gluten, kuruyemiş içerir', badge_yeni=True),
            dict(isim='Dondurma',          isim_en='Turkish Ice Cream',   fiyat=85,  aciklama='Mastic ve salep ile hazırlanan geleneksel Maraş dondurması.',    aciklama_en='Traditional Maraş ice cream with mastic and salep.',     alerjen_notu='Süt ürünü içerir'),
        ]
    },
    {
        'isim': 'Sıcak İçecekler',
        'isim_en': 'Hot Beverages',
        'sira': 9,
        'urunler': [
            dict(isim='Türk Kahvesi',       isim_en='Turkish Coffee',      fiyat=70,  aciklama='Geleneksel cezve kahvesi, lokum ile servis edilir.',             aciklama_en='Traditional cezve coffee, served with Turkish delight.',  badge_populer=True),
            dict(isim='Çay',               isim_en='Black Tea',           fiyat=25,  aciklama='Demli Türk çayı, ince belli bardakta.',                          aciklama_en='Brewed Turkish tea in a tulip glass.',                    badge_populer=True),
            dict(isim='Sütlü Kahve',       isim_en='Milk Coffee',         fiyat=75,  aciklama='Türk kahvesi sütlü versiyon.',                                   aciklama_en='Milk version of Turkish coffee.',                        alerjen_notu='Süt ürünü içerir'),
            dict(isim='Salep',             isim_en='Salep',               fiyat=80,  aciklama='Sıcak süt, salep tozu ve tarçın; kış içeceği.',                  aciklama_en='Hot milk with salep powder and cinnamon; winter drink.',  alerjen_notu='Süt ürünü içerir'),
            dict(isim='Ihlamur',           isim_en='Linden Tea',          fiyat=45,  aciklama='Taze ıhlamur çiçeği demlemesi.',                                 aciklama_en='Fresh linden blossom infusion.'),
            dict(isim='Nane Limon',        isim_en='Mint Lemon Tea',      fiyat=50,  aciklama='Nane yaprakları ve taze limon ile demlenen bitki çayı.',         aciklama_en='Herbal tea with mint leaves and fresh lemon.'),
            dict(isim='Türk Mırra',        isim_en='Mirra Coffee',        fiyat=65,  aciklama='Güneydoğu usulü acı, yoğun Türk kahvesi.',                      aciklama_en='Southeastern-style bitter, intense Turkish coffee.'),
            dict(isim='Zencefilli Çay',    isim_en='Ginger Tea',          fiyat=55,  aciklama='Taze zencefil ve karanfil ile hazırlanan ısıtıcı çay.',          aciklama_en='Warming tea with fresh ginger and cloves.'),
            dict(isim='Menengiç Kahvesi',  isim_en='Menengiç Coffee',     fiyat=75,  aciklama='Yabani Antep fıstığı ile hazırlanan geleneksel içecek.',         aciklama_en='Traditional drink made with wild pistachio.',             badge_yeni=True),
            dict(isim='Osmanlı Şerbeti',  isim_en='Ottoman Sherbet',     fiyat=80,  aciklama='Gül, tarçın ve karanfilli geleneksel Osmanlı şerbeti.',          aciklama_en='Traditional Ottoman sherbet with rose, cinnamon and clove.'),
        ]
    },
    {
        'isim': 'Soğuk İçecekler',
        'isim_en': 'Cold Beverages',
        'sira': 10,
        'urunler': [
            dict(isim='Ayran',             isim_en='Ayran',               fiyat=35,  aciklama='El yapımı taze ayran, yemek yanında klasik seçim.',              aciklama_en='Homemade fresh ayran, the classic companion.',            alerjen_notu='Süt ürünü içerir', badge_populer=True),
            dict(isim='Şalgam Suyu',       isim_en='Turnip Juice',        fiyat=40,  aciklama='Acılı ve ekşi Adana usulü şalgam suyu.',                         aciklama_en='Spicy and sour Adana-style turnip juice.',                badge_acili=True, aci_seviyesi=2),
            dict(isim='Limonata',          isim_en='Lemonade',            fiyat=55,  aciklama='Taze sıkılmış limon, nane ve soda ile.',                         aciklama_en='Freshly squeezed lemon with mint and soda.'),
            dict(isim='Portakal Suyu',     isim_en='Orange Juice',        fiyat=60,  aciklama='Taze sıkılmış portakal suyu.',                                   aciklama_en='Freshly squeezed orange juice.',                          badge_yeni=True),
            dict(isim='Vişne Suyu',        isim_en='Sour Cherry Juice',   fiyat=55,  aciklama='Soğuk servis edilen vişne meyve suyu.',                          aciklama_en='Cold-served sour cherry juice.'),
            dict(isim='Su',               isim_en='Water',               fiyat=15,  aciklama='Soğuk mineral suyu.',                                            aciklama_en='Cold mineral water.'),
            dict(isim='Soda',             isim_en='Sparkling Water',     fiyat=30,  aciklama='Meyve aromalı soda seçenekleri.',                                aciklama_en='Fruit-flavoured sparkling water options.'),
            dict(isim='Kola',             isim_en='Cola',                fiyat=50,  aciklama='Soğuk kola, buz ile servis edilir.',                             aciklama_en='Cold cola, served with ice.'),
            dict(isim='Şıra',             isim_en='Grape Juice',         fiyat=65,  aciklama='Taze üzümden yapılmış doğal şıra.',                              aciklama_en='Natural grape juice from fresh grapes.'),
            dict(isim='Tamarind Şerbeti', isim_en='Tamarind Sherbet',    fiyat=70,  aciklama='Demirhindi meyvesinden hazırlanan ekşi-tatlı Ortadoğu şerbeti.', aciklama_en='Sour-sweet Middle Eastern sherbet from tamarind.'),
        ]
    },
]


def run():
    with app.app_context():
        tenant = Tenant.query.filter_by(slug=SLUG).first()
        if not tenant:
            print(f"❌ Restoran bulunamadı: {SLUG}")
            print("Mevcut restoranlar:", [t.slug for t in Tenant.query.all()])
            return

        added_kat = 0
        added_urun = 0

        for kat_data in DATA:
            # Aynı isimde kategori varsa ekle
            existing = Kategori.query.filter_by(
                tenant_id=tenant.id,
                isim=kat_data['isim']
            ).first()

            if existing:
                kat = existing
                print(f"⚠️  Kategori zaten var: {kat.isim}")
            else:
                kat = Kategori(
                    tenant_id=tenant.id,
                    isim=kat_data['isim'],
                    isim_en=kat_data['isim_en'],
                    sira=kat_data['sira'],
                    durum=True,
                )
                db.session.add(kat)
                db.session.flush()  # id almak için
                added_kat += 1
                print(f"✅ Kategori: {kat.isim}")

            for i, u in enumerate(kat_data['urunler']):
                existing_u = Urun.query.filter_by(
                    tenant_id=tenant.id,
                    isim=u['isim']
                ).first()
                if existing_u:
                    print(f"   ⚠️  Ürün zaten var: {u['isim']}")
                    continue

                urun = Urun(
                    tenant_id=tenant.id,
                    kategori_id=kat.id,
                    isim=u['isim'],
                    isim_en=u.get('isim_en', ''),
                    fiyat=u.get('fiyat', 0),
                    aciklama=u.get('aciklama', ''),
                    aciklama_en=u.get('aciklama_en', ''),
                    durum=True,
                    badge_yeni=u.get('badge_yeni', False),
                    badge_populer=u.get('badge_populer', False),
                    badge_acili=u.get('badge_acili', False),
                    aci_seviyesi=u.get('aci_seviyesi', 2),
                    alerjen_notu=u.get('alerjen_notu', ''),
                    alerjen_notu_en=u.get('alerjen_notu_en', ''),
                    sira=i,
                )
                db.session.add(urun)
                added_urun += 1
                print(f"   ➕ {u['isim']} — {u['fiyat']}₺")

        db.session.commit()
        print(f"\n🎉 Tamamlandı: {added_kat} kategori, {added_urun} ürün eklendi.")


if __name__ == '__main__':
    run()
