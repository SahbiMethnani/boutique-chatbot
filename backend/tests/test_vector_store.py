from types import SimpleNamespace

from .. import migrate_chroma_to_pinecone, vector_store


class FakeDocuments:
    def __init__(self, index):
        self.index = index
        self.search_kwargs = None

    def upsert(self, documents, namespace):
        self.index.namespace = namespace
        self.index.documents_by_id.update(
            {document["_id"]: document for document in documents}
        )

    def search(self, **kwargs):
        self.search_kwargs = kwargs
        document = next(iter(self.index.documents_by_id.values()))
        return SimpleNamespace(
            matches=[SimpleNamespace(to_dict=lambda: dict(document))]
        )

    def list(self, namespace):
        assert namespace == self.index.namespace
        return [
            SimpleNamespace(id=vector_id)
            for vector_id in self.index.documents_by_id
        ]

    def fetch(self, ids, namespace):
        assert namespace == self.index.namespace
        return SimpleNamespace(
            documents={
                vector_id: SimpleNamespace(
                    to_dict=lambda vector_id=vector_id: dict(
                        self.index.documents_by_id[vector_id]
                    )
                )
                for vector_id in ids
            }
        )

    def delete(self, delete_all, namespace):
        self.index.deleted = (delete_all, namespace)
        if delete_all and namespace == self.index.namespace:
            self.index.documents_by_id.clear()


class FakeIndex:
    def __init__(self):
        self.documents_by_id = {}
        self.namespace = None
        self.deleted = None
        self.documents = FakeDocuments(self)

    def describe_index_stats(self):
        return SimpleNamespace(
            namespaces={
                self.namespace: SimpleNamespace(
                    vector_count=len(self.documents_by_id)
                )
            }
            if self.namespace
            else {}
        )


def test_pinecone_collection_operations():
    index = FakeIndex()
    collection = vector_store.PineconeCollection(
        index,
        embed_field="chunk_text",
        dimension=384,
        title_field="title",
        namespace="boutique-vetements",
    )
    collection.add(
        documents=["Produit: Robe"],
        metadatas=[{"nom": "Robe", "prix": 89.9}],
        ids=["product_Robe"],
    )

    assert collection.count() == 1
    assert index.documents_by_id["product_Robe"] == {
        "_id": "product_Robe",
        "chunk_text": "Produit: Robe",
        "nom": "Robe",
        "prix": 89.9,
        "title": "Robe",
    }
    assert collection.query(["robe"], n_results=3) == {
        "documents": [["Produit: Robe"]],
        "metadatas": [[
            {
                "chunk_text": "Produit: Robe",
                "nom": "Robe",
                "prix": 89.9,
                "title": "Robe",
                "document": "Produit: Robe",
            }
        ]],
    }
    assert index.documents.search_kwargs["score_by"] == [
        {
            "type": "embed",
            "fields": ["chunk_text"],
            "query": "robe",
        }
    ]
    assert collection.get()["ids"] == ["product_Robe"]

    collection.reset()
    assert index.deleted == (True, "boutique-vetements")
    assert collection.count() == 0


def test_migration_transfers_documents_for_integrated_embedding(monkeypatch, capsys):
    source = {
        "ids": ["product_Robe"],
        "documents": ["Produit: Robe"],
        "metadatas": [{"nom": "Robe", "prix": 89.9}],
    }
    fake_index = FakeIndex()

    class FakeChromaCollection:
        def get(self, include):
            assert include == ["documents", "metadatas"]
            return source

    class FakePinecone:
        def __init__(self, api_key):
            assert api_key == "test-key"

        def describe_index(self, index_name):
            assert index_name == "test-index"
            return SimpleNamespace(
                schema=SimpleNamespace(
                    fields={
                        "title": SimpleNamespace(embed=None),
                        "chunk_text": SimpleNamespace(embed=SimpleNamespace()),
                    }
                )
            )

        def Index(self, index_name):
            return fake_index

    class FakeChromaClient:
        def __init__(self, path):
            assert path == "./chroma_db"

        def get_collection(self, name):
            assert name == "boutique_vetements"
            return FakeChromaCollection()

    monkeypatch.setattr(migrate_chroma_to_pinecone, "PersistentClient", FakeChromaClient)
    monkeypatch.setattr(migrate_chroma_to_pinecone, "Pinecone", FakePinecone)
    monkeypatch.setattr(migrate_chroma_to_pinecone, "PINECONE_API_KEY", "test-key")
    monkeypatch.setattr(migrate_chroma_to_pinecone, "PINECONE_INDEX_NAME", "test-index")
    monkeypatch.setattr(
        migrate_chroma_to_pinecone, "PINECONE_NAMESPACE", "boutique-vetements"
    )

    migrate_chroma_to_pinecone.main()

    assert fake_index.documents_by_id["product_Robe"] == {
        "_id": "product_Robe",
        "chunk_text": "Produit: Robe",
        "nom": "Robe",
        "prix": 89.9,
        "title": "Robe",
    }
    assert "Pinecone a généré de nouveaux embeddings" in capsys.readouterr().out


def test_pinecone_collection_requires_query_text():
    collection = vector_store.PineconeCollection(
        FakeIndex(),
        embed_field="chunk_text",
        dimension=384,
        namespace="boutique-vetements",
    )
    try:
        collection.query([])
    except ValueError as error:
        assert "question" in str(error)
    else:
        raise AssertionError("Une recherche sans texte doit échouer.")


def test_pinecone_ids_preserve_ascii_and_encode_unicode():
    assert vector_store.pinecone_safe_id("product_Casquette_Bleue") == (
        "product_Casquette_Bleue"
    )
    first = vector_store.pinecone_safe_id("product_Robe_d'été_Blanche")
    second = vector_store.pinecone_safe_id("product_Robe_d'été_Blanche")
    assert first == second
    assert first.isascii()
    assert len(first) < 512
