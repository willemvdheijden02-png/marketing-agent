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
