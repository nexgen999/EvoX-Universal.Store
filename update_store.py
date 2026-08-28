import os
import json
import hashlib
import shutil
import urllib.request
import re
import xml.etree.ElementTree as ET

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

FEED_INT_DIR = os.path.join(BASE_DIR, "feed", "internal", "payloads")
FEED_EXT_DIR = os.path.join(BASE_DIR, "feed", "external", "payloads")

JSON_INT_DIR = os.path.join(BASE_DIR, "json", "internal")
JSON_EXT_DIR = os.path.join(BASE_DIR, "json", "external")

FILES_LATEST_DIR = os.path.join(BASE_DIR, "files", "payloads", "internal", "latest")
FILES_OLD_DIR = os.path.join(BASE_DIR, "files", "payloads", "internal", "old")

BASE_URL = "https://nexgen999.github.io/EvoX-Universal.Store"

HEADERS = {"User-Agent": "Mozilla/5.0"}

def calculate_sha256(filepath):
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def resolve_github_release(url):
    """
    Si l'URL est un repo GitHub, récupère le binaire de la dernière release via l'API GitHub.
    """
    match = re.search(r"github\.com/([^/]+)/([^/]+)", url)
    if not match:
        return url, os.path.basename(url), "v1.0"

    owner, repo = match.group(1), match.group(2).rstrip(".git")
    api_url = f"https://api.github.com/repos/{owner}/{repo}/releases/latest"

    try:
        req = urllib.request.Request(api_url, headers=HEADERS)
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode())
            version = data.get("tag_name", "v1.0")
            for asset in data.get("assets", []):
                download_url = asset.get("browser_download_url", "")
                if download_url.endswith((".elf", ".bin", ".zip", ".prx")):
                    return download_url, asset.get("name"), version
    except Exception as e:
        print(f"Erreur API GitHub pour {owner}/{repo}: {e}")

    return url, f"{repo}.elf", "v1.0"

def parse_opml(opml_path):
    items = []
    try:
        tree = ET.parse(opml_path)
        root = tree.getroot()
        body = root.find("body")
        if body is not None:
            for outline in body.findall("outline"):
                attribs = outline.attrib
                raw_url = attribs.get("xmlUrl") or attribs.get("htmlUrl") or attribs.get("url")
                if not raw_url:
                    continue
                items.append({
                    "name": attribs.get("text") or attribs.get("title") or "Unknown",
                    "description": attribs.get("description", ""),
                    "raw_url": raw_url,
                    "version": attribs.get("version", ""),
                    "author": attribs.get("author", "Unknown")
                })
    except Exception as e:
        print(f"Erreur lecture OPML {opml_path}: {e}")
    return items

def generate_export_opml(category_name, items, output_path):
    """Génère un fichier OPML récapitulatif mis à jour."""
    root = ET.Element("opml", version="2.0")
    head = ET.SubElement(root, "head")
    title = ET.SubElement(head, "title")
    title.text = category_name

    body = ET.SubElement(root, "body")
    for item in items:
        ET.SubElement(body, "outline", {
            "text": item["name"],
            "title": item["name"],
            "type": "rss",
            "xmlUrl": item["raw_url"],
            "description": item["description"],
            "version": item.get("version", "v1.0")
        })

    tree = ET.ElementTree(root)
    ET.indent(tree, space="  ")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    tree.write(output_path, encoding="utf-8", xml_declaration=True)

def process_internal_feeds():
    os.makedirs(JSON_INT_DIR, exist_ok=True)
    os.makedirs(FILES_LATEST_DIR, exist_ok=True)
    os.makedirs(FILES_OLD_DIR, exist_ok=True)

    all_aio_payloads = []

    if not os.path.exists(FEED_INT_DIR):
        print(f"Dossier introuvable: {FEED_INT_DIR}")
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
            download_url, filename, resolved_version = resolve_github_release(item["raw_url"])
            version = item["version"] if item["version"] else resolved_version

            app_latest_dir = os.path.join(FILES_LATEST_DIR, cat_name, app_name, version)
            app_old_dir = os.path.join(FILES_OLD_DIR, cat_name, app_name)
            target_file_path = os.path.join(app_latest_dir, filename)

            # Rotation des anciennes versions
            if not os.path.exists(target_file_path):
                cat_latest_base = os.path.join(FILES_LATEST_DIR, cat_name, app_name)
                if os.path.exists(cat_latest_base):
                    for old_ver in os.listdir(cat_latest_base):
                        old_ver_path = os.path.join(cat_latest_base, old_ver)
                        if os.path.isdir(old_ver_path) and old_ver != version:
                            dest_old = os.path.join(app_old_dir, old_ver)
                            os.makedirs(dest_old, exist_ok=True)
                            shutil.move(old_ver_path, dest_old)

                os.makedirs(app_latest_dir, exist_ok=True)
                try:
                    req = urllib.request.Request(download_url, headers=HEADERS)
                    with urllib.request.urlopen(req) as response, open(target_file_path, "wb") as out_file:
                        shutil.copyfileobj(response, out_file)
                except Exception as e:
                    print(f"Échec téléchargement {download_url}: {e}")
                    continue

            checksum = calculate_sha256(target_file_path) if os.path.exists(target_file_path) else ""
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

        # Génération du JSON de catégorie
        cat_json_data = {"name": cat_name, "payloads": cat_payloads}
        with open(os.path.join(JSON_INT_DIR, f"{cat_name}.json"), "w", encoding="utf-8") as f:
            json.dump(cat_json_data, f, indent=2, ensure_ascii=False)

        # Génération de l'OPML récapitulatif
        generate_export_opml(cat_name, items, os.path.join(BASE_DIR, "feed", "internal", f"{cat_name}_export.opml"))

    # Génération du fichier AIO global
    aio_data = {"name": "AIO Store", "payloads": all_aio_payloads}
    with open(os.path.join(JSON_INT_DIR, "payloads.json"), "w", encoding="utf-8") as f:
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
            download_url, filename, resolved_version = resolve_github_release(item["raw_url"])
            version = item["version"] if item["version"] else resolved_version

            payload_obj = {
                "name": item["name"],
                "filename": filename,
                "url": download_url,
                "description": item["description"],
                "version": version,
                "category": cat_name,
                "checksum": ""
            }
            cat_payloads.append(payload_obj)

        cat_json_data = {"name": cat_name, "payloads": cat_payloads}
        with open(os.path.join(JSON_EXT_DIR, f"{cat_name}.json"), "w", encoding="utf-8") as f:
            json.dump(cat_json_data, f, indent=2, ensure_ascii=False)

        generate_export_opml(cat_name, items, os.path.join(BASE_DIR, "feed", "external", f"{cat_name}_export.opml"))

if __name__ == "__main__":
    process_internal_feeds()
    process_external_feeds()
