import tkinter as tk
from tkinter import messagebox
import pyodbc
import os

aktif_kullanici_email = None
canvas = None
scrollable_kampanya_frame = None
adsoyad_label = None
detay_label = None

# ================= SQL BAĞLANTI =================
def sql_baglanti():
    sifre = os.getenv("BANKA_SIFRE")
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

# ================= KULLANICI İŞLEMLERİ =================
def kullanici_sql_den_cek(email, sifre):
    conn = sql_baglanti()
    if not conn:
        return None

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

# ================= KAMPANYA İŞLEMLERİ =================
def kampanyalari_sql_den_cek(kategori_filtresi=None, musteri_email=None):
    conn = sql_baglanti()
    if not conn:
        return []

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
                SELECT TOP 1 Kategori
                FROM Islemler
                WHERE MusteriID = ?
                GROUP BY Kategori
                ORDER BY SUM(Tutar) DESC
            """, (musteri_id,))

            tercih = cursor.fetchone()
            if tercih:
                kategori = tercih[0]
                if kategori in TAMAMLAYICI:
                    kategori = TAMAMLAYICI[kategori]

                siralama = """
                ORDER BY 
                CASE WHEN Kategori = ? THEN 0 ELSE 1 END,
                AI_oncelik DESC,
                IndirimOrani DESC
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

# ================= UI KART BİLEŞENİ =================
def kampanya_karti(parent, indirim, tarih, firma):
    # pack_propagate(True) kalsın (varsayılan budur), böylece içindeki label'lara göre boyutu ayarlanır
    kart = tk.Frame(parent, bg="pink", bd=1, relief="solid", width=350)
    kart.pack(pady=8, padx=10, fill="x") 

    tk.Label(kart, text=f"İndirim: %{indirim}",
             fg="#CFD8DC", bg="blue",
             font=("Arial", 12, "bold")).pack(anchor="w", padx=10, pady=5)

    tk.Label(kart, text=f"Geçerlilik: {tarih}",
             bg="pink").pack(anchor="w", padx=10)

    tk.Label(kart, text=f"Firma: {firma}",
             bg="pink").pack(anchor="w", padx=10, pady=5)

# ================= ANA EKRAN VE LOGIC =================
def giris_yap():
    global aktif_kullanici_email, adsoyad_label, detay_label
    global canvas, scrollable_kampanya_frame

    kul = kullanici_sql_den_cek(email_entry.get(), sifre_entry.get())
    if not kul:
        messagebox.showerror("Hata", "Hatalı Giriş Bilgileri")
        return

    aktif_kullanici_email = email_entry.get()

    # Sayfa Geçişi
    giris_sayfasi.pack_forget()
    ust_bar.pack(side="top", fill="x")
    ana_sayfa.pack(fill="both", expand=True)

    # Profil Paneli
    profil = tk.Frame(ana_sayfa, bg="#f8dff3")
    profil.pack(pady=20, padx=20, fill="x")

    adsoyad_label = tk.Label(profil, text=kul["AdSoyad"],
                            font=("Arial", 16, "bold"), bg="#f8dff3")
    adsoyad_label.pack()

    detay_label = tk.Label(
        profil,
        text=f'{kul["Yas"]} yaş • {kul["Sehir"]}\n{kul["Meslek"]}\nAylık Gelir: {kul["Gelir"]} ₺',
        bg="#f8dff3"
    )
    detay_label.pack()

    # Kaydırılabilir Alan (Scroll System)
    kampanya_container = tk.Frame(ana_sayfa)
    kampanya_container.pack(fill="both", expand=True)

    canvas = tk.Canvas(kampanya_container, bg="#f5f5f5", highlightthickness=0)
    scrollbar = tk.Scrollbar(kampanya_container, orient="vertical", command=canvas.yview)
    
    scrollable_kampanya_frame = tk.Frame(canvas, bg="#f5f5f5")

    # Pencere oluşturma ve genişliği sabitleme
    canvas_frame = canvas.create_window((0, 0), window=scrollable_kampanya_frame, anchor="nw")

    def configure_scroll_region(event):
        canvas.configure(scrollregion=canvas.bbox("all"))
        # İçerideki frame'in genişliğini canvas'a eşitle (Kartların düzgün durması için)
        canvas.itemconfig(canvas_frame, width=canvas.winfo_width())

    scrollable_kampanya_frame.bind("<Configure>", configure_scroll_region)
    canvas.bind("<Configure>", lambda e: canvas.itemconfig(canvas_frame, width=e.width))
    
    canvas.configure(yscrollcommand=scrollbar.set)

    scrollbar.pack(side="right", fill="y")
    canvas.pack(side="left", fill="both", expand=True)

    # Fare tekerleği desteği
    canvas.bind_all("<MouseWheel>", lambda e: canvas.yview_scroll(-1 * int(e.delta / 120), "units"))

    # Kampanyaları Yükle
    veriler = kampanyalari_sql_den_cek(musteri_email=aktif_kullanici_email)
    for k in veriler:
        kampanya_karti(scrollable_kampanya_frame,
                       k["IndirimOrani"],
                       k["GecerlilikTarihi"],
                       k["SponsorFirma"])

# ================= ANA PENCERE KURULUMU =================
root = tk.Tk()
root.title("Akıllı Banka")
root.geometry("430x700")
root.configure(bg="#5F4E60")

# Sayfaları tanımla
giris_sayfasi = tk.Frame(root, bg="#f5f5f5")
ana_sayfa = tk.Frame(root, bg="#f5f5f5")

# Üst Bar (Başlangıçta gizli, girişte pack ediliyor)
ust_bar = tk.Frame(root, bg="#333", height=50)
tk.Label(ust_bar, text="Akıllı Banka", bg="#333", fg="white", font=("Arial", 12, "bold")).pack(pady=10)

# Giriş Ekranı Tasarımı
giris_sayfasi.pack(fill="both", expand=True)

tk.Label(giris_sayfasi, text="Akıllı Banka", font=("Arial", 20, "bold"),
         bg="#f5f5f5", fg="#620e0e").pack(pady=40)

tk.Label(giris_sayfasi, text="E-posta", bg="#000000").pack()
email_entry = tk.Entry(giris_sayfasi, width=30)
email_entry.pack(pady=5)

tk.Label(giris_sayfasi, text="Şifre", bg="#000000").pack()
sifre_entry = tk.Entry(giris_sayfasi, show="*", width=30)
sifre_entry.pack(pady=5)

tk.Button(giris_sayfasi, text="Giriş", bg="#6a1b9a", fg="black", # fg="black" yerine beyaz daha okunur
          width=20, height=2, command=giris_yap).pack(pady=30)

root.mainloop()