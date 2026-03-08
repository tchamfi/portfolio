"""
Données du Dossier de Compétences de Lionel TCHAMFONG
découpées en chunks thématiques pour indexation dans ChromaDB.
Source : Dossier_Competences_Lionel_TCHAMFONG_PO_GenAI_Data
"""

CV_CHUNKS = [
    # ============================================================
    # IDENTITÉ & POSITIONNEMENT
    # ============================================================
    {
        "id": "profil_general",
        "text": """Lionel TCHAMFONG est un Product Owner Senior spécialisé en GenAI et Data Platforms. 
Il est basé à Fontenay-sous-Bois (94) en Île-de-France. Il est joignable au +33 6 65 34 96 56 et par email à tchamfong@gmail.com. 
Son profil LinkedIn est disponible à l'adresse https://www.linkedin.com/in/lionel-tchamfong-productowner/. 
Il travaille en freelance et est disponible immédiatement. Son TJM indicatif se situe entre 650 et 750 euros.
Il peut travailler en Île-de-France et en remote.""",
        "metadata": {"category": "profil", "keywords": "identité, contact, positionnement, freelance, TJM, disponibilité"}
    },
    {
        "id": "profil_resume",
        "text": """Lionel est un Product Owner Senior avec 15 ans d'expérience IT, dont 10 ans en ownership produit 
sur des plateformes techniques complexes (APIs Cloud, Data Platforms, architectures multi-régions). 
Il est certifié CSPO, CSM, AWS Cloud Practitioner et Databricks Fundamentals.
Passionné par l'Intelligence Artificielle, il intègre les outils IA dans son quotidien professionnel 
(utilisation de Claude avec intégration MCP data.gouv, automatisation de workflows). 
Récemment formé au Machine Learning (Jedha Bootcamp), il a réalisé un projet complet de prédiction 
de pollution de l'air (modèle XGBoost, API FastAPI, déploiement Hugging Face). 
Cette montée en compétences IA complète sa culture technique Cloud et Data.
Son approche : traduire les besoins utilisateur en features actionnables, challenger les choix d'architecture 
avec les équipes engineering, et garantir une vraie agilité. 
Il a une expérience confirmée d'encadrement de PO juniors et de coordination d'équipes offshore dans un contexte international.
Ses secteurs d'expérience : Énergie, Télécom, Data, Optique/Luxe, Services.""",
        "metadata": {"category": "profil", "keywords": "résumé, 15 ans, IA, GenAI, freelance, PO senior, approche"}
    },

    # ============================================================
    # COMPÉTENCES CLÉS
    # ============================================================
    {
        "id": "competences_genai",
        "text": """Compétences GenAI et IA/ML de Lionel :
Compréhension des architectures GenAI (RAG, Agents, LLM), ML supervisé (XGBoost, Gradient Boosting), 
déploiement de modèles (Hugging Face, FastAPI), Feature Engineering, Data Cleaning, Python.
Il utilise quotidiennement Claude avec intégration MCP data.gouv et automatise des workflows avec l'IA.
Il a réalisé un projet complet de prédiction de pollution de l'air couvrant toute la chaîne IA : 
analyse exploratoire, modélisation, déploiement API et interface utilisateur.""",
        "metadata": {"category": "competences", "keywords": "GenAI, RAG, Agents, LLM, XGBoost, ML, IA, Hugging Face, FastAPI, Python"}
    },
    {
        "id": "competences_cloud_data",
        "text": """Compétences Cloud et Data Platforms de Lionel :
AWS : S3, Lambda, DynamoDB, CloudWatch, API Gateway.
Azure : Data Factory, Azure DevOps, Azure Fabric.
Databricks, architecture Médaillon (Bronze/Silver/Gold), API REST, microservices.
Outils de data integration : Informatica IICS, PostgreSQL, Power BI.
Il a piloté des plateformes data déployées dans 36 pays et des APIs multi-régions avec SLA 99,9%.""",
        "metadata": {"category": "competences", "keywords": "AWS, Azure, Databricks, Cloud, Data, API, Lambda, S3, médaillon, Power BI"}
    },
    {
        "id": "competences_product_ownership",
        "text": """Compétences Product Ownership de Lionel :
Vision produit, roadmap, priorisation par la valeur, gestion de backlog (200+ User Stories), 
coordination multi-squads, lien Product Manager / Engineering, encadrement de PO juniors.
Il a 10 ans d'expérience en ownership produit avec une approche orientée valeur métier.
Il sait traduire les besoins utilisateur en features actionnables et challenger les choix d'architecture 
avec les équipes engineering.""",
        "metadata": {"category": "competences", "keywords": "product ownership, vision produit, roadmap, backlog, priorisation, coordination"}
    },
    {
        "id": "competences_agile_leadership",
        "text": """Compétences Agile et Leadership de Lionel :
Scrum, Kanban, SAFe (notions). Certifié CSPO et CSM. 
Plus de 200 cérémonies Agile animées. 
Enseignant vacataire en méthodologies Agile à l'IUT d'Évry (partenariat EFREI) : 
transmission des pratiques Scrum, Kanban et Product Ownership à des étudiants en informatique.
Squad lead avec équipes offshore (Inde). Encadrement de 2 PO juniors avec mentoring 
et structuration des pratiques produit.""",
        "metadata": {"category": "competences", "keywords": "Scrum, Kanban, SAFe, CSPO, CSM, leadership, enseignant, Agile, coaching"}
    },
    {
        "id": "competences_outils",
        "text": """Outils maîtrisés par Lionel :
Jira, Confluence, Azure DevOps, Git, Postman, Splunk, Python, SQL, Bubble.io, Visual Studio Code.
Pour les tests et la QA : Postman, SoapUI, HP-QC, Charles Proxy.
Pour le monitoring : Splunk, CloudWatch, Power BI.
Pour le développement IA : Python, Pandas, Scikit-learn, XGBoost, FastAPI, Hugging Face.""",
        "metadata": {"category": "competences", "keywords": "Jira, Confluence, Azure DevOps, Git, Postman, Splunk, Python, SQL, Bubble.io, VS Code"}
    },

    # ============================================================
    # PROJET IA - PRÉDICTION POLLUTION
    # ============================================================
    {
        "id": "projet_ia_pollution",
        "text": """Projet IA réalisé lors du Jedha Bootcamp en mars 2025 : Prédiction de la pollution de l'air (PM2.5).
Projet de fin de formation réalisé en autonomie, couvrant l'ensemble de la chaîne de valeur IA : 
de l'analyse exploratoire au déploiement d'un modèle en production via API, avec interface utilisateur.
Objectif : développer un outil de prédiction de la qualité de l'air (concentration PM2.5) pour 54 villes américaines, 
avec un double objectif : prévoir la pollution pour la population et identifier les facteurs clés pour les décideurs publics.""",
        "metadata": {"category": "projet_ia", "keywords": "IA, ML, pollution, PM2.5, prédiction, Jedha, XGBoost"}
    },
    {
        "id": "projet_ia_pollution_tech",
        "text": """Détails techniques du projet IA de prédiction pollution :
Data Engineering : nettoyage et préparation d'un dataset de plus de 35 000 lignes (mesures journalières sur 2 ans), 
gestion des données manquantes (météo et polluants), feature engineering.
Modélisation ML : entraînement et évaluation d'un modèle XGBRegressor (Gradient Boosting), 
analyse du R², itérations d'amélioration du scope pour optimiser les performances.
Déploiement API : création d'une API REST avec FastAPI (Python), sérialisation du modèle (.pkl), 
documentation automatique, déploiement sur Hugging Face Spaces.
Interface utilisateur : conception d'une UI avec Bubble.io connectée à l'API, 
permettant aux utilisateurs de saisir ville/date et recevoir une prédiction contextualisée avec recommandations.
Stack technique : Python, Pandas, Scikit-learn, XGBoost, FastAPI, Hugging Face, Bubble.io, Visual Studio Code.
Ce projet illustre sa compréhension concrète d'un projet IA de bout en bout.""",
        "metadata": {"category": "projet_ia", "keywords": "XGBoost, FastAPI, Hugging Face, Bubble.io, Python, Pandas, Scikit-learn, déploiement, API"}
    },

    # ============================================================
    # EXPÉRIENCE EPSA
    # ============================================================
    {
        "id": "exp_epsa_contexte",
        "text": """De janvier 2025 à février 2026, Lionel est Data Product Owner chez EPSA Group. 
Environnement technique : Azure Fabric, Azure DevOps, CI/CD, Power BI, Informatica IICS, PostgreSQL.
Mission : intégration et unification des données CRM de 4 systèmes (Salesforce, Dynamics 365, HubSpot, Pipedrive) 
vers une plateforme Data groupe déployée dans 36 pays.
Il a défini la vision produit et la roadmap Data en collaboration avec le CDO et les équipes Data Engineering.""",
        "metadata": {"category": "experience", "entreprise": "EPSA", "periode": "2025-2026", "keywords": "data, azure, CRM, 36 pays, CDO, roadmap"}
    },
    {
        "id": "exp_epsa_responsabilites",
        "text": """Responsabilités de Lionel chez EPSA Group :
Pilotage de l'architecture Médaillon (Bronze/Silver/Gold) : challenge des choix techniques, 
validation des règles de transformation, contrôle qualité.
Réconciliation de données hétérogènes entre entités internationales : définition des règles de mapping et de déduplication.
Coordination multi-squads : Data Engineering, Business Analysts, équipes métier dans 36 pays.
Data Governance : définition des KPIs de qualité, suivi de la conformité des pipelines, 
documentation fonctionnelle et dictionnaires de transcodification.
Création du Core Model unifié (Account, Opportunity, Invoice, Contract) et spécification des flux d'ingestion CRM.
Pertinence pour la mission GenAI : environnement Azure avec architecture Data complexe, 
compétence transférable au pilotage de pipelines RAG et d'ingestion pour des systèmes GenAI.""",
        "metadata": {"category": "experience", "entreprise": "EPSA", "periode": "2025-2026", "keywords": "médaillon, data governance, core model, mapping, déduplication, 36 pays, RAG"}
    },

    # ============================================================
    # EXPÉRIENCE ESSILORLUXOTTICA
    # ============================================================
    {
        "id": "exp_essilor_contexte",
        "text": """De juin 2019 à décembre 2024 (5 ans et demi), Lionel a été Lead Product Owner chez EssilorLuxottica via Wemanity. 
Environnement technique : AWS, API REST, architecture multi-région.
Il était owner de 2 produits critiques :
EyeCloud : plateforme API AWS de gestion documentaire déployée en multi-région (6 pays, 10+ systèmes sources), SLA 99,9%.
SSP (Self Service Platform) : application web de visualisation et suivi des commandes de fabrication de verres 
à destination des Zone Managers géographiques dans 6 pays.""",
        "metadata": {"category": "experience", "entreprise": "EssilorLuxottica", "periode": "2019-2024", "keywords": "Lead PO, AWS, EyeCloud, SSP, multi-région, 6 pays, SLA 99.9%"}
    },
    {
        "id": "exp_essilor_responsabilites",
        "text": """Responsabilités de Lionel chez EssilorLuxottica :
Lead PO : encadrement de 2 PO juniors, mentoring, structuration des pratiques produit sur les 2 applications.
Pilotage de l'architecture technique : challenge des choix d'architecture AWS (S3, Lambda, DynamoDB, API Gateway, CloudWatch) avec les Tech Leads.
Gestion d'un backlog de 200+ user stories, priorisation par la valeur métier, animation de 200+ cérémonies Agile.
Coordination d'équipes offshore (Inde) : communication interculturelle, alignement technique, suivi qualité.
Monitoring et observabilité : mise en place de dashboards Splunk, suivi des KPIs de performance (SLA, temps de réponse, taux d'erreur).
Intégration de 10+ systèmes sources avec onboarding structuré : documentation technique, tests d'intégration, 
accompagnement des équipes partenaires.
Pertinence pour la mission GenAI : 5,5 ans en tant que squad leader sur une plateforme API Cloud critique. 
Expérience concrète du rôle attendu : un PO qui travaille au quotidien avec les équipes techniques, 
challenge l'architecture et assure la coordination inter-squads.""",
        "metadata": {"category": "experience", "entreprise": "EssilorLuxottica", "periode": "2019-2024", "keywords": "Lead PO, AWS, S3, Lambda, DynamoDB, Splunk, offshore, Inde, 200 user stories, 200 cérémonies"}
    },

    # ============================================================
    # EXPÉRIENCE GRDF
    # ============================================================
    {
        "id": "exp_grdf",
        "text": """De juillet 2018 à mai 2019, Lionel a été Proxy Product Owner chez Talan pour le compte de GRDF à Paris.
Environnement technique : JIRA, SoapUI, SQL, HP-QC.
Il travaillait sur le suivi des demandes de raccordement au réseau de distribution de gaz.
Il a analysé et recueilli plus de 20 besoins métiers critiques liés aux raccordements clients.
Il a rédigé des User Stories avec critères d'acceptation, priorisé et géré le backlog sur environ 20 sprints.
Il a piloté la recette sur 3 projets majeurs, réalisé des tests API via SoapUI, 
et obtenu une réduction du taux d'anomalies de 30%.""",
        "metadata": {"category": "experience", "entreprise": "GRDF", "periode": "2018-2019", "keywords": "proxy PO, raccordement, gaz, SoapUI, SQL, réduction anomalies 30%"}
    },

    # ============================================================
    # EXPÉRIENCE ENEDIS
    # ============================================================
    {
        "id": "exp_enedis",
        "text": """De mai 2016 à juillet 2018, Lionel a été Product Owner chez Talan pour le compte d'Enedis à Nanterre.
Environnement technique : JIRA, Confluence, SQL, API REST, Postman.
SI stratégique gérant les flux de données entre Enedis et les fournisseurs d'énergie 
dans un environnement réglementaire complexe.
Backlog de 200+ User Stories impactant 500+ utilisateurs internes.
Il a géré la cartographie et documentation des flux inter-systèmes (SI comptage, SI facturation, fournisseurs).
Il a animé plus de 60 cérémonies Agile et assuré l'interface entre les équipes métier et les équipes de développement.
Il a assuré le suivi de la conformité réglementaire des évolutions.""",
        "metadata": {"category": "experience", "entreprise": "Enedis", "periode": "2016-2018", "keywords": "énergie, flux données, réglementaire, 200 user stories, 500 utilisateurs, Postman"}
    },

    # ============================================================
    # EXPÉRIENCE QA - ORANGE
    # ============================================================
    {
        "id": "exp_qa_orange",
        "text": """De septembre 2013 à avril 2016, Lionel a été QA Engineer chez Davidson Consulting pour le compte d'Orange.
Environnement technique : HP-QC, Postman, SoapUI, Oracle, SQL.
Application web critique permettant aux conseillers commerciaux Orange de réaliser les souscriptions, 
modifications et résiliations d'offres mobiles, internet et fixe.
Il a défini la stratégie de tests et conçu 300+ cas de tests couvrant les parcours de souscription, modification et résiliation.
Il a réalisé des tests multi-canaux (boutique, centre d'appels, espace client web) et validé les règles métier complexes 
(éligibilité, remises, promotions).
Il a réalisé des tests API back-end via Postman et SoapUI (web services d'éligibilité, tarification, provisioning) 
et analysé les logs inter-applicatifs.
Il a obtenu une réduction de 25% des erreurs de régression grâce à l'automatisation. 
Reporting hebdomadaire à la direction projet.""",
        "metadata": {"category": "experience", "entreprise": "Orange", "periode": "2013-2016", "keywords": "QA, tests, Orange, Postman, SoapUI, Oracle, SQL, automatisation, 300 cas de tests"}
    },

    # ============================================================
    # EXPÉRIENCE QA - BOUYGUES TELECOM
    # ============================================================
    {
        "id": "exp_qa_bouygues",
        "text": """De mars 2012 à août 2013, Lionel a été QA Engineer chez Davidson Consulting pour le compte de Bouygues Telecom.
Environnement technique : HP-QC, Charles Proxy, JIRA.
Application B.TV : service de télévision sur mobile et tablette (100+ chaînes TV, streaming live, replay, téléchargement offline).
Il a conçu et exécuté 200+ cas de tests sur iOS et Android : streaming live, replay, qualité adaptative (SD/HD), téléchargement offline.
Validation sur 20+ devices, tests de compatibilité OS, tests de performance (temps de chargement, consommation batterie) 
et en conditions réseau dégradées.
Tests d'intégration : API de streaming, flux DRM, synchronisation métadonnées programmes (EPG), notifications push.
Suivi de 350+ anomalies sur le cycle projet, priorisation avec l'équipe produit selon l'impact utilisateur.
Ce parcours QA apporte un regard critique systématique sur ce qui est développé vs ce qui est attendu. 
C'est un atout concret pour un PO GenAI qui doit évaluer l'adéquation entre ce qui est proposé, ce qui est livré et la cible visée.""",
        "metadata": {"category": "experience", "entreprise": "Bouygues Telecom", "periode": "2012-2013", "keywords": "QA, B.TV, streaming, iOS, Android, 350 anomalies, 200 cas de tests, DRM"}
    },

    # ============================================================
    # ENSEIGNEMENT
    # ============================================================
    {
        "id": "enseignement",
        "text": """Lionel est enseignant vacataire en méthodologies Agile à l'IUT d'Évry (partenariat EFREI). 
Il transmet les pratiques Scrum, Kanban et Product Ownership à des étudiants en informatique. 
Cette expérience renforce sa capacité de coaching et de vulgarisation technique, 
compétences essentielles pour un PO qui doit garantir une vraie agilité dans l'équipe.""",
        "metadata": {"category": "enseignement", "keywords": "enseignant, Agile, Scrum, Kanban, IUT Évry, EFREI, coaching, vulgarisation"}
    },

    # ============================================================
    # CERTIFICATIONS & FORMATION
    # ============================================================
    {
        "id": "certifications",
        "text": """Certifications, diplômes et études de Lionel TCHAMFONG. Voici la liste complète de toutes ses certifications et formations :
- 2025 : Data Essential et Prompt Engineering au Jedha Bootcamp, incluant un projet IA de prédiction pollution (XGBoost, FastAPI, Hugging Face).
- 2025 : Databricks Fundamentals (Databricks).
- 2025 : MIA Niveau II – Intermédiaire en Assurance (Prodémial).
- 2023 : AWS Cloud Practitioner (Amazon Web Services).
- 2017 : CSPO – Certified Scrum Product Owner (Scrum Alliance).
- 2015 : CSM – Certified Scrum Master (Scrum Alliance).
- 2010 : Diplôme d'Ingénieur – Systèmes Radio et Télécommunications (ENSEIRB, Institut Polytechnique de Bordeaux).
Lionel possède donc 6 certifications et un diplôme d'ingénieur.""",
        "metadata": {"category": "certification", "keywords": "certifications, diplômes, études, formations, Jedha, Databricks, AWS, CSPO, CSM, ingénieur, ENSEIRB, MIA, Prodémial"}
    },

    # ============================================================
    # LANGUES
    # ============================================================
    {
        "id": "langues",
        "text": """Lionel parle couramment le français (langue maternelle) et possède un anglais courant.
Il travaille régulièrement dans un contexte international avec des parties prenantes anglophones, 
notamment lors de son expérience chez EssilorLuxottica (6 pays) et EPSA (36 pays).""",
        "metadata": {"category": "langues", "keywords": "français, anglais, international, courant"}
    },

    # ============================================================
    # ADÉQUATION MISSION PO GENAI
    # ============================================================
    {
        "id": "adequation_genai",
        "text": """Adéquation de Lionel avec une mission Product Owner GenAI :
Transformer une opportunité IA en features, User Stories et tâches : 10 ans PO avec traduction de besoins métier en backlog actionnable (200+ US). Projet Jedha couvrant toute la chaîne IA de l'idée au déploiement.
Travailler avec AI et Software Engineers : 5,5 ans chez EssilorLuxottica en lien direct avec Tech Leads et développeurs. Dialogue technique quotidien sur API, architecture et performance.
Challenger les choix d'architecture : challenge d'architecture AWS (EssilorLuxottica) et Azure (EPSA). Validation des choix techniques avec les équipes engineering (infra/devops).
Communiquer avec les autres squads : coordination multi-squads (6 pays, 10+ systèmes, équipes offshore Inde). Interface PO/PM/Tech Lead.
Scrum Master et vraie agilité : CSPO + CSM certifié. 200+ cérémonies animées. Enseignant Agile (IUT/EFREI).
Regard critique proposé vs développé vs cible : 5 ans QA Engineer avec habitude de contrôler l'adéquation entre le besoin et la livraison.
Compréhension RAG, Agents, MCP, GenAI : formation Jedha (IA/ML), utilisateur quotidien d'outils IA (Claude + MCP). Compréhension des concepts, pas encore d'expérience en production sur ces sujets.
PO technique, leader de squad : Lead PO (2 PO juniors encadrés). Pilotage d'une plateforme technique critique (EyeCloud + SSP).""",
        "metadata": {"category": "adequation", "keywords": "GenAI, RAG, Agents, MCP, LLM, PO technique, architecture, squad lead, IA"}
    },

    # ============================================================
    # VALEUR AJOUTÉE
    # ============================================================
    {
        "id": "valeur_ajoutee",
        "text": """Les points forts de Lionel en tant que Product Owner :
Expérience internationale massive : pilotage de projets dans 6 pays (France, USA, Chine, Brésil, Canada, Pologne) 
chez EssilorLuxottica et coordination dans 36 pays chez EPSA, avec des équipes offshore (Inde).
Double compétence Data + Product + IA : capacité à piloter des produits data complexes tout en intégrant les enjeux GenAI.
Expertise cloud multi-provider : maîtrise des environnements AWS et Azure en contexte de production.
Background technique solide : ingénieur télécom de formation, 5 ans de QA, projet IA complet, 
ce qui lui permet de dialoguer efficacement avec les équipes techniques et de garantir la qualité des livrables.
Leadership confirmé : Lead PO avec encadrement de juniors, enseignant Agile, squad lead.
Volume d'expérience : 200+ cérémonies Agile animées, 200+ user stories gérées, 350+ bugs suivis, 
300+ cas de tests conçus, coordination de 10+ systèmes sources.""",
        "metadata": {"category": "valeur_ajoutee", "keywords": "international, data, cloud, IA, technique, coordination, leadership, Lead PO, 36 pays"}
    },
]
