from pydantic import BaseModel, Field
from typing import List
class Message(BaseModel):
    message: str

class Product(BaseModel):
    nom: str = Field(min_length=1)
    description: str
    prix: float = Field(ge=0)
    categorie: str
    tailles: List[str]
    couleurs: List[str]
    stock: int = Field(ge=0)