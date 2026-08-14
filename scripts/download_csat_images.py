#!/usr/bin/env python3
"""Download SuperKalam CSAT figure PNGs into static/upsc/assets/csat/.

CDN quirk: URLs must keep the double slash after the host
(e.g. https://d39jluplm5thpx.cloudfront.net//CSAT_2013_Q50_….png).
"""

from __future__ import annotations

import re
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = Path("/Users/pradheepvijayaraj/Desktop/LOOP DATA/PYQ/UPSC/CSE/PRELIMS/CSAT")
if not SRC.exists():
    SRC = ROOT / "LOOP DATA" / "PYQ" / "UPSC" / "CSE" / "PRELIMS" / "CSAT"
OUT = ROOT / "static" / "upsc" / "assets" / "csat"

IMG_RE = re.compile(r"!\[([^\]]*)\]\((https?://[^)]+)\)")
UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
)


def collect_urls() -> list[str]:
    seen: set[str] = set()
    urls: list[str] = []
    for path in sorted(SRC.glob("*/paper.json")):
        for m in IMG_RE.finditer(path.read_text(encoding="utf-8")):
            u = m.group(2)
            # Force double-slash form after domain (CloudFront allows this, 403 otherwise)
            if re.match(r"https?://[^/]+/[^/]", u) and "//" not in u[8:]:
                u = re.sub(r"(https?://[^/]+)/", r"\1//", u, count=1)
            if u not in seen:
                seen.add(u)
                urls.append(u)
    return urls


def fetch(url: str) -> tuple[str, str, int | str]:
    name = url.rstrip("/").split("/")[-1]
    dest = OUT / name
    if dest.exists() and dest.stat().st_size > 200:
        return ("skip", name, dest.stat().st_size)
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": UA,
            "Accept": "image/avif,image/webp,image/apng,image/*,*/*;q=0.8",
            "Referer": "https://www.superkalam.com/",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=45) as resp:
            data = resp.read()
        if data[:8] == b"\x89PNG\r\n\x1a\n" or data[:2] == b"\xff\xd8":
            dest.write_bytes(data)
            return ("ok", name, len(data))
        return ("bad", name, f"not an image ({len(data)} bytes)")
    except Exception as exc:  # noqa: BLE001
        return ("fail", name, str(exc))


def main() -> None:
    if not SRC.exists():
        raise SystemExit(f"CSAT source not found: {SRC}")
    OUT.mkdir(parents=True, exist_ok=True)
    urls = collect_urls()
    print(f"unique urls: {len(urls)}")
    ok = skip = fail = 0
    with ThreadPoolExecutor(max_workers=6) as pool:
        futures = [pool.submit(fetch, u) for u in urls]
        for fut in as_completed(futures):
            status, name, info = fut.result()
            if status == "ok":
                ok += 1
            elif status == "skip":
                skip += 1
            else:
                fail += 1
                print(status, name, info)
    print(f"done ok={ok} skip={skip} fail={fail} files={len(list(OUT.glob('*')))}")


if __name__ == "__main__":
    main()
