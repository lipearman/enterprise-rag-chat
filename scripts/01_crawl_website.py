import asyncio, os, re, json, time, aiohttp
import xml.etree.ElementTree as ET
from urllib.parse import urljoin, urlparse, urlunparse, parse_qsl, urlencode
from bs4 import BeautifulSoup
from _common import CRAWL_DIR, ensure_dir

START_URL = os.getenv("START_URL", "https://www.locktonwattana.co.th")
OUTPUT_FILE = f"{CRAWL_DIR}/raw_pages.jsonl"
MAX_PAGES = int(os.getenv("MAX_PAGES", "20000"))
CONCURRENCY = int(os.getenv("CRAWL_CONCURRENCY", "5"))

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "th,en-US;q=0.9,en;q=0.8",
}

def normalize_url(url):
    if not url: return ""
    url = url.split("#")[0].strip()
    p = urlparse(url)
    path = p.path.rstrip("/") if p.path != "/" else p.path
    blocked = {"utm_source","utm_medium","utm_campaign","utm_term","utm_content","fbclid","gclid"}
    q = urlencode([(k,v) for k,v in parse_qsl(p.query, keep_blank_values=True) if k.lower() not in blocked])
    return urlunparse((p.scheme.lower(), p.netloc.lower(), path, "", q, ""))

def same_domain(url):
    return urlparse(url).netloc.lower() == urlparse(START_URL).netloc.lower()

def valid(url):
    if not url or not url.startswith("http") or not same_domain(url): return False
    lower = url.lower()
    exts = [".jpg",".jpeg",".png",".gif",".webp",".svg",".pdf",".zip",".mp4",".mp3",".css",".js",".doc",".docx",".xls",".xlsx",".ppt",".pptx"]
    if any(lower.endswith(e) for e in exts): return False
    blocked = ["/wp-json/","/xmlrpc.php","/feed","/wp-admin/","/wp-login.php"]
    return not any(b in lower for b in blocked)

async def fetch_sitemap(session, sitemap):
    urls = set()
    try:
        async with session.get(sitemap, timeout=aiohttp.ClientTimeout(total=30)) as r:
            if r.status >= 400: return urls
            txt = await r.text()
        root = ET.fromstring(txt)
        for e in root.iter():
            if e.tag.endswith("loc") and e.text:
                loc = normalize_url(e.text.strip())
                if loc.endswith(".xml"):
                    urls |= await fetch_sitemap(session, loc)
                elif valid(loc):
                    urls.add(loc)
    except Exception:
        pass
    return urls

async def sitemap_urls(session):
    cands = [urljoin(START_URL, x) for x in ["/sitemap.xml","/sitemap_index.xml","/page-sitemap.xml","/post-sitemap.xml","/category-sitemap.xml","/th/sitemap.xml","/en/sitemap.xml"]]
    out = set()
    for c in cands:
        print("[SITEMAP]", c)
        out |= await fetch_sitemap(session, c)
    return sorted(out)

def extract_links(html, base):
    soup = BeautifulSoup(html or "", "html.parser")
    links = set()
    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        if href.startswith(("mailto:","tel:","javascript:")): continue
        u = normalize_url(urljoin(base, href))
        if valid(u): links.add(u)
    return links

def extract_title(html):
    soup = BeautifulSoup(html or "", "html.parser")
    tag = soup.find("title")
    if tag: return tag.get_text(strip=True)
    h1 = soup.find("h1")
    if h1: return h1.get_text(strip=True)
    return ""

async def fetch_page(session, url):
    try:
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=30), allow_redirects=True) as r:
            if r.status >= 400:
                return None, []
            ct = r.headers.get("content-type", "")
            if "text/html" not in ct:
                return None, []
            html = await r.text(errors="replace")
            return html, extract_links(html, url)
    except Exception as e:
        print(f"[ERROR] {url}: {e}")
        return None, []

async def main():
    ensure_dir()
    visited = set()
    conn = aiohttp.TCPConnector(ssl=False, limit=CONCURRENCY)
    async with aiohttp.ClientSession(headers=HEADERS, connector=conn) as session:
        seeds = set(await sitemap_urls(session))
        seeds.update([START_URL, urljoin(START_URL,"/th"), urljoin(START_URL,"/en")])
        print(f"[INFO] Starting with {len(seeds)} seed URLs")

        queue = asyncio.Queue()
        for url in seeds:
            await queue.put(url)

        with open(OUTPUT_FILE, "w", encoding="utf-8") as fout:
            async def worker():
                while True:
                    try:
                        url = queue.get_nowait()
                    except asyncio.QueueEmpty:
                        await asyncio.sleep(0.5)
                        try:
                            url = queue.get_nowait()
                        except asyncio.QueueEmpty:
                            break
                    url = normalize_url(url)
                    if not url or url in visited or len(visited) >= MAX_PAGES or not valid(url):
                        queue.task_done()
                        continue
                    visited.add(url)
                    print(f"[CRAWL] {len(visited)} {url}")
                    html, links = await fetch_page(session, url)
                    if html:
                        title = extract_title(html)
                        row = {"url": url, "title": title, "html": html, "crawled_at": time.strftime("%Y-%m-%d %H:%M:%S")}
                        fout.write(json.dumps(row, ensure_ascii=False) + "\n")
                        fout.flush()
                        for l in links:
                            if l not in visited:
                                await queue.put(l)
                    queue.task_done()

            workers = [asyncio.create_task(worker()) for _ in range(CONCURRENCY)]
            await asyncio.gather(*workers)

    print("DONE", len(visited), OUTPUT_FILE)

if __name__ == "__main__":
    asyncio.run(main())
