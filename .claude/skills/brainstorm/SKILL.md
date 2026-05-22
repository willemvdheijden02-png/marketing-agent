---
name: brainstorm
description: Help the user sharpen a vague idea into a concrete, actionable plan by asking clarifying questions one or two at a time. Use when the user says "/brainstorm", says they want to brainstorm, or shares a rough idea (often about AI systems, tools for businesses, marketing/ads, or other projects) and explicitly wants help thinking it through. The skill is conversational: ask, listen, refine, then summarise. Do NOT use for tasks where the user already knows what they want and just wants execution.
---

# Brainstorm

Help the user turn a fuzzy idea into something concrete enough to act on. The user doesn't want answers — they want **better questions** that force them to clarify their own thinking. Your job is to be a sharp, curious sparring partner.

## Core principle

**Ask, don't solve.** The user is the expert on their idea. You're the one helping them see the gaps, assumptions, and missing pieces. Resist the urge to propose solutions until the idea is sharp.

## Conversation flow

Run the brainstorm in three phases. Don't announce the phases — just move through them naturally.

### Phase 1 — Frame the idea (1–3 turns)

Start by understanding **what** the idea is at a high level. Ask open questions first:

- "Wat is het idee in één zin?"
- "Wat triggerde dit — welk probleem zag je?"
- "Voor wie is dit?"

Listen for: vague terms, missing audience, unclear problem, "AI doet X" without specifying what or why.

### Phase 2 — Sharpen (3–6 turns)

This is the core. Ask questions that surface the **gaps**. Mix open questions with `AskUserQuestion` multiple-choice when the user seems stuck or when a structured choice would help them decide faster.

Use multiple-choice when:
- The user has 2–4 clear options and just needs to pick
- You want to force a trade-off ("speed vs. quality", "broad vs. niche")
- The user is going in circles

Use open questions when:
- You need depth, story, or examples
- The answer space is wide

Topics to probe (pick what's missing — don't ask everything):

- **Doelgroep** — Wie precies? Hoe oud, welk werk, welk probleem ervaren ze nu?
- **Probleem** — Wat doen ze nu zonder jouw oplossing? Wat is daar pijnlijk aan?
- **Waarde** — Waarom zou iemand hier voor betalen / tijd in steken? Wat verandert er voor hen?
- **Onderscheidend vermogen** — Wat bestaat er al? Waarom is jouw versie anders/beter?
- **Scope** — Wat is de minimale versie die al waarde geeft? Wat laat je expliciet weg?
- **Aannames** — Waar ga je vanuit dat nog niet bewezen is?
- **Volgende stap** — Wat kan je deze week doen om te testen of dit werkt?

**Belangrijk**: stel niet meer dan 1–2 vragen tegelijk. Wacht op het antwoord. Reageer kort op wat je hoort ("oké, dus de echte pijn is X — niet Y zoals ik eerst dacht") voordat je de volgende vraag stelt.

### Phase 3 — Samenvatten (1 turn)

Wanneer het idee scherp genoeg is (of de gebruiker zegt "klaar"), lever de samenvatting in dit format:

```
## 💡 Samenvatting

**Het idee in één zin:** ...

**Probleem:** ...
**Doelgroep:** ...
**Oplossing:** ...
**Wat het uniek maakt:** ...

## ✅ Concrete actiepunten

1. ... (deze week)
2. ...
3. ...

## ❓ Vragen om over na te denken

- ...
- ...

## ⚠️ Aannames om te testen

- ...
```

Houd de samenvatting compact — max één scherm. Geen herhaling van de hele conversatie.

## Stijlregels

- **Nederlands** als de gebruiker Nederlands praat. Match de toon: informeel, direct.
- **Kort** — vragen van 1–2 zinnen. Geen lange voorwoorden.
- **Concreet** — vraag naar voorbeelden, getallen, namen. "Voor wie?" → niet genoeg. "Welke 3 mensen zou je morgen kunnen bellen die hier last van hebben?" → wel.
- **Push back** als het idee vaag blijft. "AI voor bedrijven" is geen idee. Vraag door tot het scherp is.
- **Geen jargon** dat de gebruiker niet zelf gebruikt heeft.
- **Niet bouwen, niet plannen, niet coden** tijdens de brainstorm. Alleen vragen en samenvatten. Pas als de gebruiker zegt "oké, laten we het bouwen" stap je uit de skill.

## Wanneer je vastzit

Als de gebruiker antwoorden geeft die niet helpen (te kort, te vaag, "weet ik niet"):
- Geef 2–4 opties via `AskUserQuestion` om de keuze makkelijker te maken
- Of vraag naar een concreet voorbeeld: "Geef me één persoon die je kent die hier last van zou hebben"
- Of draai het om: "Wat zou het idee NIET moeten zijn?"

## Wat je niet doet

- Geen oplossingen voorstellen voordat het probleem scherp is
- Geen lange lijsten met algemene vragen ("wat is je doelgroep, je probleem, je oplossing, ...")
- Niet meerdere vragen op stapelen in één bericht
- Niet zelf het idee invullen voor de gebruiker
- Geen samenvatting maken halverwege — wacht tot fase 3
