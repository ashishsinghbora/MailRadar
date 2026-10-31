import logging
from typing import List, Set
from urllib.parse import urljoin, urlparse
import httpx
from bs4 import BeautifulSoup
from backend.core.ssrf import validate_url_ssrf_safe, SSRFSecurityError
from backend.discovery.base import DiscoveredSourceContent

logger = logging.getLogger(__name__)


class WebsiteAdapter:
    def __init__(self, max_depth: int = 1, timeout: float = 8.0):
        self.max_depth = max_depth
        self.timeout = timeout
        self.headers = {
            "User-Agent": "MailRadar-Intelligence-Bot/1.0 (+https://github.com/ashishsinghbora/MailRadar)",
            "Accept": "text/html,application/xhtml+xml"
        }

    async def crawl_site(self, root_url: str) -> List[DiscoveredSourceContent]:
        results: List[DiscoveredSourceContent] = []
        if not root_url:
            return results

        try:
            safe_root = validate_url_ssrf_safe(root_url)
        except SSRFSecurityError as e:
            logger.warning(f"Blocked SSRF attempt on target '{root_url}': {e}")
            return results

        parsed_root = urlparse(safe_root)
        allowed_domain = parsed_root.netloc.lower()

        visited: Set[str] = set()
        queue: List[(str, int)] = [(safe_root, 0)]

        # Targeted paths to inspect for official maintainer info
        preferred_paths = ["contact", "about", "team", "community", "security", "maintainers"]

        async with httpx.AsyncClient(
            timeout=self.timeout,
            follow_redirects=True,
            max_redirects=3
        ) as client:
            while queue:
                current_url, depth = queue.pop(0)
                if current_url in visited or depth > self.max_depth:
                    continue
                visited.add(current_url)

                try:
                    # Validate safe before GET
                    validate_url_ssrf_safe(current_url)
                    resp = await client.get(current_url, headers=self.headers)
                    if resp.status_code != 200:
                        continue

                    content_type = resp.headers.get("content-type", "")
                    if "text/html" not in content_type and "text/plain" not in content_type:
                        continue

                    soup = BeautifulSoup(resp.text, "html.parser")
                    # Remove script and style tags
                    for s in soup(["script", "style", "noscript", "svg"]):
                        s.extract()

                    cleaned_text = soup.get_text(separator="\n", strip=True)

                    results.append(
                        DiscoveredSourceContent(
                            source_url=str(resp.url),
                            source_category="OFFICIAL_WEBSITE",
                            content=cleaned_text,
                            metadata={"title": soup.title.string if soup.title else ""}
                        )
                    )

                    # Extract same-domain relevant links for depth 1
                    if depth < self.max_depth:
                        for a in soup.find_all("a", href=True):
                            href = a["href"].strip()
                            resolved = urljoin(str(resp.url), href)
                            p = urlparse(resolved)
                            if p.netloc.lower() == allowed_domain:
                                # Check if it matches preferred keywords
                                path_lower = p.path.lower()
                                if any(kw in path_lower for kw in preferred_paths) and resolved not in visited:
                                    queue.append((resolved, depth + 1))

                except Exception as e:
                    logger.debug(f"Failed to crawl '{current_url}': {e}")

        return results
