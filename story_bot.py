#!/usr/bin/env python3
"""
Türkiye Anlık Haber - Instagram Bot
Video + Resim indirme destekli
"""

import os
import json
import time
import urllib.request
from datetime import datetime
from pathlib import Path

SESSION_ID = os.environ.get("INSTAGRAM_SESSION_ID", "")

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

def instagram_request(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "X-IG-App-ID": "936619743392459",
        "X-Requested-With": "XMLHttpRequest",
        "Cookie": SESSION_ID
    }
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=15) as response:
        return json.loads(response.read().decode())

def get_user_posts(username, count=6):
    posts = []
    try:
        url = f"https://www.instagram.com/api/v1/users/web_profile_info/?username={username}"
        print(f"    [*] API çağrısı: {url[:50]}...")
        data = instagram_request(url)
        
        user = data.get("data", {}).get("user")
        if not user:
            print(f"    [-] Kullanıcı bulunamadı: {data}")
            return posts
            
        edges = user.get("edge_owner_to_timeline_media", {}).get("edges", [])
        print(f"    [*] {len(edges)} post bulundu")
        
        for edge in edges[:count]:
            node = edge["node"]
            post = {
                "id": node["id"],
                "shortcode": node["shortcode"],
                "image_url": node["display_url"],
                "video_url": node.get("video_url"),
                "caption": node["edge_media_to_caption"]["edges"][0]["node"]["text"] if node["edge_media_to_caption"]["edges"] else "",
                "timestamp": datetime.fromtimestamp(node["taken_at_timestamp"]).isoformat(),
                "is_video": node["is_video"],
                "likes": node["edge_liked_by"]["count"]
            }
            posts.append(post)
            print(f"    [+] {node['shortcode']} ({'video' if node['is_video'] else 'image'})")
    except urllib.error.HTTPError as e:
        print(f"    [-] HTTP Hata: {e.code} - {e.reason}")
        print(f"    [-] Response: {e.read().decode()[:500]}")
    except Exception as e:
        print(f"    [-] Hata: {type(e).__name__}: {e}")
    return posts

def download_file(url, filepath):
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Cookie": SESSION_ID
        }
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=30) as response:
            with open(filepath, 'wb') as f:
                f.write(response.read())
        return True
    except Exception as e:
        print(f"    [-] İndirme hatası: {e}")
        return False

def fetch_all():
    if not SESSION_ID:
        print("[-] INSTAGRAM_SESSION_ID eksik!")
        return
    
    print(f"[+] Session ID uzunluk: {len(SESSION_ID)}")
    print(f"[+] Session başlangıç: {SESSION_ID[:50]}...")
    
    manifest = {
        "updated": datetime.now().isoformat(),
        "cities": {}
    }
    
    for city_key, city_data in CITIES.items():
        username = city_data["instagram"]
        print(f"\n[*] {city_data['name']} (@{username}) postları çekiliyor...")
        
        posts = get_user_posts(username, count=6)
        city_posts = []
        city_dir = STORIES_DIR / username
        
        for post in posts:
            if post["is_video"] and post["video_url"]:
                filename = f"{post['shortcode']}.mp4"
                filepath = city_dir / filename
                thumb_filename = f"{post['shortcode']}_thumb.jpg"
                thumb_filepath = city_dir / thumb_filename
                
                video_ok = download_file(post["video_url"], filepath)
                thumb_ok = download_file(post["image_url"], thumb_filepath)
                
                if video_ok:
                    city_posts.append({
                        "file": f"hikayeler/{username}/{filename}",
                        "thumb": f"hikayeler/{username}/{thumb_filename}" if thumb_ok else None,
                        "type": "video",
                        "timestamp": post["timestamp"],
                        "caption": post["caption"][:200] if post["caption"] else "",
                        "link": f"https://www.instagram.com/p/{post['shortcode']}/",
                        "likes": post["likes"]
                    })
            else:
                filename = f"{post['shortcode']}.jpg"
                filepath = city_dir / filename
                
                if download_file(post["image_url"], filepath):
                    city_posts.append({
                        "file": f"hikayeler/{username}/{filename}",
                        "thumb": None,
                        "type": "image",
                        "timestamp": post["timestamp"],
                        "caption": post["caption"][:200] if post["caption"] else "",
                        "link": f"https://www.instagram.com/p/{post['shortcode']}/",
                        "likes": post["likes"]
                    })
            
            time.sleep(1)
        
        manifest["cities"][city_key] = {
            "id": city_data["id"],
            "name": city_data["name"],
            "instagram": username,
            "stories": city_posts
        }
        
        print(f"    Toplam: {len(city_posts)} post")
        time.sleep(3)
    
    with open(MANIFEST_FILE, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)
    
    print(f"\n[+] Kaydedildi: {MANIFEST_FILE}")

if __name__ == "__main__":
    print(f"{'='*50}")
    print(f"Post güncelleme: {datetime.now()}")
    print('='*50)
    setup_directories()
    fetch_all()
