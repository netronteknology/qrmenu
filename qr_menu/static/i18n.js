// Internationalization (i18n) System - Dynamic Language Switching
// This file handles automatic DOM updates for language switching

class I18nManager {
    constructor() {
        this.currentLang = localStorage.getItem('selectedLanguage') || 'tr';
        this.translations = window.translations || {};
        this.init();
    }

    t(key, fallback = key) {
        if (this.translations && typeof this.translations.get === 'function') {
            return this.translations.get(key, this.currentLang);
        }
        return fallback;
    }

    init() {
        // Apply saved language on page load
        this.applyLanguage(this.currentLang);
        
        // Update language dropdown
        this.updateLanguageDropdown();
    }

    // Switch language and update all DOM elements
    switchLanguage(lang) {
        this.currentLang = lang;
        localStorage.setItem('selectedLanguage', lang);
        
        // Update HTML lang attribute
        document.documentElement.lang = lang;
        
        // Add transition effect for smooth language change
        document.body.style.transition = 'opacity 0.2s ease';
        document.body.style.opacity = '0.95';
        
        setTimeout(() => {
            // Update all translatable elements
            this.updateAllTranslations();
            
            // Update dynamic menu content
            this.updateMenuContent();
            
            // Update language dropdown
            this.updateLanguageDropdown();
            
            // Update body class for RTL languages
            this.updateRTLClass();
            
            // Update all buttons and interactive elements
            this.updateInteractiveElements();
            
            // Update theme-specific elements
            this.updateThemeElements();
            
            // Restore opacity
            document.body.style.opacity = '1';
        }, 100);
        
        console.log('Language switched to:', lang);
    }

    // Update all elements with data-i18n attribute
    updateAllTranslations() {
        const elements = document.querySelectorAll('[data-i18n]');
        elements.forEach(element => {
            const key = element.getAttribute('data-i18n');
            const translation = this.t(key, key);
            
            if (element.tagName === 'INPUT' && element.type === 'text') {
                element.placeholder = translation;
            } else {
                element.textContent = translation;
            }
        });

        // Update dynamic content (categories, products)
        this.updateDynamicContent();
    }

    // Update dynamic content (categories and products)
    updateDynamicContent() {
        // NOTE:
        // Category/product text is already rendered as .tr/.en/... blocks in template.
        // Replacing textContent from JSON here can overwrite DB data (e.g. descriptions).
        // So only static UI/contact labels are updated in this method.

        // Update waiter button
        const waiterButton = document.querySelector('[data-i18n="ui_call_waiter"]');
        if (waiterButton) {
            const translation = this.t('ui_call_waiter', 'Garson Çağır');
            waiterButton.innerHTML = `<i class="fas fa-bell"></i> ${translation}`;
        }

        // Update working hours
        this.updateWorkingHours();

        // Update contact information labels
        this.updateContactLabels();

        // DO NOT UPDATE BRAND NAME - Keep restaurant name constant
        // The restaurant name should never change based on language
    }

    // Update language dropdown to show current selection
    updateLanguageDropdown() {
        const trigger = document.querySelector('.lang-trigger .lang-current');
        if (trigger) {
            const langNames = {
                tr: '🇹🇷 Türkçe',
                en: '🇬🇧 English',
                ar: '🇸🇦 العربية',
                de: '🇩🇪 Deutsch',
                fr: '🇫🇷 Français',
                ru: '🇷🇺 Русский',
                zh: '🇨🇳 中文'
            };
            trigger.textContent = langNames[this.currentLang] || langNames.tr;
        }
        
        // Update active state in dropdown
        document.querySelectorAll('.lang-option').forEach(option => {
            option.classList.toggle('active', option.dataset.lang === this.currentLang);
        });
    }

    // Update RTL class for Arabic language
    updateRTLClass() {
        document.body.classList.toggle('lang-rtl', this.currentLang === 'ar');
        document.documentElement.dir = this.currentLang === 'ar' ? 'rtl' : 'ltr';
    }

    // Update dynamic menu content (categories, products, etc.)
    updateMenuContent() {
        console.log('Updating menu content for language:', this.currentLang);

        // Single source of truth: page-level setLang handles fallback chain.
        if (typeof window.setLang === 'function') {
            window.setLang(this.currentLang, null);
            return;
        }
        
        // Update working hours and contact info
        this.updateWorkingHours();
        this.updateContactLabels();
        
        console.log('Menu content updated successfully');
    }

    // Apply language (initial load)
    applyLanguage(lang) {
        this.currentLang = lang;
        document.documentElement.lang = lang;
        this.updateAllTranslations();
        this.updateRTLClass();
    }

    // Get current language
    getCurrentLanguage() {
        return this.currentLang;
    }

    // Add new translation dynamically (for future admin panel)
    addTranslation(key, translationsObj) {
        this.translations.addTranslation(key, translationsObj);
        this.updateAllTranslations();
    }

    // Add category translation dynamically
    addCategoryTranslation(categoryId, translationsObj) {
        this.translations.addCategory(categoryId, translationsObj);
        this.updateDynamicContent();
    }

    // Add product translation dynamically
    addProductTranslation(productId, translationsObj) {
        this.translations.addProduct(productId, translationsObj);
        this.updateDynamicContent();
    }

    // Update working hours display
    updateWorkingHours() {
        const hoursPill = document.getElementById('hoursPill');
        const hoursText = document.getElementById('hoursText');
        
        if (hoursPill && hoursText) {
            const hoursLabel = this.t('ui_working_hours', 'Çalışma Saatleri');
            const currentTime = hoursText.textContent;
            
            // Extract time from current text
            const timeMatch = currentTime.match(/\d{2}:\d{2}\s*-\s*\d{2}:\d{2}/);
            if (timeMatch) {
                hoursText.innerHTML = `<i class="fas fa-clock"></i> ${hoursLabel}: ${timeMatch[0]}`;
            } else {
                // Fallback: just update with current text
                hoursText.innerHTML = `<i class="fas fa-clock"></i> ${hoursLabel}: ${currentTime}`;
            }
            
            console.log('Working hours updated for language:', this.currentLang);
        }
    }

    // Update contact information labels
    updateContactLabels() {
        // Update WhatsApp labels
        const whatsappLinks = document.querySelectorAll('a[href*="wa.me"]');
        whatsappLinks.forEach(link => {
            const existingText = link.textContent.trim();
            if (existingText.includes('WhatsApp') || existingText.includes('واتساب')) {
                const whatsappText = this.t('ui_whatsapp', 'WhatsApp');
                if (link.querySelector('i.fab')) {
                    link.innerHTML = `<i class="fab fa-whatsapp"></i> ${whatsappText}`;
                }
            }
        });

        // Update Instagram labels
        const instagramLinks = document.querySelectorAll('a[href*="instagram"]');
        instagramLinks.forEach(link => {
            const existingText = link.textContent.trim();
            if (existingText.includes('Instagram') || existingText.includes('انستغرام')) {
                const instagramText = this.t('ui_instagram', 'Instagram');
                if (link.querySelector('i.fab')) {
                    link.innerHTML = `<i class="fab fa-instagram"></i> ${instagramText}`;
                }
            }
        });

        // Update location labels
        const locationLinks = document.querySelectorAll('a[href*="konum"], a[href*="location"]');
        locationLinks.forEach(link => {
            const existingText = link.textContent.trim();
            if (existingText.includes('Konum') || existingText.includes('Location') || existingText.includes('الموقع')) {
                const locationText = this.t('ui_location', 'Konum');
                if (link.querySelector('i.fas')) {
                    link.innerHTML = `<i class="fas fa-location-dot"></i> ${locationText}`;
                }
            }
        });
    }
}

// Global i18n manager instance
let i18nManager;

function bootI18n() {
    i18nManager = new I18nManager();
    window.i18nManager = i18nManager;
    if (typeof initializeTranslations === 'function') {
        initializeTranslations().then(() => {
            if (i18nManager) i18nManager.updateAllTranslations();
        }).catch(() => {});
    }
}

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', bootI18n);
} else {
    bootI18n();
}

// Additional methods for comprehensive language switching
I18nManager.prototype.updateInteractiveElements = function() {
    // Update all buttons with language-specific content
    const buttons = document.querySelectorAll('button');
    buttons.forEach(button => {
        const trText = button.querySelector('.tr');
        const enText = button.querySelector('.en');
        
        if (trText && enText) {
            if (this.currentLang === 'tr') {
                trText.classList.remove('hidden');
                enText.classList.add('hidden');
            } else {
                trText.classList.add('hidden');
                enText.classList.remove('hidden');
            }
        }
    });
    
    // Update all detail buttons
    const detailBtns = document.querySelectorAll('.detail-btn');
    detailBtns.forEach(btn => {
        const trSpan = btn.querySelector('.tr');
        const enSpan = btn.querySelector('.en');
        
        if (trSpan && enSpan) {
            if (this.currentLang === 'tr') {
                trSpan.style.display = 'inline';
                enSpan.style.display = 'none';
            } else {
                trSpan.style.display = 'none';
                enSpan.style.display = 'inline';
            }
        }
    });
};

I18nManager.prototype.updateThemeElements = function() {
    // Update theme-specific language elements
    const themeElements = document.querySelectorAll('[data-theme-i18n]');
    themeElements.forEach(element => {
        const key = element.getAttribute('data-theme-i18n');
        const translation = this.t(key, key);
        if (translation && translation !== key) {
            element.textContent = translation;
        }
    });
    
    // Update working hours with proper formatting
    this.updateWorkingHours();
    
    // Update contact information
    this.updateContactLabels();
    
    // Update footer signature
    this.updateFooterElements();
};

I18nManager.prototype.updateFooterElements = function() {
    // Update footer elements that might have language-specific content
    const footerElements = document.querySelectorAll('.footer-signature [data-lang]');
    footerElements.forEach(element => {
        const lang = element.getAttribute('data-lang');
        if (lang === this.currentLang) {
            element.style.display = 'block';
        } else {
            element.style.display = 'none';
        }
    });
};

// Language switching functions
function switchLanguage(lang) {
    if (i18nManager) {
        i18nManager.switchLanguage(lang);
    }
}

function toggleLangDropdown() {
    const dropdown = document.getElementById('langDropdown');
    const trigger = document.getElementById('langTrigger');
    
    if (dropdown && trigger) {
        dropdown.classList.toggle('open');
        trigger.classList.toggle('open');
    }
}

function setLangFromDropdown(lang) {
    if (typeof window.setLang === 'function') {
        window.setLang(lang, null);
    } else {
        switchLanguage(lang);
    }
    if (typeof window.toggleLangDropdown === 'function') {
        window.toggleLangDropdown();
    } else {
        toggleLangDropdown();
    }
}

// Export for global access
window.switchLanguage = window.switchLanguage || switchLanguage;
window.toggleLangDropdown = window.toggleLangDropdown || toggleLangDropdown;
window.setLangFromDropdown = setLangFromDropdown;
