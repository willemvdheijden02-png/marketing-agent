# 🎯 Bouwplan — LinkedIn Lead Machine

> Uitgewerkt plan voor een automatische LinkedIn Sales Navigator lead-flow in het Marketing Agent Pro dashboard.
> Workflow gebaseerd op *"I Built a $10K LinkedIn Outreach Automation"* (Design with May).
> Dit document is het bouwplan — er is nog niets in het dashboard gewijzigd. Bouw het later zelf in aan de hand van dit plan.

---

## 1. De workflow in één beeld

Vijf stappen. Alleen stap 2 en 5 kosten jou tijd (± 15 min per dag).

| # | Stap | Wie | Wat gebeurt er |
|---|------|-----|----------------|
| 1 | **Zoeken & alerts** | LinkedIn (automatisch) | 3 opgeslagen Sales Navigator zoekopdrachten met alerts aan → wekelijks automatisch nieuwe matches in je mail |
| 2 | **Exporteren** | Jij (5 min/week) | Resultaten als CSV exporteren via Evaboot, Phantombuster of handmatig |
| 3 | **ICP-scoring** | AI (Claude) | Elke lead 0–100 gescoord op jouw ICP. Onder de drempel = afgekeurd, mét reden |
| 4 | **Personalisatie** | AI (Claude) | Per gekwalificeerde lead: connectienote (≤ 280 tekens) + follow-up DM in jouw merktoon |
| 5 | **Versturen** | Jij (15 min/dag) | Wachtrij in dashboard: profiel openen, note plakken, versturen, status bijwerken |

**Waarom versturen handmatig blijft:** automatisch verzenden via bots is tegen de LinkedIn-voorwaarden en de snelste route naar een geblokkeerd Sales Navigator-account. De AI doet 95% (vinden, filteren, scoren, schrijven) — de laatste klik is van jou. Veiliger én persoonlijker.

---

## 2. Sales Navigator instellen (eenmalig, ± 15 min)

Drie zoekopdrachten, elk met dezelfde basis: **bedrijfsgrootte 11–200** en **geografie Nederland**.

| Zoekopdracht | Functietitel (Current job title) | Branche (Industry) |
|---|---|---|
| **1 · E-commerce** | Founder · E-commerce Manager · Head of Growth | Retail · Consumer Goods |
| **2 · Agency** | Founder · Owner · Managing Director | Marketing & Advertising |
| **3 · Coach / SaaS** | Founder · CEO · Head of Growth | Software Development · Professional Training & Coaching |

Checklist per zoekopdracht:

- [ ] Bedrijfsgrootte: vink **11–50** én **51–200** aan (Sales Nav kent geen "11–200" als één optie)
- [ ] Geografie: Nederland (voeg België toe als je daar ook wilt werven)
- [ ] Extra kwaliteitsfilter: *"Posted on LinkedIn in past 30 days"* — actieve mensen accepteren en reageren vaker
- [ ] Klik **"Zoekopdracht opslaan"** en zet **alerts AAN** → LinkedIn mailt je wekelijks nieuwe profielen die in het filter vallen (je gratis aanvoer)

---

## 3. Het ICP — de poortwachter

Het ICP staat als instelbaar profiel in het dashboard (`icp_config.json`). Elke geïmporteerde lead wordt hiertegen gescoord; alleen échte matches komen door.

**Startwaarden:**

```json
{
  "functietitels": ["Founder", "Co-Founder", "Owner", "E-commerce Manager", "Head of Growth", "Marketing Manager"],
  "bedrijfsgrootte": "11-200 medewerkers",
  "branches": ["Retail", "E-commerce", "Marketing & Advertising", "Consultancy", "SaaS"],
  "regio": "Nederland",
  "min_score": 60
}
```

**Hoe de score werkt:** Claude krijgt het ICP + een batch leads en geeft per lead terug: `score` (0–100) en `reden` (één zin, Nederlands). De prompt is bewust streng.

- Score **≥ 60** → status `gekwalificeerd`, door naar outreach
- Score **< 60** → status `afgekeurd`, blijft zichtbaar mét reden (zo kun je je ICP bijstellen)

---

## 4. Architectuur — hoe het gebouwd moet zijn

Alles volgt de patronen die al in `app.py` zitten: een bot in de `BOTS`-dict, JSON-bestanden als opslag (zoals `merk.json`), en tools die Claude vanuit de chat kan aanroepen.

### 4.1 Drie lagen

| Laag | Inhoud |
|---|---|
| **UI** | Nieuwe **🎯 LinkedIn Leads Bot** in de sidebar. Rechterpaneel: zoekopdracht-knoppen, ICP-instellingen, CSV-import, flow-knop. Onder de chat: pipeline over de volle breedte |
| **Data** | `icp_config.json` (het profiel) en `leads.json` (alle leads + status + berichten). Import ontdubbelt op LinkedIn-URL en op naam + bedrijf |
| **AI** | Twee losse Claude-calls met strikte JSON-uitvoer: **scoren** (batches van ~12) en **outreach schrijven** (batches van ~10). Ook aanroepbaar als chat-tools |

### 4.2 Het lead-record (`leads.json`)

| Veld | Betekenis |
|---|---|
| `id`, `naam`, `functietitel`, `bedrijf` | Basis uit de CSV. Kolomnamen flexibel herkennen: `name`/`fullName`, `title`/`jobTitle`/`headline`, `company`/`companyName`, `firstName`+`lastName` |
| `branche`, `bedrijfsgrootte`, `linkedin_url` | Voor de ICP-score en de "Open profiel"-knop |
| `score`, `score_reden` | Resultaat van de ICP-scoring, blijft altijd zichtbaar |
| `note`, `followup` | De gegenereerde connectienote (≤ 280 tekens) en het follow-up bericht |
| `status`, `bron`, `datum` | Positie in de funnel, uit welke zoekopdracht/CSV de lead komt, importdatum |

### 4.3 Statussen — de funnel

```
nieuw → (AI-scoring) → gekwalificeerd → verstuurd → geaccepteerd → gesprek → klant
                     ↘ afgekeurd (buiten ICP, door de scoring)
                                  ↘ afgewezen (handmatig, bijv. verzoek genegeerd)
```

Elke statuswissel is één klik in de wachtrij — nooit een formulier.

### 4.4 De twee AI-prompts (kern van het systeem)

**Scoring** — invoer: ICP + batch leads (JSON) · uitvoer: alléén JSON

```
Scoor elke lead 0-100 op ICP-fit: functietitel (beslisser?),
bedrijfsgrootte, branche, regio. Wees streng: alleen echte
matches boven de 60.
→ [{"id":"...","score":85,"reden":"Founder bij retail-bedrijf, 40 fte"}]
```

**Outreach** — invoer: merknaam + niche + toon (uit de sidebar) + batch gekwalificeerde leads

```
Per lead: 'note' = NL connectienote, MAX 280 tekens, persoonlijk
(voornaam, functie, bedrijf), nieuwsgierig makend, GEEN pitch.
'followup' = kort bericht na acceptatie: waarde + lichte vraag.
→ [{"id":"...","note":"...","followup":"..."}]
```

Beide calls parsen het antwoord als JSON en schrijven direct terug naar `leads.json` — de chat is er niet voor nodig, één knop ("🚀 Run automatische flow") volstaat.

### 4.5 Chat-tools voor de bot

| Tool | Doet |
|---|---|
| `scoor_leads` | Scoort alle leads met status `nieuw` op het ICP |
| `genereer_outreach` | Schrijft note + follow-up voor gekwalificeerde leads zonder bericht |
| `laad_pipeline` | Geeft ICP + tellingen + actieve leads terug (voor overzichten en rapporten) |
| `update_lead_status` | Werkt de status van een lead bij op naam of id |

---

## 5. Het design — zo ziet het scherm eruit

```
┌────────────────────────────────────────────────────────────────────┐
│  🎯 LinkedIn Leads Bot                          [LinkedIn-blauw]   │
│  Sales Navigator leads — ICP scoring en outreach pipeline          │
├──────────────────────────────────────────────┬─────────────────────┤
│  CHAT (zoals bij elke bot)                   │  SALES NAVIGATOR    │
│                                              │  [E-commerce zoek.] │
│  Skills: Run lead flow · Pipeline overzicht  │  [Agency zoek.]     │
│  Connectienote · Follow-up DM · ICP check    │  [Coach/SaaS zoek.] │
│  Zoekstrategie · Opvolg email · Analyse      │  ▸ Filters (1x)     │
│                                              │  ▸ Mijn ICP         │
│                                              │  ─────────────────  │
│                                              │  LEADS IMPORTEREN   │
│                                              │  [CSV upload]       │
│                                              │  [🚀 Run auto flow] │
│                                              │  [📧 Rapport mail]  │
├──────────────────────────────────────────────┴─────────────────────┤
│  LEAD PIPELINE                                                     │
│  ┌──────┬──────────┬──────────┬──────────┬─────────┬────────────┐  │
│  │ 12   │ 8        │ 5        │ 3        │ 1       │ 9          │  │
│  │ Nieuw│ Gekwalif.│ Verstuurd│ Geaccept.│ Gesprek │ Buiten ICP │  │
│  └──────┴──────────┴──────────┴──────────┴─────────┴────────────┘  │
│                                                                    │
│  ▾ Sanne Bakker · E-commerce Manager @ StyleBoutique · score 92    │
│    ICP: E-commerce Manager bij retailbedrijf, 45 fte — sterke fit  │
│    ┌──────────────────────────────────────────────────────────┐    │
│    │ Hoi Sanne, ik zag dat je de webshop van StyleBoutique    │    │
│    │ runt — mooi hoe jullie de collectie presenteren. (...)   │    │
│    └──────────────────────────────────────────────────────────┘    │
│    [🔗 Open profiel]  [📤 Markeer verstuurd]  [❌ Afwijzen]        │
└────────────────────────────────────────────────────────────────────┘
```

**Ontwerpkeuzes:**

- Botkleur **LinkedIn-blauw `#0A66C2`** — direct herkenbaar tussen de andere bots
- Wachtrij gesorteerd op score, hoogste eerst: beste lead altijd bovenaan
- Note in een kopieerbaar codeblok (`st.code`) — één klik kopiëren, plakken bij het verzoek
- Statuswissel is één knop per kaart; de knop toont steeds de vólgende stap (verstuurd → geaccepteerd → gesprek → klant)
- Metrics-rij bovenaan de pipeline zodat je in één blik de funnel ziet

---

## 6. Bouwplan — vier fases (± 6 uur totaal)

> **Let op:** dit is de basisversie met `leads.json` als opslag. Omdat de definitieve stack **Supabase + Vercel** wordt (volautomatische aanvoer), geldt de aangepaste bouwvolgorde uit **hoofdstuk 8.5** — fase 1 hieronder vervalt dan grotendeels en de opslag gaat naar Supabase.

1. **Fundament: data + Sales Navigator** *(± 1 uur)*
   `icp_config.json` en `leads.json` met laad/opslaan-helpers (zelfde patroon als `merk.json`). De drie zoekopdrachten als deep-links (`https://www.linkedin.com/sales/search/people?keywords=...`) + filterchecklist. Zoekopdrachten in Sales Nav opslaan, alerts aan.

2. **Import: CSV naar leads** *(± 1 uur)*
   CSV-parser met flexibele kolomherkenning (Evaboot/Phantombuster/handmatige exports), ontdubbeling op URL en naam+bedrijf, status `nieuw`. Uploadknop in het rechterpaneel.

3. **AI-flow: scoren + outreach** *(± 2 uur)*
   De twee Claude-calls met JSON-uitvoer (batches, drempel uit ICP), gekoppeld aan één "🚀 Run automatische flow"-knop. Zelfde functies ook registreren als chat-tools (`TOOLS` + `voer_tool_uit`) zodat de bot ze kan gebruiken.

4. **Pipeline-UI + rapport** *(± 2 uur)*
   Metrics-rij, wachtrij-kaarten met note/follow-up/profielknop en statusknoppen. Pipeline-rapport via de bestaande `stuur_gmail`-tool. Daarna live testen met één echte CSV-export.

---

## 7. Spelregels voor dagelijks gebruik

- **Max 20–25 connectieverzoeken per dag** — daarboven flagt LinkedIn je account, zeker de eerste weken
- **Wekelijks ritme:** maandag CSV importeren + flow draaien, daarna elke dag 15 minuten versturen en follow-uppen vanuit de wachtrij
- **Follow-up pas na acceptatie** — en maximaal één herinnering. De note wekt interesse; de follow-up geeft waarde en stelt één lichte vraag
- **Statussen bijhouden** — de pipeline is alleen betrouwbaar als "verstuurd" en "geaccepteerd" echt worden aangeklikt
- **Elke 2 weken ICP bijstellen:** kijk welke afgekeurde leads je tóch goed vond (drempel omlaag) of welke gekwalificeerde leads nooit reageren (drempel omhoog, of branche eruit)

---

## 8. Automatische flow — Supabase + Vercel (zonder Phantombuster)

De definitieve stack, zonder scraping-tool: de aanvoer kost jou **± 2 minuten per week** (kopiëren en plakken), al het scannen, filteren en schrijven is daarna **volledig automatisch**. Geen Phantombuster = €56/mnd bespaard én geen scraping in het ToS-grijze gebied.

### 8.1 Architectuur

```
LinkedIn Sales Navigator (3 opgeslagen zoekopdrachten, alerts aan)
        │
        │  LinkedIn mailt je wekelijks: "X nieuwe resultaten"
        ▼
Jij (± 2 min/week): open de zoekopdracht → selecteer alles op de
resultatenpagina (Ctrl+A, Ctrl+C) → plak in het dashboard
        │
        │  "Plak & Parse" → POST naar /api/leads-sync (Vercel)
        ▼
Vercel serverless functie  /api/leads-sync
  1. Claude haalt uit de geplakte tekst gestructureerde leads
     (naam, functietitel, bedrijf, evt. profiel-link) — geen CSV nodig
  2. Ontdubbelt tegen Supabase (linkedin_url uniek, anders naam+bedrijf)
  3. Insert nieuwe leads met status 'nieuw'
  4. Claude API: ICP-score in batches van 10 → 'gekwalificeerd' / 'afgekeurd' + reden
  5. Claude API: connectienote + follow-up voor elke gekwalificeerde lead
        │
        ▼
Supabase (Postgres) — tabellen: leads, icp_config
        │
        │  supabase-py (lezen + statussen schrijven)
        ▼
Streamlit dashboard op Railway — pipeline, wachtrij, versturen (handmatig)

Vercel Cron (maandag 07:00) — vangnet & weekrapport:
  • scoort alsnog alles wat nog status 'nieuw' heeft (vangnet)
  • leest je Gmail: LinkedIn-alertmails → telt nieuwe matches per zoekopdracht
  • mailt je: "8 leads klaar om te versturen · 27 nieuwe matches wachten op import"
```

**Waarom "Plak & Parse" de gratis vervanger van Phantombuster is:** Claude is uitstekend in het herkennen van namen, functies en bedrijven in rommelige gekopieerde tekst. Je hoeft dus geen CSV te maken en geen tool te betalen — de hele resultatenpagina in één keer plakken is genoeg. De CSV-upload blijft bestaan als tweede route (bijv. voor een Evaboot-export als je die ooit hebt). En wil je later alsnog 100% handsfree: dan vervang je alleen stap 1 van de functie door de Phantombuster-koppeling — de rest blijft identiek.

### 8.2 Supabase — databaseschema

Nieuw project aanmaken op supabase.com (gratis tier volstaat), daarna in de SQL Editor:

```sql
create table icp_config (
  id int primary key default 1,
  functietitels text[] not null default '{Founder,Co-Founder,Owner,"E-commerce Manager","Head of Growth","Marketing Manager"}',
  bedrijfsgrootte text not null default '11-200 medewerkers',
  branches text[] not null default '{Retail,E-commerce,"Marketing & Advertising",Consultancy,SaaS}',
  regio text not null default 'Nederland',
  min_score int not null default 60,
  merk_naam text, niche text, toon text default 'Warm & Persoonlijk'
);
insert into icp_config (id) values (1);

create table leads (
  id uuid primary key default gen_random_uuid(),
  naam text not null,
  functietitel text,
  bedrijf text,
  branche text,
  bedrijfsgrootte text,
  linkedin_url text unique,
  bron text,                       -- welke zoekopdracht (ecommerce / agency / coach_saas)
  score int,
  score_reden text,
  note text,
  followup text,
  status text not null default 'nieuw',
  -- nieuw | gekwalificeerd | afgekeurd | verstuurd | geaccepteerd | gesprek | klant | afgewezen
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);
create index leads_status_idx on leads (status);
create index leads_score_idx on leads (score desc);
```

- **Row Level Security aanzetten** op beide tabellen; zowel de Vercel-functie als het dashboard werken server-side met de **service role key** (nooit in code, altijd als environment variable)
- De `linkedin_url unique`-constraint is je automatische ontdubbeling: dubbele import faalt stil per rij (upsert met `on conflict do nothing`)

### 8.3 Vercel — functie + cron

Nieuw Vercel-project (mag een aparte repo of map zijn), met:

**`vercel.json`:**
```json
{
  "crons": [
    { "path": "/api/leads-sync?mode=weekly", "schedule": "0 6 * * 1" }
  ]
}
```
`0 6 * * 1` = elke maandag 06:00 UTC (07:00/08:00 NL). Hobby-plan ondersteunt cron jobs.

**Environment variables (Vercel project settings):**

| Variabele | Waarvoor |
|---|---|
| `ANTHROPIC_API_KEY` | Claude-calls voor parsen, scoring + outreach |
| `SUPABASE_URL` + `SUPABASE_SERVICE_ROLE_KEY` | Lezen/schrijven leads |
| `GMAIL_USER` + `GMAIL_APP_PASSWORD` | LinkedIn-alertmails tellen + weekrapport versturen (zelfde app-wachtwoord als in het dashboard) |
| `CRON_SECRET` | De functie weigert aanroepen zonder dit geheim in de Authorization-header — anders kan iedereen je sync triggeren |

**De functie `/api/leads-sync`** (Node of Python, ± 150 regels) heeft twee modes:

*Mode "import" — aangeroepen door de Plak & Parse-knop in je dashboard (`POST` met `{ raw_text, bron }`):*

1. Check `Authorization: Bearer CRON_SECRET`
2. Claude-call: haal uit `raw_text` een JSON-array met leads (naam, functietitel, bedrijf, linkedin_url indien zichtbaar) — geplakte Sales Nav-pagina's zijn rommelig, dat is precies waar dit goed in is
3. `upsert ... on conflict (linkedin_url) do nothing`, `bron` = de gekozen zoekopdracht, status `nieuw`
4. Select alle leads met status `nieuw` → Claude scoring-prompt (hoofdstuk 4.4) in batches van 10 → update `score`, `score_reden`, `status`
5. Select `gekwalificeerd` zonder `note` → Claude outreach-prompt in batches van 10 → update `note`, `followup`
6. Return een samenvatting `{ "nieuw": 13, "gekwalificeerd": 8, "afgekeurd": 5 }`

*Mode "weekly" — aangeroepen door de cron (vangnet & rapport):*

1. Stap 4 + 5 van hierboven (alles scoren wat nog `nieuw` is — vangnet als je doordeweeks plakte zonder te scoren)
2. Lees via IMAP je Gmail: tel ongelezen LinkedIn Sales Navigator alertmails per zoekopdracht
3. Mail het weekrapport: *"8 leads klaar om te versturen · 5 wachten op follow-up · 27 nieuwe matches wachten op import (plak ze even in het dashboard)"*

**Tijdslimiet:** zet `maxDuration` op 300 in de functie-config en houd batches klein. Duurt een run te lang → laat de functie max ~50 leads per run verwerken; de volgende aanroep pakt de rest.

### 8.4 Dashboard-aanpassingen (Railway blijft, alleen opslag wisselt)

- `supabase>=2.0` toevoegen aan `requirements.txt`; `SUPABASE_URL` + `SUPABASE_SERVICE_ROLE_KEY` als env vars op Railway
- **Nieuw invoerveld "Plak & Parse"** in het rechterpaneel: groot tekstveld ("Plak hier je Sales Navigator resultaten"), dropdown voor de bron-zoekopdracht (e-commerce / agency / coach-SaaS), knop **"🚀 Importeer & scan"** → POST naar `/api/leads-sync` → toont de samenvatting ("13 nieuw, 8 gekwalificeerd")
- De helpers uit hoofdstuk 4 wisselen van bestand naar database — de rest van de UI (hoofdstuk 5) blijft identiek:
  - `laad_leads()` → `supabase.table("leads").select("*")`
  - status/note bijwerken → `update().eq("id", ...)`
  - `laad_icp()` / `sla_icp()` → `icp_config`-tabel
- CSV-upload blijft bestaan als tweede route (bijv. voor een export die je toch al hebt) — zelfde endpoint, zelfde scan
- Extra pipeline-regel bovenin: *"Laatste sync: ma 27 jul 07:02 — 13 nieuw, 8 gekwalificeerd"* (uit een simpele `sync_log`-tabel of het laatste function-resultaat)

### 8.5 Aangepaste bouwvolgorde (vervangt hoofdstuk 6)

1. **Supabase opzetten** *(± 30 min)* — project + SQL uit 8.2 + service key noteren
2. **Sales Navigator instellen** *(± 15 min)* — 3 zoekopdrachten (hoofdstuk 2), opslaan, alerts aan. Geen tool-configuratie meer nodig
3. **Vercel-functie + cron** *(± 2,5 uur)* — 8.3 bouwen; testen door één echte resultatenpagina te plakken: komen de leads gescoord en met notes in Supabase?
4. **Dashboard koppelen** *(± 2,5 uur)* — 8.4 + de pipeline-UI uit hoofdstuk 5
5. **Eén week proefdraaien** — maandagritme: alertmail → 2 min plakken → wachtrij staat klaar → versturen. Daarna het dagelijkse ritme uit hoofdstuk 7

### 8.6 Wat je nodig hebt (accounts & kosten)

| Dienst | Kosten | Waarvoor |
|---|---|---|
| LinkedIn Sales Navigator | ± €90/mnd | De zoekopdrachten + alerts |
| Supabase | Gratis tier | Lead-database |
| Vercel | Gratis (Hobby) | Parse/scan-functie + wekelijkse cron |
| Anthropic API | ± €3–5/mnd bij dit volume | Parsen, ICP-scoring + outreach-teksten |
| Railway | Huidige plan | Dashboard blijft waar het staat |

Enige maandelijkse kosten naast Sales Navigator zijn dus een paar euro API-gebruik — geen Phantombuster (€56/mnd) nodig.

