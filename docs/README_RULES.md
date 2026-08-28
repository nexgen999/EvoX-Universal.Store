# 📖 Documentation Technique : Spécification de `config/rules.json`

## 📌 Présentation
Le fichier `config/rules.json` constitue le cœur de la configuration du moteur d'extraction (**Universal Store Engine**). Il permet de piloter et de filtrer automatiquement la récupération, l'extraction et le renommage d'assets provenant de dépôts distants (**GitHub** et **Forgejo/Gitea**).

Ce fichier est conçu pour être édité visuellement via l'interface Tkinter (`gui.py`) ou modifié manuellement.

---

## 🗂️ Structure Globale du Schéma

{
  "$schema": "Configuration universelle des règles de filtrage",
  "global_settings": {
    "user_agent": "UniversalStoreEngine/1.0",
    "http_timeout_seconds": 30
  },
  "repositories": [
    /* Liste des objets dépôts */
  ]
}

---

## 📐 Spécification des Champs

### 1. Racine (`root`)

| Champ | Type | Obligatoire | Description |
| :--- | :--- | :---: | :--- |
| `$schema` | `string` | non | Description contextuelle ou lien de validation du schéma. |
| `global_settings` | `object` | **oui** | Options globales d'exécution et de réseau. |
| `repositories` | `array` | **oui** | Liste des configurations de dépôts à examiner. |

---

### 2. Objet `global_settings`

| Champ | Type | Valeur par défaut | Description |
| :--- | :--- | :---: | :--- |
| `user_agent` | `string` | `"UniversalStoreEngine/1.0"` | En-tête HTTP `User-Agent` utilisé pour les requêtes API et les téléchargements. |
| `http_timeout_seconds` | `integer` | `30` | Délai maximal d'attente (en secondes) pour l'exécution d'une requête HTTP. |

---

### 3. Objet `repository` (Configuration d'un dépôt)

Chaque élément du tableau `repositories` définit les règles d'extraction d'un projet distant.

{
  "repo": "owner/repository",
  "enabled": true,
  "include_prerelease": true,
  "processing_mode": "multi_assets",
  "global_asset_filters": { ... },
  "assets_rules": [ ... ]
}

| Champ | Type | Obligatoire | Description |
| :--- | :--- | :---: | :--- |
| `repo` | `string` | **oui** | Identifiant ou URL du dépôt :<br>- GitHub : `owner/repo`<br>- Forgejo/Gitea : `domain.com/owner/repo` |
| `enabled` | `boolean` | **oui** | Active (`true`) ou désactive (`false`) le traitement de ce dépôt par le moteur. |
| `include_prerelease` | `boolean` | **oui** | Indique s'il faut analyser les releases marquées comme *Pre-release* (bêta/alpha). |
| `processing_mode` | `string` | **oui** | Mode d'analyse. Valeur recommandée : `"multi_assets"`. |
| `global_asset_filters` | `object` | **oui** | Regroupe les règles d'exclusion/inclusion globales au niveau du dépôt. |
| `assets_rules` | `array` | **oui** | Liste des règles spécifiques appliquées individuellement à chaque asset. |

---

### 4. Objet `global_asset_filters`

Permet d'appliquer un premier niveau de tri sur l'ensemble des fichiers disponibles dans une release.

"global_asset_filters": {
  "target_extensions": [".elf", ".zip"],
  "global_exclude_extensions": [".txt", ".pdf"],
  "global_include_keywords": ["release"],
  "global_exclude_keywords": ["debug", "test"]
}

| Champ | Type | Description |
| :--- | :--- | :--- |
| `target_extensions` | `array[string]` | Liste d'extensions autorisées. Si vide, toutes les extensions sont admises. |
| `global_exclude_extensions` | `array[string]` | Liste d'extensions systématiquement rejetées. |
| `global_include_keywords` | `array[string]` | Le nom du fichier ou de l'asset doit contenir au moins un de ces mots-clés. |
| `global_exclude_keywords` | `array[string]` | Tout fichier contenant l'un de ces mots-clés sera rejeté. |

---

### 5. Objet `assets_rules` (Règle individuelle par asset)

Définit le traitement final d'un fichier sélectionné (conservation, extraction ZIP, patron de nommage).

{
  "target_release_type": "Stable",
  "match_keyword": "payload.zip",
  "extract_archive": true,
  "target_extracted_file": "payload.elf",
  "clean_name_template": "payload_v{version}.elf",
  "enabled": true
}

| Champ | Type | Obligatoire | Description |
| :--- | :--- | :---: | :--- |
| `enabled` | `boolean` | **oui** | Active (`true`) ou ignore (`false`) cette règle précise. |
| `target_release_type` | `string` | **oui** | Type de release ciblée (`"Stable"` ou `"Pre-release"`). |
| `match_keyword` | `string` | **oui** | Nom exact de l'asset ou mot-clé permettant d'identifier le fichier distant. |
| `extract_archive` | `boolean` | **oui** | Définit s'il faut décompresser une archive `.zip` (`true`) ou traiter le fichier brut (`false`). |
| `target_extracted_file` | `string` | *conditionnel* | **Requis si `extract_archive` est `true`**. Chemin interne du fichier à extraire depuis le `.zip`. |
| `clean_name_template` | `string` | **oui** | Patron du nom de fichier final. Le marqueur `{version}` sera automatiquement remplacé par le tag de version de la release. |

---

## 💡 Exemple Complet de Validation

{
  "$schema": "Configuration universelle des règles de filtrage",
  "global_settings": {
    "user_agent": "UniversalStoreEngine/1.0",
    "http_timeout_seconds": 30
  },
  "repositories": [
    {
      "repo": "owner/example-repo",
      "enabled": true,
      "include_prerelease": true,
      "processing_mode": "multi_assets",
      "global_asset_filters": {
        "target_extensions": [".elf", ".zip"],
        "global_exclude_extensions": [".txt"],
        "global_include_keywords": [],
        "global_exclude_keywords": ["debug"]
      },
      "assets_rules": [
        {
          "target_release_type": "Stable",
          "match_keyword": "release_archive.zip",
          "extract_archive": true,
          "target_extracted_file": "binaries/app.elf",
          "clean_name_template": "app_v{version}.elf",
          "enabled": true
        },
        {
          "target_release_type": "Stable",
          "match_keyword": "standalone_tool.elf",
          "extract_archive": false,
          "clean_name_template": "tool_v{version}.elf",
          "enabled": true
        }
      ]
    }
  ]
}
