import hashlib
from typing import Any

from config import (
    PINECONE_API_KEY,
    PINECONE_INDEX_NAME,
    PINECONE_NAMESPACE,
)

PINECONE_UPSERT_BATCH_SIZE = 90


def _field(value: Any, name: str, default: Any = None) -> Any:
    if isinstance(value, dict):
        return value.get(name, default)
    return getattr(value, name, default)


def make_pinecone_document(
    vector_id: str,
    document: str,
    metadata: dict,
    embed_field: str,
    title_field: str | None,
) -> dict:
    record = dict(metadata)
    record["_id"] = pinecone_safe_id(vector_id)
    record[embed_field] = document
    if title_field:
        record[title_field] = metadata.get("nom") or vector_id
    return record


def pinecone_safe_id(vector_id: str) -> str:
    try:
        vector_id.encode("ascii")
    except UnicodeEncodeError:
        digest = hashlib.sha256(vector_id.encode("utf-8")).hexdigest()
        return f"product_unicode_{digest}"
    return vector_id


class PineconeCollection:
    def __init__(
        self,
        index: Any,
        embed_field: str,
        dimension: int,
        title_field: str | None = None,
        namespace: str = PINECONE_NAMESPACE,
    ):
        self.index = index
        self.namespace = namespace
        self.embed_field = embed_field
        self.dimension = dimension
        self.title_field = title_field

    def count(self) -> int:
        stats = self.index.describe_index_stats()
        namespaces = _field(stats, "namespaces", {}) or {}
        namespace_stats = namespaces.get(self.namespace)
        return _field(namespace_stats, "vector_count", 0) if namespace_stats else 0

    def add(self, documents: list[str], metadatas: list[dict], ids: list[str]) -> None:
        if not (len(documents) == len(metadatas) == len(ids)):
            raise ValueError("Documents, métadonnées et identifiants doivent être alignés.")
        records = [
            make_pinecone_document(
                vector_id,
                document,
                metadata,
                self.embed_field,
                self.title_field,
            )
            for vector_id, document, metadata in zip(ids, documents, metadatas)
        ]
        self.index.documents.upsert(
            documents=records,
            namespace=self.namespace,
        )

    def query(self, query_texts: list[str], n_results: int = 3) -> dict:
        if not query_texts:
            raise ValueError("Au moins une question est nécessaire pour la recherche.")
        include_fields = [
            self.embed_field,
            self.title_field,
            "nom",
            "prix",
            "categorie",
            "stock",
        ]
        result = self.index.documents.search(
            score_by=[
                {
                    "type": "embed",
                    "fields": [self.embed_field],
                    "query": query_texts[0],
                }
            ],
            top_k=n_results,
            include_fields=list(
                dict.fromkeys(field for field in include_fields if field)
            ),
            namespace=self.namespace,
        )
        matches = _field(result, "matches", []) or []
        metadatas = []
        documents = []
        for match in matches:
            fields = match.to_dict() if hasattr(match, "to_dict") else dict(match)
            fields.pop("_id", None)
            fields.pop("_score", None)
            documents.append(fields.get(self.embed_field, ""))
            fields["document"] = fields.get(self.embed_field, "")
            metadatas.append(fields)
        return {
            "documents": [documents],
            "metadatas": [metadatas],
        }

    def get(self) -> dict:
        ids = []
        ids.extend(
            _field(record, "id")
            for record in self.index.documents.list(namespace=self.namespace)
        )

        vectors = {}
        for start in range(0, len(ids), 100):
            response = self.index.documents.fetch(
                ids=ids[start : start + 100],
                namespace=self.namespace,
            )
            vectors.update(_field(response, "documents", {}))

        ordered_ids = [vector_id for vector_id in ids if vector_id in vectors]
        records = [
            vectors[vector_id].to_dict()
            if hasattr(vectors[vector_id], "to_dict")
            else dict(vectors[vector_id])
            for vector_id in ordered_ids
        ]
        metadatas = []
        documents = []
        for record in records:
            record.pop("_id", None)
            document = record.get(self.embed_field, "")
            record["document"] = document
            documents.append(document)
            metadatas.append(record)
        return {
            "ids": ordered_ids,
            "metadatas": metadatas,
            "documents": documents,
        }

    def reset(self) -> None:
        self.index.documents.delete(delete_all=True, namespace=self.namespace)


def create_pinecone_collection() -> PineconeCollection | None:
    if not PINECONE_API_KEY or not PINECONE_INDEX_NAME:
        return None

    from pinecone import Pinecone

    client = Pinecone(api_key=PINECONE_API_KEY)
    index = client.Index(PINECONE_INDEX_NAME)
    description = client.describe_index(PINECONE_INDEX_NAME)
    schema_fields = _field(_field(description, "schema"), "fields", {}) or {}
    embedding_fields = {
        name: _field(field, "embed")
        for name, field in schema_fields.items()
        if _field(field, "embed")
    }
    if len(embedding_fields) != 1:
        raise ValueError(
            "L'index Pinecone doit déclarer exactement un champ string avec "
            "l'embedding intégré pour la recherche sémantique."
        )
    embed_field, embedding_config = next(iter(embedding_fields.items()))
    dimension = _field(embedding_config, "dimension")
    if not dimension:
        raise ValueError(
            f"Le champ d'embedding Pinecone {embed_field!r} n'a pas de dimension "
            "configurée."
        )
    metric = _field(embedding_config, "metric")
    if metric and metric != "cosine":
        raise ValueError(
            f"Le champ d'embedding Pinecone doit utiliser la métrique cosine "
            f"(métrique actuelle : {metric})."
        )
    return PineconeCollection(
        index,
        embed_field=embed_field,
        dimension=dimension,
        title_field="title" if "title" in schema_fields else None,
    )
