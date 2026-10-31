import chromadb
from fastapi import APIRouter, HTTPException
from groq import Groq
from config import GROQ_API_KEY
from model import Product, Message
router = APIRouter()
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

chroma_client = chromadb.PersistentClient(path="./chroma_db")

try:
    collection = chroma_client.get_collection("boutique_vetements")
    print(f"Collection chargée avec {collection.count()} produits")
except Exception as e:
    print(f"Erreur Collection: {e}")
    collection = None

@router.get("/")
def read_root():
    status = {
        "status": "Backend actif ",
        "ia": "Groq API " if groq_client else "Groq non configurée",
        "database": f"{collection.count()} produits" if collection else " Attention!!! : Non initialisée"
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
            ids=[f"product_{product.nom.replace(' ', '_')}"]
        )
        return {"message": f" Produit '{product.nom}' ajouté avec succès"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur: {str(e)}")

@router.post("/chat")
def chat(message: Message):
    
    if not collection:
        return {"response": "Base de données non initialisée. Exécutez setup.py"}
    
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
            model="openai/gpt-oss-safeguard-20b",  
            temperature=0.7,
            max_tokens=500,
            top_p=1
        )
        
        response_text = chat_completion.choices[0].message.content
        return {"response": response_text}
    
    except Exception as e:
        error_msg = str(e)
        print(f"Erreur Groq API: {error_msg}")
        
        if "api_key" in error_msg.lower():
            return {"response": "Clé API Groq invalide. Vérifiez votre fichier .env"}
        elif "rate_limit" in error_msg.lower():
            return {"response": "Trop de requêtes. Veuillez patienter quelques secondes."}
        else:
            return {"response": f"Erreur avec le service d'IA. Contactez +216 XX XXX XXX. (Détails: {error_msg})"}

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
    global collection
    try:
        chroma_client.delete_collection("boutique_vetements")
        collection = chroma_client.create_collection("boutique_vetements")
        return {"message": "Base de données réinitialisée avec succès"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur: {str(e)}")
