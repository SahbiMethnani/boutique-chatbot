# Boutique Chatbot

**Boutique Chatbot** est une application intelligente permettant aux clients d'interagir avec un chatbot pour obtenir rapidement des informations sur les produits d'une boutique, notamment les prix, les disponibilités, les caractéristiques et les descriptions des articles.

L'application repose sur une architecture **RAG (Retrieval-Augmented Generation)**, qui combine la recherche sémantique dans une base de données vectorielle **Pinecone** avec un modèle de langage afin de générer des réponses pertinentes et contextualisées.

Le backend est développé avec **FastAPI**, qui expose les API REST nécessaires à la communication avec le frontend, tandis que l'interface utilisateur est conçue avec **React** pour offrir une expérience moderne, intuitive et responsive.

## Fonctionnalités

- Chatbot intelligent permettant aux clients de poser des questions en langage naturel.
- Consultation des prix, des disponibilités et des caractéristiques des produits.
- Recherche sémantique des informations à l'aide de Pinecone.
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
            |       Pinecone       |
            |  Base de données     |
            | vectorielle en ligne |
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
| Pinecone | Stockage et recherche vectorielle en ligne |
| Modèle d'embeddings | Transformation des données en vecteurs |
| Modèle de langage (LLM) | Génération des réponses en langage naturel |

## Fonctionnement du chatbot

1. Le client saisit une question dans l'interface React.
2. Le frontend transmet la question au backend via une API REST.
3. Le pipeline RAG transforme la question en vecteur avec le même modèle d'embeddings que Chroma.
4. Pinecone recherche les informations les plus pertinentes dans les données indexées.
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
- Un compte Pinecone et un index de dimension 384.
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

Depuis le dossier `backend`, créer ou compléter `.env` avec les paramètres Pinecone

`ADMIN_API_KEY` protège l'import CSV. Choisissez une clé longue et gardez-la secrète; vous la saisirez sur l'écran d'administration.

Pour en générer une dans PowerShell, exécutez `python -c "import secrets; print(secrets.token_urlsafe(32))"` depuis le dossier `backend`, copiez le résultat dans `ADMIN_API_KEY`, puis redémarrez le backend.

L'index Pinecone doit être un index de documents avec un champ texte configuré en embedding intégré. L'application utilise le champ d'embedding défini par le schéma Pinecone pour indexer et rechercher les descriptions. La migration transfère les textes et métadonnées Chroma ; Pinecone recrée les embeddings avec le modèle intégré à l'index. Les vecteurs Chroma ne sont pas copiés car ils ne proviennent pas du modèle d'embedding de l'index.

Pour transférer la collection locale existante vers Pinecone, ouvrez un terminal dans `backend`, activez l'environnement virtuel et lancez le script :

```powershell
cd backend
.\venv\Scripts\Activate.ps1
python migrate_chroma_to_pinecone.py
```

Le script copie les textes et métadonnées par lots, puis vérifie le nombre d'enregistrements transférés. Il ne supprime pas `backend/chroma_db`, qui reste disponible après la migration. Vous pouvez relancer le script : les identifiants sont stables et les documents Pinecone sont mis à jour.

Si une exécution précédente a échoué avec une erreur `documents API`, mettez à jour les dépendances depuis `backend` avant de relancer la migration :

```powershell
python -m pip install -r requirements.txt
python migrate_chroma_to_pinecone.py
```

Démarrer le serveur depuis `backend` et le même environnement virtuel :

```powershell
cd backend
.\venv\Scripts\Activate.ps1
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

Pour enrichir le catalogue, ouvrez `http://localhost:5173/admin`, saisissez la même valeur que `ADMIN_API_KEY`, puis importez un fichier CSV. Les colonnes requises sont `nom,description,prix,categorie,tailles,couleurs,stock`. Séparez plusieurs tailles ou couleurs avec `|`. L'interface propose un modèle à télécharger et affiche les erreurs par ligne. Les fichiers UTF-8 séparés par des virgules ou des points-virgules sont acceptés.

Pour ajouter des produits depuis l'interface, ouvrez `http://localhost:5173/admin`, saisissez `ADMIN_API_KEY`, puis importez votre CSV. Le fichier doit contenir les colonnes `nom,description,prix,categorie,tailles,couleurs,stock`; séparez les tailles et couleurs multiples avec `|`. Un modèle téléchargeable est disponible dans l'interface. Les fichiers UTF-8 séparés par des virgules ou points-virgules sont pris en charge. Les produits sont envoyés à Pinecone par lots de 90; un fichier peut contenir jusqu'à 2 000 lignes.


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

Développé avec Python, FastAPI, React et Pinecone. La base locale `backend/chroma_db` est conservée comme source de migration.