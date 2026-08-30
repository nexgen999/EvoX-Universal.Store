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

def clean_repo_name(repo_str):
    """ Nettoie proprement .git à la fin sans tronquer les lettres du nom (ex: flycast) """
    repo_str = repo_str.strip('/')
    if repo_str.endswith(".git"):
        repo_str = repo_str[:-4]
    return repo_str

def extract_clean_repo_url(url, description=""):
    """ Extrait l'URL brute du dépôt même si l'OPML contient un lien RSS FreshRSS ou HTML. """
    combined = f"{url} {description}"
    
    gh_match = re.search(r"https?://github\.com/([^/\s\"']+)/([^/\s\"']+)", combined)
    if gh_match:
        owner = gh_match.group(1)
        repo = clean_repo_name(gh_match.group(2))
        return f"https://github.com/{owner}/{repo}", "github"

    gl_match = re.search(r"https?://gitlab\.com/([^/\s\"']+)/([^/\s\"']+)", combined)
    if gl_match:
        owner = gl_match.group(1)
        repo = clean_repo_name(gl_match.group(2))
        return f"https://gitlab.com/{owner}/{repo}", "gitlab"

    # Match générique Forgejo / Gitea (prend en compte les sous-routes comme /projects/)
    cb_match = re.search(r"https?://([^/\s\"']+)/(?:projects/)?([^/\s\"']+)/([^/\s\"']+)", combined)
    if cb_match:
        domain = cb_match.group(1)
        owner = cb_match.group(2)
        repo = clean_repo_name(cb_match.group(3))
        known_domains = ["git.etawen.dev", "git.eden-emu.dev", "git.ryujinx.app", "codeberg.org"]
        if any(kd in domain for kd in known_domains) or "forgejo" in combined.lower() or "gitea" in combined.lower():
            return f"https://{domain}/{owner}/{repo}", "forgejo"

    # URL Directe
    clean_url = re.sub(r'/(releases|tags)\.(atom|rss|xml)$', '', url)
    clean_url = re.sub(r'\.(atom|rss|xml)$', '', clean_url)
    return clean_url, "generic"

def resolve_release_data(raw_url, description=""):
    repo_url, source_type = extract_clean_repo_url(raw_url, description)
    
    # 1. GITHUB
    gh_match = re.search(r"github\.com/([^/]+)/([^/]+)", repo_url)
    if gh_match:
        owner, repo = gh_match.group(1), gh_match.group(2)
        gh_headers = HEADERS.copy()
        if GITHUB_TOKEN:
            gh_headers["Authorization"] = f"token {GITHUB_TOKEN}"

        data = None
        # Détection si l'URL OPML pointe vers un tag/release spécifique (ex: /releases/tag/nightly-android)
        tag_match = re.search(r"/releases/tag/([^/\s\"']+)", raw_url)

        try:
            if tag_match:
                specific_tag = tag_match.group(1)
                api_url = f"https://api.github.com/repos/{owner}/{repo}/releases/tags/{specific_tag}"
            else:
                api_url = f"https://api.github.com/repos/{owner}/{repo}/releases/latest"
            
            data = fetch_json(api_url, gh_headers)
        except Exception:
            try:
                api_url = f"https://api.github.com/repos/{owner}/{repo}/releases"
                all_rel = fetch_json(api_url, gh_headers)
                if all_rel and isinstance(all_rel, list) and len(all_rel) > 0:
                    data = all_rel[0]
            except Exception as e:
                print(f"   [ERROR GitHub API] {owner}/{repo}: {e}")

        if data and data.get("assets"):
            version = data.get("tag_name", "v1.0")
            body = data.get("body", "")
            assets = []
            for asset in data.get("assets", []):
                dl_url = asset.get("browser_download_url", "")
                name = asset.get("name", "")
                sha = get_remote_sha256(dl_url)
                assets.append({"filename": name, "url": dl_url, "sha256": sha})
            return version, body, assets, "github", repo_url

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
                return tag_name, "Source release tag", assets, "github", repo_url
        except Exception as e:
            print(f"   [ERROR Tags GitHub] {owner}/{repo}: {e}")

    # 2. GITLAB
    gl_match = re.search(r"gitlab\.com/([^/]+)/([^/]+)", repo_url)
    if gl_match:
        owner, repo = gl_match.group(1), gl_match.group(2)
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
                return version, body, assets, "gitlab", repo_url
        except Exception as e:
            print(f"   [ERROR GitLab API] {owner}/{repo}: {e}")

    # 3. FORGEJO / GITEA
    if source_type == "forgejo":
        try:
            parsed = urllib.parse.urlparse(repo_url)
            domain = f"{parsed.scheme}://{parsed.netloc}"
            
            clean_path = re.sub(r"^/projects/", "/", parsed.path)
            parts = clean_path.strip("/").split("/")
            
            if len(parts) >= 2:
                owner, repo = parts[0], parts[1]
                data = None
                
                try:
                    api_url = f"{domain}/api/v1/repos/{owner}/{repo}/releases/latest"
                    data = fetch_json(api_url)
                except Exception:
                    try:
                        api_url_all = f"{domain}/api/v1/repos/{owner}/{repo}/releases"
                        all_rel = fetch_json(api_url_all)
                        if all_rel and isinstance(all_rel, list) and len(all_rel) > 0:
                            data = all_rel[0]
                    except Exception:
                        pass

                if data:
                    version = data.get("tag_name", "v1.0")
                    body = data.get("body", "")
                    assets = []
                    
                    for asset in data.get("assets", []):
                        dl_url = asset.get("browser_download_url", "")
                        if dl_url.startswith("/"):
                            dl_url = f"{domain}{dl_url}"
                            
                        name = asset.get("name", os.path.basename(dl_url))
                        sha = get_remote_sha256(dl_url)
                        assets.append({"filename": name, "url": dl_url, "sha256": sha})
                    
                    if not assets:
                        zip_url = data.get("zipball_url", f"{domain}/{owner}/{repo}/archive/{version}.zip")
                        assets.append({"filename": f"{repo}-{version}.zip", "url": zip_url, "sha256": get_remote_sha256(zip_url)})

                    return version, body, assets, "forgejo", repo_url

                # Fallback Tags si aucune release formelle n'a été créée
                try:
                    tags_api = f"{domain}/api/v1/repos/{owner}/{repo}/tags"
                    tags = fetch_json(tags_api)
                    if tags and len(tags) > 0:
                        tag_name = tags[0].get("name", "latest")
                        zip_url = f"{domain}/{owner}/{repo}/archive/{tag_name}.zip"
                        return tag_name, "Source release tag", [{"filename": f"{repo}-{tag_name}.zip", "url": zip_url, "sha256": get_remote_sha256(zip_url)}], "forgejo", repo_url
                except Exception:
                    pass

        except Exception as e:
            print(f"   [ERROR Forgejo API] {repo_url}: {e}")

    # 4. DIRECT / GENERIC
    filename = os.path.basename(repo_url) or "file.bin"
    sha = get_remote_sha256(repo_url)
    return "v1.0", "Fichier direct", [{"filename": filename, "url": repo_url, "sha256": sha}], source_type, repo_url

def parse_opml(opml_path):
    items = []
    try:
        tree = ET.parse(opml_path)
        root = tree.getroot()
        body = root.find("body")
        if body is not None:
            for outline in body.findall("outline"):
                attribs = outline.attrib
                raw_url = attribs.get("htmlUrl") or attribs.get("xmlUrl") or attribs.get("url")
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
                version, release_notes, assets, source_type, repo_url = resolve_release_data(item["raw_url"], item["description"])

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
