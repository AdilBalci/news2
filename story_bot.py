#!/usr/bin/env python3
"""
Türkiye Anlık Haber - Instagram Hikaye Botu
Hikayeleri indirir ve web sitesi için JSON manifest oluşturur
"""

import instaloader
import os
import json
import time
from datetime import datetime
from pathlib import Path

# Ayarlar (GitHub Secrets'tan alınır)
INSTAGRAM_USER = os.environ.get("INSTAGRAM_USER", "wwzcom")
INSTAGRAM_PASS = os.environ.get("INSTAGRAM_PASS", "")

# Aktif şehirler ve Instagram hesapları
CITIES = {
    "istanbul": {"id": "TR-34", "name": "İstanbul", "instagram": "istanbulanlik"},
    "ankara": {"id": "TR-06", "name": "Ankara", "instagram": "ankaraanlikcom"},
    "trabzon": {"id": "TR-61", "name": "Trabzon", "instagram": "trabzonanliktr"}
}

# Klasör yapısı
BASE_DIR = Path(__file__).parent
STORIES_DIR = BASE_DIR / "hikayeler"
MANIFEST_FILE = BASE_DIR / "stories.json"

def setup_directories():
    """Klasörleri oluştur"""
    STORIES_DIR.mkdir(exist_ok=True)
    for city in CITIES.values():
        (STORIES_DIR / city["instagram"]).mkdir(exist_ok=True)

def download_stories():
    """Hikayeleri indir ve manifest oluştur"""
    L = instaloader.Instaloader(
        dirname_pattern=str(STORIES_DIR / "{profile}"),
        filename_pattern="{date_utc:%Y%m%d_%H%M%S}_{shortcode}",
        download_video_thumbnails=False,
        download_geotags=False,
        download_comments=False,
        save_metadata=False,
        compress_json=False
    )
    
    # Giriş yap
    print(f"[*] Instagram'a giriş yapılıyor: {INSTAGRAM_USER}")
    try:
        L.login(INSTAGRAM_USER, INSTAGRAM_PASS)
        print("[+] Giriş başarılı!")
    except Exception as e:
        print(f"[-] Giriş hatası: {e}")
        return False
    
    manifest = {
        "updated": datetime.now().isoformat(),
        "cities": {}
    }
    
    for city_key, city_data in CITIES.items():
        username = city_data["instagram"]
        print(f"\n[*] {city_data['name']} ({username}) hikayeleri indiriliyor...")
        
        city_stories = []
        city_dir = STORIES_DIR / username
        
        # Eski hikayeleri temizle
        for old_file in city_dir.glob("*"):
            old_file.unlink()
        
        try:
            profile = instaloader.Profile.from_username(L.context, username)
            
            for story in L.get_stories(userids=[profile.userid]):
                for item in story.get_items():
                    # İndir
                    L.download_storyitem(item, target=username)
                    
                    # Dosya bilgisi
                    timestamp = item.date_utc.strftime("%Y%m%d_%H%M%S")
                    
                    # İndirilen dosyayı bul
                    for f in city_dir.glob(f"{timestamp}*"):
                        if f.suffix.lower() in ['.jpg', '.jpeg', '.png', '.mp4']:
                            story_info = {
                                "file": f"hikayeler/{username}/{f.name}",
                                "type": "video" if f.suffix.lower() == '.mp4' else "image",
                                "timestamp": item.date_utc.isoformat()
                            }
                            city_stories.append(story_info)
                            print(f"    [+] {f.name}")
                            break
                    
                    time.sleep(2)  # Rate limit
            
            print(f"    Toplam: {len(city_stories)} hikaye")
            
        except Exception as e:
            print(f"    [-] Hata: {e}")
        
        manifest["cities"][city_key] = {
            "id": city_data["id"],
            "name": city_data["name"],
            "instagram": username,
            "stories": city_stories
        }
        
        time.sleep(30)  # Hesaplar arası bekleme
    
    # Manifest kaydet
    with open(MANIFEST_FILE, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)
    
    print(f"\n[+] Manifest kaydedildi: {MANIFEST_FILE}")
    return True

def run_loop(interval_minutes=10):
    """Sürekli çalıştır"""
    setup_directories()
    
    while True:
        print(f"\n{'='*50}")
        print(f"Hikaye güncelleme başlıyor: {datetime.now()}")
        print('='*50)
        
        download_stories()
        
        print(f"\n[*] {interval_minutes} dakika bekleniyor...")
        time.sleep(interval_minutes * 60)

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--once":
        # Tek seferlik çalıştır
        setup_directories()
        download_stories()
    else:
        # Sürekli çalıştır
        run_loop(10)
