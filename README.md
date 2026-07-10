# rozklad.mutne.pl

Rozkład jazdy busów dla przystanku **Mutne** (gmina Jeleśnia, powiat żywiecki).

**Strona: https://rozklad.mutne.pl**

Jedna prosta strona zamiast czterech papierowych tabliczek na słupku — z zegarem,
podświetlonym najbliższym odjazdem i odliczaniem do niego. Dane są pobierane
automatycznie ze strony [komunikacjapowiatuzywieckiego.pl](https://komunikacjapowiatuzywieckiego.pl),
więc rozkład na stronie jest zawsze aktualny, nawet gdy tabliczki na przystanku
się zestarzeją.

## Linie

| Linia | Trasa | Przewoźnik |
|-------|-------|------------|
| 231 | Żywiec – Mutne – Pewel Wielka | Cedrom J. Kamiński |
| 232 | Żywiec – Mutne – Koszarawa (Jałowiec) | Team Bus J. Wróbel |
| 233 | Żywiec – Mutne – Korbielów – Krzyżówki | Cedrom J. Kamiński |
| 234 | Żywiec – Mutne – Sopotnia Wielka | Chrustek Travel |

## Jak to działa

- [`index.html`](index.html) — cała strona w jednym pliku, bez zależności,
  hostowana na Cloudflare Pages.
- [`scripts/update_timetables.py`](scripts/update_timetables.py) — scraper
  (czysty Python, bez bibliotek), który pobiera rozkłady ze strony powiatu
  i wpisuje je do `index.html`.
- [GitHub Actions](.github/workflows/update-timetables.yml) uruchamia scraper
  codziennie o 02:00 UTC i commituje tylko, gdy dane faktycznie się zmieniły —
  historia commitów to zarazem dziennik zmian rozkładów.
- Rozkład opublikowany przez powiat z wyprzedzeniem (data „ważny od"
  w przyszłości) nie jest pokazywany przed czasem — do tego dnia strona serwuje
  rozkład obowiązujący.
- Scraper przy każdej niespodziance (nowa linia na przystanku, pusta sekcja,
  zmiana struktury strony) kończy się błędem zamiast zapisać śmieci — czerwony
  workflow oznacza, że strona dalej serwuje ostatnie dobre dane.

Uruchomienie lokalne:

```
python3 scripts/update_timetables.py
```

## Zgłaszanie błędów

Rozkład na stronie odzwierciedla dane powiatu — jeśli bus przyjechał o innej
godzinie, najpierw sprawdź [stronę źródłową](https://komunikacjapowiatuzywieckiego.pl/przystanek-98.html).
Błędy samej strony można zgłaszać przez
[Issues](../../issues) albo na admin@mutne.pl.
