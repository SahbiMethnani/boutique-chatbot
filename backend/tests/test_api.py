
import pytest

from .. import api
from ..config import ALLOWED_ORIGINS
class TestRoot:
    def test_backend_actif(self, client, collection, groq, capture):
        r = client.get("/")
        capture("GET /", r)
        assert r.status_code == 200
        data = r.json()
        assert data["status"].strip() == "Backend actif"
        assert data["ia"].strip() == "Groq API"
        assert data["database"] == "8 produits"


    def test_base_vide(self, client, collection_vide, groq, capture):
        r = client.get("/")
        capture("GET / base vide", r)
        assert r.json()["database"] == "0 produits"
class TestAddProduct:
    def test_ajout_reussi(self, client, collection, produit_valide, capture):
        r = client.post("/add-product", json=produit_valide)
        capture("Ajout produit valide", r, base_apres_ajout=collection.count())
        assert r.status_code == 200
        assert "Casquette Bleue" in r.json()["message"]
        assert collection.count() == 9

    def test_id_et_metadonnees(self, client, collection, produit_valide, capture):
        r = client.post("/add-product", json=produit_valide)
        capture("Ajout : id et métadonnées", r, id=collection.ids[-1], metadonnees=collection.metadatas[-1])
        assert collection.ids[-1] == "product_Casquette_Bleue"
        assert collection.metadatas[-1] == {
            "nom": "Casquette Bleue",
            "prix": 25.5,
            "categorie": "Accessoires",
            "stock": 40,
        }

    def test_document_indexe(self, client, collection, produit_valide, capture):
        client.post("/add-product", json=produit_valide)
        doc = collection.documents[-1]
        capture("Document indexé", document=doc)
        assert "Produit: Casquette Bleue" in doc
        assert "Prix: 25.5 TND" in doc
        assert "Tailles disponibles: Unique" in doc
        assert "Couleurs disponibles: Bleu, Noir" in doc
        assert "Stock: 40 unités" in doc
    def test_erreur_chromadb(self, client, collection, produit_valide, capture):
        collection.add_error = RuntimeError("disque plein")
        r = client.post("/add-product", json=produit_valide)
        capture("Ajout avec erreur ChromaDB", r)
        assert r.status_code == 500
        assert "disque plein" in r.json()["detail"]

    @pytest.mark.parametrize("champ", ["nom", "description", "prix", "categorie", "tailles", "couleurs", "stock"])
    def test_champ_obligatoire_manquant(self, client, collection, produit_valide, champ, capture):
        del produit_valide[champ]
        r = client.post("/add-product", json=produit_valide)
        capture(f"Champ manquant : {champ}", r)
        assert r.status_code == 422
        assert any(champ in err["loc"] for err in r.json()["detail"])
        assert collection.count() == 8

    @pytest.mark.parametrize(
        "champ, valeur",
        [("prix", "gratuit"), ("stock", "beaucoup"), ("tailles", "M"), ("couleurs", 12)],
    )
    def test_type_invalide(self, client, collection, produit_valide, champ, valeur, capture):
        produit_valide[champ] = valeur
        r = client.post("/add-product", json=produit_valide)
        capture(f"Type invalide : {champ}={valeur!r}", r)
        assert r.status_code == 422
        assert collection.count() == 8

    @pytest.mark.parametrize("champ, valeur", [("prix", -10), ("stock", -1)])
    def test_valeurs_negatives_refusees(self, client, collection, produit_valide, champ, valeur, capture):
        produit_valide[champ] = valeur
        r = client.post("/add-product", json=produit_valide)
        capture(f"Valeur négative : {champ}={valeur}", r)
        assert r.status_code == 422
        assert collection.count() == 8

    def test_valeurs_zero_acceptees(self, client, collection, produit_valide, capture):
        produit_valide.update(prix=0, stock=0)
        r = client.post("/add-product", json=produit_valide)
        capture("Valeurs limites : prix=0, stock=0", r)
        assert r.status_code == 200
        assert collection.count() == 9

    def test_parametres_appel_llm(self, client, collection, groq, capture):
        client.post("/chat", json={"message": "Bonjour"})
        appel = groq.calls[0]
        capture("Paramètres Groq", model=appel["model"], temperature=appel["temperature"], max_tokens=appel["max_tokens"])
        roles = [m["role"] for m in appel["messages"]]
        assert roles == ["system", "user"]
        assert "boutique de vêtements" in appel["messages"][0]["content"]
        assert appel["temperature"] == 0.7
        assert appel["max_tokens"] == 500

    def test_contexte_produit_injecte(self, client, collection, groq, capture):
        r = client.post("/chat", json={"message": "Je cherche une veste"})
        capture("Chat avec contexte produit", r, prompt_envoye_a_groq=groq.prompt)
        assert "Question du client: Je cherche une veste" in groq.prompt
        assert "Produit: Veste cuir" in groq.prompt
        assert "Aucun produit spécifique" not in groq.prompt

    def test_aucun_produit_trouve(self, client, collection, groq, capture):
        r = client.post("/chat", json={"message": "xyzzy"})
        capture("Chat sans produit pertinent", r, prompt_envoye_a_groq=groq.prompt)
        assert r.status_code == 200
        assert "Aucun produit spécifique trouvé dans notre base." in groq.prompt

    def test_recherche_en_minuscules(self, client, collection, groq, capture):
        client.post("/chat", json={"message": "BONJOUR Tout Le Monde"})
        capture("Appel ChromaDB", appel=collection.query_calls[0])
        assert collection.query_calls[0] == (["bonjour tout le monde"], 3)

    def test_erreur_recherche_chromadb(self, client, collection, groq, capsys, capture):
        collection.query_error = RuntimeError("index corrompu")
        r = client.post("/chat", json={"message": "Bonjour"})
        capture("Chat avec erreur de recherche", r)
        assert r.status_code == 200
        assert r.json()["response"] == groq.reply
        assert "Aucun produit spécifique" in groq.prompt
        assert "Erreur recherche: index corrompu" in capsys.readouterr().out

    @pytest.mark.parametrize(
        "question, extrait",
        [
            ("Quels sont les délais de livraison ?", "Tunis: 2-3 jours (7 TND)"),
            ("La livraison est-elle gratuite ?", "GRATUITE à partir de 200 TND"),
            ("Puis-je retourner un article ?", "14 jours pour échanger"),
            ("Comment puis-je payer ?", "D17"),
        ],
    )
    def test_infos_boutique_dans_prompt(self, client, collection, groq, question, extrait, capture):
        r = client.post("/chat", json={"message": question})
        capture(f"Infos boutique : {question}", r, extrait_attendu=extrait)
        assert extrait in groq.prompt
    @pytest.mark.parametrize(
        "erreur, attendu",
        [
            (Exception("Invalid api_key provided"), "Clé API Groq invalide"),
            (Exception("rate_limit exceeded"), "Trop de requêtes"),
            (Exception("connexion interrompue"), "Erreur avec le service d'IA"),
        ],
    )
    def test_erreurs_groq(self, client, collection, groq, erreur, attendu, capture):
        groq.error = erreur
        r = client.post("/chat", json={"message": "Bonjour"})
        capture(f"Erreur Groq : {erreur}", r)
        assert r.status_code == 200
        assert attendu in r.json()["response"]

    """@pytest.mark.xfail(reason="Le détail technique de l'exception est renvoyé au client (fuite d'information)")
        
        def test_pas_de_fuite_du_detail_technique(self, client, collection, groq, capture):
        groq.error = Exception("secret interne: host=10.0.0.5")
        r = client.post("/chat", json={"message": "Bonjour"})
        capture("Fuite d'information", r)
        assert "10.0.0.5" not in r.json()["response"]
         """
    @pytest.mark.parametrize("corps", [{}, {"message": None}, {"msg": "Bonjour"}])
    def test_corps_invalide(self, client, collection, groq, corps, capture):
        r = client.post("/chat", json=corps)
        capture(f"Corps invalide : {corps}", r)
        assert r.status_code == 422
        assert groq.calls == []


class TestProducts:
    def test_liste_complete(self, client, collection, capture):
        r = client.get("/products")
        capture("Liste des produits", r)
        data = r.json()
        assert r.status_code == 200
        assert data["count"] == 8
        premier = data["products"][0]
        assert set(premier) == {"id", "nom", "prix", "categorie", "stock", "document"}
        assert premier["id"] == "product_Robe_fleurie"
        assert premier["nom"] == "Robe fleurie"

    def test_base_vide(self, client, collection_vide, capture):
        r = client.get("/products")
        capture("Liste vide", r)
        assert r.json() == {"count": 0, "products": []}



    def test_erreur_lecture(self, client, collection, capture):
        collection.get_error = RuntimeError("lecture impossible")
        r = client.get("/products")
        capture("Liste avec erreur", r)
        assert r.json()["error"] == "lecture impossible"
        assert r.json()["count"] == 0
class TestCors:
    def test_origine_frontend_autorisee(self, client, capture):
        origine = ALLOWED_ORIGINS[0]
        r = client.options(
            "/chat",
            headers={"Origin": origine, "Access-Control-Request-Method": "POST"},
        )
        capture("Préflight origine autorisée", statut=r.status_code, en_tetes=dict(r.headers))
        assert r.status_code == 200
        assert r.headers["access-control-allow-origin"] == origine

    def test_origine_inconnue_refusee(self, client, capture):
        r = client.options(
            "/chat",
            headers={"Origin": "http://site-malveillant.com", "Access-Control-Request-Method": "POST"},
        )
        capture("Préflight origine refusée", statut=r.status_code, en_tetes=dict(r.headers))
        assert "access-control-allow-origin" not in r.headers



def test_parcours_complet(client, collection, groq, produit_valide, capture):
    ajout = client.post("/add-product", json=produit_valide)
    liste = client.get("/products")
    chat = client.post("/chat", json={"message": "Avez-vous une casquette ?"})
    capture("1. Ajout", ajout)
    capture("2. Liste", liste, nb_produits=liste.json()["count"])
    capture("3. Chat", chat, prompt_envoye_a_groq=groq.prompt)

    assert ajout.status_code == 200
    assert liste.json()["count"] == 9
    assert "Casquette Bleue" in [p["nom"] for p in liste.json()["products"]]
    assert "Produit: Casquette Bleue" in groq.prompt
    assert chat.json()["response"] == groq.reply