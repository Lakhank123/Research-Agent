import ipaddress
import logging
import re
import socket
from typing import Optional
from urllib.parse import urlparse
import requests
import trafilatura
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

class PageReader:
    def __init__(self, timeout: int = 15):
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 (ResearchPilot/2.0 AI Analyst)",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        })

    def _is_public_http_url(self, url: str) -> bool:
        """Reject private IP spaces, localhost, cloud metadata, and non-HTTP protocols."""
        try:
            parsed = urlparse(url)
            if parsed.scheme not in ("http", "https") or not parsed.hostname:
                return False
            host = parsed.hostname.lower()
            if host in ("localhost", "127.0.0.1", "::1", "0.0.0.0", "169.254.169.254"):
                return False
            if host.endswith(".local") or host.endswith(".internal") or host.endswith(".onion"):
                return False

            addresses = []
            try:
                addresses.append(ipaddress.ip_address(host))
            except ValueError:
                for item in socket.getaddrinfo(host, None):
                    addresses.append(ipaddress.ip_address(item[4][0]))
            return bool(addresses) and all(addr.is_global for addr in addresses)
        except Exception:
            return False

    def _clean_soup_html(self, soup: BeautifulSoup) -> tuple[str, dict]:
        """Strip boilerplate and format structured markdown (headings, lists, tables)."""
        metadata = {}

        # Extract author
        author_meta = soup.find("meta", attrs={"name": re.compile(r"author", re.I)})
        if author_meta and author_meta.get("content"):
            metadata["author"] = author_meta["content"].strip()

        # Extract publication date
        date_meta = soup.find("meta", attrs={"property": re.compile(r"published_time|date", re.I)}) or \
                    soup.find("meta", attrs={"name": re.compile(r"date", re.I)})
        if date_meta and date_meta.get("content"):
            metadata["published_date"] = date_meta["content"].strip()[:20]

        # Decompose non-content / boilerplate tags
        for tag in soup(["script", "style", "nav", "footer", "header", "aside", "noscript", "svg", "form", "iframe"]):
            tag.decompose()

        # Decompose cookie banners and ads by class/id
        for bad in soup.find_all(attrs={"class": re.compile(r"cookie|banner|ad-|advert|popup|newsletter|modal|sidebar", re.I)}):
            bad.decompose()
        for bad in soup.find_all(attrs={"id": re.compile(r"cookie|banner|ad-|advert|popup|newsletter|sidebar", re.I)}):
            bad.decompose()

        # Convert headings to Markdown
        for h in soup.find_all(["h1", "h2", "h3", "h4"]):
            level = h.name
            h.replace_with(f"\n\n### {h.get_text(strip=True)}\n\n")

        # Convert list items
        for li in soup.find_all("li"):
            li.replace_with(f"\n- {li.get_text(strip=True)}")

        # Convert tables to markdown where feasible
        for table in soup.find_all("table"):
            rows = []
            for tr in table.find_all("tr"):
                cells = [td.get_text(" ", strip=True).replace("|", "/") for td in tr.find_all(["th", "td"])]
                if cells:
                    rows.append("| " + " | ".join(cells) + " |")
            if rows:
                if len(rows) > 1:
                    header_sep = "| " + " | ".join(["---"] * len(rows[0].split("|")[1:-1])) + " |"
                    rows.insert(1, header_sep)
                table.replace_with("\n\n" + "\n".join(rows) + "\n\n")

        text = soup.get_text(" ", strip=True)
        text = re.sub(r"\n{3,}", "\n\n", text)
        text = re.sub(r" {2,}", " ", text)
        return text.strip(), metadata

    def fetch(self, url: str) -> tuple[str, str, dict]:
        """
        Fetch and extract high-quality webpage text.
        Returns: (extracted_text, status, metadata)
        status: 'success' | 'partial' | 'blocked_or_invalid_url' | 'blocked_redirect' | 'fetch_failed'
        """
        if not self._is_public_http_url(url):
            return "", "blocked_or_invalid_url", {}

        try:
            response = self.session.get(url, timeout=self.timeout, allow_redirects=True)
            response.raise_for_status()

            if not self._is_public_http_url(response.url):
                return "", "blocked_redirect", {}

            content_type = response.headers.get("content-type", "").lower()
            if content_type and not any(ct in content_type for ct in ("text/html", "text/plain", "application/xhtml+xml", "text/xml")):
                return "", "unsupported_content_type", {}

            # First attempt: Trafilatura (handles main text, eliminates menus/footers)
            metadata = {}
            text = trafilatura.extract(
                response.text,
                include_comments=False,
                include_tables=True,
                include_formatting=True,
                no_fallback=False
            )

            # Trafilatura metadata extraction
            try:
                res_meta = trafilatura.extract_metadata(response.text)
                if res_meta:
                    if res_meta.author:
                        metadata["author"] = res_meta.author
                    if res_meta.date:
                        metadata["published_date"] = res_meta.date
            except Exception:
                pass

            # Fallback to BeautifulSoup if Trafilatura returned insufficient text
            if not text or len(text.strip()) < 180:
                soup = BeautifulSoup(response.text, "html.parser")
                soup_text, soup_meta = self._clean_soup_html(soup)
                if len(soup_text) > len(text or ""):
                    text = soup_text
                    metadata.update(soup_meta)

            text = (text or "").strip()
            
            # Classification
            if len(text) >= 250:
                return text[:35000], "success", metadata
            elif len(text) >= 80:
                return text, "partial", metadata
            else:
                return text, "short_or_partial_extraction", metadata

        except Exception as exc:
            return "", f"fetch_failed: {type(exc).__name__}", {}
