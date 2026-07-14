// Dynamic Translation System - QR Menu
// Structure: {key: {tr, en, ar, ru, it, de, fr, zh}}

const translations = {
    'ui_all': {
        tr: 'Tümü', en: 'All', ar: 'الكل',
        ru: 'Все', it: 'Tutto', de: 'Alle', fr: 'Tout', zh: '全部'
    },
    'ui_search_placeholder': {
        tr: 'Ürün ara...', en: 'Search products...', ar: 'البحث عن المنتجات...',
        ru: 'Поиск...', it: 'Cerca prodotti...', de: 'Suchen...', fr: 'Rechercher...', zh: '搜索产品...'
    },
    'ui_featured_products': {
        tr: 'Öne Çıkan Ürünler', en: 'Featured Products', ar: 'المنتجات المميزة',
        ru: 'Рекомендуемые', it: 'In Evidenza', de: 'Empfohlene', fr: 'En vedette', zh: '推荐产品'
    },
    'ui_categories': {
        tr: 'Kategoriler', en: 'Categories', ar: 'الفئات',
        ru: 'Категории', it: 'Categorie', de: 'Kategorien', fr: 'Catégories', zh: '分类'
    },
    'ui_call_waiter': {
        tr: 'Garson Çağır', en: 'Call Waiter', ar: 'استدعاء النادل',
        ru: 'Позвать официанта', it: 'Chiama il Cameriere', de: 'Kellner rufen', fr: 'Appeler le serveur', zh: '呼叫服务员'
    },
    'ui_whatsapp': {
        tr: 'WhatsApp', en: 'WhatsApp', ar: 'واتساب',
        ru: 'WhatsApp', it: 'WhatsApp', de: 'WhatsApp', fr: 'WhatsApp', zh: 'WhatsApp'
    },
    'ui_instagram': {
        tr: 'Instagram', en: 'Instagram', ar: 'انستغرام',
        ru: 'Instagram', it: 'Instagram', de: 'Instagram', fr: 'Instagram', zh: 'Instagram'
    },
    'ui_location': {
        tr: 'Konum', en: 'Location', ar: 'الموقع',
        ru: 'Местоположение', it: 'Posizione', de: 'Standort', fr: 'Emplacement', zh: '位置'
    },
    'ui_empty_state': {
        tr: 'Aradığınız kritere uygun ürün bulunamadı.', en: 'No products found matching your criteria.', ar: 'لم يتم العثور على منتجات.',
        ru: 'Продукты не найдены.', it: 'Nessun prodotto trovato.', de: 'Keine Produkte gefunden.', fr: 'Aucun produit trouvé.', zh: '未找到产品。'
    },
    'ui_new': {
        tr: 'Yeni', en: 'New', ar: 'جديد',
        ru: 'Новинка', it: 'Nuovo', de: 'Neu', fr: 'Nouveau', zh: '新品'
    },
    'ui_popular': {
        tr: 'Popüler', en: 'Popular', ar: 'شائع',
        ru: 'Популярное', it: 'Popolare', de: 'Beliebt', fr: 'Populaire', zh: '热门'
    },
    'ui_spicy': {
        tr: 'Acılı', en: 'Spicy', ar: 'حار',
        ru: 'Острое', it: 'Piccante', de: 'Scharf', fr: 'Épicé', zh: '辣'
    },
    'ui_allergen': {
        tr: 'Alerjen', en: 'Allergens', ar: 'مسببات الحساسية',
        ru: 'Аллергены', it: 'Allergeni', de: 'Allergene', fr: 'Allergènes', zh: '过敏原'
    },
    'ui_enlarge_photo': {
        tr: 'Fotoğrafı Büyüt', en: 'Enlarge Photo', ar: 'تكبير الصورة',
        ru: 'Увеличить фото', it: 'Ingrandisci Foto', de: 'Foto vergrößern', fr: 'Agrandir la photo', zh: '放大照片'
    },
    'ui_price': {
        tr: 'Fiyat', en: 'Price', ar: 'السعر',
        ru: 'Цена', it: 'Prezzo', de: 'Preis', fr: 'Prix', zh: '价格'
    },
    'ui_opening_hours': {
        tr: 'Çalışma Saatleri', en: 'Opening Hours', ar: 'ساعات العمل',
        ru: 'Часы работы', it: 'Orari di Apertura', de: 'Öffnungszeiten', fr: "Heures d'ouverture", zh: '营业时间'
    },
    'ui_working_hours': {
        tr: 'Çalışma Saatleri', en: 'Working Hours', ar: 'ساعات العمل',
        ru: 'Рабочее время', it: 'Orari di Lavoro', de: 'Arbeitszeiten', fr: 'Heures de travail', zh: '工作时间'
    },
    'ui_status_open': {
        tr: 'Açık', en: 'Open', ar: 'مفتوح',
        ru: 'Открыто', it: 'Aperto', de: 'Geöffnet', fr: 'Ouvert', zh: '营业中'
    },
    'ui_status_closed': {
        tr: 'Kapalı', en: 'Closed', ar: 'مغلق',
        ru: 'Закрыто', it: 'Chiuso', de: 'Geschlossen', fr: 'Fermé', zh: '已关闭'
    },
    'ui_menu_enter': {
        tr: 'Menüye Gir', en: 'Enter Menu', ar: 'ادخل القائمة',
        ru: 'Открыть меню', it: 'Entra nel Menu', de: 'Menü öffnen', fr: 'Ouvrir le menu', zh: '进入菜单'
    },
    'select_table': {
        tr: 'Masa Numarası Seçin', en: 'Select Table', ar: 'اختر الطاولة',
        ru: 'Выберите стол', it: 'Seleziona Tavolo', de: 'Tisch wählen', fr: 'Choisir la table', zh: '选择桌子'
    },

    categories: {},
    products: {},

    get: function(key, lang = 'tr') {
        if (this[key] && this[key][lang]) return this[key][lang];
        if (this[key] && this[key]['tr'])  return this[key]['tr'];
        return key;
    },
    addTranslation: function(key, t) { this[key] = t; },
    addCategory: function(id, t) { this.categories[id] = t; },
    addProduct: function(id, t) { this.products[id] = t; },
    getCategory: function(id, lang = 'tr') {
        if (this.categories[id]?.[lang]) return this.categories[id][lang];
        return this.categories[id]?.['tr'] || id;
    },
    getProduct: function(id, field, lang = 'tr') {
        if (this.products[id]?.[field]?.[lang]) return this.products[id][field][lang];
        return this.products[id]?.[field]?.['tr'] || id;
    }
};

async function initializeTranslations() {
    try {
        const response = await fetch('/static/menu-translations.json');
        const data = await response.json();
        Object.keys(data.categories || {}).forEach(id => translations.addCategory(id, data.categories[id]));
        Object.keys(data.products  || {}).forEach(id => translations.addProduct(id, data.products[id]));
        Object.keys(data.ui        || {}).forEach(key => translations.addTranslation(key, data.ui[key]));
        console.log('Translations loaded');
    } catch (e) {
        console.log('Using built-in translations');
    }
}

window.translations = translations;
window.initializeTranslations = initializeTranslations;

