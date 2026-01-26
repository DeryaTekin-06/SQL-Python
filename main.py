import tkinter as tk
from tkinter import messagebox
import pyodbc


# SQL BAĞLANTI
def sql_baglanti():
    try:
        return pyodbc.connect(
            "DRIVER={ODBC Driver 17 for SQL Server};"
            "SERVER=localhost;"
            "DATABASE=BANKA;"
            "UID=SA;"
            "PWD=DeryaBeyda123;"
        )
    except Exception as e:
        messagebox.showerror("Veritabanı Hatası", f"Bağlantı kurulamadı: {e}")
        return None



def kampanyalari_sql_den_cek(kategori_filtresi=None, musteri_email=None):
    conn = sql_baglanti()
    if not conn: return []
    cursor = conn.cursor()

    sorgu = "SELECT IndirimOrani, GecerlilikTarihi, SponsorFirma, Kategori, Aciklama FROM Kampanyalar WHERE GecerlilikTarihi >= GETDATE()"
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

                    siralama_kurali = f" ORDER BY CASE WHEN Kategori = '{en_cok_harcanan[0]}' THEN 0 ELSE 1 END, AI_oncelik DESC"
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

    cursor.execute(""" SELECT Ad, Soyad, Yas, Sehir, Meslek, Gelir FROM Musteriler WHERE Email = ? AND Sifre = ? """, (email, sifre))

    row = cursor.fetchone()
    conn.close()

    if row:
        return { "AdSoyad": f"{row.Ad} {row.Soyad}", "Yas": row.Yas, "Sehir": row.Sehir, "Meslek": row.Meslek,
            "Gelir": row.Gelir
        }
    return None



# KULLANICI KAYIT
def kullanici_kaydet(ad, soyad, yas, sehir, meslek, gelir, email, sifre):
    conn = sql_baglanti()
    if not conn: return
    cursor = conn.cursor()

    cursor.execute(""" INSERT INTO Musteriler (Ad, Soyad, Yas, Sehir, Meslek, Gelir, Email, Sifre) VALUES (?, ?, ?, ?, ?, ?, ?, ?)""", 
                   (ad, soyad, yas, sehir, meslek, gelir, email, sifre))

    conn.commit()
    conn.close()



def email_var_mi(email):
    conn = sql_baglanti()
    if not conn: return False
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM Musteriler WHERE Email = ?", (email,))
    sonuc = cursor.fetchone()
    conn.close()
    return sonuc is not None

#Profil güncelleme
def profili_sql_de_guncelle(email,  yeni_sehir, yeni_meslek, ):
    conn = sql_baglanti()
    if not conn: return False
    cursor = conn.cursor()
    try:
        cursor.execute("""
            UPDATE Musteriler 
            SET  Sehir=?, Meslek=?
            WHERE Email=?
        """, (yeni_sehir, yeni_meslek, email))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        messagebox.showerror("Hata", f"Güncelleme yapılamadı: {e}")
        conn.close()
        return False

# PENCERE

root = tk.Tk()
root.title("Akıllı Banka")
root.geometry("430x700")
root.configure(bg="#5F4E60")

giris_sayfasi = tk.Frame(root, bg="#f5f5f5")
ana_sayfa = tk.Frame(root, bg="#f5f5f5")
kampanya_sayfasi = tk.Frame(root, bg="#f5f5f5")

giris_sayfasi.pack(fill="both", expand=True)


#HAMBURGER MENU
yan_menu = tk.Frame(root, bg="#444") 
def menu_ac_kapa():
    if yan_menu.winfo_ismapped():
        yan_menu.place_forget()
        menu_btn.config(text="☰")
    else:
        yan_menu.place(x=0, y=50, relheight=1, width=200) 
        menu_btn.config(text="X") 
def kampanya_alt_menu_ac_kapat():
    if kampanya_frame.winfo_ismapped():
        kampanya_frame.pack_forget()
        btn_kampanya.config(text="Kampanya Filtreleme  ▶")
    else:
        kampanya_frame.pack(anchor="w", fill="x", padx=10) 
        btn_kampanya.config(text="Kampanya Filtreleme  ▼")


# Profil Güncelleme Ekranını Açan Fonksiyon
def profil_guncelle_ekrani_ac():
    global aktif_kullanici_email
    
    conn = sql_baglanti()
    cursor = conn.cursor()
    cursor.execute("SELECT  Sehir, Meslek FROM Musteriler WHERE Email = ?", (aktif_kullanici_email,))
    mevcut = cursor.fetchone()
    conn.close()

    if not mevcut: return

    win = tk.Toplevel(root)
    win.title("Profili Düzenle")
    win.geometry("300x450")

    tk.Label(win, text="Şehir:").pack()
    e_sehir = tk.Entry(win); e_sehir.insert(0, mevcut.Sehir); e_sehir.pack()

    tk.Label(win, text="Meslek:").pack()
    e_meslek = tk.Entry(win); e_meslek.insert(0, mevcut.Meslek); e_meslek.pack()


    def kaydet_ve_cikis():
        basarili = profili_sql_de_guncelle(
            aktif_kullanici_email, e_sehir.get(), e_meslek.get()
        )
        if basarili:
            messagebox.showinfo("Başarılı", "Bilgileriniz güncellendi!")
            adsoyad_label.config(text=f"{e_ad.get()} {e_soyad.get()}")
            detay_label.config(text=f'{e_yas.get()} yaş • {e_sehir.get()}\n{e_meslek.get()}\nAylık Gelir: {e_gelir.get()} ₺')
            win.destroy()

    tk.Button(win, text="Kaydet", bg="green", fg="black", command=kaydet_ve_cikis).pack(pady=20)


# ÜST BAR
ust_bar = tk.Frame(root, bg="#333", height=50)
menu_btn = tk.Button(ust_bar, text="☰", command=menu_ac_kapa, bg="#333", fg="black", font=("Arial", 15), bd=0)
menu_btn.pack(side="left", padx=10)
tk.Label(ust_bar, text="Akıllı Banka", bg="#333", fg="white", font=("Arial", 12, "bold")).pack(side="left", padx=10)

# MENÜ BUTONLARI
btn_profil = tk.Button(yan_menu, text="Profili Güncelle", bg="#444", fg="black", bd=0, anchor="w", padx=20, command=profil_guncelle_ekrani_ac)
btn_profil.pack(fill="x", pady=5)

btn_kampanya = tk.Button(yan_menu, text="Kampanya Filtreleme ▶", bg="#444", fg="black", bd=0, anchor="w", command=kampanya_alt_menu_ac_kapat, padx=20)
btn_kampanya.pack(fill="x", pady=5)

kampanya_frame = tk.Frame(yan_menu, bg="#555")

# Filtreleme Fonksiyonu
def kategoriye_git(kat):
    ana_sayfa.pack_forget()
    kampanya_sayfasi.pack(fill="both", expand=True)
    for w in kampanya_sayfasi.winfo_children(): w.destroy()
    
    tk.Label(kampanya_sayfasi, text=f"{kat} Kampanyaları", font=("Arial", 16, "bold")).pack(pady=20)
    veriler = kampanyalari_sql_den_cek(kategori_filtresi=kat)
    
    if not veriler: tk.Label(kampanya_sayfasi, text="Kampanya yok").pack()
    for k in veriler: kampanya_karti(kampanya_sayfasi, k["IndirimOrani"], k["GecerlilikTarihi"], k["SponsorFirma"])
    
    tk.Button(kampanya_sayfasi, text="Geri Dön", command=geri_don).pack(pady=20)
    menu_ac_kapa()

btn_alt1 = tk.Button(kampanya_frame, text="•Market", command=lambda: kategoriye_git("Market"), bg="#555", fg="black", anchor="w", padx=30)
btn_alt1.pack(fill="x")
btn_alt2 = tk.Button(kampanya_frame, text="•Seyahat", command=lambda: kategoriye_git("Seyahat"), bg="#555", fg="black", anchor="w", padx=30)
btn_alt2.pack(fill="x")
btn_alt3 = tk.Button(kampanya_frame, text="•Giyim", command=lambda: kategoriye_git("Giyim"), bg="#555", fg="black", anchor="w", padx=30)
btn_alt3.pack(fill="x")

def cikis_yap():
    global aktif_kullanici_email
    aktif_kullanici_email = None
    yan_menu.place_forget(); ust_bar.pack_forget(); ana_sayfa.pack_forget(); kampanya_sayfasi.pack_forget()
    giris_sayfasi.pack(fill="both", expand=True)

tk.Button(yan_menu, text="Çıkış", command=cikis_yap, bg="#444", fg="black", anchor="w", padx=20).pack(fill="x", pady=5)

#KAMPANYA KARTı
def kampanya_karti(parent, indirim, tarih, firma):
    kart = tk.Frame(parent, bg="pink", bd=1, relief="solid")
    kart.pack(padx=20, pady=8, fill="x")
    tk.Label(kart, text=f"İndirim: %{indirim}", fg="#e91e63", bg="pink", font=("Arial", 12, "bold")).pack(anchor="w", padx=10, pady=5)
    tk.Label(kart, text=f"Geçerlilik: {tarih}", bg="pink").pack(anchor="w", padx=10)
    tk.Label(kart, text=f"Firma: {firma}", bg="pink").pack(anchor="w", padx=10, pady=5)

def geri_don():
    kampanya_sayfasi.pack_forget()
    ana_sayfa.pack(fill="both", expand=True)

#GİRİŞ SAYFASI 
tk.Label(giris_sayfasi, text="Akıllı Banka", font=("Arial", 20, "bold"), bg="#f5f5f5", fg="#620e0e").pack(pady=40)
email_entry = tk.Entry(giris_sayfasi, width=30); email_entry.pack(pady=10)
sifre_entry = tk.Entry(giris_sayfasi, show="*", width=30); sifre_entry.pack(pady=10)

def giris_yap():
    global aktif_kullanici_email
    kul = kullanici_sql_den_cek(email_entry.get(), sifre_entry.get())
    if not kul:
        messagebox.showerror("Hata", "Hatalı Giriş")
        return

    aktif_kullanici_email = email_entry.get()
    giris_sayfasi.pack_forget()
    ust_bar.pack(side="top", fill="x")
    ana_sayfa.pack(fill="both", expand=True)
    
    adsoyad_label.config(text=kul["AdSoyad"])
    detay_label.config(text=f'{kul["Yas"]} yaş • {kul["Sehir"]}\n{kul["Meslek"]}\nAylık Gelir: {kul["Gelir"]} ₺')
    
    for w in ana_sayfa.winfo_children():
        if w not in (profil, kampanya_baslik): w.destroy()
    
    veriler = kampanyalari_sql_den_cek(musteri_email=aktif_kullanici_email)
    if not veriler: tk.Label(ana_sayfa, text="Size uygun kampanya bulunamadı").pack()
    for k in veriler: kampanya_karti(ana_sayfa, k["IndirimOrani"], k["GecerlilikTarihi"], k["SponsorFirma"])

tk.Button(giris_sayfasi, text="Giriş", bg="#6a1b9a", fg="black", width=20, command=giris_yap).pack(pady=20)
tk.Label(giris_sayfasi, text="Email: beydanurtekin06@gmail.com\nŞifre: 1234", fg="gray", bg="#f5f5f5").pack()

# KAYIT EKRANI 
def kayit_ac():
    win = tk.Toplevel(root); win.title("Kayıt")
    entries = {}
    for alan in ["Ad", "Soyad", "Yas", "Sehir", "Meslek", "Gelir", "Email", "Sifre"]:
        tk.Label(win, text=alan).pack()
        entries[alan] = tk.Entry(win)
        entries[alan].pack()
    
    def kaydet():
        if email_var_mi(entries["Email"].get()): messagebox.showerror("Hata", "Email kayıtlı"); return
        kullanici_kaydet(entries["Ad"].get(), entries["Soyad"].get(), int(entries["Yas"].get()), entries["Sehir"].get(),
                         entries["Meslek"].get(), float(entries["Gelir"].get()), entries["Email"].get(), entries["Sifre"].get())
        messagebox.showinfo("Başarılı", "Kayıt Tamam"); win.destroy()
    
    tk.Button(win, text="Kaydet", command=kaydet).pack(pady=10)

tk.Button(giris_sayfasi, text="Kayıt Ol", bg="#e91e63", fg="black", width=20, command=kayit_ac).pack(pady=10)

#AnaSayfa
profil = tk.Frame(ana_sayfa, bg="#f8dff3", bd=1, relief="solid")
profil.pack(pady=20, padx=20, fill="x")
adsoyad_label = tk.Label(profil, font=("Arial", 16, "bold"), bg="#f8dff3"); adsoyad_label.pack()
detay_label = tk.Label(profil, bg="#f8dff3"); detay_label.pack()

kampanya_baslik = tk.Label(ana_sayfa, text="Sizin İçin Akıllı Öneriler", font=("Arial", 14, "bold"), fg="#6a1b9a", bg="#f5f5f5")
kampanya_baslik.pack(pady=10)

root.mainloop()


