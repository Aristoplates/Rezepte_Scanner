# Notion Datenbank Setup

## 1. Integration erstellen

1. Gehe zu https://www.notion.so/my-integrations
2. Klicke **"New integration"**
3. Name: `Recipe Scanner`
4. Capabilities: **Read content**, **Update content**, **Insert content**
5. Kopiere den **Internal Integration Secret** → in `.env` als `NOTION_API_KEY`

## 2. Datenbank anlegen

Erstelle eine neue Notion-Datenbank (Full page) mit folgenden Properties:

| Property Name     | Typ           | Hinweis                          |
|-------------------|---------------|----------------------------------|
| `Name`            | Title         | Pflichtfeld (automatisch)        |
| `Portionen`       | Number        |                                  |
| `Vorbereitungszeit` | Text        |                                  |
| `Kochzeit`        | Text          |                                  |
| `Gesamtzeit`      | Text          |                                  |
| `Tags`            | Multi-select  | z.B. Vegetarisch, Kuchen, etc.   |
| `Zutaten`         | Text          | Zutaten-Liste (max 2000 Zeichen) |
| `Zubereitung`     | Text          | Zubereitungsschritte             |
| `Quelle`          | Text          |                                  |

## 3. Integration mit DB verbinden

1. Öffne deine Notion-Datenbank
2. Klicke oben rechts auf **`...`** → **"Add connections"**
3. Wähle `Recipe Scanner`

## 4. Database ID herausfinden

Die Database ID steht in der URL deiner Datenbank:

```
https://www.notion.so/YOUR_WORKSPACE/XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX?v=...
                                     ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
                                     Das ist deine DATABASE_ID
```

Diese ID → in `.env` als `NOTION_DATABASE_ID`
