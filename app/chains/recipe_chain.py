import base64
import os
from pathlib import Path
from typing import Union

from langchain_core.messages import HumanMessage
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain_ollama import ChatOllama

from app.models.recipe import Recipe


def _encode_image(image_input: Union[str, bytes]) -> tuple[str, str]:
    """Encode image to base64. Returns (base64_data, media_type)."""
    if isinstance(image_input, bytes):
        data = image_input
    else:
        data = Path(image_input).read_bytes()

    # Detect image type from magic bytes
    if data[:4] == b'\x89PNG':
        media_type = "image/png"
    elif data[:2] == b'\xff\xd8':
        media_type = "image/jpeg"
    elif data[:4] == b'RIFF' or data[:4] == b'WEBP':
        media_type = "image/webp"
    else:
        media_type = "image/jpeg"   # fallback

    return base64.b64encode(data).decode("utf-8"), media_type


def build_recipe_chain(use_ollama: bool = False):
    """
    Build a LangChain chain for recipe extraction from images.
    
    Args:
        use_ollama: If True, use local Ollama (qwen3.5:0.8b model). Otherwise use OpenAI GPT-4o.
    """
    parser = PydanticOutputParser(pydantic_object=Recipe)

    if use_ollama:
        llm = ChatOllama(
            model=os.getenv("OLLAMA_MODEL", "qwen3.5:0.8b"),
            base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        )
    else:
        llm = ChatOpenAI(
            model="gpt-4o",
            api_key=os.getenv("OPENAI_API_KEY"),
            max_tokens=4096,
        )

    def extract_recipe(image_input: Union[str, bytes]) -> Recipe:
        """Extract recipe data from an image."""
        b64_data, media_type = _encode_image(image_input)

        format_instructions = parser.get_format_instructions()

        message = HumanMessage(
            content=[
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:{media_type};base64,{b64_data}",
                        "detail": "high",
                    },
                },
                {
                    "type": "text",
                    "text": f"""Du bist ein Experte für das Auslesen von Rezepten aus Fotos.
Analysiere das Bild und extrahiere alle Rezeptinformationen so vollständig und präzise wie möglich.

Wichtige Hinweise:
- Lies alle sichtbaren Zutaten mit Mengenangaben aus
- Erfasse alle Zubereitungsschritte in der richtigen Reihenfolge
- Falls Informationen nicht erkennbar sind, lasse das Feld leer (None)
- Behalte die Originalsprache des Rezepts bei (Deutsch wenn auf Deutsch, etc.)
- Bei handschriftlichen Rezepten: versuche die Handschrift so gut wie möglich zu entziffern

{format_instructions}

Antworte NUR mit dem JSON-Objekt, ohne zusätzlichen Text.""",
                },
            ]
        )

        response = llm.invoke([message])
        return parser.parse(response.content)
    
    return extract_recipe