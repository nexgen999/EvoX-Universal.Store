<pre><code># 📡 Guide des Flux OPML et Génération JSON (EvoX Universal Store)

Ce document détaille le fonctionnement, l'architecture et les règles de génération des fichiers JSON à partir des flux OPML du projet **EvoX Universal Store**.

---

## 📂 Architecture Générale

La structure distingue strictly les flux **internes** (hébergés et compilés pour PLDMGR) des flux **externes** (destinés à l'interface web).

EvoX-Universal.Store/
├── feed/
│   ├── internal/
│   │   └── payloads/        &lt;-- Fichiers .opml internes
│   └── external/
│       └── payloads/        &lt;-- Fichiers .opml externes
├── files/
│   └── payloads/
│       └── internal/
│           ├── latest/      &lt;-- Stockage des dernières versions des binaires
│           │   └── [categorie]/
│           │       └── [appname]/
│           │           └── [version_build]/
│           │               └── file.elf
│           └── old/         &lt;-- Archivage des anciennes versions déplacées
│               └── [categorie]/
│                   └── [appname]/
│                       └── [version_build]/
│                           └── file.elf
└── json/
    ├── internal/
    │   ├── payloads.json     &lt;-- Fichier AIO compilé pour PLDMGR
    │   └── [catégorie].json  &lt;-- JSON individuel par catégorie
    └── external/
        └── [catégorie].json  &lt;-- JSON individuel pour l'interface web

---

## 🔄 Workflow de Traitement

### 1. Flux Internes (`feed/internal/`)
1. **Téléchargement & Gestion des Versions** :
   - Les binaires (`.elf`, `.bin`, etc.) référencés dans les fichiers OPML internes sont téléchargés.
   - La version actuelle est stockée dans : `files/payloads/internal/latest/[categorie]/[appname]/[version_build]/`
   - Si une nouvelle version de l'application est détectée, l'ancienne version présente dans `latest/` est automatiquement déplacée vers le dossier d'archivage : `files/payloads/internal/old/[categorie]/[appname]/[version_build]/`
2. **Calcul de Hash** : Le checksum SHA-256 de chaque fichier présent dans `latest/` est calculé.
3. **Génération par Catégorie** : Un fichier JSON individuel est généré pour chaque fichier OPML (ex: `json/internal/PS5_Activation.json`).
4. **Agrégation AIO** : Tous les objets du tableau `payloads` de chaque catégorie sont compilés dans le fichier unique `json/internal/payloads.json`.

### 2. Flux Externes (`feed/external/`)
1. **Téléchargement direct** : Aucun stockage local dans `files/`. L'exécution et le téléchargement se font à la volée depuis le web.
2. **Génération de Catégorie** : Un fichier JSON par OPML est généré dans `json/external/`.
3. **Pas d'agrégateur** : Aucun fichier `payloads.json` n'est créé en externe. L'interface web lit directement les fichiers JSON de catégorie.

---

## 📝 Format Standard des Fichiers JSON

Tous les fichiers JSON générés (internes comme externes) doivent respecter la structure stricte attendue par PLDMGR.

### Structure d'un JSON de Catégorie (Ex: `json/internal/PS5_Activation.json`)

{
  "name": "PS5 Activation",
  "payloads": [
    {
      "name": "np-fake-signin",
      "filename": "np-fake-signin_v1.3.elf",
      "url": "[https://nexgen999.github.io/EvoX-Universal.Store/files/payloads/internal/latest/PS5_Activation/np-fake-signin/v1.3/np-fake-signin_v1.3.elf](https://nexgen999.github.io/EvoX-Universal.Store/files/payloads/internal/latest/PS5_Activation/np-fake-signin/v1.3/np-fake-signin_v1.3.elf)",
      "description": "Fake activate PS5 without PSN.",
      "version": "v1.3",
      "category": "PS5 Activation",
      "checksum": "2ace1bb0be6d57f91cb24e4d3a221dec2d6d6114ace0a6b5748c6c0dcdb3b9c6"
    }
  ]
}

### Structure du Fichier Unique Compilé (`json/internal/payloads.json`)

Le champ `name` prend la valeur fixe `"AIO Store"` et réunit l'ensemble des éléments internes :

{
  "name": "AIO Store",
  "payloads": [
    {
      "name": "PS5-Custom-Tool-Manager-",
      "filename": "PS5-Custom-Tool-Manager-_vCustom.elf",
      "url": "[https://nexgen999.github.io/EvoX-Universal.Store/files/payloads/internal/latest/PS5_Themes-Avatars/PS5-Custom-Tool-Manager-/Custom/PS5-Custom-Tool-Manager-_vCustom.elf](https://nexgen999.github.io/EvoX-Universal.Store/files/payloads/internal/latest/PS5_Themes-Avatars/PS5-Custom-Tool-Manager-/Custom/PS5-Custom-Tool-Manager-_vCustom.elf)",
      "description": "Custom manager tool for PS5 personalization.",
      "version": "Custom",
      "category": "PS5 Themes-Avatars",
      "checksum": "297824ceaf6ea53fde57550adf9b5c2fc44c63ef60e8196ab92d351d1615d9cb"
    },
    {
      "name": "np-fake-signin",
      "filename": "np-fake-signin_v1.3.elf",
      "url": "[https://nexgen999.github.io/EvoX-Universal.Store/files/payloads/internal/latest/PS5_Activation/np-fake-signin/v1.3/np-fake-signin_v1.3.elf](https://nexgen999.github.io/EvoX-Universal.Store/files/payloads/internal/latest/PS5_Activation/np-fake-signin/v1.3/np-fake-signin_v1.3.elf)",
      "description": "Fake activate PS5 without PSN.",
      "version": "v1.3",
      "category": "PS5 Activation",
      "checksum": "2ace1bb0be6d57f91cb24e4d3a221dec2d6d6114ace0a6b5748c6c0dcdb3b9c6"
    }
  ]
}

---

## 🔑 Description des Champs `payloads`

| Clé | Type | Description |
| :--- | :--- | :--- |
| **`name`** | String | Nom de l'application ou du binaire. |
| **`filename`** | String | Nom complet du fichier binaire (ex: `.elf`). |
| **`url`** | String | Lien direct de téléchargement du fichier
