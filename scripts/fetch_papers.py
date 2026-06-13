import json
import os
import re
import time
import urllib.parse
import urllib.request
from datetime import date, datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "scripts" / "paper_config.json"
OUTPUT_PATH = ROOT / "data" / "papers.json"
SERPAPI_ENDPOINT = "https://serpapi.com/search.json"


def normalize_text(value):
  return re.sub(r"\s+", " ", value or "").strip().casefold()


def compact_text(value):
  return re.sub(r"\s+", " ", value or "").strip()


def quote_query_term(term):
  return f'"{term}"' if re.search(r"\s|-", term) else term


def build_concept_query(concept):
  terms = " OR ".join(quote_query_term(term) for term in concept["terms"])
  return f"({terms})"


def build_group_query(group, concepts_by_label, journal_name):
  concept_queries = [
    build_concept_query(concepts_by_label[label])
    for label in group["concepts"]
  ]
  return f"{' '.join(concept_queries)} source:{quote_query_term(journal_name)}"


def scholar_request(api_key, params):
  query = urllib.parse.urlencode({
    "engine": "google_scholar",
    "api_key": api_key,
    "hl": "en",
    "as_vis": "1",
    **params
  })
  request = urllib.request.Request(f"{SERPAPI_ENDPOINT}?{query}")

  with urllib.request.urlopen(request, timeout=45) as response:
    return json.loads(response.read().decode("utf-8"))


def extract_year(result):
  summary = result.get("publication_info", {}).get("summary", "")
  match = re.search(r"\b(20\d{2}|19\d{2})\b", summary)
  return match.group(1) if match else ""


def author_names(result, limit=6):
  authors = result.get("publication_info", {}).get("authors", [])

  if authors:
    names = [compact_text(author.get("name", "")) for author in authors[:limit]]
    names = [name for name in names if name]

    if len(authors) > limit:
      names.append("et al.")

    return names

  summary = result.get("publication_info", {}).get("summary", "")
  head = summary.split(" - ")[0] if summary else ""
  return [compact_text(head)] if head else []


def result_text(result):
  text = normalize_text(" ".join([
    result.get("title", ""),
    result.get("snippet", ""),
    result.get("publication_info", {}).get("summary", "")
  ]))
  return text


def text_matches_concept(text, concept):
  return any(normalize_text(term) in text for term in concept["terms"])


def result_matches_group(result, group, concepts_by_label):
  text = result_text(result)
  return all(
    text_matches_concept(text, concepts_by_label[label])
    for label in group["concepts"]
  )


def result_matches_journal(result, journal_name):
  summary = normalize_text(result.get("publication_info", {}).get("summary", ""))
  return normalize_text(journal_name) in summary


def make_paper(result, journal, group):
  year = extract_year(result)
  result_id = result.get("result_id", "")

  return {
    "title": compact_text(result.get("title", "")),
    "authors": author_names(result),
    "journal": journal["name"],
    "quartile": journal["quartile"],
    "published": f"{year}-01-01" if year else "",
    "year": year,
    "url": result.get("link", ""),
    "google_scholar_id": result_id,
    "cited_by": result.get("inline_links", {}).get("cited_by", {}).get("total"),
    "doi": "",
    "keywords": [group["label"]],
    "concepts": group["concepts"]
  }


def collect_papers(config, api_key):
  today = date.today()
  from_year = today.year - int(config["window_years"]) + 1
  to_year = today.year
  allowed_quartiles = set(config.get("allowed_quartiles", ["Q1", "Q2", "Q3"]))
  journals = [
    journal
    for journal in config["journals"]
    if journal.get("quartile") in allowed_quartiles
  ]
  concepts_by_label = {
    concept["label"]: concept
    for concept in config["concepts"]
  }
  papers_by_key = {}

  for group in config["query_groups"]:
    for journal in journals:
      scholar_query = build_group_query(group, concepts_by_label, journal["name"])
      params = {
        "q": scholar_query,
        "as_ylo": from_year,
        "as_yhi": to_year,
        "num": int(config["max_results_per_query"])
      }

      try:
        data = scholar_request(api_key, params)
      except Exception as exc:
        print(f"Google Scholar request failed: {group['label']} / {journal['name']} / {exc}")
        continue

      for result in data.get("organic_results", []):
        if not result.get("title"):
          continue

        if not result_matches_group(result, group, concepts_by_label):
          continue

        if not result_matches_journal(result, journal["name"]):
          continue

        key = normalize_text(result.get("result_id") or result.get("link") or result.get("title"))
        paper = papers_by_key.get(key) or make_paper(result, journal, group)
        keywords = set(paper["keywords"])
        keywords.add(group["label"])
        paper["keywords"] = sorted(keywords)
        paper["concepts"] = sorted(set(paper.get("concepts", []) + group["concepts"]))
        papers_by_key[key] = paper

      time.sleep(0.25)

  return sorted(
    papers_by_key.values(),
    key=lambda paper: paper.get("published") or "",
    reverse=True
  )


def main():
  api_key = os.getenv("SERPAPI_KEY")

  if not api_key:
    raise SystemExit(
      "Missing SERPAPI_KEY. Add it as a GitHub Actions secret to fetch Google Scholar results."
    )

  with CONFIG_PATH.open("r", encoding="utf-8") as file:
    config = json.load(file)

  papers = collect_papers(config, api_key)
  output = {
    "generated_at": datetime.now(timezone.utc).isoformat(),
    "status": "ok",
    "message": "Paper radar data generated successfully.",
    "source": "Google Scholar",
    "access_method": "SerpApi Google Scholar API",
    "window_years": config["window_years"],
    "keywords": [
      {
        "label": concept["label"],
        "meaning": concept["meaning"]
      }
      for concept in config["concepts"]
    ],
    "query_groups": [
      {
        "label": group["label"],
        "concepts": group["concepts"]
      }
      for group in config["query_groups"]
    ],
    "quartile_system": config.get("quartile_system", "SCI/JCR"),
    "allowed_quartiles": config.get("allowed_quartiles", ["Q1", "Q2", "Q3"]),
    "journal_filter": "Transactions journals curated as SCI/JCR Q1/Q2/Q3 in scripts/paper_config.json",
    "papers": papers
  }

  OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
  with OUTPUT_PATH.open("w", encoding="utf-8") as file:
    json.dump(output, file, ensure_ascii=False, indent=2)
    file.write("\n")

  print(f"Wrote {len(papers)} Google Scholar papers to {OUTPUT_PATH}")


if __name__ == "__main__":
  main()
