from notion_client import Client
import notion_client.helpers
import sys
import requests
import random
import json
import time

with open("notion_token", "r") as reader:
    NOTION_TOKEN = reader.read().strip()

notion = Client(auth=NOTION_TOKEN)

pages = notion.search(
    query="Parks", filter={"value": "database", "property": "object"}
).get("results")
if not pages:
    sys.exit("could not find Parks page")
park_database = pages[0]

not_visited = notion_client.helpers.collect_paginated_api(
    notion.databases.query,
    database_id=park_database["id"],
    filter={"property": "Proof", "files": {"is_empty": True}},
)

from geopy.geocoders import Nominatim

nom = Nominatim(user_agent="github.com/ryansouza/parks-notion-sync", timeout=60)


def dump_parks_json(parks):
    with open("parks.json", "w", encoding="utf-8") as f:
        f.write(json.dumps(parks, indent=2))


with open("parks.json", "r", encoding="utf-8") as f:
    parks = json.loads(f.read())

for name, park in parks.items():
    if park["location"] == "Missing address" or "lat" in park:
        continue

    print(f"geocoding {name}")
    location = park["location"]
    try:
        time.sleep(1)
        geo = nom.geocode(location)
        if not geo:
            print(f"returned empty for {location}")
            location = park.get("geocode_name", name + " portland, or")
            geo = nom.geocode(location)
            if geo:
                print(f"found alternative for {location}")
            else:
                print(f"returned empty for {location}")
                continue

        park["lat"] = geo.latitude
        park["lon"] = geo.longitude
        dump_parks_json(parks)
    except Exception as ex:
        print(f"failed geocode {name}: {ex}")


map_parks = []

for park in not_visited:
    name = park["properties"]["Name"]["title"][0]["plain_text"]
    if name in parks and "lat" in parks[name]:
        map_parks.append(parks[name])


with open("map.html", "w", encoding="utf-8") as f:
    f.write(
        """
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no" />
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"
    integrity="sha256-p4NxAoJBhIIN+hmNHrzRCf9tD/miZyoHS5obTRR9BMY="
    crossorigin=""/>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"
    integrity="sha256-20nQCchB9co0qIjJZRGuk2/Z9VM+kNiyxNV1lvTlZBo="
    crossorigin=""></script>
<style>
    body {
        padding: 0;
        margin: 0;
    }
    html, body, #map {
        height: 100%%;
        width: 100vw;
    }
    #map { height: 100%%; }
</style>
</head>
<body>
    <div id="map"></div>
    <script>
        var map = L.map('map').setView([45.523064, -122.676483], 11);
        L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
            maxZoom: 19,
            attribution: '&copy; <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a>'
        }).addTo(map);
        var data = %s;
        data.forEach( (park) => {
            var marker = L.marker([park.lat, park.lon]).addTo(map);
            marker.bindPopup("<a href=\\"" + park.url + "\\">" + park.title + "</a>");
        })
    </script>
</body>
</html>
        """
        % json.dumps(map_parks)
    )
