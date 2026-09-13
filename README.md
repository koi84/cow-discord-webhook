# Alertes CoW vers Discord

Ce projet consulte la page publique **Games List** de CoW Stats toutes les cinq
minutes et envoie un embed via un webhook Discord lorsqu’une nouvelle partie
correspond aux filtres.

## Filtres déjà configurés

- Clash of Nations `[x24]`
- World at War `[x1]`
- World at War `[x4]`
- Serveurs français (`FR`), anglais (`EN`), allemands (`DE`) et italiens (`IT`)
- Seulement les parties ayant au moins une place libre

## Installation sur GitHub

1. Crée un nouveau dépôt GitHub, puis ajoute tout le contenu de ce dossier à la
   racine du dépôt (y compris le dossier `.github`).
2. Dans Discord, ouvre **Paramètres du salon → Intégrations → Webhooks**, crée un
   webhook et copie son URL. Ne la publie jamais dans le dépôt.
3. Sur GitHub, ouvre **Settings → Secrets and variables → Actions → New repository
   secret**.
4. Nomme le secret `DISCORD_WEBHOOK_URL` et colle l’URL du webhook comme valeur.
5. Ouvre l’onglet **Actions**, sélectionne **Surveillance des parties CoW**, puis
   clique sur **Run workflow** pour le premier lancement.

Le premier lancement mémorise les parties déjà présentes sans les publier. Les
prochaines nouvelles parties déclencheront une alerte. Pour envoyer également
les parties présentes au premier lancement, passe
`send_existing_on_first_run` à `true` dans `config.json` avant de démarrer.

## Modifier les filtres

Édite simplement `config.json`. Les noms de scénarios doivent correspondre à
ceux affichés sur CoW Stats.

## Points importants

- Le fichier `data/seen_games.json` est mis à jour automatiquement par GitHub
  Actions afin d’éviter les doublons.
- Dans **Settings → Actions → General → Workflow permissions**, choisis
  **Read and write permissions** si GitHub refuse la sauvegarde de ce fichier.
- Les exécutions planifiées de GitHub Actions peuvent parfois démarrer avec
  quelques minutes de retard.
- Ce projet dépend de la structure HTML d’un site tiers. Si celle-ci change, le
  workflow échouera clairement au lieu d’envoyer des données erronées.

Source surveillée : <https://kr-cowstats.com/games_list>
