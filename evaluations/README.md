# Recette métier du matching

`matching_cases.json` contient 25 exigences ciblées et l'offre PO réelle fournie
par Lionel. Chaque attente précise sa source, le statut admissible et sa raison.
Il s'agit d'attentes de recette proposées, à relire avec le propriétaire du
profil ; aucune validation humaine préalable n'est revendiquée.

## Deux niveaux de vérification

```bash
python evaluations/evaluate_matching.py
python -m unittest tests.test_business_evaluations -v
```

Ce mode sans réseau vérifie les données de recette, la recherche lexicale
sur les vrais blocs V3 du dépôt, les seuils d'expérience à la date de référence et les
prérequis explicites. Les tests vérifient aussi la formule et le détecteur de
résultats incohérents. Il ne lit pas les connaissances administratives distantes.
**Il ne mesure pas la justesse des jugements du modèle.**

```bash
python evaluations/evaluate_matching.py --live --case jira_professional_use
python evaluations/evaluate_matching.py --live --case actual_po_agile_offer
python evaluations/evaluate_matching.py --live --full-offer --output /tmp/matching-live.json
```

Le mode `--live` appelle réellement l'extraction, la recherche hybride,
l'évaluation et la revue ciblée. Il utilise les clés et le modèle configurés
pour le fournisseur, sans cache de matching ni publication de connaissances.
`--model` permet un choix de modèle temporaire. Ces appels sont facturables.
Les clés ne sont jamais enregistrées dans le rapport ; les erreurs du
fournisseur sont limitées à leur type. Ne pas ajouter de vraies offres privées
ni de rapports de production contenant ces offres au dépôt.

Les cas Jira et Trello sont bloqués tant que les précisions confirmées ne sont
pas réellement publiées. Le runner n'insère jamais de preuves fictives pour les
faire passer. Le rapport contient les critères, statuts, preuves citées, revues,
coûts retournés par le fournisseur et empreinte du référentiel.

## Interpréter le résultat

- Un échec d'extraction, un désaccord avec les statuts attendus, une preuve
  étrangère, une erreur de score ou un prérequis oublié fait échouer la recette.
- Quelques cas acceptent deux statuts, avec une justification explicite dans
  la fixture. Cela ne rend pas acceptable une affirmation non sourcée.
- Les expressions interdites détectent certains raccourcis connus. Elles ne
  prouvent pas à elles seules que toute phrase est fidèle aux sources : relire
  les divergences et échantillonner les cas passants reste nécessaire.
- L'offre réelle attend 12 critères et une couverture sémantique identifiée.
  Une segmentation différente appelle une revue ; le nombre 12 n'est pas un
  objectif à imposer au moteur en production. Aucun score 79/100 n'est figé.
- Réviser une attente uniquement si le besoin ou les preuves ont changé,
  jamais pour masquer une régression. Une nouvelle compétence peut faire
  évoluer légitimement un résultat ; conserver la raison de l'évolution dans
  la revue du changement.

Le code de sortie vaut `0` si tous les cas exécutés passent, `1` en cas d'échec,
de blocage ou d'erreur. Le rapport distingue explicitement une vérification
offline d'une évaluation ayant réellement terminé avec le fournisseur.

## Cas observé restant à revoir

La vérification de l'offre PO réelle sur l'application en ligne a produit
**13 critères**. Le premier reprend la responsabilité du Product Backlog, la
priorisation par valeur métier et la qualité des livrables. Une autre entrée
reprend « Gestion de backlog : Capacité à définir, prioriser et gérer le backlog
produit de manière efficace. ». Les deux correspondent à des statuts directs
justifiés notamment par le backlog et le WSJF : le même aspect reçoit donc un
poids supplémentaire. L'alerte de dédoublonnage du benchmark est légitime.

Le nombre 13 ne constitue pas à lui seul une erreur : une décomposition qui
isolerait réellement des responsabilités distinctes pourrait être recevable.
Dans ce cas observé, il faut supprimer le recouvrement tout en préservant la
responsabilité de qualité et les autres contraintes. L'attente du benchmark
n'a pas été assouplie pour faire passer ce résultat. Les 25 cas n'ont pas été
annoncés comme validés avec le fournisseur réel.
