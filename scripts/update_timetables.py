#!/usr/bin/env python3
"""Refresh the AUTO-DATA section of index.html with current Mutne timetables
from komunikacjapowiatuzywieckiego.pl. Stdlib only.

The site is static trasownik.net HTML. Stop-page URLs embed the valid-from
date, so we always enter via the stable linia-XXX.html pages and follow the
links whose anchor text is "Mutne".
"""

import json
import re
import sys
import urllib.request
from pathlib import Path

BASE = "https://www.komunikacjapowiatuzywieckiego.pl/"
HTML_FILE = Path(__file__).resolve().parent.parent / "index.html"
START_MARK = "// AUTO-DATA:START"
END_MARK = "// AUTO-DATA:END"

LINES = {
    "231": {"color": "var(--c231)", "op": "Cedrom J. Kamiński"},
    "232": {"color": "var(--c232)", "op": "Team Bus J. Wróbel"},
    "233": {"color": "var(--c233)", "op": "Cedrom J. Kamiński"},
}

# nicer direction labels; anything unknown falls back to "→ <kierunek>"
LABELS = {
    "Żywiec, Dworzec Autobusowy": "→ Żywiec (dworzec autobusowy, 27 min)",
    "Pewel Wielka, Łobozówka": "→ Pewel Wielka (Łobozówka, 16 min)",
    "Koszarawa, Jałowiec Pętla": "→ Koszarawa (Jałowiec pętla, 26 min)",
    "Krzyżówki, Posesja 303": "→ Krzyżówki (przez Jeleśnię i Korbielów, 27 min)",
}


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "bus.mutne.pl updater"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8", "replace")


def strip_tags(html):
    text = re.sub(r"<script.*?</script>", " ", html, flags=re.S)
    text = re.sub(r"<[^>]+>", "\n", text)
    return re.sub(r"[ \t]+", " ", text)


def mutne_urls(line):
    """Both Mutne stop-page URLs (one per direction) from the line page."""
    html = fetch(f"{BASE}linia-{line}.html")
    urls = []
    for href in re.findall(r'href="([^"]*rozklad-[^"]+)"[^>]*>\s*Mutne\s*<', html):
        if href not in urls:
            urls.append(href)
    if len(urls) != 2:
        raise RuntimeError(f"linia {line}: oczekiwano 2 linków Mutne, jest {len(urls)}")
    return [u if u.startswith("http") else BASE + u.lstrip("/") for u in urls]


def parse_times(section):
    """Times like 06:32 / 08:19K / 13:13LS as 'HH:MM' or 'HH:MM MARKS'."""
    body = section.split("W dniach 1 stycznia")[0]
    out = []
    for t, marks in re.findall(r"\b(\d{1,2}:\d{2})([A-Z#]*)", body):
        out.append((t, marks.replace("#", "")))  # '#' = operator info, not useful here
    return out


def fmt(times):
    return [f"{t} {m}" if m else t for t, m in times]


def parse_stop(url):
    text = strip_tags(fetch(url))
    direction = [d.strip() for d in re.findall(r"Kierunek:\s*\n+\s*([^\n]+)", text)][-1]
    valid = re.search(r"ważny od:\s*\n*\s*([0-9]{2}\.[0-9]{2}\.[0-9]{4})", text).group(1)

    sat, sun, wd_school, wd_free, wd_plain = [], [], None, None, None
    for sec in re.split(r"\n(?=(?:Od poniedziałku|Soboty|Niedziele))", text)[1:]:
        head = sec.split("\n", 1)[0]
        times = parse_times(sec)
        if head.startswith("Od poniedziałku"):
            if "nauki szkolnej" in head and "wolne" not in head:
                wd_school = times
            elif "wolne" in head:
                wd_free = times
            else:
                wd_plain = times
        elif head.startswith("Soboty"):
            sat = times
        elif head.startswith("Niedziele"):
            sun = times

    extra_legend = []
    if wd_plain is not None:
        wd = wd_plain
    else:
        # merge school/non-school day variants, mark the differences
        wd_school, wd_free = wd_school or [], wd_free or []
        school_t = {t for t, _ in wd_school}
        free_t = {t for t, _ in wd_free}
        wd = [(t, m + "N" if t not in free_t else m) for t, m in wd_school]
        wd += [(t, m + "F") for t, m in wd_free if t not in school_t]
        wd.sort()
        if any(t not in free_t for t in school_t):
            extra_legend.append("N – kursuje tylko w dni nauki szkolnej")
        if any(t not in school_t for t in free_t):
            extra_legend.append("F – kursuje tylko w dni wolne od nauki szkolnej")

    legend, notes = [], []
    m = re.search(r"Objaśnienia:(.*?)Rozkład jazdy ważny", text, re.S)
    if m:
        lines = [l.strip() for l in m.group(1).split("\n") if l.strip()]
        i = 0
        while i < len(lines):
            if re.fullmatch(r"[A-Z#]", lines[i]):
                j = i + 1
                while j < len(lines) and lines[j] in ("−", "-"):
                    j += 1
                if j < len(lines) and lines[i] != "#":
                    legend.append(f"{lines[i]} – {lines[j].lstrip('−- ').strip()}")
                i = j + 1
            else:
                if "Uwaga" in lines[i]:
                    notes.append(lines[i].lstrip("−- ").strip())
                i += 1
    legend += extra_legend + notes

    return {
        "name": LABELS.get(direction, f"→ {direction}"),
        "wd": fmt(wd), "sat": fmt(sat), "sun": fmt(sun),
        "direction": direction, "valid": valid, "legend": legend,
    }


def build_line(line, cfg):
    dirs = [parse_stop(u) for u in mutne_urls(line)]
    dirs.sort(key=lambda d: "Żywiec" not in d["direction"])  # Żywiec first
    legend, seen = [], set()
    for d in dirs:
        for item in d["legend"]:
            if item not in seen:
                seen.add(item)
                legend.append(item)
    entry = {
        "badge": line,
        "color": cfg["color"],
        "op": f"{cfg['op']} · od {dirs[0]['valid']}",
        "legend": " · ".join(legend),
        "dirs": [{k: d[k] for k in ("name", "wd", "sat", "sun")} for d in dirs],
    }
    for d in entry["dirs"]:
        if not (d["wd"] and d["sat"] and d["sun"]):
            raise RuntimeError(f"linia {line}: pusta sekcja dnia w {d['name']}")
    return entry


def main():
    data = [build_line(line, cfg) for line, cfg in sorted(LINES.items())]
    block = "const DATA = " + json.dumps(data, ensure_ascii=False, indent=2) + ";"

    src = HTML_FILE.read_text(encoding="utf-8")
    a = src.index("\n", src.index(START_MARK)) + 1
    b = src.rindex("\n", 0, src.index(END_MARK)) + 1
    out = src[:a] + block + "\n" + src[b:]

    if out == src:
        print("Bez zmian.")
        return
    HTML_FILE.write_text(out, encoding="utf-8")
    for entry in data:
        print(f"{entry['badge']}: {entry['op']}")
    print("Zaktualizowano index.html")


if __name__ == "__main__":
    sys.exit(main())
