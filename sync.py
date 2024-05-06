from notion_client import Client
import notion_client.helpers
import json
import sys

with open("notion_token", "r") as reader:
    NOTION_TOKEN = reader.read().strip()

notion = Client(auth=NOTION_TOKEN)

pages = notion.search(
    query="Parks", filter={"value": "database", "property": "object"}
).get("results")
if not pages:
    sys.exit("could not find Parks page")
park_database = pages[0]

with open("parks.json", "r", encoding="utf-8") as f:
    parks = json.loads(f.read())

notion_parks = notion_client.helpers.collect_paginated_api(
    notion.databases.query, database_id=park_database["id"]
)

found_parks = {}

for park in notion_parks:
    title = park["properties"]["Name"]["title"]
    if not title:
        continue
    title = title[0]["text"]["content"]
    sync = park["properties"]["Sync"]["select"]
    manual = sync and sync["name"] == "Manual"

    if not title in parks and not manual:
        notion.pages.update(
            page_id=park["id"], properties={"Sync": {"select": {"name": "Unknown"}}}
        )
    else:
        found_parks[title] = park["id"]

for name, park in parks.items():
    properties = {
        "Sync": {"select": {"name": "Good"}},
        "Quadrant": {"select": {"name": park["city_section"] or "None"}},
        "Location": {
            "rich_text": [{"text": {"content": park["location"] or "Missing address"}}]
        },
        "Neighborhood": {"select": {"name": park["neighborhood"] or "None"}},
        "Name": {"title": [{"text": {"content": name}}]},
        "Website": {"url": park["url"]},
    }

    if name in found_parks:
        notion.pages.update(page_id=found_parks[name], properties=properties)
    else:
        notion.pages.create(
            properties=properties,
            parent={"type": "database_id", "database_id": park_database["id"]},
        )
