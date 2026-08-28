import io
import json
import os
import re
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import urllib.error
import urllib.parse
import urllib.request
import zipfile

DEFAULT_RULES_PATH = os.path.join("config", "rules.json")


class RulesBuilderApp:

    def __init__(self, root):
        self.root = root
        self.root.title(
            "Générateur de Règles Universal Store (GitHub & Forgejo/Gitea)"
        )
        self.root.geometry("1400x850")

        self.data = {
            "$schema": "Configuration universelle des règles de filtrage",
            "global_settings": {
                "user_agent": "UniversalStoreEngine/1.0",
                "http_timeout_seconds": 30,
            },
            "repositories": [],
        }

        self.current_repo_index = None
        self.detected_versions = {"stable": "v1.0.0", "prerelease": None}

        self._build_ui()
        self.load_rules_file(DEFAULT_RULES_PATH)

    def _build_ui(self):
        toolbar = ttk.Frame(self.root, padding=5)
        toolbar.pack(fill=tk.X)

        ttk.Button(
            toolbar, text="📁 Charger rules.json", command=self.load_rules_dialog
        ).pack(side=tk.LEFT, padx=5)
        ttk.Button(
            toolbar,
            text="💾 Sauvegarder rules.json",
            command=self.save_rules_dialog,
        ).pack(side=tk.LEFT, padx=5)

        paned = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # --- GAUCHE : DÉPÔTS ---
        left_frame = ttk.LabelFrame(paned, text="Dépôts configurés", padding=5)
        paned.add(left_frame, weight=1)

        self.repo_listbox = tk.Listbox(left_frame, selectmode=tk.SINGLE)
        self.repo_listbox.pack(fill=tk.BOTH, expand=True, pady=(0, 5))
        self.repo_listbox.bind("<<ListboxSelect>>", self.on_repo_select)

        btn_left_box = ttk.Frame(left_frame)
        btn_left_box.pack(fill=tk.X)

        ttk.Button(
            btn_left_box,
            text="+ Ajouter un dépôt",
            command=self.add_new_repository,
        ).pack(fill=tk.X, pady=2)
        ttk.Button(
            btn_left_box,
            text="🗑️ Supprimer le dépôt",
            command=self.delete_repository,
        ).pack(fill=tk.X, pady=2)

        # --- DROITE : PANNEAU PRINCIPAL ---
        right_frame = ttk.Frame(paned, padding=5)
        paned.add(right_frame, weight=4)

        # 1. En-tête : Configuration Dépôt + Scan
        top_config = ttk.LabelFrame(
            right_frame, text="Configuration du Dépôt", padding=5
        )
        top_config.pack(fill=tk.X, pady=(0, 5))

        f_url = ttk.Frame(top_config)
        f_url.pack(fill=tk.X, pady=2)

        ttk.Label(f_url, text="URL / Dépôt:").pack(side=tk.LEFT, padx=5)
        self.ent_repo = ttk.Entry(f_url, width=50)
        self.ent_repo.pack(side=tk.LEFT, padx=5)

        self.var_enabled = tk.BooleanVar(value=True)
        ttk.Checkbutton(f_url, text="Actif", variable=self.var_enabled).pack(
            side=tk.LEFT, padx=10
        )

        btn_scan = ttk.Button(
            f_url,
            text="🔍 Scanner le dépôt",
            command=self.fetch_repository_assets,
        )
        btn_scan.pack(side=tk.RIGHT, padx=5)

        f_scan_options = ttk.Frame(top_config)
        f_scan_options.pack(fill=tk.X, pady=2)

        self.var_include_prerelease = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            f_scan_options,
            text="Inclure les Pre-releases",
            variable=self.var_include_prerelease,
        ).pack(side=tk.LEFT, padx=5)

        self.lbl_status_scan = ttk.Label(
            f_scan_options, text="Statut: Non scanné", foreground="gray"
        )
        self.lbl_status_scan.pack(side=tk.RIGHT, padx=5)

        # 2. Tableau des Assets
        tree_container = ttk.Frame(right_frame)
        tree_container.pack(fill=tk.BOTH, expand=True, pady=5)

        columns = (
            "keep",
            "type_release",
            "original_name",
            "inner_file",
            "unzip",
            "name_template",
            "preview_render",
        )
        self.tree_assets = ttk.Treeview(
            tree_container,
            columns=columns,
            show="headings",
            selectmode="browse",
        )

        vsb = ttk.Scrollbar(
            tree_container, orient="vertical", command=self.tree_assets.yview
        )
        hsb = ttk.Scrollbar(
            tree_container, orient="horizontal", command=self.tree_assets.xview
        )
        self.tree_assets.configure(
            yscrollcommand=vsb.set, xscrollcommand=hsb.set
        )

        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        hsb.pack(side=tk.BOTTOM, fill=tk.X)
        self.tree_assets.pack(fill=tk.BOTH, expand=True)

        self.tree_assets.heading("keep", text="Garder ?")
        self.tree_assets.heading("type_release", text="Release")
        self.tree_assets.heading("original_name", text="Mot-clé Asset / Match")
        self.tree_assets.heading("inner_file", text="Fichier interne (ZIP)")
        self.tree_assets.heading("unzip", text="Extraire ?")
        self.tree_assets.heading("name_template", text="Patron ({version})")
        self.tree_assets.heading("preview_render", text="Aperçu Renommé")

        self.tree_assets.column("keep", width=75, minwidth=60, anchor="center")
        self.tree_assets.column(
            "type_release", width=90, minwidth=80, anchor="center"
        )
        self.tree_assets.column("original_name", width=240, minwidth=150)
        self.tree_assets.column("inner_file", width=240, minwidth=150)
        self.tree_assets.column(
            "unzip", width=75, minwidth=60, anchor="center"
        )
        self.tree_assets.column("name_template", width=250, minwidth=150)
        self.tree_assets.column("preview_render", width=220, minwidth=150)

        self.tree_assets.bind("<Button-1>", self.on_asset_click)
        self.tree_assets.bind("<Double-1>", self.on_asset_double_click)

        # 3. Panneau d'édition
        edit_f = ttk.LabelFrame(
            right_frame, text="Édition de la règle sélectionnée", padding=8
        )
        edit_f.pack(fill=tk.X, pady=5)

        f_row1 = ttk.Frame(edit_f)
        f_row1.pack(fill=tk.X, pady=2)

        ttk.Label(f_row1, text="Mot-clé Asset:").pack(side=tk.LEFT, padx=2)
        self.ent_rule_match = ttk.Entry(f_row1, width=28)
        self.ent_rule_match.pack(side=tk.LEFT, padx=(2, 15))

        ttk.Label(f_row1, text="Fichier interne (ZIP):").pack(
            side=tk.LEFT, padx=2
        )
        self.ent_inner_file = ttk.Entry(f_row1, width=32)
        self.ent_inner_file.pack(side=tk.LEFT, padx=(2, 15))

        self.var_rule_unzip = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            f_row1, text="Extraire le ZIP", variable=self.var_rule_unzip
        ).pack(side=tk.LEFT, padx=5)

        f_row2 = ttk.Frame(edit_f)
        f_row2.pack(fill=tk.X, pady=4)

        ttk.Label(f_row2, text="Patron du nom cible:").pack(side=tk.LEFT, padx=2)
        self.ent_rule_template = ttk.Entry(f_row2, width=50)
        self.ent_rule_template.pack(side=tk.LEFT, padx=(2, 15))

        ttk.Button(
            f_row2,
            text="✔️ Appliquer à la ligne sélectionnée",
            command=self.apply_rule_row_edit,
        ).pack(side=tk.LEFT, padx=5)

        # 4. Filtres Globaux
        filters_f = ttk.LabelFrame(
            right_frame, text="Filtres Globaux d'exclusion", padding=5
        )
        filters_f.pack(fill=tk.X, pady=5)

        ttk.Label(filters_f, text="Ext. Autorisées:").grid(
            row=0, column=0, sticky=tk.W, padx=2
        )
        self.ent_target_ext = ttk.Entry(filters_f, width=28)
        self.ent_target_ext.grid(row=0, column=1, padx=5, pady=2)

        ttk.Label(filters_f, text="Ext. Exclues:").grid(
            row=0, column=2, sticky=tk.W, padx=2
        )
        self.ent_exclude_ext = ttk.Entry(filters_f, width=28)
        self.ent_exclude_ext.grid(row=0, column=3, padx=5, pady=2)

        ttk.Label(filters_f, text="Mots Inclus:").grid(
            row=1, column=0, sticky=tk.W, padx=2
        )
        self.ent_include_kw = ttk.Entry(filters_f, width=28)
        self.ent_include_kw.grid(row=1, column=1, padx=5, pady=2)

        ttk.Label(filters_f, text="Mots Exclus:").grid(
            row=1, column=2, sticky=tk.W, padx=2
        )
        self.ent_exclude_kw = ttk.Entry(filters_f, width=28)
        self.ent_exclude_kw.grid(row=1, column=3, padx=5, pady=2)

        ttk.Button(
            filters_f,
            text="⚡ Appliquer filtres globaux",
            command=self.apply_global_filters_to_tree,
        ).grid(row=0, column=4, rowspan=2, padx=10, sticky="nsew")

        ttk.Button(
            right_frame,
            text="💾 Enregistrer la configuration pour ce dépôt",
            command=self.save_current_repo_fields,
        ).pack(fill=tk.X, pady=5)

    def parse_repository_url(self, raw_url):
        raw_url = raw_url.strip()
        if not raw_url or raw_url == "Nouveau dépôt":
            return "", "github", ""

        if not raw_url.startswith("http://") and not raw_url.startswith("https://"):
            clean = raw_url.rstrip(".git").strip("/")
            return clean, "github", f"https://api.github.com/repos/{clean}/releases"

        parsed = urllib.parse.urlparse(raw_url)
        path_parts = [p for p in parsed.path.strip("/").split("/") if p]

        if len(path_parts) < 2:
            return raw_url, "github", raw_url

        owner, repo = path_parts[0], path_parts[1].replace(".git", "")
        clean_name = f"{owner}/{repo}"

        if "github.com" in parsed.netloc:
            api_url = f"https://api.github.com/repos/{clean_name}/releases"
            return clean_name, "github", api_url
        else:
            base_scheme_domain = f"{parsed.scheme}://{parsed.netloc}"
            api_url = f"{base_scheme_domain}/api/v1/repos/{owner}/{repo}/releases"
            full_clean = f"{parsed.netloc}/{owner}/{repo}"
            return full_clean, "forgejo", api_url

    def sanitize_keyword(self, filename):
        cleaned = re.sub(
            r"[-_]v?\d+\.\d+.*?(?=\.|$)", "", filename, flags=re.IGNORECASE
        )
        return cleaned if cleaned else filename

    def fetch_repository_assets(self):
        raw_input = self.ent_repo.get().strip()
        clean_repo, provider_type, api_url = self.parse_repository_url(raw_input)

        if not clean_repo:
            messagebox.showwarning(
                "Attention", "Entrez une URL ou un nom de dépôt valide."
            )
            return

        req = urllib.request.Request(
            api_url, headers={"User-Agent": "UniversalStoreEngine/1.0"}
        )

        try:
            with urllib.request.urlopen(req, timeout=10) as response:
                releases_list = json.loads(response.read().decode())
        except Exception as e:
            messagebox.showerror(
                "Erreur API", f"Impossible d'interroger {api_url} : {e}"
            )
            return

        if not releases_list:
            messagebox.showwarning("Information", "Aucune release trouvée.")
            return

        for item in self.tree_assets.get_children():
            self.tree_assets.delete(item)

        stable_rel = None
        prerelease_rel = None

        for rel in releases_list:
            is_pre = rel.get("prerelease", False)
            if is_pre and not prerelease_rel:
                prerelease_rel = rel
            elif not is_pre and not stable_rel:
                stable_rel = rel

            if stable_rel and (
                prerelease_rel or not self.var_include_prerelease.get()
            ):
                break

        self.detected_versions["stable"] = (
            stable_rel.get("tag_name", "v1.0.0") if stable_rel else "v1.0.0"
        )
        self.detected_versions["prerelease"] = (
            prerelease_rel.get("tag_name") if prerelease_rel else None
        )

        status_text = f"Stable: {self.detected_versions['stable']}"
        if prerelease_rel and self.var_include_prerelease.get():
            status_text += f" | Pre-release: {self.detected_versions['prerelease']}"
        self.lbl_status_scan.config(text=status_text, foreground="green")

        if stable_rel:
            self._process_release_assets(
                stable_rel, "Stable", self.detected_versions["stable"]
            )

        if prerelease_rel and self.var_include_prerelease.get():
            self._process_release_assets(
                prerelease_rel,
                "Pre-release",
                self.detected_versions["prerelease"],
            )

    def _process_release_assets(self, release_data, rel_type, ver_tag):
        assets = release_data.get("assets", [])
        for asset in assets:
            asset_name = asset["name"]
            download_url = asset.get(
                "browser_download_url"
            ) or asset.get("download_url")

            # Traitement des archives ZIP
            if asset_name.lower().endswith(".zip") and download_url:
                zip_files = self._peek_zip_contents(download_url)
                if zip_files:
                    for inner_f in zip_files:
                        if inner_f.endswith("/"):
                            continue
                        filename_only = os.path.basename(inner_f)
                        ext = os.path.splitext(filename_only)[1]
                        base = os.path.splitext(filename_only)[0]
                        tmpl = f"{base}_v{{version}}{ext}"
                        preview = tmpl.replace("{version}", ver_tag)

                        self.tree_assets.insert(
                            "",
                            tk.END,
                            values=(
                                "✅ Oui",
                                rel_type,
                                asset_name,
                                inner_f,
                                "✅ Oui",
                                tmpl,
                                preview,
                            ),
                        )
                    continue

            # Traitement des fichiers normaux
            ext = os.path.splitext(asset_name)[1]
            base = os.path.splitext(self.sanitize_keyword(asset_name))[0]
            tmpl = f"{base}_v{{version}}{ext}" if base else asset_name
            preview = tmpl.replace("{version}", ver_tag)

            self.tree_assets.insert(
                "",
                tk.END,
                values=(
                    "✅ Oui",
                    rel_type,
                    asset_name,
                    "-",
                    "❌ Non",
                    tmpl,
                    preview,
                ),
            )

    def _peek_zip_contents(self, url):
        try:
            req = urllib.request.Request(
                url, headers={"User-Agent": "UniversalStoreEngine/1.0"}
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = resp.read()
                with zipfile.ZipFile(io.BytesIO(data)) as z:
                    return z.namelist()
        except Exception:
            return []

    def save_current_repo_fields(self):
        if self.current_repo_index is None:
            messagebox.showwarning("Attention", "Sélectionnez un dépôt.")
            return

        raw_input = self.ent_repo.get().strip()
        clean_repo, _, _ = self.parse_repository_url(raw_input)

        if not clean_repo:
            clean_repo = "Nouveau dépôt"

        repo = self.data["repositories"][self.current_repo_index]
        repo["repo"] = clean_repo
        repo["enabled"] = self.var_enabled.get()
        repo["include_prerelease"] = self.var_include_prerelease.get()
        repo["processing_mode"] = "multi_assets"

        repo["global_asset_filters"] = {
            "target_extensions": [
                x.strip()
                for x in self.ent_target_ext.get().split(",")
                if x.strip()
            ],
            "global_exclude_extensions": [
                x.strip()
                for x in self.ent_exclude_ext.get().split(",")
                if x.strip()
            ],
            "global_include_keywords": [
                x.strip()
                for x in self.ent_include_kw.get().split(",")
                if x.strip()
            ],
            "global_exclude_keywords": [
                x.strip()
                for x in self.ent_exclude_kw.get().split(",")
                if x.strip()
            ],
        }

        assets_rules = []
        for item_id in self.tree_assets.get_children():
            vals = self.tree_assets.item(item_id, "values")
            keep = vals[0] == "✅ Oui"
            rel_type = vals[1]
            match_kw = vals[2]
            inner_f = vals[3]
            unzip = vals[4] == "✅ Oui"
            tmpl = vals[5]

            rule_entry = {
                "target_release_type": rel_type,
                "match_keyword": match_kw,
                "extract_archive": unzip,
                "clean_name_template": tmpl,
                "enabled": keep,
            }

            if unzip and inner_f != "-":
                rule_entry["target_extracted_file"] = inner_f

            assets_rules.append(rule_entry)

        repo["assets_rules"] = assets_rules

        self.ent_repo.delete(0, tk.END)
        self.ent_repo.insert(0, clean_repo)

        self.refresh_repo_list()
        messagebox.showinfo(
            "Sauvegarde", f"Dépôt '{clean_repo}' mis à jour avec succès !"
        )

    def add_new_repository(self):
        new_repo = {
            "repo": "Nouveau dépôt",
            "enabled": True,
            "include_prerelease": True,
            "processing_mode": "multi_assets",
            "assets_rules": [],
            "global_asset_filters": {},
        }
        self.data.setdefault("repositories", []).append(new_repo)
        self.current_repo_index = len(self.data["repositories"]) - 1
        self.refresh_repo_list()
        self.on_repo_select(None)

    def apply_global_filters_to_tree(self):
        target_exts = [
            x.strip().lower()
            for x in self.ent_target_ext.get().split(",")
            if x.strip()
        ]
        excl_exts = [
            x.strip().lower()
            for x in self.ent_exclude_ext.get().split(",")
            if x.strip()
        ]
        incl_kws = [
            x.strip().lower()
            for x in self.ent_include_kw.get().split(",")
            if x.strip()
        ]
        excl_kws = [
            x.strip().lower()
            for x in self.ent_exclude_kw.get().split(",")
            if x.strip()
        ]

        for item_id in self.tree_assets.get_children():
            vals = list(self.tree_assets.item(item_id, "values"))
            asset_name = vals[2].lower()
            inner_file = vals[3].lower()
            check_name = (
                inner_file if inner_file and inner_file != "-" else asset_name
            )

            keep = True
            if target_exts and not any(
                check_name.endswith(ext) for ext in target_exts
            ):
                keep = False
            if excl_exts and any(
                check_name.endswith(ext) for ext in excl_exts
            ):
                keep = False
            if incl_kws and not any(kw in check_name for kw in incl_kws):
                keep = False
            if excl_kws and any(kw in check_name for kw in excl_kws):
                keep = False

            vals[0] = "✅ Oui" if keep else "❌ Non"
            self.tree_assets.item(item_id, values=vals)

    def on_asset_click(self, event):
        region = self.tree_assets.identify("region", event.x, event.y)
        if region != "cell":
            return

        column = self.tree_assets.identify_column(event.x)
        item_id = self.tree_assets.identify_row(event.y)
        if not item_id:
            return

        vals = list(self.tree_assets.item(item_id, "values"))
        if column == "#1":
            vals[0] = "❌ Non" if vals[0] == "✅ Oui" else "✅ Oui"
            self.tree_assets.item(item_id, values=vals)
        elif column == "#5":
            vals[4] = "❌ Non" if vals[4] == "✅ Oui" else "✅ Oui"
            self.tree_assets.item(item_id, values=vals)

    def on_asset_double_click(self, event):
        item_id = self.tree_assets.selection()
        if not item_id:
            return
        vals = self.tree_assets.item(item_id[0], "values")

        self.ent_rule_match.delete(0, tk.END)
        self.ent_rule_match.insert(0, vals[2])

        self.ent_inner_file.delete(0, tk.END)
        self.ent_inner_file.insert(0, vals[3] if vals[3] != "-" else "")

        self.var_rule_unzip.set(vals[4] == "✅ Oui")

        self.ent_rule_template.delete(0, tk.END)
        self.ent_rule_template.insert(0, vals[5])

    def apply_rule_row_edit(self):
        item_id = self.tree_assets.selection()
        if not item_id:
            return

        vals = list(self.tree_assets.item(item_id[0], "values"))
        rel_type = vals[1]
        tmpl = self.ent_rule_template.get().strip()

        ver = (
            self.detected_versions["prerelease"]
            if "Pre" in rel_type and self.detected_versions["prerelease"]
            else self.detected_versions["stable"]
        )

        vals[2] = self.ent_rule_match.get().strip()
        vals[3] = self.ent_inner_file.get().strip() or "-"
        vals[4] = "✅ Oui" if self.var_rule_unzip.get() else "❌ Non"
        vals[5] = tmpl
        vals[6] = tmpl.replace("{version}", ver)

        self.tree_assets.item(item_id[0], values=vals)

    def load_rules_file(self, path):
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    self.data = json.load(f)
                self.refresh_repo_list()
            except Exception as e:
                messagebox.showerror("Erreur", f"Lecture impossible : {e}")

    def refresh_repo_list(self):
        self.repo_listbox.delete(0, tk.END)
        for repo in self.data.get("repositories", []):
            name = repo.get("repo") or "Nouveau dépôt"
            if not repo.get("enabled", True):
                name += " (Désactivé)"
            self.repo_listbox.insert(tk.END, name)

        if (
            self.current_repo_index is not None
            and self.current_repo_index < len(self.data["repositories"])
        ):
            self.repo_listbox.select_set(self.current_repo_index)

    def on_repo_select(self, event):
        sel = self.repo_listbox.curselection()
        if not sel:
            return
        self.current_repo_index = sel[0]
        repo_data = self.data["repositories"][self.current_repo_index]

        self.ent_repo.delete(0, tk.END)
        self.ent_repo.insert(0, repo_data.get("repo", ""))
        self.var_enabled.set(repo_data.get("enabled", True))
        self.var_include_prerelease.set(
            repo_data.get("include_prerelease", True)
        )

        for item in self.tree_assets.get_children():
            self.tree_assets.delete(item)

        for rule in repo_data.get("assets_rules", []):
            keep = rule.get("enabled", True)
            rel_type = rule.get("target_release_type", "Stable")
            match_kw = rule.get("match_keyword", "")
            inner_f = rule.get("target_extracted_file", "-")
            unzip = "✅ Oui" if rule.get("extract_archive", False) else "❌ Non"
            tmpl = rule.get("clean_name_template", "")
            preview = tmpl.replace(
                "{version}", self.detected_versions["stable"]
            )

            self.tree_assets.insert(
                "",
                tk.END,
                values=(
                    "✅ Oui" if keep else "❌ Non",
                    rel_type,
                    match_kw,
                    inner_f,
                    unzip,
                    tmpl,
                    preview,
                ),
            )

        filters = repo_data.get("global_asset_filters", {})
        self.ent_target_ext.delete(0, tk.END)
        self.ent_target_ext.insert(
            0, ", ".join(filters.get("target_extensions", []))
        )
        self.ent_exclude_ext.delete(0, tk.END)
        self.ent_exclude_ext.insert(
            0, ", ".join(filters.get("global_exclude_extensions", []))
        )
        self.ent_include_kw.delete(0, tk.END)
        self.ent_include_kw.insert(
            0, ", ".join(filters.get("global_include_keywords", []))
        )
        self.ent_exclude_kw.delete(0, tk.END)
        self.ent_exclude_kw.insert(
            0, ", ".join(filters.get("global_exclude_keywords", []))
        )

    def delete_repository(self):
        if self.current_repo_index is not None:
            del self.data["repositories"][self.current_repo_index]
            self.current_repo_index = None
            self.refresh_repo_list()
            for item in self.tree_assets.get_children():
                self.tree_assets.delete(item)
            self.ent_repo.delete(0, tk.END)

    def load_rules_dialog(self):
        p = filedialog.askopenfilename(filetypes=[("JSON Files", "*.json")])
        if p:
            self.load_rules_file(p)

    def save_rules_dialog(self):
        p = filedialog.asksaveasfilename(
            defaultextension=".json",
            initialfile="rules.json",
            filetypes=[("JSON Files", "*.json")],
        )
        if p:
            self.save_current_repo_fields()
            with open(p, "w", encoding="utf-8") as f:
                json.dump(self.data, f, indent=2, ensure_ascii=False)
            messagebox.showinfo("Succès", f"Fichier sauvegardé :\n{p}")


if __name__ == "__main__":
    root = tk.Tk()
    app = RulesBuilderApp(root)
    root.mainloop()
