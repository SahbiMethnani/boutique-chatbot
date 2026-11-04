from chromadb import PersistentClient
from pinecone import Pinecone

from config import (
    PINECONE_API_KEY,
    PINECONE_INDEX_NAME,
    PINECONE_NAMESPACE,
)
from vector_store import (
    PINECONE_UPSERT_BATCH_SIZE,
    _field,
    make_pinecone_document,
)


def main() -> None:
    if not PINECONE_API_KEY or not PINECONE_INDEX_NAME:
        raise SystemExit(
            "Configurez PINECONE_API_KEY et PINECONE_INDEX_NAME dans backend/.env."
        )

    chroma = PersistentClient(path="./chroma_db")
    collection = chroma.get_collection("boutique_vetements")
    data = collection.get(
        include=["documents", "metadatas"],
    )
    if not data["ids"]:
        raise SystemExit("La collection Chroma boutique_vetements est vide.")
    if any(
        values is None or len(values) != len(data["ids"])
        for values in (data["documents"], data["metadatas"])
    ):
        raise RuntimeError("La collection Chroma contient des données incomplètes.")

    pinecone = Pinecone(api_key=PINECONE_API_KEY)
    description = pinecone.describe_index(PINECONE_INDEX_NAME)
    schema_fields = _field(_field(description, "schema"), "fields", {}) or {}
    embedding_fields = {
        name: _field(field, "embed")
        for name, field in schema_fields.items()
        if _field(field, "embed")
    }
    if len(embedding_fields) != 1:
        raise SystemExit(
            "L'index Pinecone doit déclarer exactement un champ string avec "
            "l'embedding intégré. Aucun produit n'a été transféré."
        )
    embed_field = next(iter(embedding_fields))
    title_field = "title" if "title" in schema_fields else None

    index = pinecone.Index(PINECONE_INDEX_NAME)
    batch_size = PINECONE_UPSERT_BATCH_SIZE
    for start in range(0, len(data["ids"]), batch_size):
        end = start + batch_size
        records = [
            make_pinecone_document(
                vector_id,
                document,
                metadata or {},
                embed_field,
                title_field,
            )
            for vector_id, document, metadata in zip(
            data["ids"][start:end],
            data["documents"][start:end],
            data["metadatas"][start:end],
            )
        ]
        index.documents.upsert(
            documents=records,
            namespace=PINECONE_NAMESPACE,
        )
        print(f"{min(end, len(data['ids']))}/{len(data['ids'])} produits transférés")

    stats = index.describe_index_stats()
    namespace_stats = (stats.namespaces or {}).get(PINECONE_NAMESPACE)
    pinecone_count = namespace_stats.vector_count if namespace_stats else 0
    if pinecone_count < len(data["ids"]):
        raise RuntimeError(
            f"Transfert incomplet : {pinecone_count}/{len(data['ids'])} produits "
            "présents dans l'espace de noms Pinecone."
        )
    print(
        f"Migration terminée : {len(data['ids'])} produits dans Pinecone "
        f"(espace de noms {PINECONE_NAMESPACE!r}). Pinecone a généré de nouveaux "
        "embeddings à partir des textes. Le dossier Chroma est conservé."
    )


if __name__ == "__main__":
    main()
