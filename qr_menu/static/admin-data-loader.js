// Admin Panel Data Integration - Dynamic Loading System
// This file handles loading data from existing Admin panel database structure

class AdminDataLoader {
    constructor() {
        this.tenantSlug = null;
        this.tenantData = null;
        this.categories = [];
        this.products = [];
        this.init();
    }

    init() {
        // Extract tenant slug from current URL
        this.tenantSlug = this.extractTenantSlug();
        if (this.tenantSlug) {
            this.loadTenantData();
        }
    }

    // Extract tenant slug from URL (e.g., /r/restaurant-slug/menu)
    extractTenantSlug() {
        const pathParts = window.location.pathname.split('/');
        const slugIndex = pathParts.indexOf('r');
        if (slugIndex !== -1 && pathParts[slugIndex + 1]) {
            return pathParts[slugIndex + 1];
        }
        return null;
    }

    // Load tenant data from Admin panel endpoints
    async loadTenantData() {
        try {
            // Load tenant basic info
            const tenantResponse = await fetch(`/api/tenant/${this.tenantSlug}`);
            if (tenantResponse.ok) {
                this.tenantData = await tenantResponse.json();
                this.updateTenantInfo();
            }

            // Load categories
            await this.loadCategories();

            // Load products
            await this.loadProducts();

            // Initialize translation system with loaded data
            this.initializeTranslations();

            console.log('Admin data loaded successfully');
        } catch (error) {
            console.log('Failed to load admin data, using fallback');
            this.loadFallbackData();
        }
    }

    // Load categories from Admin panel
    async loadCategories() {
        try {
            const response = await fetch(`/api/categories/${this.tenantSlug}`);
            if (response.ok) {
                this.categories = await response.json();
                this.renderCategories();
            }
        } catch (error) {
            console.log('Failed to load categories');
        }
    }

    // Load products from Admin panel
    async loadProducts() {
        try {
            const response = await fetch(`/api/products/${this.tenantSlug}`);
            if (response.ok) {
                this.products = await response.json();
                this.renderProducts();
            }
        } catch (error) {
            console.log('Failed to load products');
        }
    }

    // Update tenant information in UI
    updateTenantInfo() {
        if (!this.tenantData) return;

        // Update restaurant name (keep constant, not translatable)
        const titleElement = document.getElementById('restTitle');
        if (titleElement) {
            titleElement.textContent = this.tenantData.restoran_adi;
        }

        // Update splash text
        const subElement = document.getElementById('restSub');
        if (subElement) {
            subElement.textContent = this.tenantData.splash_text || 'Lezzet menümüze hoş geldiniz';
        }

        // Update working hours
        this.updateWorkingHours();

        // Update contact info
        this.updateContactInfo();

        // Update logo
        this.updateLogo();
    }

    // Update working hours display
    updateWorkingHours() {
        if (!this.tenantData) return;

        const hoursElement = document.querySelector('.working-hours');
        if (hoursElement) {
            const opening = this.tenantData.acilis_saati || '10:00';
            const closing = this.tenantData.kapanis_saati || '23:30';
            hoursElement.innerHTML = `<i class="fas fa-clock"></i> ${opening} - ${closing}`;
        }
    }

    // Update contact information
    updateContactInfo() {
        if (!this.tenantData) return;

        // Update WhatsApp links
        const whatsappLinks = document.querySelectorAll('a[href*="wa.me"]');
        whatsappLinks.forEach(link => {
            if (this.tenantData.whatsapp) {
                link.href = `https://wa.me/${this.tenantData.whatsapp}`;
            }
        });

        // Update Instagram
        const instagramLink = document.querySelector('a[href*="instagram"]');
        if (instagramLink && this.tenantData.instagram) {
            instagramLink.href = this.tenantData.instagram;
        }

        // Update location
        const locationLink = document.querySelector('a[href*="konum"]');
        if (locationLink && this.tenantData.konum_url) {
            locationLink.href = this.tenantData.konum_url;
        }
    }

    // Update restaurant logo
    updateLogo() {
        if (!this.tenantData || !this.tenantData.logo) return;

        const logoElement = document.querySelector('.logo');
        if (logoElement) {
            logoElement.src = `/static/uploads/${this.tenantSlug}/ayarlar/${this.tenantData.logo}`;
        }
    }

    // Render categories dynamically
    renderCategories() {
        const categoryList = document.querySelector('.category-list');
        if (!categoryList) return;

        // Clear existing categories
        categoryList.innerHTML = '';

        this.categories.forEach(category => {
            const categoryCard = this.createCategoryCard(category);
            categoryList.appendChild(categoryCard);
        });
    }

    // Create category card element
    createCategoryCard(category) {
        const card = document.createElement('div');
        card.className = 'cat-card menu-category';
        card.setAttribute('data-kat', category.id);
        card.setAttribute('data-category-id', category.id);

        const imageUrl = category.banner || category.resim;
        const imageHtml = imageUrl ? 
            `<img class="cat-cover" src="/static/uploads/${this.tenantSlug}/kategoriler/${imageUrl}" alt="${category.isim}" onerror="this.style.display='none'">` :
            '<div class="cat-cover-placeholder"></div>';

        card.innerHTML = `
            <div class="cat-head" onclick="event.preventDefault();toggleCategory('${category.id}')">
                ${imageHtml}
                <div>
                    <div class="cat-name tr" data-category-id="${category.id}">${category.isim}</div>
                    <div class="cat-name en hidden" data-category-id="${category.id}">${category.isim_en || category.isim}</div>
                    <div class="cat-meta"><i class="fas fa-utensils" style="font-size:.7rem;opacity:.7"></i> ${category.urunler?.length || 0} ürün</div>
                </div>
                <div class="cat-toggle"><i class="fas fa-chevron-down"></i></div>
            </div>
            <div class="cat-content">
                <div class="product-grid" id="products-${category.id}">
                    <!-- Products will be loaded here -->
                </div>
            </div>
        `;

        return card;
    }

    // Render products dynamically
    renderProducts() {
        this.products.forEach(product => {
            const productGrid = document.getElementById(`products-${product.kategori_id}`);
            if (productGrid) {
                const productCard = this.createProductCard(product);
                productGrid.appendChild(productCard);
            }
        });
    }

    // Create product card element
    createProductCard(product) {
        const card = document.createElement('div');
        card.className = 'product menu-item';
        card.setAttribute('data-kat', product.kategori_id);
        card.setAttribute('data-product-name-id', product.id);
        card.setAttribute('data-product-desc-id', product.id);

        const imageUrl = product.resim ? 
            `/static/uploads/${this.tenantSlug}/urunler/${product.resim}` : '';

        card.innerHTML = `
            ${imageUrl ? `<img src="${imageUrl}" alt="${product.isim}" onclick="openLightbox('${imageUrl}')">` : ''}
            <div class="product-body">
                <div class="product-top">
                    <div>
                        <div class="product-name tr" data-product-name-id="${product.id}">${product.isim}</div>
                        <div class="product-name en hidden" data-product-name-id="${product.id}">${product.isim_en || product.isim}</div>
                    </div>
                    <div class="price">${product.fiyat.toFixed(2)} ₺</div>
                </div>
                <div class="product-desc tr" data-product-desc-id="${product.id}">${product.aciklama}</div>
                <div class="product-desc en hidden" data-product-desc-id="${product.id}">${product.aciklama_en || product.aciklama}</div>
                <div class="badge-list">
                    ${product.badge_yeni ? '<span class="badge new">Yeni</span>' : ''}
                    ${product.badge_populer ? '<span class="badge popular">Popüler</span>' : ''}
                    ${product.badge_acili ? `<span class="badge spicy">Acılı</span><span class="spice-level"><i class="fas fa-pepper-hot"></i>${'🌶️'.repeat(product.aci_seviyesi || 2)}</span>` : ''}
                </div>
                ${product.alerjen_notu ? `
                    <div class="allergen-note">
                        <i class="fas fa-triangle-exclamation"></i>
                        <span class="tr">Alerjen: ${product.alerjen_notu}</span>
                        <span class="en hidden">Allergens: ${product.alerjen_notu_en || product.alerjen_notu}</span>
                    </div>
                ` : ''}
                ${imageUrl ? `
                    <button class="detail-btn" type="button" onclick="openLightbox('${imageUrl}')">
                        <i class="fas fa-expand"></i>
                        <span class="tr">Büyüt</span>
                        <span class="en hidden">Zoom</span>
                    </button>
                ` : ''}
            </div>
        `;

        return card;
    }

    // Initialize translation system with loaded data
    initializeTranslations() {
        if (typeof translations !== 'undefined') {
            // Add category translations
            this.categories.forEach(cat => {
                translations.addCategory(cat.id.toString(), {
                    tr: cat.isim,
                    en: cat.isim_en || cat.isim,
                    ar: cat.isim_en || cat.isim // Fallback to English for Arabic
                });
            });

            // Add product translations
            this.products.forEach(prod => {
                translations.addProduct(prod.id.toString(), {
                    name: {
                        tr: prod.isim,
                        en: prod.isim_en || prod.isim,
                        ar: prod.isim_en || prod.isim
                    },
                    description: {
                        tr: prod.aciklama,
                        en: prod.aciklama_en || prod.aciklama,
                        ar: prod.aciklama_en || prod.aciklama
                    }
                });
            });
        }
    }

    // Load fallback data if API fails
    loadFallbackData() {
        console.log('Loading fallback data from existing page structure');
        // Existing page data will be used as fallback
    }

    // Auto-detect new categories/products (polling system)
    startAutoDetection() {
        setInterval(async () => {
            await this.loadCategories();
            await this.loadProducts();
        }, 30000); // Check every 30 seconds
    }
}

// Global admin data loader instance
let adminDataLoader;

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    adminDataLoader = new AdminDataLoader();
    // Start auto-detection after initial load
    setTimeout(() => {
        adminDataLoader.startAutoDetection();
    }, 5000);
});

// Export for global access
window.adminDataLoader = adminDataLoader;
