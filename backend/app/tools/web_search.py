import re
import urllib.parse
from typing import Any, Dict, List, Optional
from urllib.parse import unquote, urlparse
from bs4 import BeautifulSoup
import httpx
from pydantic import BaseModel, Field

from app.core.config import settings
from app.core.logging import logger
from app.tools.academic_search import AcademicSearchInput, execute_academic_search


class WebSearchInput(BaseModel):
    query: str = Field(..., description="The search query string")
    recency: Optional[str] = Field("month", description="Recency filter: 'day', 'week', 'month', 'year'")
    domain_filters: Optional[List[str]] = Field(default_factory=list, description="Target domains")
    max_results: int = Field(5, ge=1, le=10)


class WebSearchResult(BaseModel):
    title: str
    url: str
    snippet: str
    published_date: Optional[str] = None
    domain: str
    source_type: str = "web"


async def execute_web_search(input_data: WebSearchInput) -> List[WebSearchResult]:
    query = input_data.query
    results: List[WebSearchResult] = []
    seen_urls = set()

    # 1. Tavily API Search (Primary high-fidelity web search)
    if settings.TAVILY_API_KEY:
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                payload = {
                    "api_key": settings.TAVILY_API_KEY,
                    "query": query,
                    "max_results": input_data.max_results,
                }
                if input_data.domain_filters:
                    payload["include_domains"] = input_data.domain_filters

                res = await client.post("https://api.tavily.com/search", json=payload)
                if res.status_code == 200:
                    data = res.json()
                    for item in data.get("results", []):
                        url = item.get("url", "")
                        if not url or url in seen_urls:
                            continue
                        domain = urlparse(url).netloc or "web"
                        seen_urls.add(url)
                        results.append(
                            WebSearchResult(
                                title=item.get("title") or "Web Search Source",
                                url=url,
                                snippet=item.get("content") or "",
                                published_date=item.get("published_date") or "2026-01-01",
                                domain=domain,
                                source_type="web",
                            )
                        )
                    if results:
                        return results
        except Exception as e:
            logger.warning(f"Tavily web search error for query '{query}': {e}")

    # 2. DuckDuckGo Web Search Scraper Fallback
    try:
        async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            }
            response = await client.post(
                "https://html.duckduckgo.com/html/",
                data={"q": query},
                headers=headers,
            )
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, "html.parser")
                for result in soup.find_all("div", class_="result"):
                    title_elem = result.find("a", class_="result__a")
                    snippet_elem = result.find("a", class_="result__snippet")
                    if not title_elem:
                        continue

                    raw_url = title_elem.get("href", "")
                    if "uddg=" in raw_url:
                        clean_url = unquote(raw_url.split("uddg=")[1].split("&")[0])
                    else:
                        clean_url = raw_url

                    if not clean_url.startswith("http") or clean_url in seen_urls:
                        continue

                    domain = urlparse(clean_url).netloc
                    title = title_elem.get_text().strip()
                    snippet = snippet_elem.get_text().strip() if snippet_elem else ""

                    seen_urls.add(clean_url)
                    results.append(
                        WebSearchResult(
                            title=title,
                            url=clean_url,
                            snippet=snippet,
                            published_date="2026-01-01",
                            domain=domain,
                            source_type="web",
                        )
                    )
                    if len(results) >= input_data.max_results:
                        return results
    except Exception as e:
        logger.warning(f"DuckDuckGo web search scraper failed: {e}")

    # 3. ArXiv & Crossref Scholarly Search Fallback for Technical/Academic Topics
    try:
        acad_papers = await execute_academic_search(
            AcademicSearchInput(query=query, max_results=input_data.max_results)
        )
        for paper in acad_papers:
            if paper.url and paper.url not in seen_urls:
                seen_urls.add(paper.url)
                results.append(
                    WebSearchResult(
                        title=paper.title,
                        url=paper.url,
                        snippet=paper.abstract,
                        published_date=str(paper.publication_year or "2025"),
                        domain=urlparse(paper.url).netloc or "academic",
                        source_type="academic",
                    )
                )
        if results:
            return results
    except Exception as e:
        logger.warning(f"Scholarly search fallback failed: {e}")

    logger.info(f"No web search results found for query: '{query}'")
    return results


