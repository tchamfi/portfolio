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
| Connaissances IA publiées | Fiches ajoutées par Lionel depuis l’administration : compétences, outils, langues, certifications et réalisations, avec entreprises, pratique et limites. |
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
3. Le RAG construit un index TF-IDF en mémoire, enrichi des fiches publiées.
   Pour le chat et un nouveau matching, une sélection sémantique par le modèle
   complète la recherche lexicale. Elle classe des identifiants existants ; la
   fusion des rangs conserve les blocs complets et les outils explicitement nommés.
   Cette étape utilise l’API IA existante et ajoute un coût et une latence au
   premier calcul. Aucun service d’embeddings ni base vectorielle n’est ajouté.
4. L’empreinte des sources sert à reconstruire l’index quand leur contenu change.
   La version du corpus et les informations d’indexation sont exposées dans
   l’administration pour vérifier la version réellement chargée.
5. Le chat utilise des règles applicatives explicites : faits présents dans les
   sources, références, distinction des rôles et langue demandée. Les documents,
   offres et extraits sont des données, pas des instructions exécutables.
6. Le matching extrait les exigences, recherche pour chacune des références,
   puis attribue un statut. Le calcul du score se fait en Python avec un barème
   versionné. Les jugements ambigus font l’objet d’une seconde lecture ciblée.
   Les réserves et points à confirmer restent visibles.

La sélection sémantique travaille par lots de huit critères, avec cinq blocs
complets par critère. Les identifiants inventés ou les lots incomplets sont
refusés. Une panne de cette étape empêche la publication d’un nouveau matching ;
le chat peut utiliser la recherche lexicale avec un diagnostic dans ses métriques.

Une offre contenant plusieurs critères passe aussi par un audit de redondance,
sans accès au profil ni à la note. Il peut retirer une répétition uniquement au
profit d’un critère original couvrant intégralement le même besoin. Les textes
conservés ne sont pas réécrits. Les identifiants, citations, poids, prérequis,
nombres et précisions de durée/langue sont contrôlés, ainsi que les noms explicites
d’outils et certifications. L’audit et les critères initiaux restent dans la trace
privée et sont revalidés lors de la lecture du cache. La couverture de sens reste
un jugement IA à contrôler par la recette ; aucun nombre de critères cible n’est imposé.

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

Après la validation structurelle, une seconde lecture examine les statuts
partiel, inconnu, non satisfait, formation et historique. Elle reçoit le besoin
et ses preuves, sans le premier verdict. Les contrôles d’ancienneté restent
déterministes. Un désaccord produit un statut inconnu, présenté « À vérifier » ;
un échec de revue laisse la note indisponible. L’accord entre deux lectures du
même modèle ne prouve pas la justesse : leurs erreurs peuvent être corrélées et
les correspondances directes ne sont pas relues systématiquement.

Les prérequis sont identifiés seulement sur une formulation explicite
d’obligation dans l’offre. Une négation ou une formulation contradictoire ne
devient pas un blocage automatique. Les prérequis non satisfaits ou à confirmer
apparaissent à proximité de la note, même élevée. Aucun plafond arbitraire
n’est ajouté : le barème ci-dessous reste inchangé.

Un statut « non satisfait » hors calcul d’ancienneté exige une déclaration
négative explicite dans une source citée, avec une citation exacte et le
périmètre correspondant. Une liste d’autres certifications ou l’absence de
preuve ne suffisent pas. Sans ce fondement, le code conserve une information
à préciser, même si deux lectures ont proposé le même écart.

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
Les candidats initialement sélectionnés et les deux jugements sont conservés
et contrôlés à la relecture ; un résultat réutilisé ne relance ni recherche
sémantique ni évaluation.

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

Le jeu `evaluations/matching_cases.json` ajoute 25 cas métier sourcés et l’offre
PO réelle. Son [mode d’emploi](evaluations/README.md) distingue les vérifications
hors ligne des appels réels au fournisseur :

```bash
python evaluations/evaluate_matching.py
python evaluations/evaluate_matching.py --live --case actual_po_agile_offer
```

Le mode `--live` est facturable et contourne le cache pour évaluer les jugements
du modèle. Ses résultats doivent être relus sur le sens et les preuves ; un
test hors ligne réussi ne valide pas la justesse du modèle en production.

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

## Ajouter une compétence sans modifier le code

1. Se connecter à l’administration, puis ouvrir **Connaissances IA**.
2. Choisir **Ajouter une connaissance** et renseigner l’outil ou la compétence,
   les entreprises et une contribution factuelle à la première personne.
3. Préciser la nature de la pratique, ses limites et, si elle est connue, sa
   période. Ne pas attribuer la durée entière d’une mission à un outil.
4. Utiliser **Voir l’aperçu**, puis **Enregistrer le brouillon** ou
   **Enregistrer et publier**. Seule la publication alimente l’IA.
5. Vérifier les informations retrouvées ou tester une réponse IA dans ce même
   onglet. Les preuves affichées avec une réponse sont celles réellement utilisées.

Jira chez GRDF et BNP Paribas Personal Finance, ainsi que Trello chez Enedis,
sont initialisés à partir des précisions de Lionel. Leur publication confirme
une pratique professionnelle, sans inventer de niveau d’administration avancée
ni de durée précise. Cette migration ne remplace jamais une fiche existante,
y compris archivée. Elle utilise le token Airtable existant.

Une modification enregistrée en brouillon laisse la dernière version publiée
active. **Archiver** la retire ; **Restaurer** prépare un brouillon à republier.
L’historique et les révisions protègent contre l’écrasement d’une modification
concurrente. Les écritures sont relues avant confirmation.

Pour corriger une information du Markdown de référence, indiquer son identifiant
et le passage exact à remplacer. La correction est limitée à ce passage ; les
autres contributions et limites sont conservées. L’aperçu doit être relu par
l’auteur : la validation détecte les références introuvables et les corrections
qui se chevauchent, sans prétendre détecter toute contradiction de sens.
Pour modifier une fiche administrative, sélectionner directement cette fiche.

En mode privé, **Signaler une correction** sous un critère de matching prépare
un brouillon. Cette action ne modifie pas directement la note : la fiche doit
être relue et publiée depuis l’administration.

Les fiches sont des révisions immuables dans les champs `Name`/`Notes` Airtable,
préfixées `__knowledge_v1__:`. Elles sont exclues de la configuration générale.
Une publication effective change l’empreinte commune au chat et au matching ;
une modification de brouillon ou de révision seule ne la change pas. Les autres
sessions prennent en compte la publication à leur prochaine interaction,
après un cache de lecture de dix secondes au maximum. Une panne de lecture
configurée ne devient jamais une base vide silencieuse.

Le stockage vise l’instance Streamlit actuelle. Airtable ne fournit pas de
transaction globale entre fiches : des publications simultanées de corrections
distinctes peuvent nécessiter une réparation. Une incohérence empêche l’usage
du corpus, tout en laissant l’administration accessible pour corriger ou archiver.

## Mettre à jour les sources de référence et les dates

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
