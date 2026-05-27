import os
import sys
from pathlib import Path

# Ensure the project root is on sys.path so absolute imports from `app` work
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import streamlit as st
from dotenv import load_dotenv

load_dotenv()

from app.chains.recipe_chain import build_recipe_chain
from app.services.notion_services import NotionService
from app.models.recipe import Recipe, Ingredient
from app.utils.image_utils import resize_image, get_image_preview

# --- Page Config ------------------------------------
st.set_page_config(
    page_title="Rezepte Scanner",
    page_icon="🍳",
    layout="centered",
    initial_sidebar_state="expanded"
)

# --- Custom CSS -------------------------------------
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;700&family=DM+Sans:wght@300;400;500&display=swap');

    html, body, [class*="css"] {
        font-family: 'DM Sans', sans-serif;
    }
    h1, h2, h3 {
        font-family: 'Playfair Display', serif !important;
    }
    .recipe-card {
        background: #faf9f6;
        border: 1px solid #e8e0d4;
        border-radius: 12px;
        padding: 1.5rem;
        margin: 1rem 0;
    }
    .step-badge {
        display: inline-block;
        background: #2c2c2c;
        color: white;
        border-radius: 50%;
        width: 24px;
        height: 24px;
        text-align: center;
        line-height: 24px;
        font-size: 12px;
        margin-right: 8px;
    }
    .stButton > button {
        background-color: #2c2c2c !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        font-family: 'DM Sans', sans-serif !important;
        font-weight: 500 !important;
        padding: 0.5rem 1.5rem !important;
    }
    .stButton > button:hover {
        background-color: #444 !important;
    }
    .success-banner {
        background: #e8f5e9;
        border-left: 4px solid #4caf50;
        padding: 1rem;
        border-radius: 4px;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)


# --- Sidebar ----------------------------------------------
with st.sidebar:
    st.markdown("## ⚙️ Einstellungen")

    use_ollama = st.toggle("Ollama (lokal)", value=False, help="Nutzt qwen statt GPT-4o")

    if use_ollama:
        st.info("🦙 Ollama aktiv — kein API-Cost")
        ollama_model = st.text_input("Modell", value=os.getenv("OLLAMA_MODEL", "qwen3.5:0.8b"))
        os.environ["OLLAMA_MODEL"] = ollama_model
    else:
        st.info("🤖 GPT-4o aktiv")

    st.divider()

    st.markdown("### Notion Status")
    if st.button("🔗 Verbindung testen"):
        try:
            svc = NotionService()
            if svc.test_connection():
                st.success("✅ Verbunden!")
            else:
                st.error("❌ Verbindung fehlgeschlagen")
        except Exception as e:
            st.error(f"❌ Fehler: {e}")

    st.divider()
    st.markdown("### LangSmith Tracing")
    tracing = os.getenv("LANGCHAIN_TRACING_V2", "false")
    if tracing == "true":
        st.success("✅ Aktiv")
    else:
        st.warning("⚠️ Inaktiv (ENV setzen)")


# --- Main UI ------------------------------------------------------------
st.markdown("# 🍳 Rezepte Scanner")
st.markdown("*Rezeptfoto hochladen → KI liest aus → In Notion speichern*")

st.divider()

# Upload
col1, col2 = st.columns([2, 1])

with col1:
    uploaded_file = st.file_uploader(
        "Rezeptefoto hochladen",
        type=["jpg", "jpeg", "png", "webp"],
        help="Foto eines abgedruckten oder handgeschriebenen Rezepts"
    )

with col2:
    st.markdown("**Oder Kamera nutzen:")
    camera_input = st.camera_input("📷 Foto aufnehmen")

# Determine active image
active_image = camera_input or uploaded_file
image_bytes = None

if active_image:
    image_bytes = active_image.read()
    preview = get_image_preview(image_bytes)
    st.image(preview, caption="Hochgeladenes Bild", width=300)

st.divider()

# --- Extraction ----------------------------------------------
if image_bytes and st.button("🔍 Rezept auslesen", type="primary", use_container_width=True):
    with st.spinner("KI analyisiert das Rezeptfoto..."):
        try:
            optimized = resize_image(image_bytes)
            chain = build_recipe_chain(use_ollama=use_ollama)
            recipe: Recipe = chain(optimized)
            st.session_state["recipe"] = recipe
            st.success("✅ Rezept erfolgreich ausgelesen!")
        except Exception as e:
            st.error(f"❌ Fehler beim Auslesen: {e}")
            st.stop()

# --- Edit & Review -------------------------------------------
if "recipe" in st.session_state:
    recipe: Recipe = st.session_state["recipe"]

    st.markdown("## 📋 Erkanntes Rezept")
    st.markdown("*Prüfe und bearbeite die Daten vor dem Speichern:*")

    with st.form("recipe_form"):
        # Basic Info
        col1, col2 = st.columns([3, 1])
        with col1:
            title = st.text_input("Rezeptname", value=recipe.title)
        with col2:
            servings = st.number_input("Portionen", value=recipe.servings or 4, min_value=1)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            prep_time = st.text_input("Vorbereitung", value=recipe.prep_time or "")
        with col2:
            cook_time = st.text_input("Kochzeit", value=recipe.cook_time or "")
        with col3:
            total_time = st.text_input("Gesamtzeit", value=recipe.total_time or "")
        
        # Tags
        tags_str = st.text_input(
            "Tags (kommagetrennt)",
            value=", ".join(recipe.tags) if recipe.tags else ""
        )

        st.divider()

        # Ingredients
        st.markdown("### 🧂 Zutaten")
        ingredients_text = st.text_area(
            "Zutaten (eine pro Zeile, Format: Menge Zutat)",
            value="\n".join(
                f"{i.amount} {i.name}" if i.amount else i.name
                for i in recipe.ingredients
            ),
            height=200,
        )

        st.divider()

        # Instructions
        st.markdown("### 👨‍🍳 Zubereitung")
        instructions_text = st.text_area(
            "Schritte (einer pro Zeile)",
            value="\n".join(recipe.instructions),
            height=300,
        )

        # Notes
        notes = st.text_area("📝 Hinweise (optional)", value=recipe.notes or "")

        st.divider()

        submitted = st.form_submit_button("💾 In Notion speichern", use_container_width=True)

        if submitted:
            # Parse ingredients back from text
            parsed_ingredients = []
            for line in ingredients_text.strip().split("\n"):
                line = line.strip()
                if line:
                    # Simple split: first token is amount if it contains digits
                    parts = line.split(" ", 1)
                    if len(parts) == 2 and any(c.isdigit() for c in parts[0]):
                        parsed_ingredients.append(Ingredient(amount=parts[0], name=parts[1]))
                    else:
                        parsed_ingredients.append(Ingredient(name=line))

            updated_recipe = Recipe(
                title=title,
                servings=int(servings),
                prep_time=prep_time or None,
                cook_time=cook_time or None,
                total_time=total_time or None,
                ingredients=parsed_ingredients,
                instructions=[s.strip() for s in instructions_text.strip().split("\n") if s.strip()],
                tags=[t.strip() for t in tags_str.split(",") if t.strip()],
                notes=notes or None,
                source=recipe.source,
            )                

            with st.spinner("Speichere in Notion..."):
                try:
                    svc = NotionService()
                    page = svc.create_recipe_page(updated_recipe)
                    page_url = page.get("url", "")
                    st.markdown(f"""
                    <div class="success-banner">
                        ✅ <strong>Rezept gespeichert!</strong><br>
                        <a href="{page_url}" target="_blank">In Notion öffnen →</a>
                    </div>
                    """, unsafe_allow_html=True)
                    del st.session_state["recipe"]
                except Exception as e:
                    st.error(f"❌ Fehler beim Speichern: {e}")