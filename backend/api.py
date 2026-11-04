import csv
import hmac
import io
import unicodedata

from fastapi import APIRouter, File, Header, HTTPException, UploadFile
from groq import Groq
from config import ADMIN_API_KEY, GROQ_API_KEY, MODEL_NAME
from model import Product, Message
from pydantic import ValidationError
from vector_store import (
    PINECONE_UPSERT_BATCH_SIZE,
    create_pinecone_collection,
    pinecone_safe_id,
)
router = APIRouter()

MAX_CSV_BYTES = 5 * 1024 * 1024
MAX_CSV_ROWS = 90
MAX_CSV_FILE_ROWS = 2000
CSV_COLUMNS = {
    "nom",
    "description",
    "prix",
    "categorie",
    "tailles",
    "couleurs",
    "stock",
}
if not GROQ_API_KEY:
    print("GROQ_API_KEY non trouvée")
    print("   Créez un fichier et mettre la clef la-bas")
    groq_client = None
else:
    try:
        groq_client = Groq(api_key=GROQ_API_KEY)
        print("Groq API initialisée")
    except Exception as e:
        print(f"Erreur Groq: {e}")
        groq_client = None

collection = create_pinecone_collection()
if collection:
    print(f"Collection Pinecone chargée avec {collection.count()} produits")
else:
    print("Pinecone non configuré : ajoutez PINECONE_API_KEY et PINECONE_INDEX_NAME au .env")

@router.get("/")
def read_root():
    status = {
        "status": "Backend actif ",
        "ia": "Groq API " if groq_client else "Groq non configurée",
        "database": f"{collection.count()} produits" if collection else "Pinecone non configuré"
    }
    return status

@router.post("/add-product")
def add_product(product: Product):
    if not collection:
        raise HTTPException(status_code=500, detail="Base de données non initialisée")

    if product.prix < 0:
        raise HTTPException(status_code=422, detail="Le prix ne peut pas être négatif")
    if product.stock < 0:
        raise HTTPException(status_code=422, detail="Le stock ne peut pas être négatif")

    document = f"""
Produit: {product.nom}
Catégorie: {product.categorie}
Description: {product.description}
Prix: {product.prix} TND
Tailles disponibles: {', '.join(product.tailles)}
Couleurs disponibles: {', '.join(product.couleurs)}
Stock: {product.stock} unités
    """.strip()

    try:
        collection.add(
            documents=[document],
            metadatas=[{
                "nom": product.nom,
                "prix": product.prix,
                "categorie": product.categorie,
                "stock": product.stock
            }],
            ids=[pinecone_safe_id(f"product_{product.nom.replace(' ', '_')}")]
        )
        return {"message": f" Produit '{product.nom}' ajouté avec succès"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur: {str(e)}")


@router.post("/admin/import-products-csv")
async def import_products_csv(
    file: UploadFile = File(...),
    x_admin_key: str | None = Header(default=None, alias="X-Admin-Key"),
):
    if not ADMIN_API_KEY:
        raise HTTPException(
            status_code=503,
            detail=(
                "L'import administrateur est désactivé : configurez "
                "ADMIN_API_KEY dans backend/.env."
            ),
        )
    if not x_admin_key or not hmac.compare_digest(
        x_admin_key.encode("utf-8"), ADMIN_API_KEY.encode("utf-8")
    ):
        raise HTTPException(status_code=401, detail="Clé administrateur invalide.")
    if not collection:
        raise HTTPException(status_code=503, detail="Pinecone n'est pas configuré.")
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Sélectionnez un fichier .csv.")

    content = await file.read(MAX_CSV_BYTES + 1)
    if len(content) > MAX_CSV_BYTES:
        raise HTTPException(
            status_code=413,
            detail="Le fichier CSV dépasse la limite de 5 Mo.",
        )
    try:
        csv_text = content.decode("utf-8-sig")
    except UnicodeDecodeError as error:
        raise HTTPException(
            status_code=400,
            detail="Le fichier doit être encodé en UTF-8 ou UTF-8 avec BOM.",
        ) from error

    try:
        dialect = csv.Sniffer().sniff(csv_text[:4096], delimiters=",;\t")
    except csv.Error:
        dialect = csv.excel

    reader = csv.DictReader(io.StringIO(csv_text), dialect=dialect)
    headers = [header.strip().casefold() for header in (reader.fieldnames or [])]
    if not headers:
        raise HTTPException(status_code=422, detail="Le fichier CSV est vide.")
    if len(headers) != len(set(headers)):
        raise HTTPException(
            status_code=422,
            detail="Le fichier contient des colonnes en double.",
        )
    missing_columns = sorted(CSV_COLUMNS - set(headers))
    if missing_columns:
        raise HTTPException(
            status_code=422,
            detail=f"Colonnes manquantes : {', '.join(missing_columns)}.",
        )

    products = []
    errors = []
    seen_names = set()
    for row_number, raw_row in enumerate(reader, start=2):
        if row_number > MAX_CSV_FILE_ROWS + 1:
            errors.append(
                {
                    "row": row_number,
                    "error": f"Le fichier dépasse {MAX_CSV_FILE_ROWS} lignes.",
                }
            )
            break
        if None in raw_row:
            errors.append(
                {"row": row_number, "error": "La ligne contient trop de colonnes."}
            )
            continue

        row = {
            (key or "").strip().casefold(): (value or "").strip()
            for key, value in raw_row.items()
        }
        if not any(row.values()):
            continue
        if dialect.delimiter != ",":
            row["prix"] = row["prix"].replace(",", ".")
        for field in ("tailles", "couleurs"):
            row[field] = [
                value.strip()
                for value in row[field].split("|")
                if value.strip()
            ]
        try:
            product = Product.model_validate(row)
        except ValidationError as error:
            detail = error.errors()
            message = "; ".join(
                f"{'.'.join(str(part) for part in item['loc'])}: {item['msg']}"
                for item in detail
            ) or "Données produit invalides."
            errors.append({"row": row_number, "error": message})
            continue

        normalized_name = unicodedata.normalize("NFC", product.nom).casefold()
        if normalized_name in seen_names:
            errors.append(
                {
                    "row": row_number,
                    "error": (
                        f"Le produit « {product.nom} » est en double dans le fichier."
                    ),
                }
            )
            continue
        seen_names.add(normalized_name)
        products.append(product)

    if errors:
        raise HTTPException(
            status_code=422,
            detail={
                "message": "Aucun produit importé : corrigez les lignes signalées.",
                "errors": errors[:25],
                "truncated": len(errors) > 25,
            },
        )
    if not products:
        raise HTTPException(
            status_code=422,
            detail="Le fichier ne contient aucun produit à importer.",
        )

    try:
        for start in range(0, len(products), PINECONE_UPSERT_BATCH_SIZE):
            batch = products[start : start + PINECONE_UPSERT_BATCH_SIZE]
            documents = [
                f"""Produit: {product.nom}
Catégorie: {product.categorie}
Description: {product.description}
Prix: {product.prix} TND
Tailles disponibles: {', '.join(product.tailles)}
Couleurs disponibles: {', '.join(product.couleurs)}
Stock: {product.stock} unités"""
                for product in batch
            ]
            metadatas = [
                {
                    "nom": product.nom,
                    "prix": product.prix,
                    "categorie": product.categorie,
                    "stock": product.stock,
                }
                for product in batch
            ]
            ids = [
                pinecone_safe_id(f"product_{product.nom.replace(' ', '_')}")
                for product in batch
            ]
            collection.add(documents=documents, metadatas=metadatas, ids=ids)
    except Exception as error:
        imported = start
        print(f"Erreur import CSV Pinecone après {imported} produits : {error}")
        raise HTTPException(
            status_code=502,
            detail={
                "message": "Pinecone a interrompu l'import.",
                "imported": imported,
                "total": len(products),
                "error": str(error),
            },
        ) from error

    return {
        "message": f"{len(products)} produits importés avec succès.",
        "imported": len(products),
    }


@router.post("/chat")
def chat(message: Message):
    
    if not collection:
        return {
            "response": "Pinecone non configuré. Ajoutez PINECONE_API_KEY et "
            "PINECONE_INDEX_NAME au fichier .env."
        }
    
    if not groq_client:
        return {"response": "Groq API non configurée. Vérifiez votre fichier .env avec GROQ_API_KEY"}
    
    user_message = message.message
    
    try:
        results = collection.query(
            query_texts=[user_message.lower()],
            n_results=3
        )
    except Exception as e:
        print(f"Erreur recherche: {e}")
        results = {'documents': [[]], 'metadatas': [[]]}
    
    context = ""
    if results['documents'] and results['documents'][0]:
        context = "\n\n".join(results['documents'][0])
    
    boutique_info = """
Boutique de vêtements en Tunisie.

LIVRAISON:
- Tunis: 2-3 jours (7 TND)
- Autres gouvernorats: 3-5 jours (10 TND)
- Livraison GRATUITE à partir de 200 TND

RETOURS: 14 jours pour échanger ou retourner (produits non portés avec étiquettes)

PAIEMENT: 
- À la livraison (Cash)
- Carte bancaire en ligne
- D17

SERVICE CLIENT: +21658895123 (Lun-Sam 9h-18h)
    """
    
    user_prompt = f"""Question du client: {user_message}

Informations sur la boutique:
{boutique_info}

Produits pertinents trouvés:
{context if context else "Aucun produit spécifique trouvé dans notre base."}

Réponds de manière amicale, professionnelle et en français. Sois concis mais utile."""

    try:
        chat_completion = groq_client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": "Tu es un assistant virtuel sympathique pour une boutique de vêtements en Tunisie. Tu réponds toujours en français de manière amicale et professionnelle."
                },
                {
                    "role": "user",
                    "content": user_prompt
                }
            ],
            model=MODEL_NAME,
            temperature=0.7,
            max_tokens=500,
            top_p=1
        )
        
        response_text = chat_completion.choices[0].message.content
        return {"response": response_text}
    
    except Exception as e:
        error_msg = str(e)
        #print(f"Erreur Groq API: {error_msg}")
        print(f"Erreur Groq API")

        
        
        if "api_key" in error_msg.lower():
            return {"response": "Clé API Groq invalide. Vérifiez votre fichier .env"}
        elif "rate_limit" in error_msg.lower():
            return {"response": "Trop de requêtes. Veuillez patienter quelques secondes."}
        else:
            return {"response": f"Erreur avec le service d'IA. Contactez +216 XX XXX XXX. "}#(Détails: {error_msg})}

@router.get("/products")
def list_products():
    if not collection:
        return {"count": 0, "products": [], "message": "Base non initialisée"}
    
    try:
        all_items = collection.get()
        products = []
        
        if all_items['metadatas']:
            for i, metadata in enumerate(all_items['metadatas']):
                products.append({
                    "id": all_items['ids'][i],
                    "nom": metadata.get('nom'),
                    "prix": metadata.get('prix'),
                    "categorie": metadata.get('categorie'),
                    "stock": metadata.get('stock'),
                    "document": all_items['documents'][i] if all_items['documents'] else ""
                })
        
        return {"count": len(products), "products": products}
    
    except Exception as e:
        return {"error": str(e), "count": 0, "products": []}

@router.delete("/reset-database")
def reset_database():
    if not collection:
        raise HTTPException(
            status_code=503,
            detail="Pinecone non configuré. Vérifiez le fichier .env.",
        )
    try:
        collection.reset()
        return {"message": "Base de données Pinecone réinitialisée avec succès"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur: {str(e)}")
