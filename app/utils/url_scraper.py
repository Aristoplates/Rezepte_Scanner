"""Rezepte aus Webseiten laden.

Zuerst wird versucht, strukturierte schema.org/Recipe-Daten (JSON-LD) aus der
Seite zu lesen — schnell, kostenlos und exakt. Findet sich kein JSON-LD, wird
der bereinigte Seitentext als Fallback an das LLM übergeben.
"""
import json
import re
from typing import Optional

import requests
from bs4 import BeautifulSoup

from app.models.recipe import Ingredient, Recipe

_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"
)

# Maximale Textlänge, die an das LLM übergeben wird (Token-Kosten begrenzen).
_MAX_TEXT_CHARS = 16000


def fetch_html(url: str) -> str:
    """Lade den HTML-Inhalt einer URL."""
    response = requests.get(url, headers={"User-Agent": _USER_AGENT}, timeout=10)
    response.raise_for_status()
    return response.text


def _iter_jsonld_objects(data):
    """Alle JSON-LD-Objekte flach durchlaufen (inkl. Listen und @graph)."""
    if isinstance(data, list):
        for item in data:
            yield from _iter_jsonld_objects(item)
    elif isinstance(data, dict):
        if "@graph" in data and isinstance(data["@graph"], list):
            for item in data["@graph"]:
                yield from _iter_jsonld_objects(item)
        yield data


def _is_recipe_type(obj: dict) -> bool:
    type_value = obj.get("@type")
    if isinstance(type_value, list):
        return any(str(t).lower() == "recipe" for t in type_value)
    return str(type_value).lower() == "recipe"


def extract_jsonld_recipe(html: str) -> Optional[dict]:
    """Suche das schema.org/Recipe-Objekt in den JSON-LD-Blöcken der Seite."""
    soup = BeautifulSoup(html, "html.parser")
    for script in soup.find_all("script", type="application/ld+json"):
        raw = script.string or script.get_text()
        if not raw:
            continue
        try:
            data = json.loads(raw)
        except (json.JSONDecodeError, ValueError):
            continue
        for obj in _iter_jsonld_objects(data):
            if _is_recipe_type(obj):
                return obj
    return None


def _iso_duration_to_text(value) -> Optional[str]:
    """Wandle eine ISO-8601-Dauer (z.B. 'PT1H30M') in lesbaren Text um."""
    if not value or not isinstance(value, str):
        return None
    match = re.match(
        r"P(?:(\d+)D)?T?(?:(\d+)H)?(?:(\d+)M)?", value.strip(), re.IGNORECASE
    )
    if not match or not any(match.groups()):
        return value  # kein ISO-Format — Originalwert behalten
    days, hours, minutes = (int(g) if g else 0 for g in match.groups())
    hours += days * 24
    parts = []
    if hours:
        parts.append(f"{hours} Std")
    if minutes:
        parts.append(f"{minutes} Min")
    return " ".join(parts) if parts else value


def parse_ingredient(line: str) -> Ingredient:
    """Zerlege eine Zutatenzeile in Menge und Name.

    Heuristik: Enthält das erste Token eine Ziffer, gilt es als Menge.
    """
    line = line.strip()
    parts = line.split(" ", 1)
    if len(parts) == 2 and any(c.isdigit() for c in parts[0]):
        return Ingredient(amount=parts[0], name=parts[1].strip())
    return Ingredient(name=line)


def _extract_servings(value) -> Optional[int]:
    """Extrahiere die Portionszahl aus recipeYield (Zahl, String oder Liste)."""
    if isinstance(value, list):
        value = value[0] if value else None
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return int(value)
    match = re.search(r"\d+", str(value))
    return int(match.group()) if match else None


def _extract_instructions(value) -> list[str]:
    """Normalisiere recipeInstructions in eine flache Liste von Schritten."""
    steps: list[str] = []

    def _handle(item):
        if isinstance(item, str):
            text = item.strip()
            if text:
                steps.append(text)
        elif isinstance(item, dict):
            item_type = str(item.get("@type", "")).lower()
            if item_type == "howtosection" and isinstance(
                item.get("itemListElement"), list
            ):
                for sub in item["itemListElement"]:
                    _handle(sub)
            else:
                text = (item.get("text") or item.get("name") or "").strip()
                if text:
                    steps.append(text)
        elif isinstance(item, list):
            for sub in item:
                _handle(sub)

    if isinstance(value, str):
        # Einzelner Textblock — an Zeilenumbrüchen aufteilen.
        steps.extend(s.strip() for s in value.splitlines() if s.strip())
    else:
        _handle(value)
    return steps


def _extract_tags(data: dict) -> list[str]:
    tags: list[str] = []
    for key in ("recipeCategory", "recipeCuisine", "keywords"):
        value = data.get(key)
        if not value:
            continue
        if isinstance(value, list):
            tags.extend(str(v).strip() for v in value if str(v).strip())
        else:
            tags.extend(t.strip() for t in str(value).split(",") if t.strip())
    # Duplikate entfernen, Reihenfolge beibehalten.
    seen = set()
    unique = []
    for tag in tags:
        if tag.lower() not in seen:
            seen.add(tag.lower())
            unique.append(tag)
    return unique


def jsonld_to_recipe(data: dict, source_url: str) -> Recipe:
    """Wandle ein schema.org/Recipe-JSON-LD-Objekt in ein Recipe-Modell um."""
    name = data.get("name") or "Unbenanntes Rezept"
    if isinstance(name, list):
        name = name[0] if name else "Unbenanntes Rezept"

    raw_ingredients = data.get("recipeIngredient") or data.get("ingredients") or []
    if isinstance(raw_ingredients, str):
        raw_ingredients = [raw_ingredients]
    ingredients = [
        parse_ingredient(str(i)) for i in raw_ingredients if str(i).strip()
    ]

    instructions = _extract_instructions(data.get("recipeInstructions"))

    return Recipe(
        title=str(name).strip(),
        servings=_extract_servings(data.get("recipeYield")),
        prep_time=_iso_duration_to_text(data.get("prepTime")),
        cook_time=_iso_duration_to_text(data.get("cookTime")),
        total_time=_iso_duration_to_text(data.get("totalTime")),
        ingredients=ingredients,
        instructions=instructions,
        tags=_extract_tags(data),
        notes=None,
        source=source_url,
    )


def html_to_text(html: str) -> str:
    """Extrahiere sichtbaren Seitentext für den LLM-Fallback."""
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
        tag.decompose()
    text = soup.get_text(separator="\n")
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    cleaned = "\n".join(lines)
    return cleaned[:_MAX_TEXT_CHARS]


def extract_recipe_from_url(url: str, use_ollama: bool = False) -> Recipe:
    """Lade ein Rezept von einer URL.

    Zuerst JSON-LD (schema.org/Recipe), sonst LLM-Fallback über den Seitentext.
    """
    html = fetch_html(url)

    jsonld = extract_jsonld_recipe(html)
    if jsonld:
        recipe = jsonld_to_recipe(jsonld, url)
        # Nur akzeptieren, wenn das JSON-LD tatsächlich brauchbare Daten enthält.
        if recipe.ingredients or recipe.instructions:
            return recipe

    # Fallback: bereinigten Text vom LLM auslesen lassen.
    from app.chains.recipe_chain import build_recipe_url_chain

    chain = build_recipe_url_chain(use_ollama=use_ollama)
    recipe = chain(html_to_text(html))
    recipe.source = url
    return recipe
