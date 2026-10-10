import urllib.parse
import xml.etree.ElementTree as ET
from typing import Any, Dict, List, Optional
import httpx
from pydantic import BaseModel, Field
from app.core.config import settings
from app.core.logging import logger


class AcademicSearchInput(BaseModel):
    query: str = Field(..., description="Academic query or keywords")
    max_results: int = Field(5, ge=1, le=10)


class AcademicPaperResult(BaseModel):
    title: str
    doi: Optional[str] = None
    url: str
    authors: List[str] = Field(default_factory=list)
    publication_year: Optional[int] = None
    abstract: str
    citation_count: int = 0
    source_type: str = "academic"


async def execute_academic_search(input_data: AcademicSearchInput) -> List[AcademicPaperResult]:
    query = input_data.query
    results: List[AcademicPaperResult] = []
    seen_urls = set()

    # 1. ArXiv HTTPS Search API (Rich preprints with abstracts & authors)
    try:
        encoded_query = urllib.parse.quote(query)
        arxiv_url = f"https://export.arxiv.org/api/query?search_query=all:{encoded_query}&start=0&max_results={input_data.max_results}"
        async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
            res = await client.get(arxiv_url, headers={"User-Agent": "ResAI-Academic/1.0"})
            if res.status_code == 200 and res.text:
                root = ET.fromstring(res.text)
                ns = {"atom": "http://www.w3.org/2005/Atom"}
                entries = root.findall("atom:entry", ns)
                for entry in entries:
                    title_elem = entry.find("atom:title", ns)
                    link_elem = entry.find("atom:id", ns)
                    summary_elem = entry.find("atom:summary", ns)
                    published_elem = entry.find("atom:published", ns)

                    if title_elem is None or link_elem is None:
                        continue

                    title = title_elem.text.strip().replace("\n", " ") if title_elem.text else "Academic Preprint"
                    work_url = link_elem.text.strip() if link_elem.text else ""
                    summary = summary_elem.text.strip().replace("\n", " ") if (summary_elem is not None and summary_elem.text) else ""
                    authors = [a.find("atom:name", ns).text.strip() for a in entry.findall("atom:author", ns) if a.find("atom:name", ns) is not None and a.find("atom:name", ns).text]

                    year = None
                    if published_elem is not None and published_elem.text:
                        try:
                            year = int(published_elem.text.strip()[:4])
                        except (ValueError, TypeError):
                            year = None

                    if work_url and work_url not in seen_urls:
                        seen_urls.add(work_url)
                        results.append(
                            AcademicPaperResult(
                                title=title,
                                doi=None,
                                url=work_url,
                                authors=authors[:5],
                                publication_year=year,
                                abstract=summary[:1500] or "Scholarly research paper indexed in arXiv repository.",
                                citation_count=0,
                                source_type="academic",
                            )
                        )
                        if len(results) >= input_data.max_results:
                            return results
    except Exception as e:
        logger.warning(f"ArXiv academic search failed for query '{query}': {e}")

    # 2. Crossref API (Global scholarly works, peer-reviewed DOIs)
    if len(results) < input_data.max_results:
        try:
            encoded_query = urllib.parse.quote(query)
            crossref_url = f"https://api.crossref.org/works?query={encoded_query}&rows={input_data.max_results}"
            email = settings.OPENALEX_EMAIL or "researcher@resai.local"
            headers = {"User-Agent": f"ResAI/1.0 (mailto:{email})"}
            async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
                res = await client.get(crossref_url, headers=headers)
                if res.status_code == 200:
                    data = res.json()
                    items = data.get("message", {}).get("items", [])
                    for it in items:
                        titles = it.get("title") or []
                        title = titles[0] if titles else "Peer-Reviewed Scholarly Publication"
                        doi = it.get("DOI")
                        work_url = it.get("URL") or (f"https://doi.org/{doi}" if doi else None)
                        if not work_url or work_url in seen_urls:
                            continue

                        authors = [
                            f"{a.get('given', '')} {a.get('family', '')}".strip()
                            for a in it.get("author", [])
                            if a.get("family")
                        ]
                        
                        date_parts = (it.get("published-print") or it.get("published-online") or {}).get("date-parts", [[]])[0]
                        year = date_parts[0] if (date_parts and isinstance(date_parts[0], int)) else 2025
                        citations = it.get("is-referenced-by-count", 0)

                        container = it.get("container-title", [])
                        publisher = it.get("publisher", "Academic Publisher")
                        journal_str = container[0] if container else publisher
                        abstract = f"Peer-reviewed research published in {journal_str} ({year}). Cited by {citations} academic publications."

                        seen_urls.add(work_url)
                        results.append(
                            AcademicPaperResult(
                                title=title,
                                doi=doi,
                                url=work_url,
                                authors=authors[:5],
                                publication_year=year,
                                abstract=abstract,
                                citation_count=citations,
                                source_type="academic",
                            )
                        )
                        if len(results) >= input_data.max_results:
                            return results
        except Exception as e:
            logger.warning(f"Crossref search failed for query '{query}': {e}")

    # 3. OpenAlex Search API (Fixed authors extraction & abstract reconstruction)
    if len(results) < input_data.max_results:
        try:
            email = settings.OPENALEX_EMAIL or "researcher@resai.local"
            encoded_query = urllib.parse.quote(query)
            url = f"https://api.openalex.org/works?search={encoded_query}&per_page={input_data.max_results}&mailto={email}"
            async with httpx.AsyncClient(timeout=15.0) as client:
                res = await client.get(url, headers={"User-Agent": f"ResAI/1.0 (mailto:{email})"})
                if res.status_code == 200:
                    data = res.json()
                    for item in data.get("results", []):
                        title = item.get("display_name", "Untitled Academic Paper")
                        doi = item.get("doi")
                        work_url = doi or item.get("id", "https://openalex.org")
                        if work_url in seen_urls:
                            continue

                        year = item.get("publication_year")
                        citations = item.get("cited_by_count", 0)

                        authors = [
                            a.get("author", {}).get("display_name")
                            for a in item.get("authorships", [])
                            if a.get("author", {}).get("display_name")
                        ]

                        abstract_inverted = item.get("abstract_inverted_index")
                        abstract = ""
                        if abstract_inverted and isinstance(abstract_inverted, dict):
                            word_positions = []
                            for word, positions in abstract_inverted.items():
                                for pos in positions:
                                    word_positions.append((pos, word))
                            word_positions.sort(key=lambda x: x[0])
                            abstract = " ".join(w for _, w in word_positions)

                        if not abstract:
                            topics = [t.get("display_name", "") for t in item.get("topics", []) if t.get("display_name")]
                            topics_str = f" Topics: {', '.join(topics[:4])}." if topics else ""
                            abstract = f"Peer-reviewed academic research published in {year or 'recent years'}. Cited by {citations} scholarly works.{topics_str}"

                        seen_urls.add(work_url)
                        results.append(
                            AcademicPaperResult(
                                title=title,
                                doi=doi,
                                url=work_url,
                                authors=authors[:5],
                                publication_year=year,
                                abstract=abstract,
                                citation_count=citations,
                                source_type="academic",
                            )
                        )
                        if len(results) >= input_data.max_results:
                            break
        except Exception as e:
            logger.warning(f"OpenAlex API search failed for '{query}': {e}")

    return results


