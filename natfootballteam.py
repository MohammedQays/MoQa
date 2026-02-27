import requests
import json

SPARQL_URL = "https://query.wikidata.org/sparql"

QUERY = """
PREFIX schema: <http://schema.org/>

SELECT ?item ?arTitle ?enTitle WHERE {
  VALUES ?type { wd:Q6979593 wd:Q135408445 }
  ?item wdt:P31 ?type.
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

def build_wikilink(ar_title, en_title, qid):
    if ar_title:
        short_name = ar_title.replace("منتخب ", "")
        short_name = short_name.split(" لكرة")[0]
        short_name = short_name.replace(" لكرة القدم", "")
        short_name = short_name.strip()
        return f"[[{ar_title}|{short_name}]]"
    else:
        return f"{{{{Ill-WD2|id={qid}|en=true}}}}"


def fetch_teams():
    headers = {
        "Accept": "application/sparql-results+json",
        "User-Agent": "WikiBot/1.0 (https://example.org/)"
    }

    response = requests.get(
        SPARQL_URL,
        params={"query": QUERY},
        headers=headers
    )
    response.raise_for_status()
    data = response.json()

    teams = {}

    for row in data["results"]["bindings"]:
        qid = row["item"]["value"].split("/")[-1]
        en_title = row["enTitle"]["value"]
        ar_title = row["arTitle"]["value"] if "arTitle" in row else None

        teams[en_title] = {
            "qid": qid,
            "ar": ar_title,
            "link": build_wikilink(ar_title, en_title, qid)
        }

    return teams


def save_json(data, filename="natfootballteam.json"):
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    teams = fetch_teams()
    save_json(teams)
    print(f"Saved {len(teams)} teams to natfootballteam.json")

