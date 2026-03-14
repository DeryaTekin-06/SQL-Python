# Akıllı Banka - AI Destekli Kampanya Öneri Sistemi 

Bu proje, banka müşterilerinin harcama alışkanlıklarını analiz ederek onlara en uygun kampanyaları akıllı bir sıralama ile sunan modern bir masaüstü uygulamasıdır. Kullanıcıların geçmiş işlemlerine odaklanarak onlara kişiselleştirilmiş bir deneyim sunmayı amaçlar.

## Özellikler

- **Akıllı Öneri Algoritması:** Kullanıcının en çok harcama yaptığı kategoriye göre kampanyaları önceliklendirir.
- **Modern Arayüz:** Python Tkinter kullanılarak tasarlanmış, kullanıcı dostu ve dinamik yapı.
- **Hamburger Menü:** Kolay navigasyon sağlayan, açılır-kapanır yan menü (Sidebar).
- **Kategori Filtreleme:** Market, Giyim ve Seyahat gibi kategorilere göre hızlı kampanya tarama.
- **Güvenli Giriş Sistemi:** SQL Server entegrasyonu ile kullanıcı doğrulama.
- **Dinamik Kaydırma (Scroll):** Çok sayıda kampanyayı akıcı bir şekilde görüntüleme imkanı.

## Kullanılan Teknolojiler

- **Programlama Dili:** Python 3.x
- **Arayüz Kütüphanesi:** Tkinter
- **Veritabanı:** Microsoft SQL Server
- **Bağlantı Sürücüsü:** PyODBC

## Kurulum ve Çalıştırma

1. **Gerekli Kütüphaneleri Yükleyin:**
   ```bash
   pip install pyodbc

- **Veritabanı Yapılandırması:**
SQL Server üzerinde BANKA isimli bir veritabanı oluşturun.
Musteriler, Kampanyalar ve Islemler tablolarını şemaya uygun şekilde ekleyin.


**Uygulamayı Çalıştırın:**
python main.py

