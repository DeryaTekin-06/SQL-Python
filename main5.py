import tkinter as tk
from tkinter import messagebox
import pyodbc
import os

beydanurtekin06@gmail.com


# --- SQL BAĞLANTI ---
def sql_baglanti():
    sifre = os.getenv("BANKA_SIFRE") or "GucluBirSifre123!" # Kendi şifrenizle güncelleyin
    try:
        return pyodbc.connect(
            "DRIVER={ODBC Driver 17 for SQL Server};"
            "SERVER=localhost;"
            "DATABASE=BANKA;"
            "UID=SA;"
            f"PWD={sifre};"
        )
    except Exception as e:
        messagebox.showerror("Veritabanı Hatası", f"Bağlantı kurulamadı: {e}")
        return None

# --- Sabit eşleştirme tablosu ---
TAMAMLAYICI = {
    "Mont": "Giyim",
    "Seyahat": "Seyahat",
    "Market": "Market",
    "Bakım ve hijyen": "Giyim"
}

# --- YARDIMCI FONKSİYONLAR ---
def _on_mousewheel(event):
    canvas.yview_scroll(-1 * int(event.delta/120), "units")

def giris_yap():
    global aktif_kullanici_email, canvas, scrollable_kampanya_frame, canvas_window
    
    kul = kullanici_sql_den_cek(email_entry.get(), sifre_entry.get())
    if not kul:
        messagebox.showerror("Hata", "Hatalı Giriş")
        return

    aktif_kullanici_email = email_entry.get()
    giris_sayfasi.pack_forget()
    ust_bar.pack(side="top", fill="x")
    ana_sayfa.pack(fill="both", expand=True)

    # --- Profil alanı ---
    profil = tk.Frame(ana_sayfa, bg="#620e0e", bd=1, relief="solid")
    profil.pack(pady=20, padx=20, fill="x")
    
    adsoyad_label = tk.Label(profil, text=kul["AdSoyad"], font=("Arial", 16, "bold"), bg="#620e0e")
    adsoyad_label.pack()
    detay_label = tk.Label(profil, text=f'{kul["Yas"]} yaş • {kul["Sehir"]}\n{kul["Meslek"]}\nAylık Gelir: {kul["Gelir"]} ₺', bg="#620e0e")
    detay_label.pack()
    
    # --- Scroll Sistemi Konfigürasyonu ---
    kampanya_container = tk.Frame(ana_sayfa, bg="#f5f5f5")
    kampanya_container.pack(fill="both", expand=True)
    
    canvas = tk.Canvas(kampanya_container, bg="#f5f5f5", highlightthickness=0)
    scrollbar = tk.Scrollbar(kampanya_container, orient="vertical", command=canvas.yview)
    canvas.configure(yscrollcommand=scrollbar.set)
    
    scrollable_kampanya_frame = tk.Frame(canvas, bg="#f5f5f5")
    canvas_window = canvas.create_window((0, 0), window=scrollable_kampanya_frame, anchor="nw")

    # Pencere boyutu değiştikçe canvas içindeki frame'i genişlet
    def resize_canvas(event):
        canvas.itemconfig(canvas_window, width=event.width)
    
    canvas.bind("<Configure>", resize_canvas)
    scrollable_kampanya_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
    
    # Mouse tekerleği desteği
    root.bind_all("<MouseWheel>", _on_mousewheel)

    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    # Kampanyaları Yükle
    veriler = kampanyalari_sql_den_cek(musteri_email=aktif_kullanici_email)
    if not veriler: 
        tk.Label(scrollable_kampanya_frame, text="Size uygun kampanya bulunamadı", bg="#f5f5f5").pack(pady=10)
    else:
        for k in veriler: 
            kampanya_karti(scrollable_kampanya_frame, k["IndirimOrani"], k["GecerlilikTarihi"], k["SponsorFirma"])

# --- KAMPANYA KARTI TASARIMI ---
def kampanya_karti(parent, indirim, tarih, firma):
    # pack_propagate(False) kaldırıldı veya yükseklik eklendi (Otomatik boyutlanma için kaldırıldı)
    kart = tk.Frame(parent, bg="#C5C5C5", bd=1, relief="solid", width=350)
    kart.pack(pady=8, padx=20, fill="x") 

    tk.Label(kart, text=f"İndirim: %{indirim}", fg="#000000", bg="#C5C5C5", font=("Arial", 12, "bold")).pack(anchor="w", padx=10, pady=5)
    tk.Label(kart, text=f"Geçerlilik: {tarih}", bg="#C5C5C5").pack(anchor="w", padx=10)
    tk.Label(kart, text=f"Firma: {firma}", bg="#C5C5C5").pack(anchor="w", padx=10, pady=5)

# --- SQL İŞLEMLERİ ---
def kampanyalari_sql_den_cek(kategori_filtresi=None, musteri_email=None):
    conn = sql_baglanti()
    if not conn: return []
    cursor = conn.cursor()

    sorgu = """
        SELECT IndirimOrani, GecerlilikTarihi, SponsorFirma, Kategori, Aciklama
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
                    SELECT TOP 1 Kategori FROM Islemler 
                    WHERE MusteriID = ? GROUP BY Kategori ORDER BY SUM(Tutar) DESC
                """, (musteri_id,))
                en_cok_harcanan = cursor.fetchone()
                if en_cok_harcanan:
                    tercih_kategori = en_cok_harcanan[0]
                    if tercih_kategori in TAMAMLAYICI:
                        tercih_kategori = TAMAMLAYICI[tercih_kategori]
                    siralama_kurali = " ORDER BY CASE WHEN Kategori = ? THEN 0 ELSE 1 END, AI_oncelik DESC, IndirimOrani DESC"
                    parametreler.append(tercih_kategori)
        except Exception as e:
            print("Akıllı öneri hatası:", e)

    cursor.execute(sorgu + siralama_kurali, parametreler)
    veriler = []
    for row in cursor.fetchall():
        veriler.append({
            "IndirimOrani": row.IndirimOrani,
            "GecerlilikTarihi": row.GecerlilikTarihi.strftime("%d.%m.%Y"),
            "SponsorFirma": row.SponsorFirma
        })
    conn.close()
    return veriler

def kullanici_sql_den_cek(email, sifre):
    conn = sql_baglanti()
    if not conn: return None
    cursor = conn.cursor()
    # Not: SQL tarafında Sifre kolonunun olduğundan emin olun
    cursor.execute("SELECT Ad, Soyad, Yas, Sehir, Meslek, Gelir FROM Musteriler WHERE Email = ? AND Sifre = ?", (email, sifre))
    row = cursor.fetchone()
    conn.close()
    if row:
        return {"AdSoyad": f"{row.Ad} {row.Soyad}", "Yas": row.Yas, "Sehir": row.Sehir, "Meslek": row.Meslek, "Gelir": row.Gelir}
    return None

def profili_sql_de_guncelle(email, yeni_sehir, yeni_meslek):
    conn = sql_baglanti()
    if not conn: return False
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE Musteriler SET Sehir=?, Meslek=? WHERE Email=?", (yeni_sehir, yeni_meslek, email))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        messagebox.showerror("Hata", f"Güncelleme yapılamadı: {e}")
        conn.close()
        return False

# --- UI TASARIM ---
root = tk.Tk()
root.title("Akıllı Banka")
root.geometry("430x700")
root.configure(bg="#f5f5f5")

# Paneller
ust_bar = tk.Frame(root, bg="#333", height=50)
giris_sayfasi = tk.Frame(root, bg="#f5f5f5")
ana_sayfa = tk.Frame(root, bg="#f5f5f5")
kampanya_sayfasi = tk.Frame(root, bg="#f5f5f5")
yan_menu = tk.Frame(root, bg="#444")

# Menü Fonksiyonları
def menu_ac_kapa():
    if yan_menu.winfo_ismapped():
        yan_menu.place_forget()
        menu_btn.config(text="☰")
    else:
        yan_menu.place(x=0, y=50, relheight=1, width=200)
        yan_menu.lift()
        menu_btn.config(text="X")

def kategoriye_git(kat):
    ana_sayfa.pack_forget()
    kampanya_sayfasi.pack(fill="both", expand=True)
    for w in kampanya_sayfasi.winfo_children(): w.destroy()
    
    tk.Label(kampanya_sayfasi, text=f"{kat} Kampanyaları", font=("Arial", 16, "bold"), bg="#f5f5f5").pack(pady=20)
    veriler = kampanyalari_sql_den_cek(kategori_filtresi=kat)
    
    if not veriler: 
        tk.Label(kampanya_sayfasi, text="Kampanya yok", bg="#f5f5f5").pack()
    else:
        for k in veriler: 
            kampanya_karti(kampanya_sayfasi, k["IndirimOrani"], k["GecerlilikTarihi"], k["SponsorFirma"])
    
    tk.Button(kampanya_sayfasi, text="Geri Dön", command=lambda: [kampanya_sayfasi.pack_forget(), ana_sayfa.pack(fill="both", expand=True)]).pack(pady=20)
    menu_ac_kapa()

# Giriş Sayfası Elemanları
giris_sayfasi.pack(fill="both", expand=True)
tk.Label(giris_sayfasi, text="Akıllı Banka", font=("Arial", 20, "bold"), bg="#f5f5f5", fg="#620e0e").pack(pady=40)
email_entry = tk.Entry(giris_sayfasi, width=30)
email_entry.insert(0, "beydanurtekin06@gmail.com")
email_entry.pack(pady=10)
sifre_entry = tk.Entry(giris_sayfasi, show="*", width=30)
sifre_entry.insert(0, "1234")
sifre_entry.pack(pady=10)

tk.Button(giris_sayfasi, text="Giriş", bg="#6a1b9a", fg="black", width=20, command=giris_yap).pack(pady=20)

# Üst Bar Elemanları
menu_btn = tk.Button(ust_bar, text="☰", command=menu_ac_kapa, bg="#333", fg="white", font=("Arial", 15), bd=0)
menu_btn.pack(side="left", padx=10)
tk.Label(ust_bar, text="Akıllı Banka", bg="#333", fg="white", font=("Arial", 12, "bold")).pack(side="left", padx=10)

# Menü Butonları
tk.Button(yan_menu, text="Profili Güncelle", bg="#444", fg="white", bd=0, anchor="w", padx=20, 
          command=lambda: messagebox.showinfo("Bilgi", "Profil güncelleme tıklandı")).pack(fill="x", pady=5)

tk.Button(yan_menu, text="Market Kampanyaları", bg="#444", fg="white", bd=0, anchor="w", padx=20, 
          command=lambda: kategoriye_git("Market")).pack(fill="x", pady=5)

tk.Button(yan_menu, text="Giyim Kampanyaları", bg="#444", fg="white", bd=0, anchor="w", padx=20, 
          command=lambda: kategoriye_git("Giyim")).pack(fill="x", pady=5)

tk.Button(yan_menu, text="Çıkış", bg="#444", fg="white", bd=0, anchor="w", padx=20, 
          command=lambda: root.quit()).pack(fill="x", pady=5)

root.mainloop()