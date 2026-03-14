import tkinter as tk
from tkinter import messagebox
import pyodbc
import os

#GLOBAL DEĞİŞKENLER
aktif_kullanici_email = None
canvas = None
scrollable_kampanya_frame = None
canvas_window = None

#SQL BAĞLANTI 
def sql_baglanti():
    sifre = os.getenv("BANKA_SIFRE") or "1234" # Geliştirme için varsayılan eklenebilir
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

TAMAMLAYICI = {
    "Mont": "Giyim",
    "Seyahat": "Seyahat",
    "Market": "Market",
    "Bakım ve hijyen": "Giyim"
}

# VERİ TABANI İŞLEMLERİ
def kullanici_sql_den_cek(email, sifre):
    conn = sql_baglanti()
    if not conn: return None
    cursor = conn.cursor()
    cursor.execute("""
        SELECT Ad, Soyad, Yas, Sehir, Meslek, Gelir
        FROM Musteriler
        WHERE Email = ? AND Sifre = ?
    """, (email, sifre))
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

def kampanyalari_sql_den_cek(kategori_filtresi=None, musteri_email=None):
    conn = sql_baglanti()
    if not conn: return []
    cursor = conn.cursor()

    sorgu = """
        SELECT IndirimOrani, GecerlilikTarihi, SponsorFirma, Kategori
        FROM Kampanyalar
        WHERE GecerlilikTarihi >= GETDATE()
    """
    parametreler = []
    siralama = " ORDER BY AI_oncelik DESC"

    if kategori_filtresi:
        sorgu += " AND Kategori = ?"
        parametreler.append(kategori_filtresi)
    elif musteri_email:
        cursor.execute("SELECT MusteriID FROM Musteriler WHERE Email = ?", (musteri_email,))
        row = cursor.fetchone()
        if row:
            musteri_id = row[0]
            cursor.execute("""
                SELECT TOP 1 Kategori FROM Islemler
                WHERE MusteriID = ? GROUP BY Kategori ORDER BY SUM(Tutar) DESC
            """, (musteri_id,))
            tercih = cursor.fetchone()
            if tercih:
                kategori = tercih[0]
                if kategori in TAMAMLAYICI: kategori = TAMAMLAYICI[kategori]
                siralama = """
                ORDER BY CASE WHEN Kategori = ? THEN 0 ELSE 1 END,
                AI_oncelik DESC, IndirimOrani DESC
                """
                parametreler.append(kategori)

    cursor.execute(sorgu + siralama, parametreler)
    veriler = []
    for row in cursor.fetchall():
        veriler.append({
            "IndirimOrani": row.IndirimOrani,
            "GecerlilikTarihi": row.GecerlilikTarihi.strftime("%d.%m.%Y"),
            "SponsorFirma": row.SponsorFirma
        })
    conn.close()
    return veriler

#UI BİLEŞENLERİ & FONKSİYONLAR
def kampanya_karti(parent, indirim, tarih, firma):
    kart = tk.Frame(parent, bg="#C5C5C5", bd=1, relief="solid")
    kart.pack(pady=8, padx=20, fill="x") 

    tk.Label(kart, text=f"İndirim: %{indirim}", fg="black", bg="#C5C5C5", 
             font=("Arial", 11, "bold")).pack(anchor="w", padx=10, pady=5)
    tk.Label(kart, text=f"Geçerlilik: {tarih}", bg="#C5C5C5", font=("Arial", 9)).pack(anchor="w", padx=10)
    tk.Label(kart, text=f"Firma: {firma}", bg="#C5C5C5", font=("Arial", 9, "italic")).pack(anchor="w", padx=10, pady=5)

def menu_ac_kapa():
    if yan_menu.winfo_ismapped():
        yan_menu.place_forget()
        menu_btn.config(text="☰")
    else:
        yan_menu.place(x=0, y=50, relheight=1, width=220)
        yan_menu.lift()
        menu_btn.config(text="✕")

def kategoriye_git(kat):
    ana_sayfa.pack_forget()
    kampanya_sayfasi.pack(fill="both", expand=True)
    
    for w in kampanya_sayfasi.winfo_children(): w.destroy()
    
    tk.Label(kampanya_sayfasi, text=f"{kat} Kampanyaları", font=("Arial", 16, "bold"), 
             bg="#f5f5f5", fg="#333").pack(pady=20)
    
    veriler = kampanyalari_sql_den_cek(kategori_filtresi=kat)
    if not veriler:
        tk.Label(kampanya_sayfasi, text="Bu kategoride aktif kampanya bulunamadı.", bg="#f5f5f5").pack()
    else:
        for k in veriler:
            kampanya_karti(kampanya_sayfasi, k["IndirimOrani"], k["GecerlilikTarihi"], k["SponsorFirma"])
    
    tk.Button(kampanya_sayfasi, text="Ana Sayfaya Dön", font=("Arial", 10, "bold"),
              command=lambda: [kampanya_sayfasi.pack_forget(), ana_sayfa.pack(fill="both", expand=True)]).pack(pady=20)
    menu_ac_kapa()

def giris_yap():
    global aktif_kullanici_email, canvas, scrollable_kampanya_frame, canvas_window
    
    kul = kullanici_sql_den_cek(email_entry.get(), sifre_entry.get())
    if not kul:
        messagebox.showerror("Hata", "E-posta veya şifre hatalı!")
        return

    aktif_kullanici_email = email_entry.get()
    giris_sayfasi.pack_forget()
    ust_bar.pack(side="top", fill="x")
    ana_sayfa.pack(fill="both", expand=True)

    profil = tk.Frame(ana_sayfa, bg="#620e0e", bd=0)
    profil.pack(pady=15, padx=20, fill="x")
    
    tk.Label(profil, text=kul["AdSoyad"], font=("Arial", 14, "bold"), bg="#620e0e", fg="white").pack(pady=(10,0))
    tk.Label(profil, text=f'{kul["Yas"]} yaş • {kul["Sehir"]}\n{kul["Meslek"]}\nAylık Gelir: {kul["Gelir"]} ₺', 
             bg="#620e0e", fg="white", font=("Arial", 10)).pack(pady=5)
    
    container = tk.Frame(ana_sayfa, bg="#f5f5f5")
    container.pack(fill="both", expand=True)
    
    canvas = tk.Canvas(container, bg="#f5f5f5", highlightthickness=0)
    scrollbar = tk.Scrollbar(container, orient="vertical", command=canvas.yview)
    scrollable_kampanya_frame = tk.Frame(canvas, bg="#f5f5f5")
    
    canvas_window = canvas.create_window((0, 0), window=scrollable_kampanya_frame, anchor="nw")
    
    def on_configure(e):
        canvas.configure(scrollregion=canvas.bbox("all"))
        canvas.itemconfig(canvas_window, width=e.width)

    canvas.bind("<Configure>", on_configure)
    canvas.configure(yscrollcommand=scrollbar.set)
    
    root.bind_all("<MouseWheel>", lambda e: canvas.yview_scroll(-1 * int(e.delta/120), "units"))

    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    veriler = kampanyalari_sql_den_cek(musteri_email=aktif_kullanici_email)
    for k in veriler:
        kampanya_karti(scrollable_kampanya_frame, k["IndirimOrani"], k["GecerlilikTarihi"], k["SponsorFirma"])

#ANA PENCERE TASARIMI
root = tk.Tk()
root.title("Akıllı Banka v2.0")
root.geometry("430x700")
root.configure(bg="#f5f5f5")

# Paneller
ust_bar = tk.Frame(root, bg="#333", height=55)
giris_sayfasi = tk.Frame(root, bg="#f5f5f5")
ana_sayfa = tk.Frame(root, bg="#f5f5f5")
kampanya_sayfasi = tk.Frame(root, bg="#f5f5f5")
yan_menu = tk.Frame(root, bg="#444")

#GİRİŞ SAYFA
giris_sayfasi.pack(fill="both", expand=True)

tk.Label(giris_sayfasi, text="Akıllı Banka", font=("Arial", 24, "bold"), bg="#f5f5f5", fg="#620e0e").pack(pady=(80, 40))

tk.Label(giris_sayfasi, text="E-posta Adresi", fg="black", bg="#f5f5f5", font=("Arial", 10)).pack()
email_entry = tk.Entry(giris_sayfasi, width=35, font=("Arial", 11), bd=1, relief="solid")
email_entry.insert(0, "beydanurtekin06@gmail.com") # Kolaylık için bırakıldı
email_entry.pack(pady=5)

tk.Label(giris_sayfasi, text="Şifre",  fg="black", bg="#f5f5f5", font=("Arial", 10)).pack(pady=(10,0))
sifre_entry = tk.Entry(giris_sayfasi, show="*", width=35, font=("Arial", 11), bd=1, relief="solid")
sifre_entry.insert(0, "1234")
sifre_entry.pack(pady=5)

tk.Button(giris_sayfasi, text="GİRİŞ YAP", bg="#6a1b9a", fg="white", 
          font=("Arial", 11, "bold"), width=20, height=2, bd=0, 
          command=giris_yap).pack(pady=40)

#ÜST BAR ELEMANLARI
menu_btn = tk.Button(ust_bar, text="☰", command=menu_ac_kapa, bg="#333", 
                     fg="white", font=("Arial", 18), bd=0, activebackground="#444", activeforeground="white")
menu_btn.pack(side="left", padx=15)

tk.Label(ust_bar, text="AKILLI BANKA", bg="#333", fg="white", 
         font=("Arial", 12, "bold")).pack(side="left", padx=10)

#HAMBURGER MENÜ (YAN MENÜ) 
def menu_buton_olustur(metin, komut):
    return tk.Button(yan_menu, text=metin, bg="#444", fg="white", bd=0, 
                     anchor="w", padx=20, font=("Arial", 10), height=2,
                     activebackground="#555", activeforeground="white", command=komut)

menu_buton_olustur("Ana Sayfa", lambda: [ana_sayfa.pack(fill="both", expand=True), kampanya_sayfasi.pack_forget(), menu_ac_kapa()]).pack(fill="x")
menu_buton_olustur("Market Kampanyaları", lambda: kategoriye_git("Market")).pack(fill="x")
menu_buton_olustur("Giyim Kampanyaları", lambda: kategoriye_git("Giyim")).pack(fill="x")
menu_buton_olustur("Seyahat Kampanyaları", lambda: kategoriye_git("Seyahat")).pack(fill="x")
tk.Frame(yan_menu, bg="#666", height=1).pack(fill="x", pady=10) 
menu_buton_olustur("Çıkış Yap", root.quit).pack(fill="x")

root.mainloop()