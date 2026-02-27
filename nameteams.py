import requests
import json
from datetime import datetime

SPARQL_URL = "https://query.wikidata.org/sparql"

QUERY = """
PREFIX schema: <http://schema.org/>

SELECT ?item ?arTitle ?enTitle WHERE {
  ?item wdt:P31/wdt:P279* wd:Q476028.
  ?enArticle schema:about ?item ;
             schema:isPartOf <https://en.wikipedia.org/> ;
             schema:name ?enTitle .
  OPTIONAL {
    ?arArticle schema:about ?item ;
               schema:isPartOf <https://ar.wikipedia.org/> ;
               schema:name ?arTitle .
  }
}
"""

def fetch_clubs():
    headers = {"Accept": "application/sparql-results+json"}
    response = requests.get(SPARQL_URL, params={"query": QUERY}, headers=headers)
    data = response.json()

    clubs = {}

    for row in data["results"]["bindings"]:
        qid = row["item"]["value"].split("/")[-1]
        en_title = row["enTitle"]["value"]
        ar_title = row["arTitle"]["value"] if "arTitle" in row else None

        clubs[en_title] = {
            "qid": qid,
            "ar": ar_title
        }

    return clubs


def save_json(data):
    with open("nameteams.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    clubs = fetch_clubs()
    save_json(clubs)
    print(f"Saved {len(clubs)} clubs to nameteams.json")


