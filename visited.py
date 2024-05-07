from notion_client import Client
import notion_client.helpers
import sys
import requests
from datetime import datetime
from exif import Image


with open("notion_token", "r") as reader:
    NOTION_TOKEN = reader.read().strip()

notion = Client(auth=NOTION_TOKEN)

pages = notion.search(
    query="Parks", filter={"value": "database", "property": "object"}
).get("results")
if not pages:
    sys.exit("could not find Parks page")
park_database = pages[0]

visited_without_date = notion_client.helpers.collect_paginated_api(
    notion.databases.query,
    database_id=park_database["id"],
    filter={
        "and": [
            {"property": "Proof", "files": {"is_not_empty": True}},
            {"property": "Visited On", "date": {"is_empty": True}},
        ]
    },
)

for park in visited_without_date:
    photo_url = park["properties"]["Proof"]["files"][0]["file"]["url"]
    photo = requests.get(photo_url)
    photo.raise_for_status
    photo = Image(photo.content)
    date = photo.get("datetime_original")

    if date:
        date = datetime.strptime(date, "%Y:%m:%d %H:%M:%S")
        notion.pages.update(
            page_id=park["id"],
            properties={"Visited On": {"date": {"start": date.isoformat()}}},
        )
