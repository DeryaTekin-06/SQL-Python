print("PROGRAM BASLADI")

import tkinter as tk
from tkinter import messagebox
import pyodbc
import os
from datetime import datetime



# SQL BAĞLANTI
def sql_baglanti():
    try:
        return pyodbc.connect(
            f"DRIVER={{ODBC Driver 17 for SQL Server}};"
            f"SERVER=localhost;"
            f"DATABASE=BANKA;"
            f"UID={os.getenv('DB_USER')};"
            f"PWD={os.getenv('DB_PASS')};"
        )
    except Exception as e:
        messagebox.showerror("Veritabanı Hatası", f"Bağlantı kurulamadı: {e}")
        return None


def kampanyalari_sql_den_cek(kategori_filtresi=None, musteri_email=None):
    conn = sql_baglanti()
    if not conn: return []
    cursor = conn.cursor()

    sorgu = """
    SELECT IndirimOrani, GecerlilikTarihi, SponsorFirma, Kategori, Aciklama, AI_oncelik
    FROM Kampanyalar 
    WHERE GecerlilikTarihi >= GETDATE()
    """
    parametreler = []
    siralama_kurali = " ORDER BY AI_oncelik DESC"

    if kategori_filtresi:
        sorgu += " AND Kategori = ?"
        parametreler.append(kategori_filtresi)

    elif musteri_email:
        try:
            cursor.execute("SELECT MusteriID FROM Musteriler WHERE Email = ?", (musteri_email,))
            user_row = cursor.fetchone()

            if user_row:
                musteri_id = user_row[0]

                cursor.execute("""
                    SELECT TOP 1 Kategori 
                    FROM Islemler 
                    WHERE MusteriID = ? 
                    GROUP BY Kategori 
                    ORDER BY SUM(Tutar) DESC
                """, (musteri_id,))
                en_cok_harcanan = cursor.fetchone()

                if en_cok_harcanan:
                    # ❗ SQL Injection kaldırıldı
                    sorgu += " AND (Kategori = ? OR 1=1)"
                    parametreler.append(en_cok_harcanan[0])

        except Exception as e:
            print("Akıllı öneri hatası:", e)

    tam_sorgu = sorgu + siralama_kurali
    cursor.execute(tam_sorgu, parametreler)

    veriler = []
    for row in cursor.fetchall():
        veriler.append({
            "IndirimOrani": row.IndirimOrani,
            "GecerlilikTarihi": row.GecerlilikTarihi.strftime("%d.%m.%Y"),
            "SponsorFirma": row.SponsorFirma
        })

    conn.close()
    return veriler


# KULLANICI SQL
def kullanici_sql_den_cek(email, sifre):
    conn = sql_baglanti()
    if not conn: return None
    cursor = conn.cursor()

    # ⚠ Eğer Musteriler tablosunda Sifre kolonu yoksa bu satır hata verir.
    cursor.execute("""
        SELECT Ad, Soyad, Yas, Sehir, Meslek, Gelir 
        FROM Musteriler 
        WHERE Email = ?
    """, (email,))

    row = cursor.fetchone()
    conn.close()

    if row:
        return {
            "AdSoyad": f"{row.Ad} {row.Soyad}",
            "Yas": row.Yas,
            "Sehir": row.Sehir,
            "Meslek": row.Meslek,
            "Gelir": row.Gelir
        }
    return None


# Profil güncelleme düzeltildi
def profili_sql_de_guncelle(email, yeni_sehir, yeni_meslek):
    conn = sql_baglanti()
    if not conn: return False
    cursor = conn.cursor()
    try:
        cursor.execute("""
            UPDATE Musteriler 
            SET Sehir=?, Meslek=?
            WHERE Email=?
        """, (yeni_sehir, yeni_meslek, email))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        messagebox.showerror("Hata", f"Güncelleme yapılamadı: {e}")
        conn.close()
        return False


# 🔧 yeni_nesil_ai_oneri NULL hatası düzeltildi
def yeni_nesil_ai_oneri(musteri_email):
    conn = sql_baglanti()
    if not conn:
        return None
    cursor = conn.cursor()

    cursor.execute("""
        SELECT TOP 1 Kategori FROM Islemler 
        WHERE MusteriID = (SELECT MusteriID FROM Musteriler WHERE Email = ?)
        ORDER BY Tarih DESC
    """, (musteri_email,))

    sonuc = cursor.fetchone()
    if not sonuc:
        conn.close()
        return None

    son_kategori = sonuc[0]

    TAMAMLAYICI_URUNLER = {
        "Mont": "Bot",
        "Telefon": "Kılıf",
        "Uçak Bileti": "Otel",
        "Giyim": "Aksesuar"
    }

    onerilecek_kategori = TAMAMLAYICI_URUNLER.get(son_kategori, son_kategori)

    cursor.execute("""
        SELECT TOP 1 KampanyaAdi 
        FROM Kampanyalar 
        WHERE Kategori = ? 
        ORDER BY AI_oncelik DESC
    """, (onerilecek_kategori,))

    kampanya = cursor.fetchone()
    conn.close()

    if kampanya:
        return kampanya[0]

    return None


if __name__ == "__main__":
    root = tk.Tk()
    app = BankaApp(root)
    root.mainloop()





