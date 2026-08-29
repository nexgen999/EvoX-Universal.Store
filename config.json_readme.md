Documentation de config.json
Le fichier config.json permet de personnaliser l'interface web du Store sans toucher au code HTML ou JavaScript :

site_title : Titre affiché dans l'onglet du navigateur.

hero :

title_prefix & title_suffix : Mots composant le titre de la bannière.

subtitle : Texte de description sous le titre.

tags : Badges d'information avec leurs icônes FontAwesome (icon) et leur libellé (label).

quick_links :

dev_name & dev_url : Nom et lien du développeur.

repo_url : Lien vers le dépôt GitHub.

Champs sociaux/email (email, twitter_url, discord_url, etc.) : Si l'URL est renseignée, le bouton apparaît dans le menu. Si la valeur est vide (""), le bouton reste masqué.

store_data_path : Chemin d'accès au fichier JSON du catalogue (json/evox-store.json).

footer.text : Texte du bas de page, complété par la date de dernière mise à jour.
