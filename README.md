🍳 Recipe Scanner → Notion
Fotografiere ein Rezept, lass es von GPT-4o auslesen und speichere es strukturiert in deiner Notion-Datenbank.
Stack
Streamlit – UI (inkl. Kamera-Input)
LangChain + GPT-4o Vision – OCR & strukturierte Extraktion
LangSmith – Tracing & Debugging der Chain
Notion API – Ziel-Datenbank
Ollama (llava) – lokale Alternative zu GPT-4o
Docker – Deployment
Schnellstart
```bash
# 1. Repo klonen
git clone <repo-url>
cd recipe-notion-app

# 2. Umgebungsvariablen setzen
cp .env.example .env
# → .env editieren mit deinen Keys

# 3. Notion einrichten
# Siehe NOTION_SETUP.md

# 4a. Lokal starten
pip install -r requirements.txt
streamlit run app/main.py

# 4b. Oder via Docker
docker compose up --build
```
Dann: http://localhost:8501
Projektstruktur
```
app/
├── main.py                  # Streamlit UI
├── chains/
│   └── recipe_chain.py      # LangChain GPT-4o / Ollama Chain
├── services/
│   └── notion_service.py    # Notion API Integration
├── models/
│   └── recipe.py            # Pydantic Datenmodell
└── utils/
    └── image_utils.py       # Bildoptimierung
```
Umgebungsvariablen
Variable	Pflicht	Beschreibung
`OPENAI_API_KEY`	Ja (wenn kein Ollama)	GPT-4o API Key
`NOTION_API_KEY`	Ja	Notion Integration Secret
`NOTION_DATABASE_ID`	Ja	ID der Ziel-Datenbank
`LANGCHAIN_TRACING_V2`	Nein	`true` für LangSmith Tracing
`LANGCHAIN_API_KEY`	Nein	LangSmith API Key
`OLLAMA_BASE_URL`	Nein	Standard: `http://localhost:11434`
`OLLAMA_MODEL`	Nein	Standard: `llava`
Geplante Erweiterungen
[ ] Pinecone: Vektorsuche über alle gespeicherten Rezepte
[ ] Tavily: Automatische Anreicherung mit Nährwerten
[ ] Batch-Upload mehrerer Fotos
[ ] Export als PDF