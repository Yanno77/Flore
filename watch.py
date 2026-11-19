#!/usr/bin/env python3
"""Lost-dog watcher: checks Swiss lost/found-pet sites for new FOUND-dog posts
in canton Vaud and sends a loud push notification to your phone via ntfy.

Runs every 10 minutes on GitHub Actions (see .github/workflows/watch.yml).
State (posts already seen) is kept in seen.json, committed back to the repo.
"""
import json
import os
import re
import sys
import unicodedata
import urllib.request

NTFY_TOPIC = os.environ.get("NTFY_TOPIC", "").strip()
STATE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "seen.json")

# Posts you have already followed up, so they never ring again.
IGNORE_KEYS = {"petalert:379460", "petalert:379461"}

# Pages listing recent alerts for canton Vaud.
SOURCES = [
    ("PetAlert Vaud", "https://m.pet-alert-vaud.ch/fr/recherche/decouverte-switzerland-vaud-animaux"),
    ("PetAlert", "https://www.petalert.fr/fr/recherche/alertes-suisse-vaud-animaux"),
    ("PetAlert CH", "https://m.petalert.ch/en/search/alertes-switzerland-vaud-animaux"),
    ("PetAlert Vaud home", "https://www.pet-alert-vaud.ch/"),
    ("chien-perdu.org", "https://www.chien-perdu.org/fr-ch/rechercher/ch/vaud"),
]

# Communes around Lausanne (as they appear in URL slugs, no accents/hyphens).
NEAR_LAUSANNE = [
    "lausanne", "romanel", "prilly", "renens", "pully", "epalinges", "crissier",
    "cheseaux", "jouxtens", "mezery", "bussigny", "ecublens", "chavannes",
    "lemont", "le-mont", "belmont", "lutry", "paudex", "savigny", "cugy",
    "morrens", "bretigny", "froideville", "villars-sainte-croix", "st-sulpice",
    "saint-sulpice", "chexbres", "montpreveyres", "bottens", "assens",
]

HEADERS = {
    "User-Agent": ("Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) "
                   "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1"),
    "Accept-Language": "fr-CH,fr;q=0.9,en;q=0.8",
}

# PetAlert found alerts: /fr/alerte-decouverte/379460-chien-trouve-suisse-vaud-town
#                        /en/alert-found/123456-dog-found-switzerland-vaud-town
PETALERT_RE = re.compile(
    r'href="([^"]*/(?:alerte-decouverte|alert-found|discovery-alert)/(\d+)-([^"?#]*))"', re.I)
# chien-perdu.org found listings: any link mentioning "trouve" with a 5+ digit id.
CHIENPERDU_RE = re.compile(r'href="([^"]*trouve[^"]*?(\d{5,})[^"]*)"', re.I)


def fetch(url):
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=25) as r:
        return r.read().decode("utf-8", errors="replace")


def absolute(base, href):
    if href.startswith("http"):
        return href
    m = re.match(r"(https?://[^/]+)", base)
    return (m.group(1) if m else "") + ("" if href.startswith("/") else "/") + href


def find_posts(name, url, html):
    posts = {}
    for href, pid, slug in PETALERT_RE.findall(html):
        if not re.search(r"chien|dog|hund|cane", slug, re.I):
            continue  # cats etc.
        posts["petalert:" + pid] = {"source": name, "url": absolute(url, href), "slug": slug}
    if "chien-perdu.org" in url:
        for href, pid in CHIENPERDU_RE.findall(html):
            posts["chienperdu:" + pid] = {"source": name, "url": absolute(url, href),
                                          "slug": href.rsplit("/", 1)[-1]}
    return posts


def town_from(slug):
    s = slug.lower()
    for marker in ("-vaud-", "-vd-"):
        if marker in s:
            return s.split(marker, 1)[1].replace("-", " ").strip() or "?"
    return s.replace("-", " ")[:40]


def near_lausanne(slug):
    s = slug.lower().replace("-", "")
    return any(k.replace("-", "") in s for k in NEAR_LAUSANNE)


def ascii_only(text):
    return unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()


def notify(title, message, priority=5, click=None, tags="rotating_light,dog"):
    if not NTFY_TOPIC:
        print("NTFY_TOPIC not set; would notify:", title, "|", message)
        return
    headers = {"Title": ascii_only(title), "Priority": str(priority), "Tags": tags}
    if click:
        headers["Click"] = click
    req = urllib.request.Request("https://ntfy.sh/" + NTFY_TOPIC,
                                 data=message.encode("utf-8"), headers=headers, method="POST")
    urllib.request.urlopen(req, timeout=20).read()


def main():
    first_run = not os.path.exists(STATE_FILE)
    seen = set()
    if not first_run:
        with open(STATE_FILE) as f:
            seen = set(json.load(f))

    found, working = {}, 0
    for name, url in SOURCES:
        try:
            posts = find_posts(name, url, fetch(url))
            print(f"{name}: {len(posts)} found-dog links")
            working += 1
            for k, v in posts.items():
                found.setdefault(k, v)
        except Exception as e:  # one broken site must not stop the others
            print(f"{name}: ERROR {e}", file=sys.stderr)

    new = {k: v for k, v in found.items() if k not in seen and k not in IGNORE_KEYS}

    if first_run:
        notify("Dog watcher is running",
               f"Watching {working}/{len(SOURCES)} sites. {len(found)} existing posts recorded; "
               "you'll only be alerted about NEW found-dog posts from now on.",
               priority=3, tags="white_check_mark")
    else:
        for k, v in new.items():
            town = town_from(v["slug"])
            close = near_lausanne(v["slug"])
            notify(("NEW FOUND DOG - " if close else "New found dog (Vaud) - ") + town.title(),
                   f"{v['source']}: {v['url']}\nTap to open the post.",
                   priority=5 if close else 4, click=v["url"])
            print("ALERT:", k, v["url"])

    if working == 0 and not first_run:
        print("All sources failed this run.", file=sys.stderr)

    seen |= set(found)
    with open(STATE_FILE, "w") as f:
        json.dump(sorted(seen), f, indent=0)


if __name__ == "__main__":
    main()
