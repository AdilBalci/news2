#!/usr/bin/env python3
"""
Türkiye Anlık Haber - Instagram Hikaye/Post Botu
Instaloader ile login yaparak çeker
"""

import instaloader
import os
import json
import time
from datetime import datetime
from pathlib import Path

# Ayarlar (GitHub Secrets'tan alınır)
INSTAGRAM_USER = os.environ.get("INSTAGRAM_USER", "")
INSTAGRAM_PASS = os.environ.get("INSTAGRAM_PASS", "")

# Aktif şehirler
CITIES = {
    "istanbul": {"id": "TR-34", "name": "İstanbul", "instagram": "istanbulanlik"},
    "ankara": {"id": "TR-06", "name": "Ankara", "instagram": "ankaraanlikcom"},
    "trabzon": {"id": "TR-61", "name": "Trabzon", "instagram": "trabzonanliktr"}
}

BASE_DIR = Path(__file__).parent
STORIES_DIR = BASE_DIR / "hikayeler"
MANIFEST_FILE = BASE_DIR / "stories.json"

def setup_directories():
    if STORIES_DIR.exists() and STORIES_DIR.is_file():
        STORIES_DIR.unlink()
    STORIES_DIR.mkdir(exist_ok=True)
    for city in CITIES.values():
        city_dir = STORIES_DIR / city["instagram"]
        if city_dir.exists() and city_dir.is_file():
            city_dir.unlink()
        city_dir.mkdir(exist_ok=True)

def fetch_posts():
    """Instagram'dan son postları çek"""
    
    L = instaloader.Instaloader(
        download_video_thumbnails=False,
        download_geotags=False,
        download_comments=False,
        save_metadata=False,
        compress_json=False,
        post_metadata_txt_pattern=""
    )
    
    # Login yap
    if INSTAGRAM_USER and INSTAGRAM_PASS:
        print(f"[*] Instagram'a giriş yapılıyor: {INSTAGRAM_USER}")
        try:
            L.login(INSTAGRAM_USER, INSTAGRAM_PASS)
            print("[+] Giriş başarılı!")
        except Exception as e:
            print(f"[-] Giriş hatası: {e}")
            return
    else:
        print("[-] Instagram kullanıcı bilgileri eksik!")
        return
    
    manifest = {
        "updated": datetime.now().isoformat(),
        "cities": {}
    }
    
    for city_key, city_data in CITIES.items():
        username = city_data["instagram"]
        print(f"\n[*] {city_data['name']} (@{username}) postları çekiliyor...")
        
        city_posts = []
        city_dir = STORIES_DIR / username
        
        try:
            profile = instaloader.Profile.from_username(L.context, username)
            
            # Son 5 postu çek
            count = 0
            for post in profile.get_posts():
                if count >= 5:
                    break
                
                filename = f"{post.shortcode}.jpg"
                filepath = city_dir / filename
                
                # Resmi indir
                try:
                    L.download_pic(filepath.stem, post.url, post.date_utc, filename_suffix="", _attempt=1)
                    # Dosyayı doğru yere taşı
                    for f in Path(".").glob(f"{post.shortcode}*"):
                        f.rename(filepath)
                        break
                except Exception as e:
                    print(f"    [-] İndirme hatası: {e}")
                    continue
                
                city_posts.append({
                    "file": f"hikayeler/{username}/{filename}",
                    "type": "video" if post.is_video else "image",
                    "timestamp": post.date_utc.isoformat(),
                    "caption": (post.caption or "")[:200],
                    "link": f"https://www.instagram.com/p/{post.shortcode}/",
                    "likes": post.likes
                })
                
                print(f"    [+] {post.shortcode}")
                count += 1
                time.sleep(2)
            
            print(f"    Toplam: {len(city_posts)} post")
            
        except Exception as e:
            print(f"    [-] Hata: {e}")
        
        manifest["cities"][city_key] = {
            "id": city_data["id"],
            "name": city_data["name"],
            "instagram": username,
            "stories": city_posts
        }
        
        time.sleep(10)
    
    # Kaydet
    with open(MANIFEST_FILE, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)
    
    print(f"\n[+] Kaydedildi: {MANIFEST_FILE}")

if __name__ == "__main__":
    print(f"{'='*50}")
    print(f"Post güncelleme: {datetime.now()}")
    print('='*50)
    setup_directories()
    fetch_posts()
