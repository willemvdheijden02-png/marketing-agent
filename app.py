import streamlit as st
import anthropic, base64, json, os, re, imaplib, smtplib, requests, subprocess
from pathlib import Path
from datetime import datetime
from email.mime.multipart import MIMEMultipart
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

# PWA — manifest + service worker injectie via JavaScript
st.markdown("""
<script>
(function(){
  // Manifest
  if (!document.querySelector('link[rel="manifest"]')) {
    var l=document.createElement('link');l.rel='manifest';l.href='/app/static/manifest.json';
    document.head.appendChild(l);
  }
  // Apple meta tags
  var tags=[
    ['meta','name','apple-mobile-web-app-capable','content','yes'],
    ['meta','name','apple-mobile-web-app-status-bar-style','content','black-translucent'],
    ['meta','name','apple-mobile-web-app-title','content','Marketing Agent'],
    ['link','rel','apple-touch-icon','href','/app/static/icons/icon-152x152.png'],
    ['meta','name','theme-color','content','#1E3A8A']
  ];
  tags.forEach(function(t){
    if(document.querySelector(t[0]+'['+t[1]+'="'+t[2]+'"]'))return;
    var el=document.createElement(t[0]);el.setAttribute(t[1],t[2]);el.setAttribute(t[3],t[4]);
    document.head.appendChild(el);
  });
  // Install banner
  var deferred=null;
  var isIOS=/iPad|iPhone|iPod/.test(navigator.userAgent)&&!window.MSStream;
  var isStandalone=window.matchMedia('(display-mode: standalone)').matches||navigator.standalone;
  if(!isStandalone&&!localStorage.getItem('pwa-dismissed')){
    window.addEventListener('beforeinstallprompt',function(e){
      e.preventDefault();deferred=e;
      setTimeout(showBanner,3000);
    });
    if(isIOS)setTimeout(showBanner,3000);
  }
  function showBanner(){
    if(document.getElementById('pwa-banner'))return;
    var b=document.createElement('div');
    b.id='pwa-banner';
    b.style.cssText='position:fixed;bottom:16px;left:50%;transform:translateX(-50%);background:#1e293b;border:1px solid rgba(59,130,246,0.4);border-radius:14px;padding:14px 18px;z-index:999999;display:flex;align-items:center;gap:12px;box-shadow:0 8px 32px rgba(0,0,0,0.5);max-width:340px;width:calc(100% - 32px);';
    var btnTxt=isIOS?'Hoe?':'Installeer';
    b.innerHTML='<img src="/app/static/icons/icon-72x72.png" style="width:40px;height:40px;border-radius:10px;flex-shrink:0"><div style="flex:1"><div style="font-size:13px;font-weight:700;color:#e2e8f0">Marketing Agent Pro</div><div style="font-size:11px;color:#94a3b8;margin-top:1px">Installeer als app op je telefoon</div></div><button onclick="installPWA()" style="background:#1E3A8A;color:white;border:none;padding:8px 14px;border-radius:8px;font-size:12px;font-weight:600;cursor:pointer">'+btnTxt+'</button><button onclick="sluitBanner()" style="background:none;border:none;color:#64748b;cursor:pointer;font-size:20px;line-height:1">×</button>';
    document.body.appendChild(b);
  }
  window.installPWA=function(){
    if(deferred){deferred.prompt();deferred=null;document.getElementById('pwa-banner')?.remove();}
    else if(isIOS){alert('Safari → Deel-knop (□↑) → "Zet op beginscherm"');}
  };
  window.sluitBanner=function(){
    document.getElementById('pwa-banner')?.remove();
    localStorage.setItem('pwa-dismissed','1');
  };
})();
</script>
""", unsafe_allow_html=True)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap');
html,body,[class*="css"]{font-family:'Inter',sans-serif!important}
.stApp{background:#F1F5F9}
.bot-header{border-radius:14px;padding:18px 22px;margin-bottom:16px;color:white}
.bot-title{font-size:1.2rem;font-weight:900}
.bot-desc{font-size:.8rem;opacity:.8;margin-top:3px}
.chat-wrap{background:#fff;border:1.5px solid #E2E8F0;border-radius:14px;padding:18px;min-height:180px;max-height:480px;overflow-y:auto;margin-bottom:12px}
.msg-user{display:flex;justify-content:flex-end;margin-bottom:10px}
.msg-user-bubble{color:white;border-radius:16px 16px 3px 16px;padding:10px 15px;max-width:76%;font-size:.87rem;line-height:1.55;white-space:pre-wrap}
.msg-bot{display:flex;align-items:flex-start;gap:9px;margin-bottom:10px}
.msg-av{width:30px;height:30px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:1rem;flex-shrink:0}
.msg-bot-bubble{background:#F8FAFC;border:1.5px solid #E2E8F0;color:#1E293B;border-radius:3px 16px 16px 16px;padding:10px 15px;max-width:76%;font-size:.87rem;line-height:1.6;white-space:pre-wrap}
.chat-leeg{text-align:center;padding:30px 16px;color:#94A3B8}
.sec-lbl{font-size:.67rem;font-weight:800;color:#64748B;text-transform:uppercase;letter-spacing:.09em;margin:10px 0 6px;display:block}
.auto-card{background:#EFF6FF;border:1.5px solid #BFDBFE;border-radius:12px;padding:14px 16px;margin-top:10px}
</style>
""", unsafe_allow_html=True)

BASE_DIR        = Path(__file__).parent
IMG_DIR         = BASE_DIR / "images"; IMG_DIR.mkdir(exist_ok=True)
MERK_FILE       = BASE_DIR / "merk.json"
RAPPORT_LOG     = BASE_DIR / "rapport_log.json"
AUTO_CONFIG_FILE= BASE_DIR / "auto_rapport_config.json"
AUTO_LOG_FILE   = BASE_DIR / "auto_rapport_log.json"

def laad_merk():
    try: return json.loads(MERK_FILE.read_text())
    except: return {}
def sla_merk(d): MERK_FILE.write_text(json.dumps(d,ensure_ascii=False,indent=2))
def laad_rapport_log():
    try: return json.loads(RAPPORT_LOG.read_text())
    except: return []
def sla_rapport_log(l): RAPPORT_LOG.write_text(json.dumps(l,ensure_ascii=False,indent=2))
def laad_auto_config():
    try: return json.loads(AUTO_CONFIG_FILE.read_text())
    except: return {}
def sla_auto_config(d): AUTO_CONFIG_FILE.write_text(json.dumps(d,ensure_ascii=False,indent=2))
def laad_auto_log():
    try: return json.loads(AUTO_LOG_FILE.read_text())
    except: return []

SLASH={"/weekrapport":"Genereer een gedetailleerd weekrapport","/maandrapport":"Genereer een uitgebreid maandrapport","/advertentie":"Schrijf 3 Facebook/Instagram advertentievarianten voor:","/email":"Schrijf een volledige marketing email voor:","/analyse":"Analyseer de volgende data uitgebreid:","/strategie":"Maak een complete marketingstrategie voor:","/concurrent":"Analyseer concurrent en geef inzichten over:","/landingspagina":"Schrijf een landingspagina in AIDA structuur voor:","/seo":"Schrijf SEO-geoptimaliseerde teksten voor:"}

def parse_slash(t):
    for cmd,prefix in SLASH.items():
        if t.strip().startswith(cmd):
            rest=t.strip()[len(cmd):].strip()
            return f"{prefix} {rest}".strip() if rest else prefix
    return t

BOTS={
"marketing":{"label":"🤖 Marketing Agent","kleur":"#1E3A8A","avatar":"🤖","desc":"Algemene marketing AI — stel alles wat je wilt","system":"Je bent een expert AI marketing agent. Geef directe, concrete adviezen in het Nederlands. Focus op vrouwen 40-65 in de lingerie en slaapkussenmarkt.","skills":[("📣 Facebook Ads","Schrijf 3 Facebook advertenties voor mijn product"),("🎬 Reels Script","Schrijf een Instagram Reels script voor mijn product"),("🎨 Afbeelding genereren","Genereer een advertentieafbeelding voor mijn product"),("🔍 Zoekwoorden","Doe zoekwoordonderzoek voor mijn niche"),("📅 Content kalender","Maak een content kalender voor volgende maand"),("🕵️ Concurrent analyse","Analyseer mijn concurrent"),("🧪 A/B Test","Schrijf een A/B test hypothese"),("🗺️ Strategie","Geef een complete marketingstrategie")]},
"meta":{"label":"📊 Meta Ads Bot","kleur":"#1D4ED8","avatar":"📊","desc":"Facebook & Instagram campagnes — structuur, targeting en scaling","system":"Je bent een Meta Ads expert. Geef concrete campagne-adviezen voor Facebook en Instagram gericht op vrouwen 40-65.","skills":[("🏗️ Campagne structuur","Maak een Meta campagne structuur TOFU MOFU BOFU"),("🔄 Retargeting","Maak een retargeting strategie voor mijn webshop"),("📈 Budget scaling","Geef een budget scaling strategie"),("🔍 Account audit","Doe een Meta Ads account audit"),("👥 Lookalike audience","Maak een lookalike audience strategie"),("🧪 A/B test opzet","Maak een A/B test opzet voor Facebook ads"),("📉 Campagne analyse","Analyseer mijn campagne performance"),("🎠 Carousel ads","Schrijf een carousel advertentie met 8 slides")]},
"email":{"label":"📨 Email & Klaviyo Bot","kleur":"#6D28D9","avatar":"📨","desc":"Email flows, Klaviyo automations, SMS en nieuwsbrieven","system":"Je bent een email marketing en Klaviyo expert. Schrijf emails voor vrouwen 40-65: warm, persoonlijk. Altijd met onderwerpregel, preheader en volledige tekst.","skills":[("📧 Promotie email","Schrijf een promotie email voor mijn product"),("🌊 Welcome flow","Maak een Klaviyo welcome flow met 5 emails"),("🛒 Abandoned cart","Maak een abandoned cart flow met 3 emails en SMS"),("📦 Post-purchase","Maak een post-purchase email flow na aankoop"),("📬 Welcome serie","Schrijf een 5-delige welcome email serie"),("👑 VIP programma","Maak VIP programma teksten en email flows"),("💬 SMS marketing","Schrijf SMS campagne teksten"),("💔 Winback","Maak een 3-delige winback email campagne"),("🎂 Verjaardag email","Schrijf een verjaardag email campagne"),("📰 Nieuwsbrief","Maak een nieuwsbrief template")]},
"copy":{"label":"✍️ Copywriting Bot","kleur":"#065F46","avatar":"✍️","desc":"Advertentieteksten, landingspagina's, SEO en productteksten","system":"Je bent een expert copywriter voor e-commerce. Schrijf overtuigende teksten voor vrouwen 40-65 in lingerie en slaapkussenniche. Altijd direct bruikbaar.","skills":[("🏷️ Productbeschrijving","Schrijf een SEO productbeschrijving voor mijn product"),("📄 Landingspagina","Schrijf een landingspagina in AIDA structuur"),("📂 Categoriepagina","Schrijf SEO teksten voor mijn categoriepagina"),("📝 Blog artikel","Schrijf een SEO blog artikel voor mijn webshop"),("⬆️ Upsell teksten","Schrijf upsell teksten voor mijn productpagina"),("🪟 Pop-up tekst","Schrijf een pop-up tekst voor email opt-in"),("⭐ Social proof","Zet klantreviews om naar social proof teksten"),("🔍 Meta descriptions","Schrijf meta descriptions en title tags"),("🔎 Google Ads","Schrijf Google responsive search ads"),("💰 Prijspsychologie","Geef advies over prijs psychologie")]},
"social":{"label":"📱 Social Media Bot","kleur":"#9D174D","avatar":"📱","desc":"TikTok, Instagram, Reels, UGC, Pinterest en WhatsApp","system":"Je bent een social media expert voor e-commerce. Schrijf content voor TikTok, Instagram en WhatsApp die vrouwen 40-65 bereikt.","skills":[("🎵 TikTok ads","Schrijf een TikTok advertentie script"),("🎬 Instagram Reels","Schrijf een Instagram Reels script met caption"),("🎥 UGC script","Schrijf een UGC script en creator briefing"),("🛍️ Social shopping","Schrijf Instagram Shopping en Facebook Shop teksten"),("💬 WhatsApp","Maak WhatsApp Business berichten en broadcasts"),("🤝 Influencer outreach","Schrijf een influencer outreach email"),("📌 Pinterest","Maak een Pinterest strategie met pin beschrijvingen"),("#️⃣ Hashtag strategie","Maak een hashtag strategie voor Instagram en TikTok"),("🎞️ Video script","Schrijf een 30-seconden video advertentie script")]},
"ecom":{"label":"🛒 E-commerce Bot","kleur":"#92400E","avatar":"🛒","desc":"Shopify, Bol.com, checkout, retour en seizoensverkoop","system":"Je bent een e-commerce expert voor Nederlandse webshops. Specifiek voor lingerie en slaapkussens. Geef concrete, direct toepasbare adviezen.","skills":[("🛒 Shopify","Optimaliseer mijn Shopify productpagina teksten"),("📦 Bol.com","Optimaliseer mijn Bol.com product listings"),("💳 Checkout copy","Optimaliseer mijn checkout pagina copy"),("↩️ Retour preventie","Maak een retour preventie strategie"),("📋 Pakbon insert","Schrijf teksten voor pakbon insert kaartjes"),("🎁 Bundel strategie","Maak een bundel strategie"),("📦 Voorraad teksten","Schrijf back-in-stock en voorraad teksten"),("🇳🇱 NL feestdagen","Maak een Nederlandse feestdagen actiekalender"),("⚡ Flash sale","Maak een flash sale campagne"),("🔁 Herhalingsaankoop","Maak een herhalingsaankoop strategie")]},
"ks":{"label":"📞 Klantenservice Bot","kleur":"#0E7490","avatar":"📞","desc":"Klachten, retours, FAQ, maatadvies en reviews","system":"Je bent een klantenservice expert voor een lingerie en slaapkussenwebshop. Schrijf warm, empathisch en duidelijk voor klanten van 40-65.","skills":[("😤 Klacht templates","Geef klacht response templates met LEAP methode"),("↩️ Retour handling","Schrijf retour en refund email templates"),("❓ FAQ pagina","Schrijf een FAQ pagina voor mijn webshop"),("⭐ Review antwoord","Geef review antwoord templates"),("💬 Live chat scripts","Maak live chat scripts voor mijn webshop"),("📏 Maatadvies","Schrijf een maatadvies script voor mijn klanten"),("📊 NPS enquête","Schrijf een NPS enquête en follow-up emails"),("📚 Product educatie","Schrijf educatieve content over BH of kussen kiezen")]},
"branding":{"label":"🎨 Branding Bot","kleur":"#7C2D12","avatar":"🎨","desc":"Brand story, positionering, USP's en klantprofielen","system":"Je bent een branding expert. Je helpt merken hun identiteit en positionering definiëren voor lingerie en slaapkussenbedrijven gericht op vrouwen 40-65.","skills":[("📖 Brand story","Schrijf het brand verhaal en over-ons pagina tekst"),("🗣️ Tone of voice","Maak een tone of voice gids voor mijn merk"),("💎 USP's","Ontwikkel de USP's voor mijn merk en producten"),("🎯 Positionering","Maak een merkpositionering strategie"),("👤 Klantprofiel","Maak een gedetailleerd klantprofiel buyer persona"),("🔍 Competitor analyse","Analyseer mijn concurrenten"),("🤝 Partnership voorstel","Schrijf een samenwerkingsvoorstel"),("📰 Persbericht","Schrijf een persbericht voor mijn productlancering")]},
"rapport":{"label":"📋 Rapporten Bot","kleur":"#374151","avatar":"📋","desc":"Weekrapporten, klantrapportages en automatische markt updates","system":"Je bent een marketing rapportage expert. Maak professionele rapporten voor marketing bureaus. Ook zoek je naar markttrends, concurrentenactiviteit en nieuws in de niche.","skills":[("📆 Weekrapport","Genereer een marketing weekrapport"),("📅 Maandrapport","Genereer een marketing maandrapport"),("📊 Klantrapportage","Maak een professionele klantrapportage"),("📋 Klant briefing","Maak een intake briefing document voor een nieuwe klant"),("💼 Offerte","Schrijf een offerte voor een nieuwe klant"),("🚀 Onboarding plan","Maak een onboarding plan voor een nieuwe marketing klant"),("🕵️ Markt + concurrent scan","Zoek actieve concurrent advertenties en markttrends in mijn niche en geef een overzicht"),("📨 Stuur marktrapport","Genereer een volledig marktrapport met concurrent ads analyse en stuur het via Gmail")]},
}

merk_data=laad_merk()
defaults={"actieve_bot":"marketing","merk_naam":merk_data.get("merk_naam",""),"niche":merk_data.get("niche",""),"doelgroep":merk_data.get("doelgroep",""),"toon":merk_data.get("toon","Warm & Persoonlijk"),"anthropic_key":"","gemini_key":"","klaviyo_key":"","gmail_user":"","gmail_pass":"","gorgias_domain":"","gorgias_user":"","gorgias_token":"","shopify_url":"","shopify_token":"","bestanden":[]}
for bid in BOTS:
    defaults[f"chat_{bid}"]=[];defaults[f"gesprek_{bid}"]=[];defaults[f"history_{bid}"]=[];defaults[f"pending_{bid}"]=None
for k,v in defaults.items():
    if k not in st.session_state: st.session_state[k]=v

def sla_gesprek_op(bid):
    ck=f"chat_{bid}"; hk=f"history_{bid}"; gk=f"gesprek_{bid}"
    b=st.session_state.get(ck,[])
    if not b: return
    preview=next((x["tekst"][:55] for x in b if x["rol"]=="gebruiker"),"Gesprek")
    st.session_state[hk]=[{"id":datetime.now().strftime("%H%M%S%f"),"timestamp":datetime.now().strftime("%d %b %H:%M"),"preview":preview,"berichten":list(b),"gesprek":list(st.session_state.get(gk,[]))}]+st.session_state[hk][:19]

def laad_gesprek(bid,conv_id):
    hk=f"history_{bid}"; ck=f"chat_{bid}"; gk=f"gesprek_{bid}"
    for c in st.session_state[hk]:
        if c["id"]==conv_id:
            sla_gesprek_op(bid)
            st.session_state[ck]=list(c["berichten"]); st.session_state[gk]=list(c["gesprek"]); break

def get_client():
    k=st.session_state.get("anthropic_key","") or os.environ.get("ANTHROPIC_API_KEY","")
    if not k: raise ValueError("Voer een Anthropic API key in via de sidebar.")
    return anthropic.Anthropic(api_key=k)

def zoek_concurrent(naam):
    try:
        r=requests.get(f"https://api.duckduckgo.com/?q={naam}+lingerie+advertising&format=json",timeout=8)
        t=[x.get("Text","") for x in r.json().get("RelatedTopics",[])[:5] if x.get("Text")]
        return "\n".join(t) or "Geen resultaten."
    except Exception as e: return f"Fout: {e}"

def zoek_concurrent_ads(naam,niche):
    queries=[f"{naam} Facebook ads {niche}",f"{naam} Instagram advertentie",f"{naam} Meta Ads Library"]
    resultaten=[]
    for q in queries:
        try:
            r=requests.get(f"https://api.duckduckgo.com/?q={q}&format=json",timeout=8)
            for x in r.json().get("RelatedTopics",[])[:3]:
                if x.get("Text"): resultaten.append(x["Text"][:200])
        except: pass
    return resultaten[:6]

def zoek_markt_trends(niche,producten):
    queries=[f"{niche} markt trends 2025",f"{producten} e-commerce Nederland",f"lingerie slaapkussens online shoppen vrouwen"]
    resultaten=[]
    for q in queries:
        try:
            r=requests.get(f"https://api.duckduckgo.com/?q={q}&format=json",timeout=8)
            for x in r.json().get("RelatedTopics",[])[:3]:
                if x.get("Text"): resultaten.append(x["Text"][:200])
        except: pass
    return resultaten[:8]

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
                    if part.get_content_type()=="text/plain": body=part.get_payload(decode=True).decode(errors="replace")[:300]; break
            else: body=msg.get_payload(decode=True).decode(errors="replace")[:300]
            mails.append(f"Van: {msg.get('From','')}\nOnderwerp: {subj}\nBericht: {body}")
        m.logout(); return "\n\n---\n\n".join(mails) or "Geen e-mails."
    except Exception as e: return f"Gmail fout: {e}"

def stuur_gmail_rapport(aan,onderwerp,tekst_body,gmail_user,gmail_pass):
    msg=MIMEMultipart("alternative"); msg["Subject"]=onderwerp; msg["From"]=gmail_user; msg["To"]=aan
    msg.attach(MIMEText(tekst_body,"plain","utf-8"))
    html=f"<html><body style='font-family:Arial,sans-serif;max-width:680px;margin:auto;padding:20px'><div style='background:#374151;padding:16px;border-radius:8px;margin-bottom:16px'><h2 style='color:white;margin:0'>📋 Marketing Agent Pro</h2><p style='color:#9CA3AF;margin:4px 0 0'>{onderwerp}</p></div><div style='background:#F9FAFB;padding:20px;border-radius:8px;line-height:1.7'>{tekst_body.replace(chr(10),'<br>')}</div><p style='color:#9CA3AF;font-size:11px;margin-top:16px'>Automatisch gegenereerd {datetime.now().strftime('%d %B %Y %H:%M')}</p></body></html>"
    msg.attach(MIMEText(html,"html","utf-8"))
    with smtplib.SMTP_SSL("smtp.gmail.com",465) as s: s.login(gmail_user,gmail_pass); s.sendmail(gmail_user,aan,msg.as_string())

def stuur_gmail(aan,onderwerp,tekst):
    try:
        user=st.session_state.get("gmail_user",""); pw=st.session_state.get("gmail_pass","")
        if not user or not pw: return "Gmail niet geconfigureerd."
        stuur_gmail_rapport(aan,onderwerp,tekst,user,pw); return f"Verstuurd naar {aan}."
    except Exception as e: return f"Gmail fout: {e}"

def maak_gorgias_ticket(onderwerp,bericht,email="klant@voorbeeld.nl"):
    try:
        dom=st.session_state.get("gorgias_domain",""); usr=st.session_state.get("gorgias_user",""); tok=st.session_state.get("gorgias_token","")
        if not all([dom,usr,tok]): return "Gorgias niet geconfigureerd."
        r=requests.post(f"https://{dom}.gorgias.com/api/tickets",json={"channel":"email","subject":onderwerp,"messages":[{"channel":"email","from_agent":False,"body_text":bericht,"sender":{"email":email}}]},auth=(usr,tok),headers={"Content-Type":"application/json"},timeout=10)
        return f"Ticket #{r.json().get('id','?')} aangemaakt." if r.status_code in [200,201] else f"Fout {r.status_code}"
    except Exception as e: return f"Gorgias fout: {e}"

def laad_shopify_producten():
    try:
        url=st.session_state.get("shopify_url",""); tok=st.session_state.get("shopify_token","")
        if not url or not tok: return "Shopify niet geconfigureerd."
        r=requests.get(f"https://{url}/admin/api/2024-01/products.json?limit=10",headers={"X-Shopify-Access-Token":tok},timeout=10)
        prods=r.json().get("products",[])
        return "\n".join([f"- {p['title']} (€{p['variants'][0].get('price','?')})" for p in prods]) or "Geen producten."
    except Exception as e: return f"Shopify fout: {e}"

def stuur_klaviyo_template(naam,html):
    try:
        k=st.session_state.get("klaviyo_key","")
        if not k: return "Klaviyo niet geconfigureerd."
        r=requests.post("https://a.klaviyo.com/api/templates/",json={"data":{"type":"template","attributes":{"name":naam,"html":html}}},headers={"Authorization":f"Klaviyo-API-Key {k}","revision":"2023-12-15","Content-Type":"application/json"},timeout=10)
        return f"Template '{naam}' aangemaakt." if r.status_code in [200,201] else f"Fout {r.status_code}"
    except Exception as e: return f"Klaviyo fout: {e}"

def genereer_afbeelding(omschrijving,bestandsnaam="advertentie"):
    try:
        k=st.session_state.get("gemini_key","")
        if not k: return "Gemini API key niet ingesteld."
        if not GEMINI_OK: return "Installeer: pip install google-genai"
        client=genai.Client(api_key=k)
        resp=client.models.generate_images(model="imagen-3.0-generate-002",prompt=omschrijving,config=gtypes.GenerateImagesConfig(number_of_images=1,aspect_ratio="1:1"))
        if not resp.generated_images: return "Geen afbeelding gegenereerd."
        ts=datetime.now().strftime("%H%M%S"); pad=IMG_DIR/f"{bestandsnaam}_{ts}.png"
        pad.write_bytes(resp.generated_images[0].image.image_bytes)
        if str(pad) not in st.session_state.bestanden: st.session_state.bestanden.append(str(pad))
        return f"Afbeelding opgeslagen: {pad}"
    except Exception as e: return f"Afbeelding fout: {e}"

def sla_rapport_op(inhoud,type_rapport="rapport"):
    try:
        ts=datetime.now().strftime("%Y%m%d_%H%M"); naam=re.sub(r'[^a-zA-Z0-9]','_',st.session_state.get("merk_naam","rapport"))
        pad=BASE_DIR/f"{naam}_{type_rapport}_{ts}.txt"; pad.write_text(inhoud,encoding="utf-8")
        log=laad_rapport_log(); log.append({"type":type_rapport,"merk":st.session_state.get("merk_naam",""),"datum":ts,"pad":str(pad)}); sla_rapport_log(log)
        if str(pad) not in st.session_state.bestanden: st.session_state.bestanden.append(str(pad))
        return f"Rapport opgeslagen: {pad}"
    except Exception as e: return f"Opslaan fout: {e}"

TOOLS=[
    {"name":"zoek_concurrent","description":"Zoek informatie over een concurrent online","input_schema":{"type":"object","properties":{"naam":{"type":"string"}},"required":["naam"]}},
    {"name":"zoek_concurrent_ads","description":"Zoek advertentie-activiteit van een concurrent in Meta Ads Library","input_schema":{"type":"object","properties":{"naam":{"type":"string"},"niche":{"type":"string","default":"lingerie"}},"required":["naam"]}},
    {"name":"zoek_markt_trends","description":"Zoek markttrends en nieuws voor een niche","input_schema":{"type":"object","properties":{"niche":{"type":"string"},"producten":{"type":"string"}},"required":["niche","producten"]}},
    {"name":"lees_gmail","description":"Lees Gmail emails","input_schema":{"type":"object","properties":{"aantal":{"type":"integer","default":5}},"required":[]}},
    {"name":"stuur_gmail","description":"Stuur email via Gmail","input_schema":{"type":"object","properties":{"aan":{"type":"string"},"onderwerp":{"type":"string"},"tekst":{"type":"string"}},"required":["aan","onderwerp","tekst"]}},
    {"name":"maak_gorgias_ticket","description":"Maak Gorgias ticket","input_schema":{"type":"object","properties":{"onderwerp":{"type":"string"},"bericht":{"type":"string"},"email":{"type":"string"}},"required":["onderwerp","bericht"]}},
    {"name":"laad_shopify_producten","description":"Laad Shopify producten","input_schema":{"type":"object","properties":{},"required":[]}},
    {"name":"stuur_klaviyo_template","description":"Stuur template naar Klaviyo","input_schema":{"type":"object","properties":{"naam":{"type":"string"},"html":{"type":"string"}},"required":["naam","html"]}},
    {"name":"genereer_afbeelding","description":"Genereer afbeelding met Google Imagen","input_schema":{"type":"object","properties":{"omschrijving":{"type":"string"},"bestandsnaam":{"type":"string","default":"advertentie"}},"required":["omschrijving"]}},
    {"name":"sla_rapport_op","description":"Sla rapport op als bestand","input_schema":{"type":"object","properties":{"inhoud":{"type":"string"},"type_rapport":{"type":"string","default":"rapport"}},"required":["inhoud"]}},
]
TOOL_LABELS={"zoek_concurrent":"Concurrent zoeken","zoek_concurrent_ads":"Concurrent Ads Library","zoek_markt_trends":"Markttrends zoeken","lees_gmail":"Gmail lezen","stuur_gmail":"Email sturen","maak_gorgias_ticket":"Gorgias ticket","laad_shopify_producten":"Shopify laden","stuur_klaviyo_template":"Klaviyo template","genereer_afbeelding":"Afbeelding genereren","sla_rapport_op":"Rapport opslaan"}

def voer_tool_uit(naam,invoer):
    match naam:
        case "zoek_concurrent": return zoek_concurrent(invoer.get("naam",""))
        case "zoek_concurrent_ads": return str(zoek_concurrent_ads(invoer.get("naam",""),invoer.get("niche","lingerie")))
        case "zoek_markt_trends": return str(zoek_markt_trends(invoer.get("niche",""),invoer.get("producten","")))
        case "lees_gmail": return lees_gmail(invoer.get("aantal",5))
        case "stuur_gmail": return stuur_gmail(invoer.get("aan",""),invoer.get("onderwerp",""),invoer.get("tekst",""))
        case "maak_gorgias_ticket": return maak_gorgias_ticket(invoer.get("onderwerp",""),invoer.get("bericht",""),invoer.get("email","klant@voorbeeld.nl"))
        case "laad_shopify_producten": return laad_shopify_producten()
        case "stuur_klaviyo_template": return stuur_klaviyo_template(invoer.get("naam",""),invoer.get("html",""))
        case "genereer_afbeelding": return genereer_afbeelding(invoer.get("omschrijving",""),invoer.get("bestandsnaam","advertentie"))
        case "sla_rapport_op": return sla_rapport_op(invoer.get("inhoud",""),invoer.get("type_rapport","rapport"))
        case _: return f"Onbekende tool: {naam}"

def verwerk_bericht(bid,vraag,img_bytes=None,media_type=None):
    bot=BOTS[bid]; client=get_client(); vraag=parse_slash(vraag)
    system=(f"{bot['system']}\n\nKlant: Merk={st.session_state.get('merk_naam','—')}, Niche={st.session_state.get('niche','—')}, Doelgroep={st.session_state.get('doelgroep','—')}, Toon={st.session_state.get('toon','Warm & Persoonlijk')}\n\nVoor markt/concurrent onderzoek gebruik je de tools zoek_concurrent_ads en zoek_markt_trends. Voor rapporten stuur je ze via stuur_gmail als het om een auto-rapport gaat.")
    content=[{"type":"image","source":{"type":"base64","media_type":media_type,"data":base64.standard_b64encode(img_bytes).decode()}},{"type":"text","text":vraag}] if img_bytes and media_type else vraag
    gk=f"gesprek_{bid}"; ck=f"chat_{bid}"
    st.session_state[gk].append({"role":"user","content":content})
    antwoord=client.messages.create(model="claude-sonnet-4-6",max_tokens=4096,temperature=0.7,system=system,tools=TOOLS,messages=st.session_state[gk])
    tool_log=[]
    while antwoord.stop_reason=="tool_use":
        tool_results=[]
        for block in antwoord.content:
            if block.type=="tool_use":
                label=TOOL_LABELS.get(block.name,block.name); resultaat=voer_tool_uit(block.name,block.input); res_str=str(resultaat)
                if "opgeslagen:" in res_str.lower():
                    pad=res_str.split("opgeslagen:")[-1].strip()
                    if Path(pad).exists() and pad not in st.session_state.bestanden: st.session_state.bestanden.append(pad)
                img_path=None
                if block.name=="genereer_afbeelding" and "opgeslagen:" in res_str.lower(): img_path=res_str.split("opgeslagen:")[-1].strip()
                tool_log.append({"label":label,"resultaat":resultaat,"img_path":img_path})
                tool_results.append({"type":"tool_result","tool_use_id":block.id,"content":res_str})
        st.session_state[gk].append({"role":"assistant","content":antwoord.content})
        st.session_state[gk].append({"role":"user","content":tool_results})
        antwoord=client.messages.create(model="claude-sonnet-4-6",max_tokens=4096,temperature=0.7,system=system,tools=TOOLS,messages=st.session_state[gk])
    bot_tekst=antwoord.content[0].text
    st.session_state[gk].append({"role":"assistant","content":bot_tekst})
    img_b64=base64.standard_b64encode(img_bytes).decode() if img_bytes else None
    st.session_state[ck].append({"rol":"gebruiker","tekst":vraag,"img_b64":img_b64})
    st.session_state[ck].append({"rol":"bot","tekst":bot_tekst,"tools":tool_log})

# ─── SIDEBAR ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🚀 Marketing Agent Pro")
    st.caption("9 Bots • 101 Skills • Claude + Gemini")
    st.divider()
    st.markdown("**Bot selecteren**")
    gekozen=st.radio("Bot",options=list(BOTS.keys()),format_func=lambda x:BOTS[x]["label"],index=list(BOTS.keys()).index(st.session_state.actieve_bot),label_visibility="collapsed",key="bot_radio")
    if gekozen!=st.session_state.actieve_bot: st.session_state.actieve_bot=gekozen; st.rerun()
    st.divider()
    st.markdown("**Verbindingen**")
    for naam,ok in [("Claude",bool(st.session_state.get("anthropic_key",""))),("Gemini",bool(st.session_state.get("gemini_key",""))),("Gmail",bool(st.session_state.get("gmail_user",""))),("Klaviyo",bool(st.session_state.get("klaviyo_key",""))),("Shopify",bool(st.session_state.get("shopify_url",""))),("Gorgias",bool(st.session_state.get("gorgias_domain","")))]:
        st.markdown(f'<span style="color:{"green" if ok else "red"};font-weight:700;font-size:.82rem">{"●" if ok else "○"} {naam}</span>',unsafe_allow_html=True)
    with st.expander("🔑 API Sleutels"):
        st.session_state.anthropic_key=st.text_input("Anthropic",value=st.session_state.get("anthropic_key",""),type="password",key="i_ant")
        st.session_state.gemini_key=st.text_input("Gemini",value=st.session_state.get("gemini_key",""),type="password",key="i_gem")
        st.session_state.klaviyo_key=st.text_input("Klaviyo",value=st.session_state.get("klaviyo_key",""),type="password",key="i_klav")
    with st.expander("🔌 Integraties"):
        st.session_state.gmail_user=st.text_input("Gmail adres",value=st.session_state.get("gmail_user",""),key="i_gm")
        st.session_state.gmail_pass=st.text_input("Gmail wachtwoord",value=st.session_state.get("gmail_pass",""),type="password",key="i_gp")
        st.session_state.gorgias_domain=st.text_input("Gorgias domein",value=st.session_state.get("gorgias_domain",""),key="i_gd")
        st.session_state.gorgias_user=st.text_input("Gorgias gebruiker",value=st.session_state.get("gorgias_user",""),key="i_gu")
        st.session_state.gorgias_token=st.text_input("Gorgias token",value=st.session_state.get("gorgias_token",""),type="password",key="i_gt")
        st.session_state.shopify_url=st.text_input("Shopify URL",value=st.session_state.get("shopify_url",""),key="i_su")
        st.session_state.shopify_token=st.text_input("Shopify token",value=st.session_state.get("shopify_token",""),type="password",key="i_st")
    with st.expander("🏪 Klant & Niche",expanded=True):
        st.session_state.merk_naam=st.text_input("Merknaam",value=st.session_state.get("merk_naam",""),key="i_mn")
        st.session_state.niche=st.text_input("Niche",value=st.session_state.get("niche",""),placeholder="bijv. lingerie 40-65+",key="i_ni")
        st.session_state.doelgroep=st.text_input("Doelgroep",value=st.session_state.get("doelgroep",""),key="i_do")
        st.session_state.toon=st.selectbox("Toon",["Warm & Persoonlijk","Professioneel","Energiek","Luxe"],key="s_to")
        if st.button("💾 Opslaan",use_container_width=True,key="btn_save"):
            sla_merk({"merk_naam":st.session_state.merk_naam,"niche":st.session_state.niche,"doelgroep":st.session_state.doelgroep,"toon":st.session_state.toon}); st.success("Opgeslagen!")
    if st.session_state.get("bestanden"):
        st.divider(); st.markdown("**Bestanden**")
        for pad in st.session_state.bestanden[-5:]:
            p=Path(pad)
            if p.exists():
                try: st.download_button(f"⬇️ {p.name}",data=p.read_bytes(),file_name=p.name,key=f"dl_{pad[-12:]}")
                except: pass

# ─── MAIN ─────────────────────────────────────────────────────────────────────
bid=st.session_state.actieve_bot; bot=BOTS[bid]; kleur=bot["kleur"]
ck=f"chat_{bid}"; hk=f"history_{bid}"; pk=f"pending_{bid}"
n_msg=len(st.session_state.get(ck,[]))
st.markdown(f'<div class="bot-header" style="background:linear-gradient(135deg,{kleur} 0%,{kleur}CC 100%)"><span style="font-size:2rem">{bot["avatar"]}</span>&nbsp;&nbsp;<div style="flex:1;display:inline-block"><div class="bot-title">{bot["label"]}</div><div class="bot-desc">{bot["desc"]}</div></div><span style="float:right;text-align:right;opacity:.9"><strong style="font-size:1.3rem">{n_msg//2}</strong><br><span style="font-size:.6rem;text-transform:uppercase">berichten</span></span></div>',unsafe_allow_html=True)

# Skills
st.markdown('<span class="sec-lbl">Skills — klik om direct te gebruiken</span>',unsafe_allow_html=True)
sc=st.columns(min(len(bot["skills"]),5))
for i,(lbl,cmd) in enumerate(bot["skills"]):
    with sc[i%5]:
        if st.button(lbl,key=f"sk_{bid}_{i}",use_container_width=True):
            st.session_state[pk]=cmd  # ✅ Overleeft rerun
st.divider()

# 3-kolom layout
col_hist,col_chat,col_opts=st.columns([1,3,1])

# ── HISTORY ──
with col_hist:
    st.markdown('<span class="sec-lbl">Eerdere gesprekken</span>',unsafe_allow_html=True)
    if st.button("+ Nieuw gesprek",use_container_width=True,key=f"new_{bid}"):
        sla_gesprek_op(bid); st.session_state[ck]=[]; st.session_state[f"gesprek_{bid}"]=[]; st.rerun()
    history=st.session_state.get(hk,[])
    if not history: st.caption("Nog geen eerdere gesprekken.")
    else:
        for conv in history:
            lbl=f"**{conv['timestamp']}**\n{conv['preview'][:42]}{'...' if len(conv['preview'])>42 else ''}"
            if st.button(lbl,key=f"load_{bid}_{conv['id']}",use_container_width=True):
                laad_gesprek(bid,conv["id"]); st.rerun()

# ── CHAT ──
with col_chat:
    berichten=st.session_state.get(ck,[])
    chat_html='<div class="chat-wrap">'
    if not berichten:
        chat_html+=f'<div class="chat-leeg"><div style="font-size:2rem;margin-bottom:8px">{bot["avatar"]}</div><div style="font-weight:700;color:#334155;margin-bottom:4px">{bot["label"]} staat klaar</div><div style="font-size:.82rem">{bot["desc"]}</div><div style="margin-top:8px;font-size:.76rem;color:#94A3B8">Klik een skill of typ hieronder. Gebruik / voor commando\'s.</div></div>'
    else:
        for b in berichten:
            if b["rol"]=="gebruiker":
                t=b["tekst"].replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")
                chat_html+=f'<div class="msg-user"><div class="msg-user-bubble" style="background:{kleur}">{t}</div></div>'
            else:
                t=b["tekst"].replace("&","&amp;").replace("<","&lt;").replace(">","&gt;").replace("\n","<br>")
                chat_html+=f'<div class="msg-bot"><div class="msg-av" style="background:{kleur}22;color:{kleur}">{bot["avatar"]}</div><div class="msg-bot-bubble">{t}</div></div>'
    chat_html+="</div>"
    st.markdown(chat_html,unsafe_allow_html=True)
    for b in berichten:
        if b["rol"]=="bot":
            for t in b.get("tools",[]):
                st.info(f"**{t['label']}** — uitgevoerd\n\n{str(t['resultaat'])[:400]}")
                if t.get("img_path") and Path(t["img_path"]).exists():
                    st.image(t["img_path"],use_column_width=True,caption="Gegenereerde afbeelding — Google Imagen")
                    try: st.download_button("⬇️ Download",data=Path(t["img_path"]).read_bytes(),file_name=Path(t["img_path"]).name,mime="image/png",key=f"img_dl_{t['img_path'][-10:]}")
                    except: pass
        if b["rol"]=="gebruiker" and b.get("img_b64"):
            try: st.image(base64.b64decode(b["img_b64"]),width=220,caption="Meegestuurde afbeelding")
            except: pass
    st.caption("Slash commando's: "+", ".join([f"`{c}`" for c in SLASH.keys()]))
    invoer=st.chat_input(f"Stuur een bericht naar {bot['label']}...",key=f"ci_{bid}")
    pending=st.session_state.get(pk)
    trigger=invoer or pending
    if trigger:
        st.session_state[pk]=None
        with st.spinner(f"{bot['avatar']} Bezig..."):
            try: verwerk_bericht(bid,str(trigger),st.session_state.get(f"img_{bid}"),st.session_state.get(f"img_type_{bid}"))
            except Exception as e: st.error(f"Fout: {e}")
        st.rerun()

# ── OPTIES ──
with col_opts:
    st.markdown('<span class="sec-lbl">Opties</span>',unsafe_allow_html=True)
    geup=st.file_uploader("Afbeelding",type=["png","jpg","jpeg","webp"],key=f"up_{bid}")
    if geup:
        ib=geup.read(); st.session_state[f"img_{bid}"]=ib; st.session_state[f"img_type_{bid}"]=geup.type or "image/jpeg"
        st.image(ib,use_column_width=True,caption=geup.name)
    else:
        st.session_state[f"img_{bid}"]=None; st.session_state[f"img_type_{bid}"]=None
    st.markdown("")
    if st.button("Gesprek wissen",use_container_width=True,key=f"reset_{bid}"):
        sla_gesprek_op(bid); st.session_state[ck]=[]; st.session_state[f"gesprek_{bid}"]=[]; st.rerun()

    if bid=="email":
        st.markdown('<span class="sec-lbl">Klaviyo</span>',unsafe_allow_html=True)
        kn=st.text_input("Template naam",placeholder="bijv. Promo Mei",key="klav_n")
        if st.button("Push naar Klaviyo",use_container_width=True,key="klav_btn") and kn:
            st.session_state[pk]=f"Stuur het email concept als Klaviyo template met naam '{kn}'"; st.rerun()

    if bid=="ks":
        st.markdown('<span class="sec-lbl">Gorgias ticket</span>',unsafe_allow_html=True)
        g_ond=st.text_input("Onderwerp",key="g_ond"); g_ber=st.text_area("Bericht",height=70,key="g_ber")
        if st.button("Maak ticket",use_container_width=True,key="btn_gorg") and g_ond:
            st.session_state[pk]=f"Maak Gorgias ticket: '{g_ond}' — '{g_ber}'"; st.rerun()

    # ── AUTO-RAPPORT (Rapport Bot) ──
    if bid=="rapport":
        st.divider()
        st.markdown('<span class="sec-lbl">Automatische Rapporten</span>',unsafe_allow_html=True)
        auto_cfg=laad_auto_config()
        em_best=st.text_input("Sturen naar (email)",value=auto_cfg.get("email_bestemming",st.session_state.get("gmail_user","")),placeholder="jouw@email.nl",key="ar_email")
        conc_str=st.text_input("Concurrenten (komma gescheiden)",value=", ".join(auto_cfg.get("concurrenten",[])),placeholder="Anita, Triumph, Sloggi",key="ar_conc")
        prod_str=st.text_input("Producten/niche context",value=auto_cfg.get("producten",st.session_state.get("niche","")),placeholder="comfort BH's, slaapkussens",key="ar_prod")
        wekelijks=st.checkbox("Wekelijks rapport (elke maandag)",value=auto_cfg.get("wekelijks",False),key="ar_week")
        maandelijks=st.checkbox("Maandelijks rapport (elke 1e v/d maand)",value=auto_cfg.get("maandelijks",False),key="ar_maand")
        if st.button("💾 Config opslaan",use_container_width=True,key="ar_save"):
            nieuwe_cfg={**auto_cfg,"email_bestemming":em_best,"concurrenten":[c.strip() for c in conc_str.split(",") if c.strip()],"producten":prod_str,"wekelijks":wekelijks,"maandelijks":maandelijks,"merk_naam":st.session_state.get("merk_naam",""),"niche":st.session_state.get("niche",""),"doelgroep":st.session_state.get("doelgroep",""),"anthropic_key":st.session_state.get("anthropic_key",""),"gmail_user":st.session_state.get("gmail_user",""),"gmail_pass":st.session_state.get("gmail_pass","")}
            sla_auto_config(nieuwe_cfg); st.success("✅ Config opgeslagen!")
        if st.button("📧 Test rapport nu sturen",use_container_width=True,key="ar_test"):
            niche=st.session_state.get("niche","lingerie en slaapkussens"); concs=conc_str
            st.session_state[pk]=(f"Stuur een automatisch marktrapport: 1) Gebruik zoek_markt_trends voor niche '{niche}' en producten '{prod_str}', 2) Gebruik zoek_concurrent_ads voor elke concurrent in '{concs}', 3) Genereer een volledig professioneel {('wekelijks' if wekelijks else 'maandelijks')} marktrapport met samenvatting, markttrends, concurrent analyse en 5 concrete aanbevelingen, 4) Sla het op via sla_rapport_op, 5) Stuur het via stuur_gmail naar '{em_best}' met onderwerp '🚀 Marketing Rapport — {st.session_state.get('merk_naam','Merk')} — {datetime.now().strftime('%d %B %Y')}'")
            st.rerun()
        auto_log=laad_auto_log()
        if auto_log:
            st.markdown('<span class="sec-lbl">Laatste auto-rapporten</span>',unsafe_allow_html=True)
            for entry in auto_log[:3]:
                icon="✅" if entry.get("succes") else "❌"
                st.caption(f"{icon} {entry.get('type','')} — {entry.get('datum',''[:16])}")
        rlog=laad_rapport_log()
        if rlog:
            st.markdown('<span class="sec-lbl">Eerdere rapporten</span>',unsafe_allow_html=True)
            for i,r in enumerate(reversed(rlog[-4:])):
                pad=r.get("pad","")
                if pad and Path(pad).exists():
                    try: st.download_button(f"⬇️ {r.get('type','')} {r.get('datum','')[:10]}",data=Path(pad).read_bytes(),file_name=Path(pad).name,key=f"rp_dl_{i}")
                    except: pass
