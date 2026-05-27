#!/usr/bin/env python3
"""
Debug script to test Notion page creation
"""
import os
from dotenv import load_dotenv
from notion_client import Client
from app.models.recipe import Recipe, Ingredient

load_dotenv()

def test_notion_page_creation():
    api_key = os.getenv("NOTION_API_KEY")
    database_id = os.getenv("NOTION_DATABASE_ID")

    if not api_key or not database_id:
        print("❌ Missing environment variables")
        return

    try:
        client = Client(auth=api_key)
        print("✅ Client created successfully")

        # Test database access
        db_info = client.databases.retrieve(database_id=database_id)
        print("✅ Database access successful")
        print(f"Database title: {db_info['title'][0]['plain_text'] if db_info.get('title') else 'No title'}")

        # Create a test recipe
        test_recipe = Recipe(
            title="Test Rezept - Debug",
            servings=2,
            ingredients=[
                Ingredient(name="Mehl", amount="200g"),
                Ingredient(name="Milch", amount="300ml"),
                Ingredient(name="Eier", amount="2")
            ],
            instructions=[
                "Mehl in eine Schüssel geben",
                "Milch und Eier hinzufügen",
                "Verrühren bis glatt"
            ],
            tags=["Test", "Debug"],
            notes="Dies ist ein Test-Rezept zum Debuggen"
        )

        print("📝 Attempting to create test recipe page...")

        # Create the page
        properties = {
            "Name": {
                "title": [{"text": {"content": test_recipe.title}}]
            },
        }

        # Add optional fields
        if test_recipe.servings:
            properties["Portionen"] = {"number": test_recipe.servings}

        if test_recipe.tags:
            properties["Tags"] = {
                "multi_select": [{"name": tag} for tag in test_recipe.tags]
            }

        # Build page children (body blocks)
        children = []

        # Ingredients section
        ingredients_text = "\n".join(f"• {ing.amount} {ing.name}" if ing.amount else f"• {ing.name}" for ing in test_recipe.ingredients)

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
        for i, step in enumerate(test_recipe.instructions, 1):
            children.append({
                "object": "block",
                "type": "numbered_list_item",
                "numbered_list_item": {
                    "rich_text": [{"text": {"content": step}}]
                }
            })

        # Notes section
        if test_recipe.notes:
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
                    "rich_text": [{"text": {"content": test_recipe.notes}}],
                    "icon": {"emoji": "💡"}
                }
            })

        print(f"Properties: {properties}")
        print(f"Children count: {len(children)}")

        page = client.pages.create(
            parent={"database_id": database_id},
            properties=properties,
            children=children,
        )

        print("✅ Page created successfully!")
        print(f"Page URL: {page.get('url', 'No URL')}")
        print(f"Page ID: {page.get('id', 'No ID')}")

        return page

    except Exception as e:
        print(f"❌ Page creation failed: {e}")
        print(f"Error type: {type(e).__name__}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    test_notion_page_creation()