# Boutique Chatbot

**Boutique Chatbot** est une application intelligente permettant aux clients d'interagir avec un chatbot pour obtenir rapidement des informations sur les produits d'une boutique, notamment les prix, les disponibilités, les caractéristiques et les descriptions des articles.

L'application repose sur une architecture **RAG (Retrieval-Augmented Generation)**, qui combine la recherche sémantique dans une base de données vectorielle **ChromaDB** avec un modèle de langage afin de générer des réponses pertinentes et contextualisées.

Le backend est développé avec **FastAPI**, qui expose les API REST nécessaires à la communication avec le frontend, tandis que l'interface utilisateur est conçue avec **React** pour offrir une expérience moderne, intuitive et responsive.

## Fonctionnalités

- Chatbot intelligent permettant aux clients de poser des questions en langage naturel.
- Consultation des prix, des disponibilités et des caractéristiques des produits.
- Recherche sémantique des informations à l'aide de ChromaDB.
- Architecture RAG pour améliorer la pertinence des réponses générées.
- API REST développées avec FastAPI.
- Interface utilisateur moderne, responsive et intuitive avec React.

## Architecture

Le projet repose sur une architecture frontend/backend intégrant un pipeline RAG.

```text
                    CLIENT
                       |
                       v
            +----------------------+
            |    React Frontend    |
            |  Interface Chatbot   |
            +----------------------+
                       |
                       | Requêtes HTTP
                       v
            +----------------------+
            |    FastAPI Backend   |
            |       API REST       |
            +----------------------+
                       |
                       v
            +----------------------+
            |      Pipeline RAG    |
            |                      |
            |  1. Recherche        |
            |  2. Récupération     |
            |  3. Construction     |
            |     du contexte      |
            |  4. Génération       |
            +----------------------+
                       |
                       v
            +----------------------+
            |       ChromaDB       |
            |  Base de données      |
            |     vectorielle      |
            +----------------------+
                       |
                       v
            +----------------------+
            |     Modèle LLM       |
            | Génération de réponse|
            +----------------------+
```

## Technologies utilisées

| Technologie | Rôle |
|---|---|
| Python | Développement du backend et du pipeline RAG |
| FastAPI | Exposition des API REST |
| React | Développement de l'interface utilisateur |
| ChromaDB | Stockage et recherche vectorielle |
| Modèle d'embeddings | Transformation des données en vecteurs |
| Modèle de langage (LLM) | Génération des réponses en langage naturel |

## Fonctionnement du chatbot

1. Le client saisit une question dans l'interface React.
2. Le frontend transmet la question au backend via une API REST.
3. Le pipeline RAG prépare la question pour la recherche sémantique.
4. ChromaDB recherche les informations les plus pertinentes dans les données indexées.
5. Les résultats récupérés sont transmis au modèle de langage comme contexte.
6. Le modèle génère une réponse fondée sur les informations disponibles.
7. Le backend renvoie la réponse au frontend, qui l'affiche au client.

## Structure du projet

```text
boutique-chatbot/
├── backend/
│   ├── main.py
│   ├── requirements.txt
│   └── ...
├── frontend/
│   ├── package.json
│   ├── src/
│   └── ...
├── .env.example
├── .gitignore
└── README.md
```

Cette structure est indicative et peut être adaptée à l'organisation réelle du projet.

## Installation et lancement

### Prérequis

- Python et pip.
- Node.js et npm.
- Un environnement compatible avec les dépendances de ChromaDB.
- Un modèle de langage accessible via une API ou exécuté localement.

### 1. Cloner le projet

```bash
git clone <URL_DU_DEPOT>
cd boutique-chatbot
```

### 2. Installer et lancer le backend

Accéder au répertoire du backend :

```bash
cd backend
```

Créer un environnement virtuel :

```bash
python -m venv .venv
```

Activer l'environnement sous Windows :

```bash
.venv\Scripts\activate
```

Sous Linux ou macOS :

```bash
source .venv/bin/activate
```

Installer les dépendances :

```bash
pip install -r requirements.txt
```

Configurer les variables d'environnement nécessaires, puis démarrer le serveur :

```bash
uvicorn main:app --reload
```

Par défaut, le backend est accessible à l'adresse `http://127.0.0.1:8000`.

La documentation interactive des API est disponible aux adresses suivantes :

- Swagger UI : `http://127.0.0.1:8000/docs`
- ReDoc : `http://127.0.0.1:8000/redoc`

### 3. Installer et lancer le frontend

Dans un autre terminal, accéder au répertoire du frontend :

```bash
cd frontend
```

Installer les dépendances :

```bash
npm install
```

Démarrer l'application :

```bash
npm run dev
```

L'adresse du frontend dépend de l'outil utilisé pour créer le projet React.

## Configuration

Les clés API et les paramètres sensibles doivent être stockés dans un fichier `.env` local, qui ne doit pas être versionné.

Exemple de configuration :

```env
GROQ_API_KEY=
CHROMA_PERSIST_DIRECTORY=./chroma_db
```

Les variables doivent être adaptées aux paramètres réellement utilisés par l'application.

## Perspectives d'évolution

- Synchronisation avec un catalogue de produits actualisé en temps réel.
- Amélioration de la précision des recherches sémantiques.
- Ajout de filtres par catégorie, prix et disponibilité.
- Gestion de l'historique des conversations.
- Mise en place d'une authentification et d'une gestion des utilisateurs.
- Optimisation des performances du pipeline RAG.
- Déploiement de l'application dans un environnement de production.

## Objectif du projet

L'objectif de Boutique Chatbot est de faciliter l'accès aux informations commerciales grâce à une interface conversationnelle intelligente. En combinant la recherche vectorielle, les modèles de langage et les technologies web modernes, l'application vise à améliorer l'expérience client et à simplifier la recherche de produits.

---

Développé avec Python, FastAPI, React et ChromaDB.