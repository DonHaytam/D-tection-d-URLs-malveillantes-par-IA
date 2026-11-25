"""URL validation and normalization helpers.

Passive analysis only: never fetches, resolves, or renders URLs.
"""
import re
from urllib.parse import urlparse, urlunparse


def normalize_url(url):
    """Normalize a URL string for deduplication and storage.

    - Strip whitespace.
    - If no scheme present, prepend 'https://'.
    - Lowercase the host (not the path/query, to preserve case-sensitive paths).
    - Remove trailing whitespace and a single trailing slash on the path is kept as-is
      (we do not collapse path semantics).
    """
    if url is None:
        return None
    u = str(url).strip()
    if not u:
        return None
    if "://" not in u:
        u = "https://" + u
    try:
        p = urlparse(u)
    except Exception:
        return u
    if not p.netloc:
        # malformed; return as-is
        return u
    netloc = p.netloc.lower()
    # remove default ports
    if netloc.endswith(":80"):
        netloc = netloc[:-3]
    if netloc.endswith(":443"):
        netloc = netloc[:-4]
    return urlunparse((p.scheme.lower(), netloc, p.path, p.params, p.query, p.fragment))


def is_valid_url(url):
    """Basic syntactic validity check (no network access)."""
    if url is None:
        return False
    u = str(url).strip()
    if not u or len(u) > 8192:
        return False
    if "://" not in u:
        u = "https://" + u
    try:
        p = urlparse(u)
    except Exception:
        return False
    if not p.netloc:
        return False
    # host must contain at least one dot or be localhost/ip-ish
    host = p.netloc.split(":")[0]
    if not host or " " in host:
        return False
    # reject obvious garbage
    if "\n" in u or "\r" in u or "\t" in u:
        return False
    return True


def extract_components(url):
    """Extract scheme, host, path, query, fragment from a URL (passive)."""
    u = url if "://" in str(url) else "https://" + str(url)
    p = urlparse(str(u).strip())
    host = p.netloc.split(":")[0].lower()
    return {
        "scheme": p.scheme.lower(),
        "host": host,
        "port": p.port,
        "path": p.path,
        "query": p.query,
        "fragment": p.fragment,
    }
