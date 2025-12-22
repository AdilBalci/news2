#!/usr/bin/env python3
"""
Türkiye Anlık Haber - Instagram Post Çekici
Login gerektirmeden son postları çeker
"""

import json
import os
import urllib.request
import re
from datetime import datetime
from pathlib import Path

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
    # Eğer hikayeler bir dosya ise sil
    if STORIES_DIR.exists() and STORIES_DIR.is_file():
        STORIES_DIR.unlink()
    STORIES_DIR.mkdir(exist_ok=True)
    for city in CITIES.values():
        city_dir = STORIES_DIR / city["instagram"]
        if city_dir.exists() and city_dir.is_file():
            city_dir.unlink()
        city_dir.mkdir(exist_ok=True)

def get_instagram_posts(username, count=5):
    """Instagram profilinden son postları çek (login gerektirmez)"""
    posts = []
    
    try:
        url = f"https://www.instagram.com/api/v1/users/web_profile_info/?username={username}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "X-IG-App-ID": "936619743392459"
        }
        
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode())
            
        edges = data["data"]["user"]["edge_owner_to_timeline_media"]["edges"]
        
        for edge in edges[:count]:
            node = edge["node"]
            post = {
                "id": node["id"],
                "shortcode": node["shortcode"],
                "image": node["display_url"],
                "caption": node["edge_media_to_caption"]["edges"][0]["node"]["text"] if node["edge_media_to_caption"]["edges"] else "",
                "timestamp": datetime.fromtimestamp(node["taken_at_timestamp"]).isoformat(),
                "type": "video" if node["is_video"] else "image",
                "likes": node["edge_liked_by"]["count"],
                "link": f"https://www.instagram.com/p/{node['shortcode']}/"
            }
            posts.append(post)
            print(f"    [+] {post['shortcode']} - {post['timestamp'][:10]}")
            
    except Exception as e:
        print(f"    [-] Hata: {e}")
    
    return posts

def download_image(url, filepath):
    """Resmi indir"""
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=15) as response:
            with open(filepath, 'wb') as f:
                f.write(response.read())
        return True
    except:
        return False

def fetch_all():
    """Tüm şehirlerin postlarını çek"""
    setup_directories()
    
    manifest = {
        "updated": datetime.now().isoformat(),
        "cities": {}
    }
    
    for city_key, city_data in CITIES.items():
        username = city_data["instagram"]
        print(f"\n[*] {city_data['name']} (@{username}) postları çekiliyor...")
        
        posts = get_instagram_posts(username, count=6)
        city_posts = []
        
        for post in posts:
            # Resmi indir
            filename = f"{post['shortcode']}.jpg"
            filepath = STORIES_DIR / username / filename
            
            if download_image(post["image"], filepath):
                city_posts.append({
                    "file": f"hikayeler/{username}/{filename}",
                    "type": post["type"],
                    "timestamp": post["timestamp"],
                    "caption": post["caption"][:200] if post["caption"] else "",
                    "link": post["link"],
                    "likes": post["likes"]
                })
        
        manifest["cities"][city_key] = {
            "id": city_data["id"],
            "name": city_data["name"],
            "instagram": username,
            "stories": city_posts
        }
        
        print(f"    Toplam: {len(city_posts)} post")
    
    # Manifest kaydet
    with open(MANIFEST_FILE, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)
    
    print(f"\n[+] Kaydedildi: {MANIFEST_FILE}")

if __name__ == "__main__":
    print(f"{'='*50}")
    print(f"Post güncelleme: {datetime.now()}")
    print('='*50)
    fetch_all()
