from urllib.parse import urlparse
import httpx
from bs4 import BeautifulSoup
from pydantic import BaseModel, Field
import trafilatura

from app.core.exceptions import SSRFProtectionException
from app.core.logging import logger
from app.core.security import validate_url_for_ssrf


class FetchUrlInput(BaseModel):
    url: str = Field(..., description="Target web URL to fetch")


class FetchUrlResult(BaseModel):
    url: str
    status_code: int
    content_type: str
    text_content: str
    title: str = "Untitled"
    extracted_text: str = ""


async def execute_fetch_url(input_data: FetchUrlInput) -> FetchUrlResult:
    url = input_data.url
    is_valid, reason = validate_url_for_ssrf(url)
    if not is_valid:
        raise SSRFProtectionException(url, reason)

    async with httpx.AsyncClient(timeout=20.0, follow_redirects=True) as client:
        try:
            res = await client.get(url, headers={"User-Agent": "ResAI-ResearchBot/1.0"})
            
            # Re-validate redirect target URL
            final_url = str(res.url)
            is_final_valid, final_reason = validate_url_for_ssrf(final_url)
            if not is_final_valid:
                raise SSRFProtectionException(final_url, f"Redirect target blocked: {final_reason}")

            raw_html = res.text
            extracted = trafilatura.extract(raw_html) or ""
            
            title = "Untitled"
            soup = BeautifulSoup(raw_html, "html.parser")
            if soup.title and soup.title.string:
                title = soup.title.string.strip()

            if not extracted:
                # Fallback to paragraph text extraction
                paragraphs = [p.get_text().strip() for p in soup.find_all("p") if p.get_text().strip()]
                extracted = "\n\n".join(paragraphs)

            return FetchUrlResult(
                url=final_url,
                status_code=res.status_code,
                content_type=res.headers.get("content-type", "text/html"),
                text_content=raw_html[:2000],
                title=title,
                extracted_text=extracted[:10000],
            )
        except SSRFProtectionException:
            raise
        except Exception as e:
            logger.warning(f"Live URL fetch failed for '{url}': {e}")
            return FetchUrlResult(
                url=url,
                status_code=500,
                content_type="text/plain",
                text_content="",
                title=f"Source ({urlparse(url).netloc})",
                extracted_text="",
            )
