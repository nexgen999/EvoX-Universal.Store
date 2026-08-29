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
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

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
        print(f"      [WARN] SHA256 non calcule ({e})")
        return ""

def detect_source_type(url):
    if "github.com" in url: return "github"
    if "gitlab.com" in url: return "gitlab"
    if "codeberg.org" in url or "forgejo" in url: return "forgejo"
    if "gitea" in url: return "gitea"
    return "generic"

def resolve_release_data(url):
    source_type = detect_source_type(url)
    
    # 1. GITHUB
    gh_match = re.search(r"github\.com/([^/]+)/([^/]+)", url)
    if gh_match:
        owner, repo = gh_match.group(1), gh_match.group(2).rstrip(".git")
        repo_url = f"https://github.com/{owner}/{repo}"
        gh_headers = HEADERS.copy()
        if GITHUB_TOKEN:
            gh_headers["Authorization"] = f"token {GITHUB_TOKEN}"

        data = None
        # Tente /releases/latest, puis /releases, puis /tags
        try:
            api_url = f"https://api.github.com/repos/{owner}/{repo}/releases/latest"
            data = fetch_json(api_url, gh_headers)
        except Exception:
            try:
                api_url = f"https://api.github.com/repos/{owner}/{repo}/releases"
                all_rel = fetch_json(api_url, gh_headers)
                if all_rel and isinstance(all_rel, list) and len(all_rel) > 0:
                    data = all_rel[0]
            except Exception as e:
                print(f"   [ERROR GitHub] {owner}/{repo}: {e}")

        if data and data.get("assets"):
            version = data.get("tag_name", "v1.0")
            body = data.get("body", "")
            assets = []
            for asset in data.get("assets", []):
                dl_url = asset.get("browser_download_url", "")
                name = asset.get("name", "")
                sha = get_remote_sha256(dl_url)
                assets.append({"filename": name, "url": dl_url, "sha256": sha})
            return version, body, assets, source_type, repo_url

        # Fallback Tags (ex: Flycast si pas d'assets dans les releases)
        try:
            tags_url = f"https://api.github.com/repos/{owner}/{repo}/tags"
            tags = fetch_json(tags_url, gh_headers)
            if tags and len(tags) > 0:
                tag_name = tags[0].get("name", "latest")
                zip_url = f"https://github.com/{owner}/{repo}/archive/refs/tags/{tag_name}.zip"
                tar_url = f"https://github.com/{owner}/{repo}/archive/refs/tags/{tag_name}.tar.gz"
                assets = [
                    {"filename": f"{repo}-{tag_name}.zip", "url": zip_url, "sha256": get_remote_sha256(zip_url)},
                    {"filename": f"{repo}-{tag_name}.tar.gz", "url": tar_url, "sha256": get_remote_sha256(tar_url)}
                ]
                return tag_name, "Source release tag", assets, source_type, repo_url
        except Exception as e:
            print(f"   [ERROR Tags GitHub] {owner}/{repo}: {e}")

    # 2. GITLAB
    gl_match = re.search(r"gitlab\.com/([^/]+)/([^/]+)", url)
    if gl_match:
        owner, repo = gl_match.group(1), gl_match.group(2).rstrip(".git")
        repo_url = f"https://gitlab.com/{owner}/{repo}"
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
                return version, body, assets, source_type, repo_url
        except Exception as e:
            print(f"   [ERROR GitLab] {owner}/{repo}: {e}")

    # 3. DIRECT URL
    filename = os.path.basename(url) or "file.bin"
    sha = get_remote_sha256(url)
    return "v1.0", "Fichier direct", [{"filename": filename, "url": url, "sha256": sha}], source_type, url

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
                if not raw_url: continue
                items.append({
                    "name": attribs.get("text") or attribs.get("title") or "Unknown App",
                    "description": attribs.get("description", ""),
                    "raw_url": raw_url
                })
    except Exception as e:
        print(f"[ERROR] OPML {opml_path}: {e}")
    return items

def process_all_feeds():
    os.makedirs(JSON_DIR, exist_ok=True)
    all_store_categories = []

    for root_dir, _, files in os.walk(FEED_DIR):
        for file in files:
            if not file.endswith(".opml"): continue

            opml_path = os.path.join(root_dir, file)
            rel_path = os.path.relpath(opml_path, FEED_DIR)
            path_parts = rel_path.split(os.sep)

            category = path_parts[0] if len(path_parts) > 1 else "General"
            sub_category = os.path.splitext(path_parts[-1])[0]

            items = parse_opml(opml_path)
            apps = []

            for item in items:
                version, release_notes, assets, source_type, repo_url = resolve_release_data(item["raw_url"])

                apps.append({
                    "name": item["name"],
                    "description": item["description"],
                    "version": version,
                    "release_notes": release_notes,
                    "assets": assets,
                    "source_type": source_type,
                    "repo_url": repo_url
                })

            cat_json_data = {
                "category": category,
                "subcategory": sub_category,
                "apps": apps
            }

            out_cat_dir = os.path.join(JSON_DIR, category)
            os.makedirs(out_cat_dir, exist_ok=True)
            with open(os.path.join(out_cat_dir, f"{sub_category}.json"), "w", encoding="utf-8") as f:
                json.dump(cat_json_data, f, indent=2, ensure_ascii=False)

            all_store_categories.append(cat_json_data)

    aio_store = {
        "name": "EvoX Universal Store",
        "updated_at": datetime.utcnow().isoformat() + "Z",
        "store": all_store_categories
    }
    with open(os.path.join(JSON_DIR, "evox-store.json"), "w", encoding="utf-8") as f:
        json.dump(aio_store, f, indent=2, ensure_ascii=False)

if __name__ == "__main__":
    process_all_feeds()
