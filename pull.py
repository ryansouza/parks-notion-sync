import requests
import urllib.parse
import random
import json
import subprocess
from bs4 import BeautifulSoup


def relative_url(base, relative):
    parts = urllib.parse.urlsplit(relative)
    relative = urllib.parse.urlunsplit(["", "", parts[2], parts[3], ""])
    return urllib.parse.urljoin(base, relative)


def fetch_park_urls(url):
    last_url = ""
    while url != last_url:
        print("GET ", url)
        parks = requests.get(url)
        parks.raise_for_status
        soup = BeautifulSoup(parks.text, "html.parser")

        for park in soup.select(".view-park-finder .view-content .morsel"):
            yield park.find("a").get("href")

        next = soup.select('[role="navigation"] [rel="next"]')
        if not next:
            break

        last_url = url
        url = relative_url(last_url, next[0].get("href"))


def clean_field(field):
    if not field:
        return None

    return " ".join(
        filter(
            None,
            [line.strip() for line in field[0].text.strip().splitlines()],
        )
    )


def fetch_park_details(url):
    print("GET ", url)
    parks = requests.get(url)
    parks.raise_for_status
    soup = BeautifulSoup(parks.text, "html.parser")
    content = soup.find(id="main-content")

    park_title = content.select(".page-title")
    location = content.select(".field.field--name-field-location address")
    neighborhood = content.select(".field.field--name-field-neighborhood .field__item")
    city_section = content.select(".field.field--name-field-city-section .field__item")

    return {
        "title": park_title[0].text.strip(),
        "url": url,
        "location": clean_field(location),
        "neighborhood": clean_field(neighborhood),
        "city_section": clean_field(city_section),
    }


base = "https://www.portland.gov/parks/search?search=&sort_by=content_title"

park_urls = list(fetch_park_urls(base))
park_details = [fetch_park_details(relative_url(base, url)) for url in park_urls]
park_details = {park["title"]: park for park in park_details}
park_json = json.dumps(park_details, indent=2)

subprocess.run(["diff", "-u", "parks.json", "-"], input=park_json, text=True)

with open("parks.json", "w", encoding="utf-8") as f:
    f.write(park_json)
