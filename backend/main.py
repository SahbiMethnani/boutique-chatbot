from fastapi import FastAPI

from config import GROQ_API_KEY
from cors import setup_cors
from api import router

app = FastAPI()

setup_cors(app)
app.include_router(router)

if __name__ == "__main__":
    import uvicorn

    if not GROQ_API_KEY:
        print("Obtenez une clé sur: https://console.groq.com\n")

    uvicorn.run(app, port=8000)