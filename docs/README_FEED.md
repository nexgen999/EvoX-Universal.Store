<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <title>Guide de Gestion des Flux OPML - EvoX Universal Store</title>
</head>
<body>

    <h1>📡 Guide de Gestion des Flux OPML (EvoX Universal Store)</h1>
    <p>Ce document explique l'architecture, la structure et la gestion des flux (feeds) de dépôts et de fichiers au sein du projet <strong>EvoX Universal Store</strong>.</p>

    <hr>

    <h2>📂 Architecture des Dossiers (<code>feed/</code>)</h2>
    <p>Les flux sont séparés en deux catégories distinctes selon la provenance des éléments : <strong>interne</strong> (géré par le dépôt) ou <strong>externe</strong> (sources tierces).</p>

    <pre><code>EvoX-Universal.Store/
└── feed/
    ├── external/
    │   └── payloads/
    │       └── demo.opml        &lt;-- Flux de sources/dépôts externes
    └── internal/
        └── payloads/            &lt;-- Flux de fichiers hébergés en interne</code></pre>

    <h3>1. Flux Externes (<code>feed/external/</code>)</h3>
    <ul>
        <li><strong>Usage</strong> : Utilisé pour référencer des dépôts distants (GitHub, GitLab, Codeberg, etc.) ou des flux RSS/Atom de projets tiers.</li>
        <li><strong>Exemple d'utilisation</strong> : Suivre les nouvelles versions publiées sur des dépôts comme <code>itsPLK/ps5-unified-autoloader</code>.</li>
        <li><strong>Emplacement conseillé</strong> : <code>feed/external/payloads/</code></li>
    </ul>

    <h3>2. Flux Internes (<code>feed/internal/</code>)</h3>
    <ul>
        <li><strong>Usage</strong> : Utilisé pour référencer des fichiers, archives ou paquets hébergés directement sur ton propre serveur, ton dépôt ou ton infrastructure locale/NAS.</li>
        <li><strong>Exemple d'utilisation</strong> : Distribuer des paquets <code>.elf</code>, <code>.bin</code> ou des configurations personnalisées spécifiques au projet EvoX.</li>
        <li><strong>Emplacement conseillé</strong> : <code>feed/internal/payloads/</code></li>
    </ul>

    <hr>

    <h2>🛠️ Outil d'Édition GUI (<code>Tool/GUI/Opml_Builder/</code>)</h2>
    <p>Pour éviter d'éditer manuellement la syntaxe XML/OPML, une interface graphique en Python est disponible dans le dépôt :</p>
    <ul>
        <li><strong>Emplacement du script</strong> : <code>Tool/GUI/Opml_Builder/opml_builder.py</code></li>
        <li><strong>Fichier de démo</strong> : <code>Tool/GUI/Opml_Builder/demo.opml</code></li>
    </ul>

    <h3>Fonnalités de l'éditeur :</h3>
    <ol>
        <li><strong>Auto-complétion intelligente</strong> : En collant une URL de dépôt (ex: <code>https://github.com/itsPLK/ps5-unified-autoloader</code>), l'outil extrait automatiquement l'<strong>Auteur</strong> (<code>itsPLK</code>) et le <strong>Nom du projet</strong> (<code>ps5-unified-autoloader</code>).</li>
        <li><strong>Support du clic droit</strong> : Menu contextuel activé pour coller rapidement tes URLs.</li>
        <li><strong>Thème sombre optimisé</strong> : Lisibilité maximale des champs et du tableau.</li>
    </ol>

    <hr>

    <h2>📝 Format et Structure d'une Entrée OPML</h2>
    <p>Chaque fichier de flux <code>.opml</code> généré par l'outil respecte la structure standard ci-dessous :</p>

    <pre><code>&lt;?xml version="1.0" encoding="UTF-8"?&gt;
&lt;opml version="2.0"&gt;
  &lt;head&gt;
    &lt;title&gt;demo&lt;/title&gt;
  &lt;/head&gt;
  &lt;body&gt;
    &lt;outline 
      text="ps5-unified-autoloader" 
      title="ps5-unified-autoloader" 
      type="rss" 
      xmlUrl="https://github.com/itsPLK/ps5-unified-autoloader" 
      author="itsPLK" 
      description="Autoloader PS5 unifié" 
      htmlUrl="https://github.com/itsPLK/ps5-unified-autoloader" /&gt;
  &lt;/body&gt;
&lt;/opml&gt;</code></pre>

    <h3>Description des Attributs :</h3>
    <table border="1" cellpadding="5" cellspacing="0">
        <thead>
            <tr>
                <th>Attribut</th>
                <th>Obligatoire</th>
                <th>Description</th>
            </tr>
        </thead>
        <tbody>
            <tr>
                <td><strong><code>&lt;title&gt;</code></strong></td>
                <td><strong>Oui</strong></td>
                <td>Détermine le nom du fichier généré (ex: <code>&lt;title&gt;demo&lt;/title&gt;</code> enregistre sous <code>demo.opml</code>).</td>
            </tr>
            <tr>
                <td><strong><code>text</code> / <code>title</code></strong></td>
                <td><strong>Oui</strong></td>
                <td>Nom de l'application ou du dépôt.</td>
            </tr>
            <tr>
                <td><strong><code>type</code></strong></td>
                <td><strong>Oui</strong></td>
                <td>Type de source (<code>rss</code>, <code>atom</code>, ou <code>file</code> pour un lien direct vers un fichier).</td>
            </tr>
            <tr>
                <td><strong><code>xmlUrl</code></strong></td>
                <td><strong>Oui</strong></td>
                <td>URL du flux RSS/Atom ou lien direct vers le dépôt/fichier.</td>
            </tr>
            <tr>
                <td><strong><code>author</code></strong></td>
                <td>Non</td>
                <td>Nom du créateur ou propriétaire du dépôt.</td>
            </tr>
            <tr>
                <td><strong><code>description</code></strong></td>
                <td>Non</td>
                <td>Brève description de ce que contient le flux.</td>
            </tr>
            <tr>
                <td><strong><code>htmlUrl</code></strong></td>
                <td>Non</td>
                <td>Page web source / site officiel du projet.</td>
            </tr>
        </tbody>
    </table>

    <hr>

    <h2>🔄 Workflow de Mise à Jour d'un Flux</h2>
    <ol>
        <li>Lance le script :<br><code>python Tool/GUI/Opml_Builder/opml_builder.py</code></li>
        <li>Ouvre un fichier existant ou configure le nom du flux dans <strong>Titre de l'OPML (<code>&lt;title&gt;</code>)</strong>.</li>
        <li>Renseigne l'URL dans <strong><code>URL Flux / Fichier (xmlUrl)</code></strong>.</li>
        <li>L'auteur et le nom se pré-remplissent automatiquement s'il s'agit d'un dépôt distant.</li>
        <li>Clique sur <strong><code>➕ Ajouter l'élément</code></strong>.</li>
        <li>Enregistre le fichier dans le dossier approprié (<code>feed/external/payloads/</code> ou <code>feed/internal/payloads/</code>).</li>
    </ol>

</body>
</html>
