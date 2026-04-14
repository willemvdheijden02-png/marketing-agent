import streamlit as st
import anthropic, base64, json, os, re, imaplib, smtplib, requests
from pathlib import Path
from datetime import datetime
from email.mime.text import MIMEText
from email.header import decode_header
try:
    from google import genai
    from google.genai import types as gtypes
    GEMINI_OK = True
except Exception:
    GEMINI_OK = False

st.set_page_config(page_title="Marketing Agent Pro", page_icon="🚀",
    layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap');
html, body { font-family: 'Inter', sans-serif !important; }
.stApp { background: #F1F5F9; }

/* Bot header */
.bot-header {
    border-radius: 16px; padding: 22px 26px;
    margin-bottom: 20px; color: white;
}
.bot-title { font-size: 1.3rem; font-weight: 900; letter-spacing: -.02em; }
.bot-desc  { font-size: .82rem; opacity: .82; margin-top: 4px; }
.bot-count { font-size: 1.5rem; font-weight: 900; }
.bot-count-lbl { font-size: .6rem; opacity: .7; text-transform: uppercase; letter-spacing: .08em; }

/* Chat bubble container */
.chat-wrap {
    background: #fff; border: 1.5px solid #E2E8F0;
    border-radius: 16px; padding: 20px;
    min-height: 200px; max-height: 520px;
    overflow-y: auto; margin-bottom: 14px;
}
.msg-user {
    display: flex; justify-content: flex-end; margin-bottom: 12px;
}
.msg-user-bubble {
    background: #1E3A8A; color: white;
    border-radius: 18px 18px 4px 18px;
    padding: 11px 16px; max-width: 78%;
    font-size: .88rem; line-height: 1.55; white-space: pre-wrap;
}
.msg-bot { display: flex; align-items: flex-start; gap: 10px; margin-bottom: 12px; }
.msg-bot-av {
    width: 34px; height: 34px; border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    font-size: 1.1rem; flex-shrink: 0;
}
.msg-bot-bubble {
    background: #F8FAFC; border: 1.5px solid #E2E8F0; color: #1E293B;
    border-radius: 4px 18px 18px 18px;
    padding: 11px 16px; max-width: 78%;
    font-size: .88rem; line-height: 1.6; white-space: pre-wrap;
}
.chat-leeg { text-align: center; padding: 36px 20px; color: #94A3B8; }
.chat-leeg-icon { font-size: 2.4rem; margin-bottom: 10px; }

/* Section label */
.sec-lbl {
    font-size: .68rem; font-weight: 800; color: #64748B;
    text-transform: uppercase; letter-spacing: .1em;
    margin-bottom: 8px; margin-top: 4px;
}

/* Status pill */
.pill {
    display: inline-flex; align-items: center; gap: 4px;
    font-size: .68rem; font-weight: 700;
    padding: 3px 9px; border-radius: 20px; margin: 2px;
}

/* Tool resultaat */
.tool-blok {
    background: #EFF6FF; border-left: 3px solid #3B82F6;
    border-radius: 0 8px 8px 0; padding: 8px 12px;
    font-size: .78rem; color: #1E40AF; margin: 6px 0;
}
</style>
""", unsafe_allow_html=True)

# ─── Paden ───────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).parent
IMG_DIR  = BASE_DIR / "images"; IMG_DIR.mkdir(exist_ok=True)
MERK_FILE   = BASE_DIR / "merk.json"
RAPPORT_LOG = BASE_DIR / "rapport_log.json"

def laad_merk():
    try: return json.loads(MERK_FILE.read_text())
    except: return {}
def sla_merk(d): MERK_FILE.write_text(json.dumps(d, ensure_ascii=False, indent=2))
def laad_rapport_log():
    try: return json.loads(RAPPORT_LOG.read_text())
    except: return []
def sla_rapport_log(l): RAPPORT_LOG.write_text(json.dumps(l, ensure_ascii=False, indent=2))

# ─── Bot definities ───────────────────────────────────────────────────────────
BOTS = {
    "marketing": {
        "label": "🤖 Marketing Agent", "kleur": "#1E3A8A", "avatar": "🤖",
        "desc": "Algemene AI marketing agent — stel alles wat je wilt",
        "system": "Je bent een expert AI marketing agent. Geef directe, concrete adviezen in het Nederlands. Focus op vrouwen 40-65 in de lingerie en slaapkussenmarkt.",
        "skills": [
            ("📣 Facebook Ads", "Schrijf 3 Facebook advertenties voor mijn product"),
            ("🎬 Reels Script", "Schrijf een Instagram Reels script voor mijn product"),
            ("🎨 Afbeelding", "Genereer een advertentieafbeelding voor mijn product"),
            ("🔍 Zoekwoorden", "Doe zoekwoordonderzoek voor mijn niche en producten"),
            ("📅 Content Plan", "Maak een content kalender voor volgende maand"),
            ("🕵️ Concurrent", "Analyseer mijn concurrent en geef inzichten"),
            ("🧪 A/B Test", "Schrijf een A/B test hypothese voor mijn advertentie"),
            ("🗺️ Strategie", "Geef een complete marketingstrategie voor mijn merk"),
        ],
    },
    "meta": {
        "label": "📊 Meta Ads Bot", "kleur": "#1D4ED8", "avatar": "📊",
        "desc": "Facebook & Instagram campagnes — structuur, targeting, scaling",
        "system": "Je bent een Meta Ads expert. Geef concrete campagne-adviezen voor Facebook en Instagram gericht op vrouwen 40-65.",
        "skills": [
            ("🏗️ Campagne Structuur", "Maak een Meta campagne structuur met TOFU MOFU BOFU"),
            ("🔄 Retargeting", "Maak een retargeting strategie voor mijn webshop"),
            ("📈 Budget Scaling", "Geef een budget scaling strategie voor mijn campagnes"),
            ("🔍 Account Audit", "Doe een Meta Ads account audit met checklist"),
            ("👥 Lookalike", "Maak een lookalike audience strategie"),
            ("🧪 A/B Test Opzet", "Maak een A/B test opzet voor mijn Facebook ads"),
            ("📉 Campagne Analyse", "Analyseer mijn campagne performance"),
            ("🎠 Carousel Ads", "Schrijf een carousel advertentie met 8 slides"),
        ],
    },
    "email": {
        "label": "📨 Email & Klaviyo Bot", "kleur": "#6D28D9", "avatar": "📨",
        "desc": "Email flows, Klaviyo automations, SMS en nieuwsbrieven",
        "system": "Je bent een email marketing en Klaviyo expert. Schrijf emails voor vrouwen 40-65: warm, persoonlijk, direct. Altijd met onderwerpregel, preheader en volledige tekst.",
        "skills": [
            ("📧 Promotie Email", "Schrijf een promotie email voor mijn product"),
            ("🌊 Welcome Flow", "Maak een Klaviyo welcome flow met 5 emails"),
            ("🛒 Abandoned Cart", "Maak een abandoned cart flow met 3 emails en SMS"),
            ("📦 Post-Purchase", "Maak een post-purchase email flow na aankoop"),
            ("📬 Welcome Serie", "Schrijf een 5-delige welcome email serie"),
            ("👑 VIP Programma", "Maak VIP programma teksten en email flows"),
            ("💬 SMS Marketing", "Schrijf SMS campagne teksten voor mijn webshop"),
            ("💔 Winback", "Maak een 3-delige winback email campagne"),
            ("🎂 Verjaardag", "Schrijf een verjaardag email campagne"),
            ("📰 Nieuwsbrief", "Maak een nieuwsbrief template met onderwerpregel varianten"),
        ],
    },
    "copy": {
        "label": "✍️ Copywriting Bot", "kleur": "#065F46", "avatar": "✍️",
        "desc": "Advertentieteksten, landingspagina's, SEO en productteksten",
        "system": "Je bent een expert copywriter voor e-commerce. Schrijf overtuigende teksten voor vrouwen 40-65 in lingerie en slaapkussenniche. Altijd direct bruikbaar, geen placeholders.",
        "skills": [
            ("🏷️ Productbeschrijving", "Schrijf een SEO productbeschrijving voor mijn product"),
            ("📄 Landingspagina", "Schrijf een landingspagina in AIDA structuur"),
            ("📂 Categoriepagina", "Schrijf SEO teksten voor mijn categoriepagina"),
            ("📝 Blog Artikel", "Schrijf een SEO blog artikel voor mijn webshop"),
            ("⬆️ Upsell Teksten", "Schrijf upsell teksten voor mijn productpagina"),
            ("🪟 Pop-up", "Schrijf een pop-up tekst voor email opt-in"),
            ("⭐ Social Proof", "Zet klantreviews om naar social proof teksten"),
            ("🔍 Meta Descriptions", "Schrijf meta descriptions en title tags"),
            ("🔎 Google Ads", "Schrijf Google responsive search ads"),
            ("💰 Prijs Psychologie", "Geef advies over prijs psychologie en schrijf prijs copy"),
        ],
    },
    "social": {
        "label": "📱 Social Media Bot", "kleur": "#9D174D", "avatar": "📱",
        "desc": "TikTok, Instagram, Reels, UGC, Pinterest en WhatsApp",
        "system": "Je bent een social media expert voor e-commerce. Schrijf content voor TikTok, Instagram en WhatsApp die vrouwen 40-65 bereikt. Altijd authentiek en platform-specifiek.",
        "skills": [
            ("🎵 TikTok Ads", "Schrijf een TikTok advertentie script voor mijn product"),
            ("🎬 Instagram Reels", "Schrijf een Instagram Reels script met caption"),
            ("🎥 UGC Script", "Schrijf een UGC script en creator briefing"),
            ("🛍️ Social Shopping", "Schrijf Instagram Shopping en Facebook Shop teksten"),
            ("💬 WhatsApp", "Maak WhatsApp Business berichten en broadcast campagnes"),
            ("🤝 Influencer", "Schrijf een influencer outreach email en briefing"),
            ("📌 Pinterest", "Maak een Pinterest strategie met pin beschrijvingen"),
            ("#️⃣ Hashtags", "Maak een hashtag strategie voor Instagram en TikTok"),
            ("🎞️ Video Script", "Schrijf een 30-seconden video advertentie script"),
        ],
    },
    "ecom": {
        "label": "🛒 E-commerce Bot", "kleur": "#92400E", "avatar": "🛒",
        "desc": "Shopify, Bol.com, checkout, retour en seizoensverkoop",
        "system": "Je bent een e-commerce expert voor Nederlandse webshops. Specifiek voor lingerie en slaapkussens. Geef concrete, direct toepasbare adviezen.",
        "skills": [
            ("🛒 Shopify", "Optimaliseer mijn Shopify productpagina teksten"),
            ("📦 Bol.com", "Optimaliseer mijn Bol.com product listings"),
            ("💳 Checkout", "Optimaliseer mijn checkout pagina copy met trust signalen"),
            ("↩️ Retour Preventie", "Maak een retour preventie strategie"),
            ("📋 Pakbon Insert", "Schrijf teksten voor pakbon insert kaartjes"),
            ("🎁 Bundels", "Maak een bundel strategie voor mijn producten"),
            ("📦 Voorraad", "Schrijf back-in-stock en voorraad teksten"),
            ("🇳🇱 NL Feestdagen", "Maak een Nederlandse feestdagen actiekalender"),
            ("⚡ Flash Sale", "Maak een flash sale campagne met email en social posts"),
            ("🔁 Herhalingsaankoop", "Maak een herhalingsaankoop strategie"),
        ],
    },
    "ks": {
        "label": "📧 Klantenservice Bot", "kleur": "#0E7490", "avatar": "📞",
        "desc": "Klachten, retours, FAQ, maatadvies en reviews",
        "system": "Je bent een klantenservice expert voor een lingerie en slaapkussenwebshop. Schrijf warm, empathisch en duidelijk voor klanten van 40-65.",
        "skills": [
            ("😤 Klacht Afhandeling", "Geef klacht response templates met LEAP methode"),
            ("↩️ Retour Handling", "Schrijf retour en refund email templates"),
            ("❓ FAQ", "Schrijf een FAQ pagina voor mijn webshop"),
            ("⭐ Review Antwoord", "Geef review antwoord templates positief en negatief"),
            ("💬 Live Chat", "Maak live chat scripts voor mijn webshop"),
            ("📏 Maatadvies", "Schrijf een maatadvies script voor mijn klanten"),
            ("📊 NPS", "Schrijf een NPS enquête en follow-up emails"),
            ("📚 Product Educatie", "Schrijf educatieve content over BH of kussen kiezen"),
        ],
    },
    "branding": {
        "label": "🎨 Branding Bot", "kleur": "#7C2D12", "avatar": "🎨",
        "desc": "Brand story, positionering, USP's en klantprofielen",
        "system": "Je bent een branding expert. Je helpt merken hun identiteit en positionering definiëren voor lingerie en slaapkussenbedrijven gericht op vrouwen 40-65.",
        "skills": [
            ("📖 Brand Story", "Schrijf het brand verhaal en over-ons pagina tekst"),
            ("🗣️ Tone of Voice", "Maak een tone of voice gids voor mijn merk"),
            ("💎 USP's", "Ontwikkel de USP's voor mijn merk en producten"),
            ("🎯 Positionering", "Maak een merkpositionering strategie"),
            ("👤 Klantprofiel", "Maak een gedetailleerd klantprofiel buyer persona"),
            ("🔍 Competitor", "Analyseer mijn concurrenten en maak een vergelijkingsmatrix"),
            ("🤝 Partnership", "Schrijf een samenwerkingsvoorstel voor een partner"),
            ("📰 Persbericht", "Schrijf een persbericht voor mijn productlancering"),
        ],
    },
    "rapport": {
        "label": "📋 Rapporten Bot", "kleur": "#374151", "avatar": "📋",
        "desc": "Weekrapporten, klantrapportages, offertes en strategiedocumenten",
        "system": "Je bent een marketing rapportage expert. Maak professionele rapporten en strategiedocumenten voor marketing bureaus. Altijd duidelijk en direct bruikbaar voor klanten.",
        "skills": [
            ("📆 Weekrapport", "Genereer een marketing weekrapport"),
            ("📅 Maandrapport", "Genereer een marketing maandrapport"),
            ("📊 Klantrapport", "Maak een professionele klantrapportage"),
            ("📋 Briefing", "Maak een intake briefing document voor een nieuwe klant"),
            ("💼 Offerte", "Schrijf een offerte voor een nieuwe klant"),
            ("🚀 Onboarding", "Maak een onboarding plan voor een nieuwe marketing klant"),
            ("📽️ Presentatie", "Maak een marketing strategie presentatie structuur"),
            ("📄 Template", "Maak een rapportage template voor maandelijkse rapporten"),
        ],
    },
}


# ─── Session state ────────────────────────────────────────────────────────────
merk_data = laad_merk()
defaults  = {
    "actieve_bot": "marketing",
    "merk_naam":   merk_data.get("merk_naam", ""),
    "niche":       merk_data.get("niche", ""),
    "doelgroep":   merk_data.get("doelgroep", ""),
    "toon":        merk_data.get("toon", "Warm & Persoonlijk"),
    "anthropic_key":st.secrets.get("ANTHROPIC_API_KEY",""), "gemini_key":st.secrets.get("GOOGLE_API_KEY",""), "klaviyo_key":"",
    "gmail_user":"", "gmail_pass":"",
    "gorgias_domain":"", "gorgias_user":"", "gorgias_token":"",
    "shopify_url":"", "shopify_token":"",
    "bestanden": [],
}
for bot_id in BOTS:
    defaults[f"chat_{bot_id}"]    = []
    defaults[f"gesprek_{bot_id}"] = []
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ─── API functies ─────────────────────────────────────────────────────────────
def get_client():
    k = st.session_state.get("anthropic_key","") or os.environ.get("ANTHROPIC_API_KEY","")
    if not k: raise ValueError("Voer een Anthropic API key in via de sidebar.")
    return anthropic.Anthropic(api_key=k)

def zoek_concurrent(naam):
    try:
        r = requests.get(f"https://api.duckduckgo.com/?q={naam}+lingerie+advertising&format=json", timeout=8)
        topics = [t.get("Text","") for t in r.json().get("RelatedTopics",[])[:5] if t.get("Text")]
        return "\n".join(topics) or "Geen resultaten."
    except Exception as e: return f"Fout: {e}"

def lees_gmail(n=5):
    try:
        user=st.session_state.get("gmail_user",""); pw=st.session_state.get("gmail_pass","")
        if not user or not pw: return "Gmail niet geconfigureerd in de sidebar."
        m=imaplib.IMAP4_SSL("imap.gmail.com"); m.login(user,pw); m.select("INBOX")
        _,ids=m.search(None,"ALL"); mail_ids=ids[0].split()[-n:]
        mails=[]
        for mid in reversed(mail_ids):
            _,data=m.fetch(mid,"(RFC822)")
            import email as em; msg=em.message_from_bytes(data[0][1])
            subj=decode_header(msg["Subject"])[0][0]
            if isinstance(subj,bytes): subj=subj.decode(errors="replace")
            body=""
            if msg.is_multipart():
                for part in msg.walk():
                    if part.get_content_type()=="text/plain":
                        body=part.get_payload(decode=True).decode(errors="replace")[:300]; break
            else: body=msg.get_payload(decode=True).decode(errors="replace")[:300]
            mails.append(f"Van: {msg.get('From','')}\nOnderwerp: {subj}\nBericht: {body}")
        m.logout()
        return "\n\n---\n\n".join(mails) or "Geen e-mails."
    except Exception as e: return f"Gmail fout: {e}"

def stuur_gmail(aan, onderwerp, tekst):
    try:
        user=st.session_state.get("gmail_user",""); pw=st.session_state.get("gmail_pass","")
        if not user or not pw: return "Gmail niet geconfigureerd."
        msg=MIMEText(tekst,"plain","utf-8"); msg["Subject"]=onderwerp; msg["From"]=user; msg["To"]=aan
        with smtplib.SMTP_SSL("smtp.gmail.com",465) as s: s.login(user,pw); s.sendmail(user,aan,msg.as_string())
        return f"Verstuurd naar {aan}."
    except Exception as e: return f"Gmail fout: {e}"

def maak_gorgias_ticket(onderwerp, bericht, email="klant@voorbeeld.nl"):
    try:
        dom=st.session_state.get("gorgias_domain",""); usr=st.session_state.get("gorgias_user",""); tok=st.session_state.get("gorgias_token","")
        if not all([dom,usr,tok]): return "Gorgias niet geconfigureerd."
        r=requests.post(f"https://{dom}.gorgias.com/api/tickets",
            json={"channel":"email","subject":onderwerp,"messages":[{"channel":"email","from_agent":False,"body_text":bericht,"sender":{"email":email}}]},
            auth=(usr,tok),headers={"Content-Type":"application/json"},timeout=10)
        return f"Ticket #{r.json().get('id','?')} aangemaakt." if r.status_code in [200,201] else f"Fout {r.status_code}"
    except Exception as e: return f"Gorgias fout: {e}"

def laad_shopify_producten():
    try:
        url=st.session_state.get("shopify_url",""); tok=st.session_state.get("shopify_token","")
        if not url or not tok: return "Shopify niet geconfigureerd."
        r=requests.get(f"https://{url}/admin/api/2024-01/products.json?limit=10",
            headers={"X-Shopify-Access-Token":tok},timeout=10)
        prods=r.json().get("products",[])
        return "\n".join([f"- {p['title']} (€{p['variants'][0].get('price','?')})" for p in prods]) or "Geen producten."
    except Exception as e: return f"Shopify fout: {e}"

def stuur_klaviyo_template(naam, html):
    try:
        k=st.session_state.get("klaviyo_key","")
        if not k: return "Klaviyo niet geconfigureerd."
        r=requests.post("https://a.klaviyo.com/api/templates/",
            json={"data":{"type":"template","attributes":{"name":naam,"html":html}}},
            headers={"Authorization":f"Klaviyo-API-Key {k}","revision":"2023-12-15","Content-Type":"application/json"},timeout=10)
        return f"Template '{naam}' aangemaakt." if r.status_code in [200,201] else f"Fout {r.status_code}"
    except Exception as e: return f"Klaviyo fout: {e}"

def genereer_afbeelding(omschrijving, bestandsnaam="advertentie"):
    try:
        k=st.session_state.get("gemini_key","")
        if not k: return "Gemini API key niet ingesteld."
        if not GEMINI_OK: return "Installeer: pip install google-genai"
        client=genai.Client(api_key=k)
        resp=client.models.generate_images(model="imagen-4.0-generate-001",prompt=omschrijving,
            config=gtypes.GenerateImagesConfig(number_of_images=1,aspect_ratio="1:1"))
        if not resp.generated_images: return "Geen afbeelding gegenereerd."
        ts=datetime.now().strftime("%H%M%S")
        pad=IMG_DIR/f"{bestandsnaam}_{ts}.png"
        pad.write_bytes(resp.generated_images[0].image.image_bytes)
        if str(pad) not in st.session_state.bestanden: st.session_state.bestanden.append(str(pad))
        return f"Afbeelding opgeslagen: {pad}"
    except Exception as e: return f"Afbeelding fout: {e}"

def sla_rapport_op(inhoud, type_rapport="rapport"):
    try:
        ts=datetime.now().strftime("%Y%m%d_%H%M")
        naam=re.sub(r'[^a-zA-Z0-9]','_',st.session_state.get("merk_naam","rapport"))
        pad=BASE_DIR/f"{naam}_{type_rapport}_{ts}.txt"
        pad.write_text(inhoud,encoding="utf-8")
        log=laad_rapport_log()
        log.append({"type":type_rapport,"merk":st.session_state.get("merk_naam",""),"datum":ts,"pad":str(pad)})
        sla_rapport_log(log)
        if str(pad) not in st.session_state.bestanden: st.session_state.bestanden.append(str(pad))
        return f"Rapport opgeslagen: {pad}"
    except Exception as e: return f"Opslaan fout: {e}"

TOOLS = [
    {"name":"zoek_concurrent","description":"Zoek informatie over een concurrent","input_schema":{"type":"object","properties":{"naam":{"type":"string"}},"required":["naam"]}},
    {"name":"lees_gmail","description":"Lees Gmail emails","input_schema":{"type":"object","properties":{"aantal":{"type":"integer","default":5}},"required":[]}},
    {"name":"stuur_gmail","description":"Stuur email via Gmail","input_schema":{"type":"object","properties":{"aan":{"type":"string"},"onderwerp":{"type":"string"},"tekst":{"type":"string"}},"required":["aan","onderwerp","tekst"]}},
    {"name":"maak_gorgias_ticket","description":"Maak Gorgias ticket","input_schema":{"type":"object","properties":{"onderwerp":{"type":"string"},"bericht":{"type":"string"},"email":{"type":"string"}},"required":["onderwerp","bericht"]}},
    {"name":"laad_shopify_producten","description":"Laad Shopify producten","input_schema":{"type":"object","properties":{},"required":[]}},
    {"name":"stuur_klaviyo_template","description":"Stuur template naar Klaviyo","input_schema":{"type":"object","properties":{"naam":{"type":"string"},"html":{"type":"string"}},"required":["naam","html"]}},
    {"name":"genereer_afbeelding","description":"Genereer afbeelding met Google Imagen","input_schema":{"type":"object","properties":{"omschrijving":{"type":"string"},"bestandsnaam":{"type":"string","default":"advertentie"}},"required":["omschrijving"]}},
    {"name":"sla_rapport_op","description":"Sla rapport op als bestand","input_schema":{"type":"object","properties":{"inhoud":{"type":"string"},"type_rapport":{"type":"string","default":"rapport"}},"required":["inhoud"]}},
]
ICONEN = {"zoek_concurrent":"Concurrent zoeken","lees_gmail":"Gmail lezen","stuur_gmail":"Email sturen","maak_gorgias_ticket":"Gorgias ticket","laad_shopify_producten":"Shopify producten","stuur_klaviyo_template":"Klaviyo template","genereer_afbeelding":"Afbeelding genereren","sla_rapport_op":"Rapport opslaan"}

def voer_tool_uit(naam, invoer):
    match naam:
        case "zoek_concurrent":        return zoek_concurrent(invoer.get("naam",""))
        case "lees_gmail":             return lees_gmail(invoer.get("aantal",5))
        case "stuur_gmail":            return stuur_gmail(invoer.get("aan",""),invoer.get("onderwerp",""),invoer.get("tekst",""))
        case "maak_gorgias_ticket":    return maak_gorgias_ticket(invoer.get("onderwerp",""),invoer.get("bericht",""),invoer.get("email","klant@voorbeeld.nl"))
        case "laad_shopify_producten": return laad_shopify_producten()
        case "stuur_klaviyo_template": return stuur_klaviyo_template(invoer.get("naam",""),invoer.get("html",""))
        case "genereer_afbeelding":    return genereer_afbeelding(invoer.get("omschrijving",""),invoer.get("bestandsnaam","advertentie"))
        case "sla_rapport_op":         return sla_rapport_op(invoer.get("inhoud",""),invoer.get("type_rapport","rapport"))
        case _: return f"Onbekende tool: {naam}"

def verwerk_bericht(bot_id, vraag, img_bytes=None, media_type=None):
    bot    = BOTS[bot_id]
    client = get_client()
    merk   = st.session_state.get("merk_naam","—")
    niche  = st.session_state.get("niche","—")
    system = f"{bot['system']}\n\nKlant: Merk={merk}, Niche={niche}, Doelgroep={st.session_state.get('doelgroep','—')}, Toon={st.session_state.get('toon','Warm & Persoonlijk')}"
    content = [{"type":"image","source":{"type":"base64","media_type":media_type,"data":base64.standard_b64encode(img_bytes).decode()}},{"type":"text","text":vraag}] if img_bytes and media_type else vraag
    gk = f"gesprek_{bot_id}"; ck = f"chat_{bot_id}"
    st.session_state[gk].append({"role":"user","content":content})
    antwoord = client.messages.create(model="claude-sonnet-4-6",max_tokens=4096,temperature=0.7,system=system,tools=TOOLS,messages=st.session_state[gk])
    tool_log = []
    while antwoord.stop_reason == "tool_use":
        tool_results = []
        for block in antwoord.content:
            if block.type == "tool_use":
                label    = ICONEN.get(block.name, block.name)
                resultaat = voer_tool_uit(block.name, block.input)
                res_str   = str(resultaat)
                if "opgeslagen:" in res_str.lower():
                    pad = res_str.split("opgeslagen:")[-1].strip()
                    if Path(pad).exists() and pad not in st.session_state.bestanden:
                        st.session_state.bestanden.append(pad)
                img_path = None
                if block.name == "genereer_afbeelding" and "opgeslagen:" in res_str.lower():
                    img_path = res_str.split("opgeslagen:")[-1].strip()
                tool_log.append({"label":label,"resultaat":resultaat,"img_path":img_path})
                tool_results.append({"type":"tool_result","tool_use_id":block.id,"content":res_str})
        st.session_state[gk].append({"role":"assistant","content":antwoord.content})
        st.session_state[gk].append({"role":"user","content":tool_results})
        antwoord = client.messages.create(model="claude-sonnet-4-6",max_tokens=4096,temperature=0.7,system=system,tools=TOOLS,messages=st.session_state[gk])
    bot_tekst = antwoord.content[0].text
    st.session_state[gk].append({"role":"assistant","content":bot_tekst})
    img_b64 = base64.standard_b64encode(img_bytes).decode() if img_bytes else None
    st.session_state[ck].append({"rol":"gebruiker","tekst":vraag,"img_b64":img_b64})
    st.session_state[ck].append({"rol":"bot","tekst":bot_tekst,"tools":tool_log})


# ─── SIDEBAR — lichte achtergrond, zwarte tekst ────────────────────────────────
with st.sidebar:
    st.markdown("## 🚀 Marketing Agent Pro")
    st.caption("9 Bots • 101 Skills • Claude + Gemini")
    st.divider()

    # Bot navigatie — simpele radio buttons, geen custom CSS nodig
    st.markdown("**Kies een bot**")
    bot_namen = {bid: bot["label"] for bid, bot in BOTS.items()}
    gekozen = st.radio(
        "Bot selectie",
        options=list(bot_namen.keys()),
        format_func=lambda x: bot_namen[x],
        index=list(BOTS.keys()).index(st.session_state.actieve_bot),
        label_visibility="collapsed",
        key="bot_radio"
    )
    if gekozen != st.session_state.actieve_bot:
        st.session_state.actieve_bot = gekozen
        st.rerun()

    st.divider()

    # Verbindingsstatus
    st.markdown("**Verbindingen**")
    checks = [
        ("Claude",   bool(st.session_state.get("anthropic_key",""))),
        ("Gemini",   bool(st.session_state.get("gemini_key",""))),
        ("Gmail",    bool(st.session_state.get("gmail_user",""))),
        ("Klaviyo",  bool(st.session_state.get("klaviyo_key",""))),
        ("Shopify",  bool(st.session_state.get("shopify_url",""))),
        ("Gorgias",  bool(st.session_state.get("gorgias_domain",""))),
    ]
    pills = ""
    for naam, ok in checks:
        klr = "green" if ok else "red"
        dot = "●" if ok else "○"
        pills += f'<span style="color:{klr};font-size:.8rem;font-weight:700;margin-right:10px">{dot} {naam}</span>'
    st.markdown(pills, unsafe_allow_html=True)
    st.markdown("")

    with st.expander("🔑 API Sleutels"):
        st.session_state.anthropic_key = st.text_input("Anthropic API Key", value=st.session_state.get("anthropic_key",""), type="password", key="i_ant")
        st.session_state.gemini_key    = st.text_input("Gemini API Key",    value=st.session_state.get("gemini_key",""),    type="password", key="i_gem")
        st.session_state.klaviyo_key   = st.text_input("Klaviyo API Key",   value=st.session_state.get("klaviyo_key",""),   type="password", key="i_klav")

    with st.expander("🔌 Integraties"):
        st.session_state.gmail_user    = st.text_input("Gmail adres",       value=st.session_state.get("gmail_user",""),    key="i_gm")
        st.session_state.gmail_pass    = st.text_input("Gmail wachtwoord",  value=st.session_state.get("gmail_pass",""),    type="password", key="i_gp")
        st.session_state.gorgias_domain= st.text_input("Gorgias domein",    value=st.session_state.get("gorgias_domain",""),key="i_gd")
        st.session_state.gorgias_user  = st.text_input("Gorgias gebruiker", value=st.session_state.get("gorgias_user",""),  key="i_gu")
        st.session_state.gorgias_token = st.text_input("Gorgias token",     value=st.session_state.get("gorgias_token",""), type="password", key="i_gt")
        st.session_state.shopify_url   = st.text_input("Shopify URL",       value=st.session_state.get("shopify_url",""),   key="i_su")
        st.session_state.shopify_token = st.text_input("Shopify token",     value=st.session_state.get("shopify_token",""), type="password", key="i_st")

    with st.expander("🏪 Klant & Niche", expanded=True):
        st.session_state.merk_naam = st.text_input("Merknaam",   value=st.session_state.get("merk_naam",""), key="i_mn")
        st.session_state.niche     = st.text_input("Niche",      value=st.session_state.get("niche",""),     placeholder="bijv. lingerie 40-65+", key="i_ni")
        st.session_state.doelgroep = st.text_input("Doelgroep",  value=st.session_state.get("doelgroep",""), key="i_do")
        st.session_state.toon      = st.selectbox("Toon",        ["Warm & Persoonlijk","Professioneel","Energiek","Luxe"], key="s_to")
        if st.button("💾 Opslaan", use_container_width=True, key="btn_save"):
            sla_merk({"merk_naam":st.session_state.merk_naam,"niche":st.session_state.niche,
                      "doelgroep":st.session_state.doelgroep,"toon":st.session_state.toon})
            st.success("Opgeslagen!")

    if st.session_state.get("bestanden"):
        st.divider()
        st.markdown("**Gegenereerde bestanden**")
        for pad in st.session_state.bestanden[-6:]:
            p = Path(pad)
            if p.exists():
                try:
                    st.download_button(f"⬇️ {p.name}", data=p.read_bytes(),
                        file_name=p.name, key=f"dl_{pad[-12:]}")
                except: pass


# ─── MAIN CONTENT — actieve bot ───────────────────────────────────────────────
bot_id = st.session_state.actieve_bot
bot    = BOTS[bot_id]
kleur  = bot["kleur"]
ck     = f"chat_{bot_id}"

# Bot header
n_conv = len(st.session_state.get(ck, [])) // 2
st.markdown(f"""
<div class="bot-header" style="background:linear-gradient(135deg,{kleur} 0%,{kleur}BB 100%)">
  <div style="display:flex;align-items:center;gap:14px">
    <span style="font-size:2.2rem">{bot['avatar']}</span>
    <div style="flex:1">
      <div class="bot-title">{bot['label']}</div>
      <div class="bot-desc">{bot['desc']}</div>
    </div>
    <div style="text-align:right">
      <div class="bot-count">{n_conv}</div>
      <div class="bot-count-lbl">gesprekken</div>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

# Skill knoppen van deze bot
st.markdown('<p class="sec-lbl">Skills — klik om direct te gebruiken</p>', unsafe_allow_html=True)
n_skills = len(bot["skills"])
skill_cols = st.columns(min(n_skills, 4))
trigger_skill = None
for i, (lbl, cmd) in enumerate(bot["skills"]):
    with skill_cols[i % 4]:
        if st.button(lbl, key=f"sk_{bot_id}_{i}", use_container_width=True):
            trigger_skill = cmd

st.divider()

# Twee kolommen: chat (breed) + opties (smal)
col_chat, col_side = st.columns([3, 1])

# ── Opties kolom ──
with col_side:
    st.markdown('<p class="sec-lbl">Opties</p>', unsafe_allow_html=True)

    geup = st.file_uploader("Afbeelding", type=["png","jpg","jpeg","webp"],
        key=f"up_{bot_id}", label_visibility="visible")
    img_bytes_up, media_type_up = None, None
    if geup:
        img_bytes_up   = geup.read()
        media_type_up  = geup.type or "image/jpeg"
        st.image(img_bytes_up, use_column_width=True, caption=geup.name)

    if st.button("Gesprek wissen", use_container_width=True, key=f"reset_{bot_id}"):
        st.session_state[ck] = []
        st.session_state[f"gesprek_{bot_id}"] = []
        st.rerun()

    # Bot-specifieke extras
    if bot_id == "email":
        st.markdown('<p class="sec-lbl" style="margin-top:16px">Klaviyo</p>', unsafe_allow_html=True)
        klav_naam = st.text_input("Template naam", placeholder="bijv. Promo Mei", key="klav_n")
        if st.button("Push naar Klaviyo", use_container_width=True, key="klav_btn") and klav_naam:
            trigger_skill = f"Stuur het email concept als Klaviyo template met naam '{klav_naam}'"

    if bot_id == "ks":
        st.markdown('<p class="sec-lbl" style="margin-top:16px">Gorgias ticket</p>', unsafe_allow_html=True)
        g_ond = st.text_input("Onderwerp", key="g_ond")
        g_ber = st.text_area("Klant bericht", height=80, key="g_ber")
        if st.button("Maak ticket", use_container_width=True, key="btn_gorg") and g_ond:
            trigger_skill = f"Maak Gorgias ticket: onderwerp '{g_ond}', bericht '{g_ber}'"

    if bot_id == "rapport":
        rlog = laad_rapport_log()
        if rlog:
            st.markdown('<p class="sec-lbl" style="margin-top:16px">Eerdere rapporten</p>', unsafe_allow_html=True)
            for i, r in enumerate(reversed(rlog[-4:])):
                pad = r.get("pad","")
                if pad and Path(pad).exists():
                    try:
                        st.download_button(
                            f"⬇️ {r.get('type','rapport')} {r.get('datum','')[:10]}",
                            data=Path(pad).read_bytes(), file_name=Path(pad).name,
                            key=f"rp_dl_{i}")
                    except: pass

# ── Chat kolom ──
with col_chat:
    berichten = st.session_state.get(ck, [])

    # Chat weergave
    chat_html = '<div class="chat-wrap">'
    if not berichten:
        chat_html += f"""
        <div class="chat-leeg">
          <div class="chat-leeg-icon">{bot['avatar']}</div>
          <div style="font-weight:700;color:#334155;font-size:.95rem;margin-bottom:6px">{bot['label']} staat klaar</div>
          <div style="font-size:.82rem">{bot['desc']}</div>
          <div style="margin-top:12px;font-size:.78rem;color:#94A3B8">Klik een skill hierboven of typ hieronder.</div>
        </div>"""
    else:
        for b in berichten:
            if b["rol"] == "gebruiker":
                tekst_esc = b["tekst"].replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")
                chat_html += f'<div class="msg-user"><div class="msg-user-bubble">{tekst_esc}</div></div>'
            else:
                tekst_esc = b["tekst"].replace("&","&amp;").replace("<","&lt;").replace(">","&gt;").replace("\n","<br>")
                av_bg = kleur + "22"
                chat_html += f"""<div class="msg-bot">
                  <div class="msg-bot-av" style="background:{av_bg};color:{kleur}">{bot['avatar']}</div>
                  <div class="msg-bot-bubble">{tekst_esc}</div>
                </div>"""
    chat_html += "</div>"
    st.markdown(chat_html, unsafe_allow_html=True)

    # Geüploade afbeelding tonen
    for b in berichten:
        if b["rol"] == "gebruiker" and b.get("img_b64"):
            try:
                st.image(base64.b64decode(b["img_b64"]), width=260, caption="Meegestuurde afbeelding")
            except: pass

    # Tool resultaten — simpele st.info blokken, geen expanders
    for b in berichten:
        if b["rol"] == "bot":
            for t in b.get("tools", []):
                st.info(f"**{t['label']}** — uitgevoerd\n\n{str(t['resultaat'])[:300]}")
                if t.get("img_path") and Path(t["img_path"]).exists():
                    st.image(t["img_path"], use_column_width=True, caption="Gegenereerde afbeelding — Google Imagen")
                    try:
                        st.download_button("⬇️ Download afbeelding",
                            data=Path(t["img_path"]).read_bytes(),
                            file_name=Path(t["img_path"]).name,
                            mime="image/png",
                            key=f"img_dl_{t['img_path'][-10:]}")
                    except: pass

    # Chat input
    invoer = st.chat_input(f"Stuur een bericht naar {bot['label']}...", key=f"ci_{bot_id}")
    trigger = invoer or trigger_skill

    if trigger:
        with st.spinner(f"{bot['avatar']} Bezig..."):
            try:
                verwerk_bericht(bot_id, str(trigger), img_bytes_up, media_type_up)
            except Exception as e:
                st.error(f"Fout: {e}")
        st.rerun()

