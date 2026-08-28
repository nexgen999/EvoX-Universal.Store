<h1>📖 Documentation Technique : Spécification de <code>config/rules.json</code></h1>

<h2>📌 Présentation</h2>
<p>Le fichier <code>config/rules.json</code> constitue le cœur de la configuration du moteur d'extraction (<strong>Universal Store Engine</strong>). Il permet de piloter et de filtrer automatiquement la récupération, l'extraction et le renommage d'assets provenant de dépôts distants (<strong>GitHub</strong> et <strong>Forgejo/Gitea</strong>).</p>
<p>Ce fichier est conçu pour être édité visuellement via l'interface Tkinter (<code>gui.py</code>) ou modifié manuellement.</p>

<hr>

<h2>🗂️ Structure Globale du Schéma</h2>
<pre><code>{
  "$schema": "Configuration universelle des règles de filtrage",
  "global_settings": {
    "user_agent": "UniversalStoreEngine/1.0",
    "http_timeout_seconds": 30
  },
  "repositories": [
    /* Liste des objets dépôts */
  ]
}</code></pre>

<hr>

<h2>📐 Spécification des Champs</h2>

<h3>1. Racine (<code>root</code>)</h3>
<table>
  <thead>
    <tr>
      <th>Champ</th>
      <th>Type</th>
      <th>Obligatoire</th>
      <th>Description</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td><code>$schema</code></td>
      <td><code>string</code></td>
      <td>non</td>
      <td>Description contextuelle ou lien de validation du schéma.</td>
    </tr>
    <tr>
      <td><code>global_settings</code></td>
      <td><code>object</code></td>
      <td><strong>oui</strong></td>
      <td>Options globales d'exécution et de réseau.</td>
    </tr>
    <tr>
      <td><code>repositories</code></td>
      <td><code>array</code></td>
      <td><strong>oui</strong></td>
      <td>Liste des configurations de dépôts à examiner.</td>
    </tr>
  </tbody>
</table>

<h3>2. Objet <code>global_settings</code></h3>
<table>
  <thead>
    <tr>
      <th>Champ</th>
      <th>Type</th>
      <th>Valeur par défaut</th>
      <th>Description</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td><code>user_agent</code></td>
      <td><code>string</code></td>
      <td><code>"UniversalStoreEngine/1.0"</code></td>
      <td>En-tête HTTP <code>User-Agent</code> utilisé pour les requêtes API et les téléchargements.</td>
    </tr>
    <tr>
      <td><code>http_timeout_seconds</code></td>
      <td><code>integer</code></td>
      <td><code>30</code></td>
      <td>Délai maximal d'attente (en secondes) pour l'exécution d'une requête HTTP.</td>
    </tr>
  </tbody>
</table>

<h3>3. Objet <code>repository</code> (Configuration d'un dépôt)</h3>
<p>Chaque élément du tableau <code>repositories</code> définit les règles d'extraction d'un projet distant.</p>
<pre><code>{
  "repo": "owner/repository",
  "enabled": true,
  "include_prerelease": true,
  "processing_mode": "multi_assets",
  "global_asset_filters": { ... },
  "assets_rules": [ ... ]
}</code></pre>

<table>
  <thead>
    <tr>
      <th>Champ</th>
      <th>Type</th>
      <th>Obligatoire</th>
      <th>Description</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td><code>repo</code></td>
      <td><code>string</code></td>
      <td><strong>oui</strong></td>
      <td>Identifiant ou URL du dépôt : GitHub (<code>owner/repo</code>) ou Forgejo/Gitea (<code>domain.com/owner/repo</code>).</td>
    </tr>
    <tr>
      <td><code>enabled</code></td>
      <td><code>boolean</code></td>
      <td><strong>oui</strong></td>
      <td>Active (<code>true</code>) ou désactive (<code>false</code>) le traitement de ce dépôt par le moteur.</td>
    </tr>
    <tr>
      <td><code>include_prerelease</code></td>
      <td><code>boolean</code></td>
      <td><strong>oui</strong></td>
      <td>Indique s'il faut analyser les releases marquées comme <em>Pre-release</em> (bêta/alpha).</td>
    </tr>
    <tr>
      <td><code>processing_mode</code></td>
      <td><code>string</code></td>
      <td><strong>oui</strong></td>
      <td>Mode d'analyse. Valeur recommandée : <code>"multi_assets"</code>.</td>
    </tr>
    <tr>
      <td><code>global_asset_filters</code></td>
      <td><code>object</code></td>
      <td><strong>oui</strong></td>
      <td>Regroupe les règles d'exclusion/inclusion globales au niveau du dépôt.</td>
    </tr>
    <tr>
      <td><code>assets_rules</code></td>
      <td><code>array</code></td>
      <td><strong>oui</strong></td>
      <td>Liste des règles spécifiques appliquées individuellement à chaque asset.</td>
    </tr>
  </tbody>
</table>

<h3>4. Objet <code>global_asset_filters</code></h3>
<p>Permet d'appliquer un premier niveau de tri sur l'ensemble des fichiers disponibles dans une release.</p>
<pre><code>"global_asset_filters": {
  "target_extensions": [".elf", ".zip"],
  "global_exclude_extensions": [".txt", ".pdf"],
  "global_include_keywords": ["release"],
  "global_exclude_keywords": ["debug", "test"]
}</code></pre>

<table>
  <thead>
    <tr>
      <th>Champ</th>
      <th>Type</th>
      <th>Description</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td><code>target_extensions</code></td>
      <td><code>array[string]</code></td>
      <td>Liste d'extensions autorisées. Si vide, toutes les extensions sont admises.</td>
    </tr>
    <tr>
      <td><code>global_exclude_extensions</code></td>
      <td><code>array[string]</code></td>
      <td>Liste d'extensions systématiquement rejetées.</td>
    </tr>
    <tr>
      <td><code>global_include_keywords</code></td>
      <td><code>array[string]</code></td>
      <td>Le nom du fichier ou de l'asset doit contenir au moins un de ces mots-clés.</td>
    </tr>
    <tr>
      <td><code>global_exclude_keywords</code></td>
      <td><code>array[string]</code></td>
      <td>Tout fichier contenant l'un de ces mots-clés sera rejeté.</td>
    </tr>
  </tbody>
</table>

<h3>5. Objet <code>assets_rules</code> (Règle individuelle par asset)</h3>
<p>Définit le traitement final d'un fichier sélectionné (conservation, extraction ZIP, patron de nommage).</p>
<pre><code>{
  "target_release_type": "Stable",
  "match_keyword": "payload.zip",
  "extract_archive": true,
  "target_extracted_file": "payload.elf",
  "clean_name_template": "payload_v{version}.elf",
  "enabled": true
}</code></pre>

<table>
  <thead>
    <tr>
      <th>Champ</th>
      <th>Type</th>
      <th>Obligatoire</th>
      <th>Description</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td><code>enabled</code></td>
      <td><code>boolean</code></td>
      <td><strong>oui</strong></td>
      <td>Active (<code>true</code>) ou ignore (<code>false</code>) cette règle précise.</td>
    </tr>
    <tr>
      <td><code>target_release_type</code></td>
      <td><code>string</code></td>
      <td><strong>oui</strong></td>
      <td>Type de release ciblée (<code>"Stable"</code> ou <code>"Pre-release"</code>).</td>
    </tr>
    <tr>
      <td><code>match_keyword</code></td>
      <td><code>string</code></td>
      <td><strong>oui</strong></td>
      <td>Nom exact de l'asset ou mot-clé permettant d'identifier le fichier distant.</td>
    </tr>
    <tr>
      <td><code>extract_archive</code></td>
      <td><code>boolean</code></td>
      <td><strong>oui</strong></td>
      <td>Définit s'il faut décompresser une archive <code>.zip</code> (<code>true</code>) ou traiter le fichier brut (<code>false</code>).</td>
    </tr>
    <tr>
      <td><code>target_extracted_file</code></td>
      <td><code>string</code></td>
      <td><em>conditionnel</em></td>
      <td>Requis si <code>extract_archive</code> est à <code>true</code>. Chemin interne du fichier à extraire depuis le <code>.zip</code>.</td>
    </tr>
    <tr>
      <td><code>clean_name_template</code></td>
      <td><code>string</code></td>
      <td><strong>oui</strong></td>
      <td>Patron du nom de fichier final. Le marqueur <code>{version}</code> sera automatiquement remplacé par le tag de version de la release.</td>
    </tr>
  </tbody>
</table>

<hr>

<h2>💡 Exemple Complet de Validation</h2>
<pre><code>{
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
}</code></pre>
