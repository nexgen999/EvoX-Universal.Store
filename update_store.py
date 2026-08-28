import os
import json
import hashlib
import shutil
import urllib.request
import xml.etree.ElementTree as ET

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

FEED_INT_DIR = os.path.join(BASE_DIR, "feed", "internal", "payloads")
FEED_EXT_DIR = os.path.join(BASE_DIR, "feed", "external", "payloads")

JSON_INT_DIR = os.path.join(BASE_DIR, "json", "internal")
JSON_EXT_DIR = os.path.join(BASE_DIR, "json", "external")

FILES_LATEST_DIR = os.path.join(BASE_DIR, "files", "payloads", "internal", "latest")
FILES_OLD_DIR = os.path.join(BASE_DIR, "files", "payloads", "internal", "old")

BASE_URL = "https://nexgen999.github.io/EvoX-Universal.Store"

def calculate_sha256(filepath):
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def parse_opml(opml_path):
    items = []
    tree = ET.parse(opml_path)
    root = tree.getroot()
    body = root.find("body")
    if body is not None:
        for outline in body.findall("outline"):
            attribs = outline.attrib
            url = attribs.get("xmlUrl") or attribs.get("htmlUrl") or attribs.get("url")
            if not url:
                continue
            item = {
                "name": attribs.get("text") or attribs.get("title") or "Unknown",
                "description": attribs.get("description", ""),
                "url": url,
                "version": attribs.get("version", "v1.0"),
                "author": attribs.get("author", "Unknown")
            }
            items.append(item)
    return items

def process_internal_feeds():
    os.makedirs(JSON_INT_DIR, exist_ok=True)
    os.makedirs(FILES_LATEST_DIR, exist_ok=True)
    os.makedirs(FILES_OLD_DIR, exist_ok=True)

    all_aio_payloads = []

    if not os.path.exists(FEED_INT_DIR):
        return

    for file_name in os.listdir(FEED_INT_DIR):
        if not file_name.endswith(".opml"):
            continue

        cat_name = os.path.splitext(file_name)[0]
        opml_path = os.path.join(FEED_INT_DIR, file_name)
        items = parse_opml(opml_path)

        cat_payloads = []

        for item in items:
            app_name = item["name"]
            version = item["version"]
            download_url = item["url"]
            filename = os.path.basename(download_url) or f"{app_name}.elf"

            app_latest_dir = os.path.join(FILES_LATEST_DIR, cat_name, app_name, version)
            app_old_dir = os.path.join(FILES_OLD_DIR, cat_name, app_name)
            
            target_file_path = os.path.join(app_latest_dir, filename)

            if not os.path.exists(target_file_path):
                cat_latest_base = os.path.join(FILES_LATEST_DIR, cat_name, app_name)
                if os.path.exists(cat_latest_base):
                    for old_ver in os.listdir(cat_latest_base):
                        old_ver_path = os.path.join(cat_latest_base, old_ver)
                        if os.path.isdir(old_ver_path) and old_ver != version:
                            dest_old = os.path.join(app_old_dir, old_ver)
                            os.makedirs(os.path.dirname(dest_old), exist_ok=True)
                            if os.path.exists(dest_old):
                                shutil.rmtree(dest_old)
                            shutil.move(old_ver_path, dest_old)

                os.makedirs(app_latest_dir, exist_ok=True)
                try:
                    urllib.request.urlretrieve(download_url, target_file_path)
                except Exception as e:
                    print(f"Erreur téléchargement {download_url}: {e}")
                    continue

            checksum = calculate_sha256(target_file_path)
            public_url = f"{BASE_URL}/files/payloads/internal/latest/{cat_name}/{app_name}/{version}/{filename}"

            payload_obj = {
                "name": app_name,
                "filename": filename,
                "url": public_url,
                "description": item["description"],
                "version": version,
                "category": cat_name,
                "checksum": checksum
            }

            cat_payloads.append(payload_obj)
            all_aio_payloads.append(payload_obj)

        cat_json_data = {
            "name": cat_name,
            "payloads": cat_payloads
        }
        cat_json_path = os.path.join(JSON_INT_DIR, f"{cat_name}.json")
        with open(cat_json_path, "w", encoding="utf-8") as f:
            json.dump(cat_json_data, f, indent=2, ensure_ascii=False)

    aio_data = {
        "name": "AIO Store",
        "payloads": all_aio_payloads
    }
    aio_json_path = os.path.join(JSON_INT_DIR, "payloads.json")
    with open(aio_json_path, "w", encoding="utf-8") as f:
        json.dump(aio_data, f, indent=2, ensure_ascii=False)

def process_external_feeds():
    os.makedirs(JSON_EXT_DIR, exist_ok=True)

    if not os.path.exists(FEED_EXT_DIR):
        return

    for file_name in os.listdir(FEED_EXT_DIR):
        if not file_name.endswith(".opml"):
            continue

        cat_name = os.path.splitext(file_name)[0]
        opml_path = os.path.join(FEED_EXT_DIR, file_name)
        items = parse_opml(opml_path)

        cat_payloads = []

        for item in items:
            app_name = item["name"]
            download_url = item["url"]
            filename = os.path.basename(download_url) or f"{app_name}.elf"

            payload_obj = {
                "name": app_name,
                "filename": filename,
                "url": download_url,
                "description": item["description"],
                "version": item["version"],
                "category": cat_name,
                "checksum": ""
            }
            cat_payloads.append(payload_obj)

        cat_json_data = {
            "name": cat_name,
            "payloads": cat_payloads
        }
        cat_json_path = os.path.join(JSON_EXT_DIR, f"{cat_name}.json")
        with open(cat_json_path, "w", encoding="utf-8") as f:
            json.dump(cat_json_data, f, indent=2, ensure_ascii=False)

if __name__ == "__main__":
    process_internal_feeds()
    process_external_feeds()
