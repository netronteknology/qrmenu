# Netron Print Service Mimarisi

## Genel Bakış
Netron Print Service, QR Menu uygulamasının yazıcı yönetimi ve fiş basma işlemlerini yöneten merkezi bir servistir. Bu servis, REST API ve WebSocket üzerinden iletişim kurarak gerçek zamanlı yazdırma işlemlerini yönetir.

## Mimari Bileşenleri

### 1. Print Service Core
- **Yazıcı Yönetimi**: Ağ yazıcılarının keşfi, bağlantı yönetimi ve durum takibi
- **Kuyruk Sistemi**: Yazdırma işlemleri için asenkron kuyruk yönetimi
- **ESC/POS İşleme**: Standart ESC/POS komutlarının işlenmesi ve formatlanması

### 2. API Katmanı
- **REST API Endpoints**:
  - `POST /api/printers` - Yazıcı ekleme
  - `GET /api/printers` - Yazıcı listesi
  - `PUT /api/printers/{id}` - Yazıcı güncelleme
  - `DELETE /api/printers/{id}` - Yazıcı silme
  - `POST /api/print/test` - Test yazdırma
  - `POST /api/print/receipt` - Fiş yazdırma

- **WebSocket Events**:
  - `print_queue_update` - Yazdırma kuyruğu güncellemeleri
  - `printer_status` - Yazıcı durum değişiklikleri
  - `print_completed` - Yazdırma tamamlandı bildirimi

### 3. Yazıcı Sürücüleri
- **Network Printer Driver**: TCP/IP üzerinden ağ yazıcılarına bağlantı
- **USB Printer Driver**: USB yazıcıları için yerel bağlantı yönetimi
- **Bluetooth Printer Driver**: Bluetooth yazıcıları için kablosuz bağlantı

### 4. Fiş Şablonları
- **Standart Fiş**: Basit sipariş fişi
- **Mutfak Fişi**: Mutfak için detaylı fiş
- **Müşteri Fişi**: Müşteri kopyası
- **Özel Şablonlar**: Kullanıcı tanımlı fiş tasarımları

## Teknik Detaylar

### Yazdırma Akışı
1. Sipariş oluşturulur → Print Service'e bildirim
2. Fiş şablonu seçilir → ESC/POS formatına dönüştürülür
3. Yazıcı seçilir → Kuyruğa eklenir
4. Yazıcıya bağlanılır → Fiş gönderilir
5. Durum güncellenir → WebSocket ile bildirim

### Yazıcı Keşfi
- **Otomatik Keşif**: Ağda ESC/POS yazıcılarını otomatik tespit
- **Manuel Ekleme**: IP ve port ile manuel yazıcı ekleme
- **Durum İzleme**: Yazıcı bağlantı durumunun sürekli kontrolü

### Hata Yönetimi
- **Yeniden Deneme**: Başarısız işlemler için otomatik yeniden deneme
- **Fallback**: Ana yazıcı çalışmazsa yedek yazıcıya yönlendirme
- **Loglama**: Tüm yazdırma işlemlerinin detaylı loglanması

## Entegrasyon Noktaları

### QR Menu Uygulaması ile Entegrasyon
- Flask-SocketIO üzerinden gerçek zamanlı iletişim
- REST API üzerinden yazıcı yönetimi
- Sipariş durum değişikliklerinde otomatik fiş yazdırma

### Gelecek Özellikler
- **Cloud Print**: Bulut tabanlı yazıcı yönetimi
- **Mobile Print**: Mobil uygulama üzerinden yazdırma
- **Analytics**: Yazıcı kullanım istatistikleri
- **Multi-location**: Birden fazla lokasyon için merkezi yönetim

## Teknoloji Stack
- **Backend**: Python + Flask + Flask-SocketIO
- **Queue**: Redis/RabbitMQ
- **Database**: PostgreSQL
- **Protocol**: TCP/IP, USB, Bluetooth
- **Format**: ESC/POS

## Güvenlik
- **API Authentication**: JWT token tabanlı kimlik doğrulama
- **Network Security**: TLS şifreli iletişim
- **Access Control**: Rol tabanlı yetkilendirme
- **Audit Log**: Tüm işlemlerin güvenlik loglaması
