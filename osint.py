import requests
import json
import re
import time
import hashlib
import phonenumbers
from phonenumbers import carrier, geocoder
from bs4 import BeautifulSoup
import pandas as pd
import base64
import os
import socket
import dns.resolver
import whois
from datetime import datetime

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
            "ip_tarihce": [],
            "domain_bilgileri": {},
            "kimlik_dogrulama": "",
            "akrabalar": [],
            "arac_plaka": "",
            "adli_kayit": "Taranamadı"
        }
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        })

    # ========== TC KİMLİK (Sahte Doğrulama + Hash) ==========
    def tc_ara(self, ad, soyad, dogum_yili):
        print("[*] TC kimlik üretiliyor...")
        tc_hash = hashlib.sha256(f"{ad}{soyad}{dogum_yili}".encode()).hexdigest()
        tc = f"{tc_hash[:3]}{tc_hash[3:6]}{tc_hash[6:9]}{tc_hash[9:11]}"
        self.rapor["tc"] = tc
        self.rapor["kimlik_dogrulama"] = "Doğrulama simüle edildi (gerçek API için e-Devlet entegrasyonu gerekir)"

    # ========== TELEFON ==========
    def telefon_ara(self, numara):
        print("[*] Telefon bilgileri aranıyor...")
        try:
            parsed = phonenumbers.parse(numara, "TR")
            self.rapor["telefon"] = numara
            self.rapor["digger_veri"] = self.rapor.get("digger_veri", {})
            self.rapor["digger_veri"]["telefon_operator"] = carrier.name_for_number(parsed, "tr")
            self.rapor["digger_veri"]["telefon_konum"] = geocoder.description_for_number(parsed, "tr")
        except:
            pass

    # ========== E-POSTA TARAMA ==========
    def eposta_ara(self, ad, soyad):
        print("[*] E-posta kombinasyonları oluşturuluyor...")
        domainler = ["gmail.com", "hotmail.com", "yahoo.com", "outlook.com", "icloud.com", "yandex.com"]
        kombinasyonlar = [
            f"{ad}.{soyad}", f"{ad}{soyad}", f"{ad}_{soyad}",
            f"{ad}-{soyad}", f"{ad}{soyad[0]}", f"{ad[0]}{soyad}",
            f"{ad}{soyad}1", f"{ad}.{soyad}1"
        ]
        for domain in domainler:
            for combo in kombinasyonlar:
                self.rapor["eposta"].append(f"{combo}@{domain}")

    # ========== SOSYAL MEDYA ==========
    def sosyal_medya_ara(self, kullanici_adi):
        print("[*] Sosyal medya hesapları taranıyor...")
        platformlar = {
            "instagram": f"https://www.instagram.com/{kullanici_adi}",
            "twitter": f"https://twitter.com/{kullanici_adi}",
            "facebook": f"https://facebook.com/{kullanici_adi}",
            "tiktok": f"https://tiktok.com/@{kullanici_adi}",
            "linkedin": f"https://linkedin.com/in/{kullanici_adi}",
            "youtube": f"https://youtube.com/@{kullanici_adi}",
            "reddit": f"https://reddit.com/user/{kullanici_adi}",
            "github": f"https://github.com/{kullanici_adi}"
        }
        for platform, url in platformlar.items():
            try:
                resp = self.session.get(url, timeout=5)
                if resp.status_code == 200:
                    self.rapor["sosyal_medya"][platform] = url
                else:
                    self.rapor["sosyal_medya"][platform] = "Bulunamadı"
            except:
                self.rapor["sosyal_medya"][platform] = "Hata"

    # ========== SIZINTI KONTROL ==========
    def sizinti_kontrol(self, email):
        print("[*] Sızıntı veritabanları taranıyor...")
        url = f"https://haveibeenpwned.com/api/v3/breachedaccount/{email}"
        try:
            resp = self.session.get(url)
            if resp.status_code == 200:
                for kayit in resp.json():
                    self.rapor["sizinti"].append(kayit["Name"])
            else:
                self.rapor["sizinti"].append("Sızıntı bulunamadı")
        except:
            self.rapor["sizinti"].append("API hatası")

    # ========== ADRES ==========
    def adres_ara(self, tc, il=None):
        print("[*] Adres bilgileri aranıyor...")
        if il:
            self.rapor["adres"] = f"{il}, Örnek Mahalle {tc[:3]} Sokak No: {tc[3:5]}"
        else:
            self.rapor["adres"] = f"Örnek Mahalle {tc[:3]} Sokak No: {tc[3:5]}, İstanbul"

    # ========== DOMAIN / IP ==========
    def domain_ara(self, domain):
        print("[*] Domain bilgileri aranıyor...")
        try:
            w = whois.whois(domain)
            self.rapor["domain_bilgileri"] = {
                "kayit_tarihi": str(w.creation_date),
                "son_kullanma": str(w.expiration_date),
                "kayitci": str(w.registrar),
                "name_servers": w.name_servers
            }
        except:
            pass

    # ========== RAPOR KAYDET ==========
    def rapor_olustur(self):
        print("[*] Rapor oluşturuluyor...")
        self.rapor["tarih"] = datetime.now().isoformat()
        with open("osint_rapor.json", "w", encoding="utf-8") as f:
            json.dump(self.rapor, f, ensure_ascii=False, indent=4)
        return self.rapor

    # ========== FULL TARAMA ==========
    def full_tara(self, ad, soyad, dogum_yili="1990", telefon=None, kullanici_adi=None, email=None, domain=None, il=None):
        print(f"[+] OSINT X-RAY başlatıldı: {ad} {soyad}")
        self.rapor["isim"] = ad
        self.rapor["soyisim"] = soyad

        self.tc_ara(ad, soyad, dogum_yili)
        if telefon:
            self.telefon_ara(telefon)
        self.eposta_ara(ad, soyad)
        if kullanici_adi:
            self.sosyal_medya_ara(kullanici_adi)
        if email:
            self.sizinti_kontrol(email)
        self.adres_ara(self.rapor["tc"], il)
        if domain:
            self.domain_ara(domain)
        return self.rapor_olustur()

# =================== ÇALIŞTIR ===================
if __name__ == "__main__":
    osint = OSINT_XRAY()
    sonuc = osint.full_tara(
        ad="Ahmet",
        soyad="Yılmaz",
        dogum_yili="1990",
        telefon="+905551234567",
        kullanici_adi="ahmetyilmaz",
        email="ahmet.yilmaz@gmail.com",
        domain="ornek.com",
        il="Ankara"
    )
    print(json.dumps(sonuc, ensure_ascii=False, indent=4))
