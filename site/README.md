# 8eonAI — website

Statische site (HTML/CSS/JS, geen build-stap) die 8eonAI positioneert als AI-consultant.
Gebouwd volgens het productieplan in Notion: *8eon Website Refonte — Productieplan (façon 187n)*.

## Structuur

```
site/
├── index.html                             Home
├── dashboards.html                        Galerij met de zes live demo-dashboards
├── demo.html                              Boekingspagina met Calendly-embed
├── juridisch/
│   ├── algemene-voorwaarden.html          Versie augustus 2026
│   ├── privacybeleid.html
│   ├── cookiebeleid.html
│   ├── verwerkersovereenkomst.html
│   └── opzeg-en-annuleringsbeleid.html
├── assets/css/styles.css                  Design tokens + componenten
├── assets/js/main.js                      Nav, scroll, reveals, cookietoestemming, meting
├── vercel.json                            Cache- en securityheaders
├── robots.txt
└── sitemap.xml
```

## Design tokens

Gemeten op het site-modèle met `getComputedStyle`, niet geraden. Alles staat in één
`:root`-blok bovenin `styles.css`.

| Token | Waarde |
| --- | --- |
| Achtergrond | `#161514` |
| Tekst / accent | `#f4f2ee` |
| Gedempt | `#a39d92` · `#726c62` |
| Koppen | Newsreader (Google Fonts) |
| Body | Inter (Google Fonts) |
| Buttons | pill, `999px` |
| Radius kaarten | `3px` / `10px` |

## Lokaal draaien

Geen build nodig — het is platte HTML.

```bash
cd site && python3 -m http.server 8080
# open http://localhost:8080
```

## Deployen

```bash
cd site
vercel deploy --prod --yes --scope <scope>
```

`vercel.json` zet `Cache-Control: public, max-age=0, must-revalidate` op css en js.
Wijzig je een asset, verhoog dan ook de querystring in de `<link>`/`<script>`-tags
(`styles.css?v=2`). Dat voorkomt dat bezoekers na een redeploy de oude CSS blijven zien.

## Vóór livegang invullen

- [ ] `data-analytics-id="VUL_IN_GA4_ID"` in elke HTML-pagina vervangen door het echte GA4-ID.
      Zolang de placeholder staat, laadt er geen analytics — ook niet na toestemming.
- [ ] Cases en testimonials op de home (blokken met `class="todo"`) invullen met echte
      cijfers, of de hele sectie verwijderen. **Nooit live met verzonnen resultaten.**
- [ ] Foto toevoegen op `demo.html` (`.who__avatar` → `<img src="/assets/willem.jpg">`).
- [ ] OG-image maken op `assets/og-image.png` (1200×630).
- [ ] Plaatsnaam bevestigen — nu ingevuld als Geffen op basis van postcode 5386 LA.
- [ ] Domein koppelen en de redirects van de oude URL's inregelen.
- [ ] Juridische check op de vijf documenten in `juridisch/`.

## Keuzes die in de code vastliggen

- **Geen prijzen op de site.** Het bedrag volgt uit de offerte na het gesprek.
- **Geen eigendomsclaim.** De algemene voorwaarden geven de opdrachtgever een
  gebruiksrecht voor de duur van de overeenkomst, geen eigendom. De site zegt dat
  ook zo, inclusief de afkoopregeling uit artikel 8.7.
- **Analytics achter toestemming.** De cookiebanner blokkeert het laden van analytics
  tot iemand akkoord gaat.
- **Eén schrijfwijze: 8eonAI.** Overal gelijk aan de KvK-inschrijving en de voorwaarden.
