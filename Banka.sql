 CREATE DATABASE BANKA
 ON(
    NAME = banka_dat,
    FILENAME = '/Users/deryatekin/Documents/SQLData/bankadat.mdf',
    SIZE = 40 MB,
    MAXSIZE = 80 MB,
    FILEGROWTH = 5%
 )
 LOG ON(
    NAME = banka_log,
    FILENAME = '/Users/deryatekin/Documents/SQLData/bankadat.ndf',
    SIZE = 20 MB,
    MAXSIZE = 40 MB,
    FILEGROWTH = 5%
 )

 use BANKA


 SELECT * FROM Musteriler
 SELECT * FROM Islemler 
 SELECT * FROM Kampanyalar
 SELECT * FROM Oneriler

 CREATE TABLE Musteriler(
    MusteriID  INT IDENTITY(1,1) PRIMARY KEY,
    Ad NVARCHAR(60) NOT NULL,
    Soyad NVARCHAR(60) NOT NULL,
    Yas INT NOT NULL,
    Sehir NVARCHAR(60) NOT NULL,
    Meslek Nvarchar(60) NOT NULL,
    Gelir DECIMAL(10, 4),
    Email NVARCHAR(50) UNIQUE NOT NULL

 );



 CREATE TABLE Islemler(
    IslemID  INT IDENTITY(1,1) PRIMARY KEY,
    MusteriID INT FOREIGN KEY REFERENCES Musteriler(MusteriID),
    Kategori NVARCHAR(50) NOT NULL,
    Tutar DECIMAL(12,4),
    Tarih DATETIME DEFAULT GETDATE(),
    Lokasyon NVARCHAR(50),
    Kaynak NVARCHAR(50),
    Platform NVARCHAR (50),
    CihazTipi NVARCHAR(50) 
 );



 CREATE TABLE Kampanyalar(
    KampanyaID INT IDENTITY(1,1) PRIMARY KEY,
    KampanyaAdi NVARCHAR(100) NOT NULL,
    Kategori NVARCHAR(50) NOT NULL,
    Aciklama NVARCHAR(500),
    IndirimOrani INT,
    GecerlilikTarihi DATETIME NOT NULL,
    SponsorFirma NVARCHAR(100),
    AI_oncelik INT DEFAULT 0

 );



 CREATE TABLE Oneriler(
    OneriID INT IDENTITY(1,1) PRIMARY KEY,
    MusteriID INT FOREIGN KEY REFERENCES Musteriler(MusteriID), 
    KampanyaID INT FOREIGN KEY REFERENCES Kampanyalar(KampanyaID),
    Tarih DATETIME DEFAULT GETDATE(),
    GeriBildirim NVARCHAR(255)

 );



INSERT INTO Musteriler (Ad, Soyad, Yas, Sehir, Meslek, Gelir, Email)
VALUES ('Beydanur','Tekin', 24, 'Ankara', 'Avukat', 350000.0000 , 'beydanurtekin06@gmail.com')



INSERT INTO Islemler (MusteriID, Kategori, Tutar, Tarih, Lokasyon, Kaynak, Platform, CihazTipi)
VALUES(1, 'Seyahat', 15.000, '2025-10-10', 'Paris', 'Pegasus', 'Mobil', 'Macbook');
INSERT INTO Islemler (MusteriID, Kategori, Tutar, Tarih, Lokasyon, Kaynak, Platform, CihazTipi)
VALUES(1, 'Market', 1000, '2025-10-29', 'Bim', 'Bim Aktüel', 'Mobil', 'Samsung');
INSERT INTO Islemler (MusteriID, Kategori, Tutar, Tarih, Lokasyon, Kaynak, Platform, CihazTipi)
VALUES(1, 'Bakım ve hijyen', 15.000, '2025-10-10', 'Sephora', 'Bakım ürünleri', 'Mobil', 'Samsung');



INSERT INTO Kampanyalar (KampanyaAdi, Kategori, Aciklama, IndirimOrani, GecerlilikTarihi, SponsorFirma, AI_oncelik)
VALUES('Pegasus yurtdışı uçuşlarında %25 uçak indirimi', 'Seyahat', 'Yurtdışı uçuşlarda geçerli', 25, '2025-10-30', 'Pegasus Hava yolları', 8);
INSERT INTO Kampanyalar (KampanyaAdi, Kategori, Aciklama, IndirimOrani, GecerlilikTarihi, SponsorFirma, AI_oncelik)
VALUES('Black Friday', 'Giyim', 'Zara da dev indirim', 45, '2025-11-10', 'ZARA', 9);
INSERT INTO Kampanyalar (KampanyaAdi, Kategori, Aciklama, IndirimOrani, GecerlilikTarihi, SponsorFirma, AI_oncelik)
VALUES('Yemek Sepeti', 'Yiyecek', 'Sepete %15 indirim ', 15, '2025-12-15', 'Birsev Tantunş', 1);
INSERT INTO Kampanyalar (KampanyaAdi, Kategori, Aciklama, IndirimOrani, GecerlilikTarihi, SponsorFirma, AI_oncelik)
VALUES('TrendyolMilla', 'Giyim', 'Tüm Ceketlerde %35 indirim', 35, '2025-10-30', 'TrendyolMilla', 10);


INSERT INTO Oneriler (MusteriID, KampanyaID, Tarih, GeriBildirim)
VALUES (1, 1, GETDATE(), NULL);

SELECT * FROM Musteriler WHERE Email = 'beydanurtekin06@gmail.com';


--Beydanın son 3ay ki harcamaları 
SELECT Kategori, SUM(Tutar) AS ToplamHarcama
FROM Islemler
WHERE MusteriID = 1 
  AND Tarih >= DATEADD(MONTH, -3, GETDATE())
GROUP BY Kategori
ORDER BY ToplamHarcama DESC;


--“Bugünün tarihi hâlâ geçerli olan Pegasus kampanyasının ID’sini bul ve onu @KampanyaID değişkenine kaydet.”
DECLARE @KampanyaID INT;
SELECT @KampanyaID = KampanyaID 
FROM Kampanyalar 
WHERE KampanyaAdi LIKE '%Pegasus%' AND GecerlilikTarihi >= GETDATE();

