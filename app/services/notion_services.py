import os
from notion_client import Client
from app.models.recipe import Recipe

class NotionService:
    def __init__(self):
        self.client = Client(auth=os.getenv("NOTION_API_KEY"))
        self.database_id = os.getenv("NOTION_DATABASE_ID")

    def create_recipe_page(self, recipe: Recipe, image_bytes: bytes | None = None) -> dict:
        """
        Write a recipe to the Notion database.
        Returns the created Notion page object.
        """
        ingredients_text = self._format_ingredients(recipe.ingredients)
        instructions_text = self._format_instructions(recipe.instructions)

        properties = {
            "Name": {
                "title": [{"text": {"content": recipe.title}}]
            },
        }

        # Optional fields — only add if present
        if recipe.servings:
            properties["Portionen"] = {"number": recipe.servings}

        if recipe.prep_time:
            properties["Vorbereitungszeit"] = {
                "rich_text": [{"text": {"content": recipe.prep_time}}]
            }

        if recipe.cook_time:
            properties["Kochzeit"] = {
                "rich_text": [{"text": {"content": recipe.cook_time}}]
            }

        if recipe.total_time:
            properties["Gesamtzeit"] = {
                "rich_text": [{"text": {"content": recipe.total_time}}]
            }

        if recipe.tags:
            properties["Tags"] = {
                "multi_select": [{"name": tag} for tag in recipe.tags]
            }

        if recipe.source:
            properties["Quelle"] = {
                "rich_text": [{"text": {"content": recipe.source}}]
            }

         # Zutaten als Rich Text Property (max 2000 Zeichen — Notion-Limit)
        if recipe.ingredients:
            ingredients_text = self._format_ingredients(recipe.ingredients)
            properties["Zutaten"] = {
                "rich_text": [{"text": {"content": ingredients_text[:2000]}}]
            }

        # Zubereitung als Rich Text Property
        if recipe.instructions:
            instructions_text = self._format_instructions(recipe.instructions)
            properties["Zubereitung"] = {
                "rich_text": [{"text": {"content": instructions_text[:2000]}}]
            }

        # Build page children (body blocks)
        children = []

        # Ingredients section
        children.append({
            "object": "block",
            "type": "heading_2",
            "heading_2": {
                "rich_text": [{"text": {"content": "🧂 Zutaten"}}]
            }
        })
        children.append({
            "object": "block",
            "type": "paragraph",
            "paragraph": {
                "rich_text": [{"text": {"content": ingredients_text}}]
            }
        })

        # Instructions section
        children.append({
            "object": "block",
            "type": "heading_2",
            "heading_2": {
                "rich_text": [{"text": {"content": "👨‍🍳 Zubereitung"}}]
            }
        })
        for i, step in enumerate(recipe.instructions, 1):
            children.append({
                "object": "block",
                "type": "numbered_list_item",
                "numbered_list_item": {
                    "rich_text": [{"text": {"content": step}}]
                }
            })

        # Notes section (if present)
        if recipe.notes:
            children.append({
                "object": "block",
                "type": "heading_2",
                "heading_2": {
                    "rich_text": [{"text": {"content": "📝 Hinweise"}}]
                }
            })
            children.append({
                "object": "block",
                "type": "callout",
                "callout": {
                    "rich_text": [{"text": {"content": recipe.notes}}],
                    "icon": {"emoji": "💡"}
                }
            })

        page = self.client.pages.create(
            parent={"database_id": self.database_id},
            properties=properties,
            children=children,
        )

        return page
    
    def _format_ingredients(self, ingredients) -> str:
        lines = []
        for ing in ingredients:
            if ing.amount:
                lines.append(f"• {ing.amount} {ing.name}")
            else:
                lines.append(f"• {ing.name}")
        return "\n".join(lines)

    def _format_instructions(self, instructions: list[str]) -> str:
        return "\n".join(f"{i}. {step}" for i, step in enumerate(instructions, 1))

    def test_connection(self) -> bool:
        """Test if the Notion connection works."""
        try:
            self.client.databases.retrieve(database_id=self.database_id)
            return True
        except Exception as e:
            print(f"Notion connection failed: {e}")
            return False