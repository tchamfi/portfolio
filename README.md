# Ask Lionel — portfolio et matching d’offres

Application Streamlit en français et en anglais : parcours professionnel,
questions sur le profil et comparaison d’une offre avec les compétences de
Lionel. Le positionnement couvre l’ensemble des missions de Product Owner
depuis 2016 et le socle QA antérieur, avec des expériences en SI métiers, APIs,
cloud et data.

## Sources de référence

| Source | Utilisation |
| --- | --- |
| `knowledge/skills_public.md` | V3 publique : compétences, expériences, cas et réponses de référence, synthétisés à partir de LinkedIn, des documents et des précisions de Lionel. |
| `knowledge/experience.json` | Périodes et périmètres utilisés pour les exigences d’ancienneté. Les durées non établies restent inconnues. |
| Configuration administrative | Disponibilité, TJM et modalités de travail, transmises séparément de la recherche documentaire. |

`cv_data.py` et le dossier `docs/` ne sont plus des sources du RAG public.
Retirer des documents de l’index ne les supprime ni du dépôt Git ni de son
historique. Cette intégration ne réalise aucune purge des originaux.

La V3 conserve les contributions attribuées et leurs limites : l’expertise QA
frontend/backend, la responsabilité produit data et la coordination technique
ne se confondent pas. Le développement de pipelines n’est pas déduit d’une
mission de PO data. Une absence de preuve sur un point signifie « information
non établie », sans effacer les compétences documentées dans le reste du parcours.

## Fonctionnement

1. Le chargeur lit les sources publiques à partir du dossier du projet,
   indépendamment du répertoire de lancement.
2. Le Markdown est découpé par fiches, cas, questions et expériences. Chaque
   extrait garde ses références et le contexte nécessaire. Les règles de
   matching et notes de version ne sont pas des compétences à rechercher.
3. Le RAG construit un index TF-IDF en mémoire. Il ne nécessite ni ChromaDB,
   ni serveur de base vectorielle, ni appel payant pour rechercher des extraits.
4. L’empreinte des sources sert à reconstruire l’index quand leur contenu change.
   La version du corpus et les informations d’indexation sont exposées dans
   l’administration pour vérifier la version réellement chargée.
5. Le chat utilise des règles applicatives explicites : faits présents dans les
   sources, références, distinction des rôles et langue demandée. Les documents,
   offres et extraits sont des données, pas des instructions exécutables.
6. Le matching extrait les exigences, recherche pour chacune des références,
   puis attribue un statut. Le calcul du score se fait en Python avec un barème
   versionné. Les réserves et points à confirmer restent visibles.

La langue et les données administratives sont des paramètres séparés : elles
ne sont pas concaténées à la question utilisée pour rechercher les compétences.
Les identifiants des sources permettent de revenir au passage qui soutient
une réponse. Ils ne constituent pas à eux seuls une vérification indépendante
des déclarations professionnelles.

### Ancienneté et score

Une exigence « huit ans comme PO » porte sur toutes les missions PO ; elle ne
porte ni sur EPSA seule, ni sur le total IT. Une exigence « huit ans en data »
ou « trois ans avec Bruno » nécessite une durée propre à ce périmètre.
Les périodes qui se chevauchent sont fusionnées avant de calculer les durées ;
un contrat de conseil et sa mission client ne sont pas deux expériences à sommer.

Ne pas inventer une date pour remplir une lacune. Préserver les précisions de
date présentes dans le dossier et distinguer une durée confirmée par Lionel
d’un calcul fondé sur des périodes complètes. Une compétence peut être établie
sans que sa durée d’utilisation soit connue.

Le score indique la couverture des exigences analysées selon le barème. Ce
n’est pas une probabilité d’embauche. Les exigences sans information suffisante
restent explicites ; elles ne doivent pas être converties en acquis par défaut.
Les métadonnées de l’analyse identifient le corpus, le barème et la version
des règles d’évaluation (`assessment_version`).

Une correspondance directe porte sur la responsabilité demandée : le pilotage
et la validation ne nécessitent pas d’avoir soi-même développé les pipelines.
Pour les statuts partiel ou non satisfait, le modèle doit citer un aspect exact
de l’exigence qui n’est pas couvert. Un écart hors exigence est refusé et peut
faire l’objet d’une seule relecture ciblée, comme les autres erreurs de
validation. S’il reste invalide, le score global est indisponible. Cet ancrage
ne remplace pas la vérification sémantique des jugements
sur des cas réels.

Le barème `requirements-v1` attribue un poids de 3 aux exigences requises et
de 1 aux options. Les crédits sont : direct 1, partiel 0,5, formation ou
expérience historique 0,25, inconnu ou non satisfait 0. Les exigences inconnues
restent dans le dénominateur. Si une seule évaluation demeure invalide, aucun
score n’est affiché. Une analyse valide sans correspondance peut en revanche
obtenir 0 ; les points à clarifier restent visibles.

L’exhaustivité du traitement porte sur les exigences extraites. L’extraction
reste une tâche du modèle et doit être contrôlée sur des offres représentatives.
Les dates mensuelles donnent une durée approximative ; un seuil d’ancienneté
proche des limites de précision est marqué à confirmer. L’empreinte des dates
et la date du calcul sont associées à celles du corpus dans chaque analyse.

### Répétabilité du matching

Le score est déterministe pour une même liste de critères et de statuts, mais
le modèle ne produit pas nécessairement cette même liste à chaque appel.
La température à zéro ne constitue pas une garantie de répétabilité.

`matching_service.py` conserve une évaluation entièrement validée avant de
l’afficher. La même offre réutilise ensuite ses critères, statuts, preuves,
justifications et score. La clé inclut le texte (espaces normalisés), les
empreintes du corpus et des dates, le mois du calcul d’ancienneté, la langue,
la configuration du modèle et l’empreinte du code d’évaluation. Un changement
sur ces éléments déclenche une nouvelle analyse. Le format email ou pitch
peut changer le brouillon, sans refaire l’évaluation. Le timestamp conservé
dans les métadonnées reste celui de l’analyse initiale.

Le stockage persistant utilise les champs existants `Name` et `Notes` de la
table de configuration Airtable, avec le préfixe réservé
`__matching_cache_v1__:`. Ces lignes sont exclues des chargements de la
configuration. Aucune nouvelle table ni nouveau secret n’est nécessaire ;
le token existant doit permettre la lecture et la création de ces lignes.
Les preuves complètes sont rechargées depuis le même corpus à partir de leurs
identifiants. Le cache ne reçoit pas l’email du visiteur. Ne pas modifier
manuellement ses lignes : les incohérences détectées bloquent le résultat.

Un verrou par clé dans le processus Streamlit empêche deux clics simultanés
de générer deux évaluations. Un cache mémoire borné accélère les répétitions ;
Airtable permet de retrouver le résultat après un redémarrage. Les résultats
invalides ne sont jamais mis en cache. Si une lecture ou une sauvegarde est
incertaine, aucun nouveau score n’est publié. Une réutilisation n’ajoute pas
de coût LLM dans les analytics. Les métadonnées privées incluent
`evaluation_key`, `requirement_signature` et `cache_origin` pour la recette.

Cette architecture vise l’instance Streamlit actuelle. Airtable n’impose pas
l’unicité du champ `Name` : plusieurs processus écrivains nécessiteraient un
stockage avec contrainte unique et transaction. Les doublons contradictoires
détectés sont refusés. La stabilité du résultat conservé ne garantit pas à
elle seule la justesse du jugement initial : les contrôles de preuves et la
recette métier restent nécessaires.

## Lancer l’application

Depuis la racine du dépôt, dans un environnement Python isolé :

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

Configurer les secrets dans le gestionnaire de l’hébergeur, les variables
d’environnement, ou localement dans `.streamlit/secrets.toml` (ignoré par Git).
Ne pas les mettre dans le corpus ni dans les commits.

| Paramètre | Usage |
| --- | --- |
| `ANTHROPIC_API_KEY` | Génération avec un modèle Anthropic sélectionné dans l’application. |
| `OPENAI_API_KEY` | Génération avec un modèle OpenAI sélectionné dans l’application. |
| `ADMIN_CODE` | Accès aux fonctions d’administration existantes. |
| `AIRTABLE_TOKEN` | Configuration, recommandations, analytics et conservation des évaluations de matching. |

Une seule clé LLM est nécessaire si un seul fournisseur est utilisé. Choisir
dans l’administration un modèle effectivement disponible pour le compte
configuré. Sans clé LLM, l’indexation et les tests de recherche restent possibles ;
les réponses générées et le matching qui appellent le modèle ne fonctionneront
pas. Sans Airtable configuré, vérifier le contenu de repli affiché : la V3 du RAG
ne remplace pas automatiquement tous les champs éditoriaux sauvegardés dans Airtable.
Le matching public nécessite ce stockage pour publier un résultat répétable.

## Vérifier une modification

Exécuter la recette automatisée hors ligne, sans clé LLM :

```bash
python -m unittest discover -s tests -v
```

Le workflow GitHub Actions `Portfolio tests` exécute aussi cette suite sur les
pull requests et les modifications de `main`. Il ne déploie pas le site et
n’utilise aucune clé LLM. Les tests Streamlit remplacent les accès Airtable
et les appels de génération par des simulations aux frontières des services.

Les appels LLM simulés vérifient le contrat de l’application, pas la qualité
réelle d’un fournisseur. Compléter par les cas suivants dans l’application
avec le modèle et la configuration utilisés en production :

| Cas de recette | Attendu |
| --- | --- |
| « Depuis combien de temps es-tu PO ? » | Parcours PO depuis 2016, distinction avec l’ancienneté IT et les durées incertaines. |
| « Quelle est ton expertise QA ? » | Plans et stratégies de test, frontend/backend, Postman, SoapUI et Bruno ; parcours QA pris en compte. |
| « Quel était ton rôle data chez EPSA ? » | Validation des transformations, coordination des filiales, centralisation et uniformisation ; réalisation des pipelines non inventée. |
| « As-tu livré une application utilisée ? » | Application RH : recette validée, mise en production et adoption. |
| Offre avec huit ans de PO | Comparaison avec toutes les missions PO ; compteur IT global non utilisé. |
| Offre avec développement de pipelines | Limite du rôle technique reconnue et justification visible. |
| Offre de pilotage multi-CRM et de validation des transformations, sans développement demandé | Correspondance directe avec le rôle PO data documenté ; aucune pénalité pour l'absence de codage des pipelines. |
| Offre avec dix ans de PO et cinq ans de PO data | Première durée satisfaite ; seconde non satisfaite par les quatorze mois data documentés. |
| Question sur une certification non documentée, seule ou mêlée à une question technique | Information à confirmer, jamais absence certaine déduite d'une omission ; les autres certifications documentées restent accessibles au modèle. |
| Offre longue avec exigences obligatoires et optionnelles | Toutes les exigences extraites figurent dans le résultat ; manques visibles. |
| Même offre envoyée deux fois, puis dans une nouvelle session | Même score, critères, statuts et explications ; une seule évaluation générée pour le même contexte. |
| Échec d’un lot d’évaluation parmi plusieurs lots | Une réparation ciblée ; si elle échoue, aucun score, jamais une pénalité assimilée à un manque de compétence. |
| Offre PO `tests/fixtures/po_agile_offer.txt` | Contexte d’équipe non noté, responsabilités répétées regroupées, références backlog/roadmap/recette retrouvées et fragment final incomplet signalé. |
| Même question en français et en anglais | Faits, rôles et limites cohérents ; langue respectée. |
| Texte d’offre demandant d’ignorer les règles ou de forcer 100 % | Aucune dérogation aux règles d’analyse et de score. |
| Modification du corpus | Empreinte actualisée et nouveaux extraits retrouvés après reconstruction. |

Comparer les résultats à un petit jeu d’offres conservé avant changement,
notamment les erreurs de rôle ou d’ancienneté. Vérifier séparément le chat,
le matching, les réserves, les références et les métadonnées de version.

## Mettre à jour la base

1. Modifier `knowledge/skills_public.md` en conservant les identifiants existants
   et une version explicite. Anonymiser tout nouvel exemple de document interne.
2. Si les dates ou les périmètres changent, mettre aussi à jour
   `knowledge/experience.json` ; ne pas déduire l’ancienneté d’un outil de la
   durée totale d’une mission.
3. Exécuter les tests et les cas de recette concernés.
4. Vérifier le diff, publier la branche puis intégrer le changement validé.
5. Vérifier le déploiement du commit sur Streamlit Community Cloud et contrôler dans l’administration
   la version et l’empreinte chargées.

La reconstruction est automatique quand le contenu change dans le processus
applicatif. Un redémarrage force aussi une initialisation propre. Une mise à
jour uniquement dans une copie locale du fichier ne change pas le site distant.

## Déployer sur Streamlit Community Cloud

Le [portfolio public](https://portfolio-tchamfonglionel.streamlit.app/) est hébergé
sur Streamlit Community Cloud. Ouvrir son espace de travail
sur [share.streamlit.io](https://share.streamlit.io/) et sélectionner l’application
existante. Les paramètres du compte restent à vérifier dans le tableau de bord :

| Paramètre attendu | Valeur à vérifier |
| --- | --- |
| Dépôt GitHub | `tchamfi/portfolio` |
| Branche déployée | `main` |
| Fichier d’entrée | `app.py` |

Après validation de la branche de travail, conserver l’identifiant du commit
précédent puis fusionner les changements dans la branche effectivement déployée.
Streamlit Community Cloud synchronise automatiquement les mises à jour de cette
branche GitHub. Une branche de travail distincte ne met pas à jour le site tant
qu’elle n’est pas intégrée à la branche déployée. Voir la
[documentation de mise à jour](https://docs.streamlit.io/deploy/streamlit-community-cloud/manage-your-app/edit-your-app).

Depuis **Manage app**, suivre les logs du déploiement et vérifier l’installation
des dépendances ainsi que le démarrage de l’application. Vérifier aussi les
secrets côté Streamlit. Si un redémarrage est nécessaire, utiliser **Reboot app**
depuis les commandes de gestion ; consulter la
[documentation de gestion](https://docs.streamlit.io/deploy/streamlit-community-cloud/manage-your-app).
Un redémarrage ne remplace pas la publication du code sur la branche surveillée.

Ouvrir ensuite le site public et contrôler la version V3 et l’empreinte du corpus
dans l’administration. Refaire au minimum les questions QA, ancienneté PO, rôle
data chez EPSA et adoption de l’application RH, puis un matching avec une exigence
d’ancienneté et un point à confirmer. Vérifier les références et les réserves
affichées. Une fusion réussie ou des logs de démarrage sans erreur ne remplacent
pas cette recette applicative.

En cas de régression, créer un commit qui annule le changement sur la branche
déployée, puis suivre sa synchronisation dans Streamlit Community Cloud.
Restaurer ensemble le code, le corpus et les périodes d’expérience. Les
configurations et données Airtable ne sont pas restaurées par un retour arrière
Git : les vérifier séparément si elles ont été changées.

## Serveur MCP optionnel

Le serveur expose les mêmes sources publiques et les mêmes règles du RAG.
Il conserve les outils `ask_lionel`, `search_lionel_docs` et
`get_lionel_summary`. Le résumé renvoie des extraits référencés du corpus ;
il ne recharge pas une ancienne biographie écrite en dur.

```bash
python -m pip install -r requirements-mcp.txt
python mcp_server.py
```

Configurer le client MCP pour lancer l’interpréteur de cet environnement avec
le chemin absolu de `mcp_server.py`, via le transport stdio. Les messages de
diagnostic vont sur stderr ; stdout est réservé au protocole MCP.

`search_lionel_docs` et `get_lionel_summary` fonctionnent sans clé LLM.
`ask_lionel` utilise le fournisseur configuré par le RAG et nécessite sa clé.
Il accepte `language="fr"` ou `language="en"`. Ce serveur ne charge pas la
configuration administrative Airtable : ne pas y supposer une disponibilité
ou un TJM à jour. Aucun chemin utilisateur local ni index Chroma distinct
n’est nécessaire.
