#!/usr/bin/env python3
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
        data = instagram_request(url)
        
        # DEBUG: Tam response yapısını göster
        print(f"    [DEBUG] Response keys: {list(data.keys())}")
        if "data" in data:
            print(f"    [DEBUG] data keys: {list(data['data'].keys()) if data['data'] else 'None'}")
            if data['data'] and 'user' in data['data']:
                user = data['data']['user']
                print(f"    [DEBUG] user keys: {list(user.keys())[:10]}...")
                if 'edge_owner_to_timeline_media' in user:
                    media = user['edge_owner_to_timeline_media']
                    print(f"    [DEBUG] media keys: {list(media.keys())}")
                    print(f"    [DEBUG] edge count: {len(media.get('edges', []))}")
        
        user = data.get("data", {}).get("user")
        if not user:
            print(f"    [-] User yok")
            return posts
            
        edges = user.get("edge_owner_to_timeline_media", {}).get("edges", [])
        
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
            print(f"    [+] {node['shortcode']}")
    except Exception as e:
        print(f"    [-] Hata: {type(e).__name__}: {e}")
    return posts

def download_file(url, filepath):
    try:
        headers = {
            "User-Agent": "Mozilla/5.0",
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
    
    print(f"[+] Session OK")
    
    manifest = {"updated": datetime.now().isoformat(), "cities": {}}
    
    for city_key, city_data in CITIES.items():
        username = city_data["instagram"]
        print(f"\n[*] {city_data['name']} (@{username})")
        
        posts = get_user_posts(username, count=6)
        city_posts = []
        city_dir = STORIES_DIR / username
        
        for post in posts:
            if post["is_video"] and post["video_url"]:
                filename = f"{post['shortcode']}.mp4"
                thumb_filename = f"{post['shortcode']}_thumb.jpg"
                if download_file(post["video_url"], city_dir / filename):
                    download_file(post["image_url"], city_dir / thumb_filename)
                    city_posts.append({
                        "file": f"hikayeler/{username}/{filename}",
                        "thumb": f"hikayeler/{username}/{thumb_filename}",
                        "type": "video",
                        "timestamp": post["timestamp"],
                        "caption": post["caption"][:200] if post["caption"] else "",
                        "link": f"https://www.instagram.com/p/{post['shortcode']}/",
                        "likes": post["likes"]
                    })
            else:
                filename = f"{post['shortcode']}.jpg"
                if download_file(post["image_url"], city_dir / filename):
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
        print(f"    Toplam: {len(city_posts)}")
        time.sleep(3)
    
    with open(MANIFEST_FILE, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)
    print(f"\n[+] Kaydedildi")

if __name__ == "__main__":
    print(f"{'='*50}")
    print(f"Post güncelleme: {datetime.now()}")
    print('='*50)
    setup_directories()
    fetch_all()
