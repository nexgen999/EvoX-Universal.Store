# 📦 EvoX Universal AIO Store

Bienvenue sur **EvoX Universal AIO Store**, un catalogue web dynamique permettant d'explorer, filtrer et télécharger des applications et des ressources centralisées.

---

## 📘 Documentation de `config.json`

Le fichier `config.json` permet de personnaliser l'interface web du Store sans toucher au code HTML ou JavaScript :

* **`site_title`** : Titre affiché dans l'onglet du navigateur.
* **`hero`** :
  * **`title_prefix`** & **`title_suffix`** : Mots composant le titre de la bannière.
  * **`subtitle`** : Texte de description sous le titre principal.
  * **`tags`** : Badges d'information avec leurs icônes FontAwesome (`icon`) et leur libellé (`label`).
* **`quick_links`** :
  * **`dev_name` & `dev_url`** : Nom et lien vers le profil du développeur.
  * **`repo_url`** : Lien vers le dépôt GitHub du projet.
  * **Champs sociaux & Contact** (`email`, `twitter_url`, `discord_url`, etc.) : Si l'URL est renseignée, le bouton apparaît dans le menu. Si la valeur est vide (`""`), le bouton reste masqué.
* **`store_data_path`** : Chemin d'accès au fichier JSON du catalogue (`json/evox-store.json`).
* **`footer.text`** : Texte du bas de page, complété par la date de dernière mise à jour.

---

## 🚀 Fonctionnalités

* 🔍 **Recherche & Filtrage** : Recherche textuelle instantanée et filtres par catégories et sous-catégories.
* 🛡️ **Contrôle d'intégrité** : Copie rapide de l'empreinte **SHA-256** pour chaque asset.
* 🌐 **Support multi-forges** : Prise en charge des liens vers GitHub, GitLab, Forgejo, Gitea et pages HTML5.
* ⚙️ **Configuration modulaire** : Interface personnalisable directement depuis un fichier `config.json`.

---

## 🛠️ Installation & Configuration

1. Dupliquez le fichier d'exemple pour créer votre configuration :
   ```bash
   cp config.json.sample config.json
   ```
2. Renseignez vos liens, réseaux sociaux et préférences visuelles dans `config.json`.
3. Ajoutez ou mettez à jour la liste de vos logiciels dans `json/evox-store.json`.

---

## 📊 Catalogue des Applications

<!-- START_APP_LIST -->
| Catégorie | Sous-catégorie | Application | Version |
| :--- | :--- | :--- | :--- |
| forgejo_test | forgejo_test | elf-arsenal | v1.6.22 |
| Switch-Emu | Switch-Emu | Citron-neo_windows-nightly | nightly-windows |
| Switch-Emu | Switch-Emu | Citron-neo_android-nightly | nightly-android |
| Switch-Emu | Switch-Emu | Ryujinx-Nextendo | v1.7.9 |
| Switch-Emu | Switch-Emu | Ryubing | v1.0 |
| Switch-Emu | Switch-Emu | Kenji-NX | v1.0 |
| Switch-Emu | Switch-Emu | eden-stable | v0.2.1 |
| Switch-Emu | Switch-Emu | eden-nightly | v1788380429.1dcc574591 |
| github_test | github_test | flycast | v2.7 |
| github_test | github_test | flycast-dojo | dojo-6.46 |
| github_test | github_test | duckstation | latest |
| html_test | html_test | retroarch_windows_nightly | v1.0 |
| gitlab_test | gitlab_test | emulationstation-de | v3.4.1 |

<!-- END_APP_LIST -->

---

## 👤 Auteur

* **Développé par** : [nexgen999](https://github.com/nexgen999)
* **Dépôt officiel** : [EvoX-Universal.Store](https://github.com/nexgen999/EvoX-Universal.Store)
