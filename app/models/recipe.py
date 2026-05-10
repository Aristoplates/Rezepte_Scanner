from pydantic import BaseModel, Field
from typing import Optional

class Ingredient(BaseModel):
    name: str = Field(description="Name der Zutat")
    amount: Optional[str] = Field(default=None, description="Menge, z.B. '200g', '2 EL', '1 Prise'")

class Recipe(BaseModel):
    title: str = Field(description="Titel des Rezepts")
    servings: Optional[int] = Field(default=None, description="Anzahl der Portionen")
    prep_time: Optional[str] = Field(default=None, description="Vorbereitungszeit")
    cook_time: Optional[str] = Field(default=None, description="Koch-/Backzeit, z.B. '30 Minuten'")
    total_time: Optional[str] = Field(default=None, description="Gesamtzeit")
    ingredients: list[Ingredient] = Field(description="Liste der Zutaten")
    instructions: list[str] = Field(description="Zubereitungsschritte als geordnete Liste")
    tags: list[str] = Field(
        default_factory=list,
        description="Kategorien, wie 'Vegetarisch', 'Kuchen', 'Schnell', 'Italienisch', etc."
    )
    notes: Optional[str] = Field(default=None, description="Zusätzliche Hinweise oder Tipps")
    source: Optional[str] = Field(default=None, description="Quelle des Rezepts, falls erkennbar")