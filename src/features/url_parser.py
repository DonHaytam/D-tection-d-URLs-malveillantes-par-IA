"""URL parsing helpers (passive, no network access)."""
from urllib.parse import urlparse, parse_qs


def parse_url(url):
    u = url if "://" in str(url) else "https://" + str(url)
    p = urlparse(str(u).strip())
    host = p.netloc.split(":")[0].lower() if p.netloc else ""
    # safe port extraction
    port = None
    try:
        if p.port is not None:
            port = p.port
    except ValueError:
        port = None
    # fallback: try splitting netloc
    if port is None and ":" in (p.netloc or ""):
        try:
            port = int(p.netloc.rsplit(":", 1)[-1])
        except ValueError:
            port = None
    return {
        "scheme": (p.scheme or "").lower(),
        "host": host,
        "port": port,
        "path": p.path or "",
        "query": p.query or "",
        "fragment": p.fragment or "",
        "params": p.params or "",
    }


def count_query_params(q):
    try:
        return len(parse_qs(q, keep_blank_values=True))
    except Exception:
        return 0
