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
Les métadonnées de l’analyse identifient le corpus et le barème utilisés.

Le barème `requirements-v1` attribue un poids de 3 aux exigences requises et
de 1 aux options. Les crédits sont : direct 1, partiel 0,5, formation ou
expérience historique 0,25, inconnu ou non satisfait 0. Les exigences inconnues
restent dans le dénominateur. Si toutes les évaluations sont invalides, aucun
score n’est affiché. Une analyse valide sans correspondance peut en revanche
obtenir 0 ; les points à clarifier restent visibles.

L’exhaustivité du traitement porte sur les exigences extraites. L’extraction
reste une tâche du modèle et doit être contrôlée sur des offres représentatives.
Les dates mensuelles donnent une durée approximative ; un seuil d’ancienneté
proche des limites de précision est marqué à confirmer. L’empreinte des dates
et la date du calcul sont associées à celles du corpus dans chaque analyse.

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
| `AIRTABLE_TOKEN` | Configuration, recommandations et analytics via l’intégration Airtable existante. |

Une seule clé LLM est nécessaire si un seul fournisseur est utilisé. Choisir
dans l’administration un modèle effectivement disponible pour le compte
configuré. Sans clé LLM, l’indexation et les tests de recherche restent possibles ;
les réponses générées et le matching qui appellent le modèle ne fonctionneront
pas. Sans Airtable configuré, vérifier le contenu de repli affiché : la V3 du RAG
ne remplace pas automatiquement tous les champs éditoriaux sauvegardés dans Airtable.

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
| Offre longue avec exigences obligatoires et optionnelles | Toutes les exigences extraites figurent dans le résultat ; manques visibles. |
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
5. Déployer le commit sur l’hébergeur réel et contrôler dans l’administration
   la version et l’empreinte chargées.

La reconstruction est automatique quand le contenu change dans le processus
applicatif. Un redémarrage force aussi une initialisation propre. Une mise à
jour uniquement dans une copie locale du fichier ne change pas le site distant.

## Déployer sur l’hébergement existant

Le dépôt fourni n’identifie pas à lui seul le service qui exécute le site :
aucun workflow de déploiement ni configuration Docker ou métadonnée de Space
n’était présent lors de cette intégration. Un push GitHub n’atteste donc pas
qu’une nouvelle version est en ligne.

Après validation de la branche, conserver l’identifiant du commit précédent
pour le retour arrière, puis fusionner le changement et utiliser le chemin
correspondant à l’hébergement effectivement configuré :

| Hébergement effectif | Action |
| --- | --- |
| Streamlit connecté à ce dépôt | Vérifier le dépôt, la branche et le fichier d’entrée `app.py` dans le tableau de bord ; lancer ou attendre le redéploiement de ce commit. Vérifier les secrets côté hébergeur. |
| Hugging Face Space existant | Vérifier son dépôt propre, sa configuration de lancement et son éventuelle synchronisation GitHub. Si aucune synchronisation n’existe, publier le commit dans le dépôt du Space selon son mécanisme existant, puis suivre la reconstruction. Ne pas remplacer arbitrairement son SDK ou son point d’entrée. |
| Autre serveur ou hébergeur | Mettre à jour le checkout ou l’image vers le commit validé, installer les dépendances et redémarrer le service Streamlit avec sa configuration existante. |

Dans tous les cas, ouvrir le site public et refaire la recette ciblée. Contrôler
la version du corpus dans l’administration et au moins une réponse QA, une
réponse data et un matching. Une fusion réussie ou un build vert ne remplace
pas ces contrôles applicatifs.

En cas de régression, revenir au commit de code précédent et redéployer ;
conserver ensemble les versions du code, du corpus et des périodes d’expérience.
Les configurations et données Airtable ne sont pas restaurées par un retour
arrière Git : les vérifier séparément si elles ont été changées.

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
