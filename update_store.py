import os
import json
import hashlib
import urllib.request
import urllib.parse
import re
from datetime import datetime
import xml.etree.ElementTree as ET

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FEED_DIR = os.path.join(BASE_DIR, "feed")
JSON_DIR = os.path.join(BASE_DIR, "json")

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
HEADERS = {"User-Agent": "Mozilla/5.0"}

def fetch_json(url, headers=None):
    req = urllib.request.Request(url, headers=headers or HEADERS)
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode())

def get_remote_sha256(file_url):
    try:
        req = urllib.request.Request(file_url, headers=HEADERS)
        sha256_hash = hashlib.sha256()
        with urllib.request.urlopen(req) as resp:
            while chunk := resp.read(8192):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()
    except Exception as e:
        print(f"      [WARN] SHA256 non calculé ({e})")
        return ""

def resolve_release_data(url):
    # 1. GITHUB
    gh_match = re.search(r"github\.com/([^/]+)/([^/]+)", url)
    if gh_match:
        owner, repo = gh_match.group(1), gh_match.group(2).rstrip(".git")
        gh_headers = HEADERS.copy()
        if GITHUB_TOKEN:
            gh_headers["Authorization"] = f"token {GITHUB_TOKEN}"

        # Essai Release 'latest' puis fallback sur l'ensemble des releases (inclut pre-releases)
        data = None
        try:
            api_url = f"https://api.github.com/repos/{owner}/{repo}/releases/latest"
            data = fetch_json(api_url, gh_headers)
        except Exception:
            try:
                api_url = f"https://api.github.com/repos/{owner}/{repo}/releases"
                all_releases = fetch_json(api_url, gh_headers)
                if all_releases and isinstance(all_releases, list):
                    data = all_releases[0]
            except Exception as e:
                print(f"   [ERROR GitHub] {owner}/{repo}: {e}")

        if data:
            version = data.get("tag_name", "v1.0")
            body = data.get("body", "")
            assets = []
            for asset in data.get("assets", []):
                dl_url = asset.get("browser_download_url", "")
                name = asset.get("name", "")
                sha = get_remote_sha256(dl_url)
                assets.append({"filename": name, "url": dl_url, "sha256": sha})
            return version, body, assets

    # 2. GITLAB
    gl_match = re.search(r"gitlab\.com/([^/]+)/([^/]+)", url)
    if gl_match:
        owner, repo = gl_match.group(1), gl_match.group(2).rstrip(".git")
        project_id = urllib.parse.quote_plus(f"{owner}/{repo}")
        api_url = f"https://gitlab.com/api/v4/projects/{project_id}/releases"
        try:
            releases = fetch_json(api_url)
            if releases:
                latest = releases[0]
                version = latest.get("tag_name", "v1.0")
                body = latest.get("description", "")
                assets = []
                for link in latest.get("assets", {}).get("links", []):
                    dl_url = link.get("direct_asset_url", link.get("url", ""))
                    name = link.get("name", os.path.basename(dl_url))
                    sha = get_remote_sha256(dl_url)
                    assets.append({"filename": name, "url": dl_url, "sha256": sha})
                return version, body, assets
        except Exception as e:
            print(f"   [ERROR GitLab] {owner}/{repo}: {e}")

    # 3. URL FIXE
    filename = os.path.basename(url) or "file.bin"
    sha = get_remote_sha256(url)
    return "v1.0", "Direct download file", [{"filename": filename, "url": url, "sha256": sha}]

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
                    "name": attribs.get("text") or attribs.get("title") or "Unknown App",
                    "description": attribs.get("description", ""),
                    "raw_url": raw_url
                })
    except Exception as e:
        print(f"[ERROR] Lecture OPML {opml_path}: {e}")
    return items

def process_all_feeds():
    os.makedirs(JSON_DIR, exist_ok=True)
    all_store_categories = []

    for root_dir, _, files in os.walk(FEED_DIR):
        for file in files:
            if not file.endswith(".opml"):
                continue

            opml_path = os.path.join(root_dir, file)
            rel_path = os.path.relpath(opml_path, FEED_DIR)
            path_parts = rel_path.split(os.sep)

            category = path_parts[0] if len(path_parts) > 1 else "General"
            sub_category = os.path.splitext(path_parts[-1])[0]

            print(f"-> Traitement: {category} / {sub_category}")

            items = parse_opml(opml_path)
            apps = []

            for item in items:
                print(f"   Scrapping: {item['name']}...")
                version, release_notes, assets = resolve_release_data(item["raw_url"])

                apps.append({
                    "name": item["name"],
                    "description": item["description"],
                    "version": version,
                    "release_notes": release_notes,
                    "assets": assets
                })

            cat_json_data = {
                "category": category,
                "subcategory": sub_category,
                "apps": apps
            }

            out_cat_dir = os.path.join(JSON_DIR, category)
            os.makedirs(out_cat_dir, exist_ok=True)
            out_json_path = os.path.join(out_cat_dir, f"{sub_category}.json")

            with open(out_json_path, "w", encoding="utf-8") as f:
                json.dump(cat_json_data, f, indent=2, ensure_ascii=False)

            all_store_categories.append(cat_json_data)

    aio_store = {
        "name": "EvoX Universal Store",
        "updated_at": datetime.utcnow().isoformat() + "Z",
        "store": all_store_categories
    }
    with open(os.path.join(JSON_DIR, "evox-store.json"), "w", encoding="utf-8") as f:
        json.dump(aio_store, f, indent=2, ensure_ascii=False)

    print("\n[SUCCESS] Génération terminée avec succès !")

if __name__ == "__main__":
    process_all_feeds()
