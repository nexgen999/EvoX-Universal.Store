# 📡 Guide de Gestion des Flux OPML (EvoX Universal Store)

Ce document explique l'architecture, la structure et la gestion des flux (feeds) de dépôts et de fichiers au sein du projet **EvoX Universal Store**.

---

## 📂 Architecture des Dossiers (`feed/`)

Les flux sont séparés en deux catégories distinctes selon la provenance des éléments : **interne** (géré par le dépôt) ou **externe** (sources tierces).

EvoX-Universal.Store/
└── feed/
    ├── external/
    │   └── payloads/
    │       └── demo.opml        <-- Flux de sources/dépôts externes
    └── internal/
        └── payloads/            <-- Flux de fichiers hébergés en interne

### 1. Flux Externes (`feed/external/`)
* **Usage** : Utilisé pour référencer des dépôts distants (GitHub, GitLab, Codeberg, etc.) ou des flux RSS/Atom de projets tiers.
* **Exemple d'utilisation** : Suivre les nouvelles versions publiées sur des dépôts comme `itsPLK/ps5-unified-autoloader`.
* **Emplacement conseillé** : `feed/external/payloads/`

### 2. Flux Internes (`feed/internal/`)
* **Usage** : Utilisé pour référencer des fichiers, archives ou paquets hébergés directement sur ton propre serveur, ton dépôt ou ton infrastructure locale/NAS.
* **Exemple d'utilisation** : Distribuer des paquets `.elf`, `.bin` ou des configurations personnalisées spécifiques au projet EvoX.
* **Emplacement conseillé** : `feed/internal/payloads/`

---

## 🛠️ Outil d'Édition GUI (`Tool/GUI/Opml_Builder/`)

Pour éviter d'éditer manuellement la syntaxe XML/OPML, une interface graphique en Python est disponible dans le dépôt :

* **Emplacement du script** : `Tool/GUI/Opml_Builder/opml_builder.py`
* **Fichier de démo** : `Tool/GUI/Opml_Builder/demo.opml`

### Fonctionnalités de l'éditeur :
1. **Auto-complétion intelligente** : En collant une URL de dépôt (ex: `https://github.com/itsPLK/ps5-unified-autoloader`), l'outil extrait automatiquement l'**Auteur** (`itsPLK`) et le **Nom du projet** (`ps5-unified-autoloader`).
2. **Support du clic droit** : Menu contextuel activé pour coller rapidement tes URLs.
3. **Thème sombre optimisé** : Lisibilité maximale des champs et du tableau.

---

## 📝 Format et Structure d'une Entrée OPML

Chaque fichier de flux `.opml` généré par l'outil respecte la structure standard ci-dessous :

<?xml version="1.0" encoding="UTF-8"?>
<opml version="2.0">
  <head>
    <title>demo</title>
  </head>
  <body>
    <outline 
      text="ps5-unified-autoloader" 
      title="ps5-unified-autoloader" 
      type="rss" 
      xmlUrl="https://github.com/itsPLK/ps5-unified-autoloader" 
      author="itsPLK" 
      description="Autoloader PS5 unifié" 
      htmlUrl="https://github.com/itsPLK/ps5-unified-autoloader" />
  </body>
</opml>

### Description des Attributs :

| Attribut | Obligatoire | Description |
| :--- | :---: | :--- |
| **`<title>`** | **Oui** | Détermine le nom du fichier généré (ex: `<title>demo</title>` enregistre sous `demo.opml`). |
| **`text` / `title`** | **Oui** | Nom de l'application ou du dépôt. |
| **`type`** | **Oui** | Type de source (`rss`, `atom`, ou `file` pour un lien direct vers un fichier). |
| **`xmlUrl`** | **Oui** | URL du flux RSS/Atom ou lien direct vers le dépôt/fichier. |
| **`author`** | Non | Nom du créateur ou propriétaire du dépôt. |
| **`description`** | Non | Brève description de ce que contient le flux. |
| **`htmlUrl`** | Non | Page web source / site officiel du projet. |

---

## 🔄 Workflow de Mise à Jour d'un Flux

1. Lance le script : `python Tool/GUI/Opml_Builder/opml_builder.py`
2. Ouvre un fichier existant ou configure le nom du flux dans **Titre de l'OPML (`<title>`)**.
3. Renseigne l'URL dans **`URL Flux / Fichier (xmlUrl)`**.
4. L'auteur et le nom se pré-remplissent automatiquement s'il s'agit d'un dépôt distant.
5. Clique sur **`➕ Ajouter l'élément`**.
6. Enregistre le fichier dans le dossier approprié (`feed/external/payloads/` ou `feed/internal/payloads/`).
