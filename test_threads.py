import json
from playwright.sync_api import sync_playwright

creds = json.load(open("threads_creds.json"))["cookies"]
q = "baking soda kanker"
with sync_playwright() as p:
    b = p.chromium.launch(headless=True)
    ctx = b.new_context()
    ck = []
    for k, v in creds.items():
        ck.append({"name": k, "value": v, "domain": ".threads.net", "path": "/"})
        ck.append({"name": k, "value": v, "domain": ".instagram.com", "path": "/"})
    ctx.add_cookies(ck)
    pg = ctx.new_page()
    pg.goto("https://www.threads.net/search?q=" + q.replace(" ", "%20"), timeout=30000)
    pg.wait_for_timeout(6000)
    txt = pg.inner_text("body")
    print("LOGIN STATE:", "Log in or sign up" not in txt)
    bodies = pg.query_selector_all("div")
    hits = []
    for d in bodies:
        t = d.inner_text().strip()
        if 20 < len(t) < 280 and q.split()[0] in t.lower():
            hits.append(t)
    print("hits:", len(hits))
    for h in hits[:5]:
        print(" -", h[:90])
    b.close()
