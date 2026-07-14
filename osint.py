import requests
import json
import hashlib
import phonenumbers
from phonenumbers import carrier, geocoder
from datetime import datetime
import os

class OSINT_XRAY:
    def __init__(self):
        self.rapor = {
            "isim": "",
            "soyisim": "",
            "tc": "",
            "telefon": "",
            "eposta": [],
            "sosyal_medya": {},
            "adres": "",
            "sizinti": [],
            "tarih": datetime.now().isoformat()
        }
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        })

    def tc_ara(self, ad, soyad, dogum_yili):
        tc_hash = hashlib.sha256(f"{ad}{soyad}{dogum_yili}".encode()).hexdigest()
        self.rapor["tc"] = f"{tc_hash[:3]}{tc_hash[3:6]}{tc_hash[6:9]}{tc_hash[9:11]}"

    def telefon_ara(self, numara):
        try:
            parsed = phonenumbers.parse(numara, "TR")
            self.rapor["telefon"] = numara
            self.rapor["telefon_bilgi"] = {
                "operator": carrier.name_for_number(parsed, "tr"),
                "konum": geocoder.description_for_number(parsed, "tr")
            }
        except:
            pass

    def eposta_ara(self, ad, soyad):
        domainler = ["gmail.com", "hotmail.com", "yahoo.com", "outlook.com", "icloud.com"]
        kombinasyonlar = [
            f"{ad}.{soyad}", f"{ad}{soyad}", f"{ad}_{soyad}",
            f"{ad}-{soyad}", f"{ad}{soyad[0]}", f"{ad[0]}{soyad}"
        ]
        for domain in domainler:
            for combo in kombinasyonlar:
                self.rapor["eposta"].append(f"{combo}@{domain}")

    def sosyal_medya_ara(self, kullanici_adi):
        platformlar = {
            "instagram": f"https://instagram.com/{kullanici_adi}",
            "twitter": f"https://twitter.com/{kullanici_adi}",
            "facebook": f"https://facebook.com/{kullanici_adi}",
            "tiktok": f"https://tiktok.com/@{kullanici_adi}",
            "linkedin": f"https://linkedin.com/in/{kullanici_adi}"
        }
        for platform, url in platformlar.items():
            try:
                resp = self.session.get(url, timeout=5)
                if resp.status_code == 200:
                    self.rapor["sosyal_medya"][platform] = "Aktif"
                else:
                    self.rapor["sosyal_medya"][platform] = "Bulunamadı"
            except:
                self.rapor["sosyal_medya"][platform] = "Hata"

    def sizinti_kontrol(self, email):
        try:
            resp = self.session.get(f"https://haveibeenpwned.com/api/v3/breachedaccount/{email}")
            if resp.status_code == 200:
                for kayit in resp.json():
                    self.rapor["sizinti"].append(kayit["Name"])
            else:
                self.rapor["sizinti"].append("Sızıntı yok")
        except:
            self.rapor["sizinti"].append("API hatası")

    def adres_ara(self, tc, il):
        self.rapor["adres"] = f"{il}, Örnek Mahalle {tc[:3]} Sokak No: {tc[3:5]}"

    def rapor_olustur(self):
        with open("osint_rapor.json", "w", encoding="utf-8") as f:
            json.dump(self.rapor, f, ensure_ascii=False, indent=4)
        print("[✓] Rapor kaydedildi: osint_rapor.json")
        return self.rapor

    def full_tara(self, ad, soyad, dogum_yili, telefon, kullanici_adi, email, il):
        self.rapor["isim"] = ad
        self.rapor["soyisim"] = soyad
        self.tc_ara(ad, soyad, dogum_yili)
        self.telefon_ara(telefon)
        self.eposta_ara(ad, soyad)
        self.sosyal_medya_ara(kullanici_adi)
        self.sizinti_kontrol(email)
        self.adres_ara(self.rapor["tc"], il)
        return self.rapor_olustur()

if __name__ == "__main__":
    with open("config.json", "r", encoding="utf-8") as f:
        config = json.load(f)

    osint = OSINT_XRAY()
    sonuc = osint.full_tara(
        ad=config["ad"],
        soyad=config["soyad"],
        dogum_yili=config["dogum_yili"],
        telefon=config["telefon"],
        kullanici_adi=config["kullanici_adi"],
        email=config["email"],
        il=config["il"]
    )
    print(json.dumps(sonuc, ensure_ascii=False, indent=4))
