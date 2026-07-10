# mutne-timetables

Static bus timetable page for the Mutne stop (gmina Jeleśnia, powiat żywiecki),
hosted at https://rozklad.mutne.pl via Cloudflare Pages, auto-deployed from this repo.

## Architecture

- `index.html` — single self-contained page, no dependencies. Dark theme, mono
  times, live clock, day-type detection (Pon–Pt / Sob / Niedz+święta), next
  departure highlighted with countdown, past departures dimmed.
- `scripts/update_timetables.py` — stdlib-only scraper. Rewrites the section of
  `index.html` between `// AUTO-DATA:START` and `// AUTO-DATA:END` markers.
- `.github/workflows/update-timetables.yml` — runs the scraper daily 02:00 UTC
  (+ manual dispatch), commits only on change. Git log = changelog of county
  timetable updates.

## Data source

https://komunikacjapowiatuzywieckiego.pl — static trasownik.net HTML, no GTFS/API.

- `przystanek-98.html` — authoritative list of lines serving Mutne. The scraper
  checks it and fails loudly if a new line appears that isn't in `LINES`.
- `linia-XXX.html` — stable per-line entry points. Stop-page URLs embed the
  valid-from date (e.g. `rozklad-233_20260209-15-2.html`) so they rot on every
  update; always enter via the line pages and follow links with anchor text "Mutne".

## Lines at Mutne (as of 2026-06)

| Line | Route | Operator | Valid from |
|------|-------|----------|------------|
| 231 | Żywiec – Mutne – Pewel Wielka | Cedrom J. Kamiński | 09.02.2026 |
| 232 | Żywiec – Mutne – Koszarawa (Jałowiec) | Team Bus J. Wróbel | 16.03.2026 |
| 233 | Żywiec – Mutne – Korbielów – Krzyżówki | Cedrom J. Kamiński | 09.02.2026 |
| 234 | Żywiec – Mutne – Sopotnia Wielka | Chrustek Travel | 23.03.2026 |

Only county-site lines are shown. An unnumbered "F.U.H Józef Kamiński" poster at
the stop was determined to be the pre-county-network version of 233 (same
operator as Cedrom, same phone) and was deliberately dropped.

## Findings / conventions

- Physical posters at the stop go stale: photographed 01.01.2026 versions
  differed from the site by several minutes and missing courses (line 234 was
  absent from the posters entirely). Trust the site, never the posters.
- Course markers: `L` (do Leśnianka II), `S` (przez Pola Lisickich Szpital),
  `K` (232: przez Koszarawa Bystra; 233: do Korbielów Kamienna),
  `B` (do Koszarawa Bystra pętla).
- `#` on the site marks which operator runs a course — dropped by the scraper as
  noise, its legend entry is skipped too.
- Weekday school/non-school variants (232, 234) are merged by the scraper:
  school-only courses get `N`, holiday-only would get `F`, legend entries added
  automatically.
- 232: Nov–Mar bad weather may limit service through Koszarawa Bystra (the
  "Uwaga" note, scraped into the legend).
- No service network-wide: 1 Jan, Easter Sunday/Monday, 25–26 Dec; holidays
  follow the Sunday schedule.
- Scraper fails loudly (empty day section, missing Mutne links, unknown line)
  rather than writing garbage — a red workflow means the page keeps serving the
  last good data.
- The county publishes new schedules ahead of their "ważny od" date (dropping
  the old pages at the same time). `defer_future_schedules` keeps the last
  committed entry for a line until its new valid-from date arrives, so the page
  never shows a not-yet-effective schedule.

## Conventions for changes

- Keep `index.html` self-contained: no external fonts, scripts, or CSS.
- Simplicity over cleverness; stdlib only in the scraper.
- New line: add to `LINES` (color + operator) in the scraper, add a `--cXXX`
  CSS variable, optionally a nice `LABELS` entry.
