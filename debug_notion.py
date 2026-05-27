#!/usr/bin/env python3
"""
Debug script to test Notion connection
"""
import os
from dotenv import load_dotenv
from notion_client import Client

load_dotenv()

def test_notion_connection():
    api_key = os.getenv("NOTION_API_KEY")
    database_id = os.getenv("NOTION_DATABASE_ID")

    print(f"API Key present: {bool(api_key)}")
    print(f"Database ID present: {bool(database_id)}")

    if not api_key or not database_id:
        print("❌ Missing environment variables")
        return False

    print(f"API Key starts with: {api_key[:10]}...")
    print(f"Database ID: {database_id}")

    try:
        client = Client(auth=api_key)
        print("✅ Client created successfully")

        # Test database access
        db_info = client.databases.retrieve(database_id=database_id)
        print("✅ Database access successful")
        print(f"Database title: {db_info['title'][0]['plain_text'] if db_info.get('title') else 'No title'}")
        return True

    except Exception as e:
        print(f"❌ Connection failed: {e}")
        print(f"Error type: {type(e).__name__}")
        return False

if __name__ == "__main__":
    test_notion_connection()