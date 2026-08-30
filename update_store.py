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
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
}

def fetch_json(url, headers=None):
    req_headers = HEADERS.copy()
    req_headers["Accept"] = "application/json"
    if headers:
        req_headers.update(headers)
    req = urllib.request.Request(url, headers=req_headers)
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
    repo_str = repo_str.strip('/')
    if repo_str.endswith(".git"):
        repo_str = repo_str[:-4]
    return repo_str

def extract_clean_repo_url(url, description=""):
    combined = f"{url} {description}"
    
    # GitHub
    gh_match = re.search(r"https?://github\.com/([^/\s\"']+)/([^/\s\"']+)", combined)
    if gh_match:
        return f"https://github.com/{gh_match.group(1)}/{clean_repo_name(gh_match.group(2))}", "github"

    # GitLab
    gl_match = re.search(r"https?://gitlab\.com/([^/\s\"']+)/([^/\s\"']+)", combined)
    if gl_match:
        return f"https://gitlab.com/{gl_match.group(1)}/{clean_repo_name(gl_match.group(2))}", "gitlab"

    # Forgejo / Gitea (prise en compte explicite de /projects/)
    cb_match = re.search(r"https?://([^/\s\"']+)/(?:projects/)?([^/\s\"']+)/([^/\s\"']+)", combined)
    if cb_match:
        domain, owner, repo = cb_match.group(1), cb_match.group(2), clean_repo_name(cb_match.group(3))
        if domain.startswith("git.") or "codeberg" in domain or any(k in combined.lower() for k in ["forgejo", "gitea", "eden", "ryujinx"]):
            return f"https://{domain}/projects/{owner}/{repo}", "forgejo"

    clean_url = re.sub(r'/(releases|tags|src)\.*$', '', url)
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

    # 3. FORGEJO / GITEA (AVEC SUPPORT DES TAGS/PROJECTS)
    if source_type == "forgejo":
        try:
            parsed = urllib.parse.urlparse(repo_url)
            domain = f"{parsed.scheme}://{parsed.netloc}"
            
            # Nettoyage de la route
            clean_path = re.sub(r"^/projects/", "/", parsed.path)
            parts = clean_path.strip("/").split("/")
            
            if len(parts) >= 2:
                owner, repo = parts[0], parts[1]
                data = None
                
                # Test des endpoints d'API possibles
                api_endpoints = [
                    f"{domain}/api/v1/repos/{owner}/{repo}/releases",
                    f"{domain}/api/v1/repos/projects/{owner}/{repo}/releases"
                ]
                
                for api_url in api_endpoints:
                    try:
                        releases_list = fetch_json(api_url)
                        if isinstance(releases_list, list) and len(releases_list) > 0:
                            data = releases_list[0]
                            break
                    except Exception:
                        continue

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
                    
                    # Si aucun binaire attaché, construction de l'archive de tag
                    if not assets:
                        zip_url = f"{domain}/projects/{owner}/{repo}/archive/{version}.zip"
                        sha_val = get_remote_sha256(zip_url)
                        if not sha_val:
                            zip_url = f"{domain}/{owner}/{repo}/archive/{version}.zip"
                            sha_val = get_remote_sha256(zip_url)
                        assets.append({"filename": f"{repo}-{version}.zip", "url": zip_url, "sha256": sha_val})

                    return version, body, assets, "forgejo", repo_url

                # Extraction via l'API Tags en cas d'absence de section Releases
                tag_endpoints = [
                    f"{domain}/api/v1/repos/{owner}/{repo}/tags",
                    f"{domain}/api/v1/repos/projects/{owner}/{repo}/tags"
                ]
                for tag_url in tag_endpoints:
                    try:
                        tags = fetch_json(tag_url)
                        if isinstance(tags, list) and len(tags) > 0:
                            tag_name = tags[0].get("name", "1.0.0")
                            zip_url = f"{domain}/projects/{owner}/{repo}/archive/{tag_name}.zip"
                            sha_val = get_remote_sha256(zip_url)
                            if not sha_val:
                                zip_url = f"{domain}/{owner}/{repo}/archive/{tag_name}.zip"
                                sha_val = get_remote_sha256(zip_url)
                            return tag_name, "Source release tag", [{"filename": f"{repo}-{tag_name}.zip", "url": zip_url, "sha256": sha_val}], "forgejo", repo_url
                    except Exception:
                        continue

                # Extraction manuelle directe pour les URLs soumises contenant un tag (ex: /tag/1.3.3)
                tag_match = re.search(r"/tag/([^/\s\"']+)", raw_url)
                if tag_match:
                    found_tag = tag_match.group(1)
                    zip_url = f"{domain}/projects/{owner}/{repo}/archive/{found_tag}.zip"
                    sha_val = get_remote_sha256(zip_url)
                    if not sha_val:
                        zip_url = f"{domain}/{owner}/{repo}/archive/{found_tag}.zip"
                        sha_val = get_remote_sha256(zip_url)
                    return found_tag, "Tag extrait directement de l'URL", [{"filename": f"{repo}-{found_tag}.zip", "url": zip_url, "sha256": sha_val}], "forgejo", repo_url

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
