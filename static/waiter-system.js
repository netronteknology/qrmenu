// Waiter Calling System with Table Number Support
class WaiterSystem {
    constructor() {
        this.currentTable = localStorage.getItem('selectedTable') || null;
        this.init();
    }

    init() {
        this.createTableSelector();
        this.updateWaiterButton();
    }

    // Create table number selector modal
    createTableSelector() {
        const modal = document.createElement('div');
        modal.id = 'tableSelectorModal';
        modal.innerHTML = `
            <div class="table-selector-overlay">
                <div class="table-selector-modal">
                    <h3 data-i18n="select_table">Masa Numarası Seçin</h3>
                    <div class="table-grid">
                        ${this.generateTableGrid()}
                    </div>
                    <button class="table-selector-close" onclick="waiterSystem.closeTableSelector()">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
            </div>
        `;
        document.body.appendChild(modal);
    }

    // Generate table grid (1-20 tables)
    generateTableGrid() {
        let grid = '';
        for (let i = 1; i <= 20; i++) {
            grid += `
                <button class="table-btn" onclick="waiterSystem.selectTable(${i})">
                    <i class="fas fa-chair"></i>
                    <span>Masa ${i}</span>
                </button>
            `;
        }
        return grid;
    }

    // Show table selector
    showTableSelector() {
        const modal = document.getElementById('tableSelectorModal');
        if (modal) {
            modal.style.display = 'flex';
        }
    }

    // Close table selector
    closeTableSelector() {
        const modal = document.getElementById('tableSelectorModal');
        if (modal) {
            modal.style.display = 'none';
        }
    }

    // Select table number
    selectTable(tableNumber) {
        this.currentTable = tableNumber;
        localStorage.setItem('selectedTable', tableNumber);
        this.closeTableSelector();
        this.updateWaiterButton();
        this.showTableSelectedNotification(tableNumber);
    }

    // Update waiter button with table info
    updateWaiterButton() {
        const button = document.querySelector('[data-i18n="ui_call_waiter"]');
        if (button) {
            if (this.currentTable) {
                const translation = translations.get('ui_call_waiter', i18nManager?.getCurrentLanguage() || 'tr');
                button.innerHTML = `<i class="fas fa-bell"></i> ${translation} (Masa ${this.currentTable})`;
            } else {
                const translation = translations.get('ui_call_waiter', i18nManager?.getCurrentLanguage() || 'tr');
                button.innerHTML = `<i class="fas fa-bell"></i> ${translation}`;
            }
        }
    }

    // Show notification for table selection
    showTableSelectedNotification(tableNumber) {
        this.showNotification(`Masa ${tableNumber} seçildi`, 'success');
    }

    // Call waiter with table number
    callWaiter() {
        if (!this.currentTable) {
            this.showTableSelector();
            return;
        }

        // Global değişkenden al (index.html'de tanımlı)
        const whatsappNumber = window.TENANT_WHATSAPP;
        if (!whatsappNumber) {
            this.showNotification('WhatsApp numarası bulunamadı', 'error');
            return;
        }

        const message = encodeURIComponent(`Merhaba, Masa ${this.currentTable} garson çağırıyor. Yardıma ihtiyacımız var.`);
        const whatsappUrl = `https://wa.me/${whatsappNumber}?text=${message}`;
        
        window.open(whatsappUrl, '_blank');
        this.showNotification(`Masa ${this.currentTable} için garson çağrıldı`, 'success');
    }

    // Show notification
    showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `waiter-notification ${type}`;
        notification.innerHTML = `
            <div class="notification-content">
                <i class="fas fa-${type === 'success' ? 'check-circle' : type === 'error' ? 'exclamation-circle' : 'info-circle'}"></i>
                <span>${message}</span>
            </div>
        `;
        
        document.body.appendChild(notification);
        
        // Auto remove after 3 seconds
        setTimeout(() => {
            notification.remove();
        }, 3000);
    }

    // Clear selected table
    clearTable() {
        this.currentTable = null;
        localStorage.removeItem('selectedTable');
        this.updateWaiterButton();
        this.showNotification('Masa seçimi temizlendi', 'info');
    }
}

// Global waiter system instance
let waiterSystem;

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    waiterSystem = new WaiterSystem();
});

// Global functions
function callWaiterWithTable() {
    if (waiterSystem) {
        waiterSystem.callWaiter();
    }
}

function showTableSelector() {
    if (waiterSystem) {
        waiterSystem.showTableSelector();
    }
}
