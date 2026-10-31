import json
import os
import re
from types import SimpleNamespace
os.environ["GROQ_API_KEY"] = "test_clef"
import chromadb
import pytest
import pytest_html
from fastapi.testclient import TestClient
from .. import main
def construire_document(nom, categorie, description, prix, tailles, couleurs, stock):
    return f"""
Produit: {nom}
Catégorie: {categorie}
Description: {description}
Prix: {prix} TND
Tailles disponibles: {', '.join(tailles)}
Couleurs disponibles: {', '.join(couleurs)}
Stock: {stock} unités
    """.strip()


PRODUITS_INITIAUX = [
    ("Robe fleurie", "Robes", 89.9, 12, "Robe légère à fleurs pour l'été"),
    ("Jean slim", "Pantalons", 119.0, 20, "Jean bleu coupe slim pour homme"),
    ("T-shirt blanc", "T-shirts", 35.0, 50, "T-shirt en coton blanc"),
    ("Veste cuir", "Vestes", 350.0, 5, "Veste en cuir noir"),
    ("Pull laine", "Pulls", 99.0, 15, "Pull chaud en laine mérinos"),
    ("Chemise lin", "Chemises", 79.0, 18, "Chemise en lin respirante"),
    ("Short sport", "Shorts", 45.0, 30, "Short de sport léger"),
    ("Manteau hiver", "Manteaux", 420.0, 7, "Manteau long pour l'hiver"),
]


def _mots(texte):
    return set(re.findall(r"\w+", texte.lower()))


class FakeCollection:

    def __init__(self, produits=()):
        self.ids, self.documents, self.metadatas = [], [], []
        self.query_calls = []
        self.add_error = self.query_error = self.get_error = None
        for nom, categorie, prix, stock, description in produits:
            self.ids.append(f"product_{nom.replace(' ', '_')}")
            self.documents.append(
                construire_document(nom, categorie, description, prix, ["S", "M", "L"], ["Noir"], stock)
            )
            self.metadatas.append({"nom": nom, "prix": prix, "categorie": categorie, "stock": stock})

    def count(self):
        return len(self.ids)

    def add(self, documents, metadatas, ids):
        if self.add_error:
            raise self.add_error
        self.documents.extend(documents)
        self.metadatas.extend(metadatas)
        self.ids.extend(ids)

    def query(self, query_texts, n_results=3):
        self.query_calls.append((query_texts, n_results))
        if self.query_error:
            raise self.query_error
        mots = _mots(query_texts[0])
        trouves = [
            (doc, meta)
            for doc, meta in zip(self.documents, self.metadatas)
            if mots & _mots(doc)
        ][:n_results]
        return {
            "documents": [[d for d, _ in trouves]],
            "metadatas": [[m for _, m in trouves]],
        }

    def get(self):
        if self.get_error:
            raise self.get_error
        return {"ids": list(self.ids), "metadatas": list(self.metadatas), "documents": list(self.documents)}


class FakeChromaClient:
    def __init__(self):
        self.deleted, self.created = [], []
        self.delete_error = None

    def get_collection(self, name):
        return FakeCollection(PRODUITS_INITIAUX)

    def delete_collection(self, name):
        if self.delete_error:
            raise self.delete_error
        self.deleted.append(name)

    def create_collection(self, name):
        self.created.append(name)
        return FakeCollection()


class FakeGroq:

    def __init__(self, reply="Bonjour ! Voici ma réponse simulée."):
        self.reply = reply
        self.error = None
        self.calls = []
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self._create))

    def _create(self, **kwargs):
        self.calls.append(kwargs)
        if self.error:
            raise self.error
        message = SimpleNamespace(content=self.reply)
        return SimpleNamespace(choices=[SimpleNamespace(message=message)])

    @property
    def prompt(self):
        return self.calls[-1]["messages"][1]["content"]

_vrai_persistent_client = chromadb.PersistentClient
chromadb.PersistentClient = lambda *args, **kwargs: FakeChromaClient()
try:
    from .. import main
finally:
    chromadb.PersistentClient = _vrai_persistent_client


@pytest.fixture
def client():
    return TestClient(main.app)


@pytest.fixture
def collection(monkeypatch):
    fausse = FakeCollection(PRODUITS_INITIAUX)
    monkeypatch.setattr(main, "collection", fausse)
    return fausse


@pytest.fixture
def collection_vide(monkeypatch):
    fausse = FakeCollection()
    monkeypatch.setattr(main, "collection", fausse)
    return fausse


@pytest.fixture
def groq(monkeypatch):
    faux = FakeGroq()
    monkeypatch.setattr(main, "groq_client", faux)
    return faux


@pytest.fixture
def chroma(monkeypatch):
    faux = FakeChromaClient()
    monkeypatch.setattr(main, "chroma_client", faux)
    return faux


@pytest.fixture
def produit_valide():
    return {
        "nom": "Casquette Bleue",
        "description": "Casquette réglable en coton",
        "prix": 25.5,
        "categorie": "Accessoires",
        "tailles": ["Unique"],
        "couleurs": ["Bleu", "Noir"],
        "stock": 40,
    }



@pytest.fixture
def capture(extras):

    def _capture(titre, response=None, **infos):
        bloc = {}
        if response is not None:
            req = response.request
            corps = req.content.decode("utf-8") if req.content else None
            try:
                corps = json.loads(corps) if corps else None
            except ValueError:
                pass
            try:
                contenu = response.json()
            except ValueError:
                contenu = response.text
            bloc = {
                "requête": f"{req.method} {req.url.path}",
                "corps_envoyé": corps,
                "statut_http": response.status_code,
                "réponse": contenu,
            }
        bloc.update(infos)
        texte = json.dumps(bloc, indent=2, ensure_ascii=False)
        print(f"--- {titre} ---\n{texte}")
        extras.append(pytest_html.extras.text(texte, name=titre))

    return _capture

def pytest_html_report_title(report):
    report.title = "Rapport de tests - Boutique Chatbot (FastAPI + ChromaDB + Groq)"


def pytest_html_results_table_header(cells):
    cells.insert(2, "<th>Scénario</th>")


def pytest_html_results_table_row(report, cells):
    cells.insert(2, f"<td>{getattr(report, 'description', '')}</td>")


@pytest.hookimpl(wrapper=True)
def pytest_runtest_makereport(item, call):
    report = yield
    report.description = (item.function.__doc__ or "").strip()
    return report