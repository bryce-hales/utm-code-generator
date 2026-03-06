# python3 -m streamlit run /Users/brycehales/Documents/GitHub/utm-code-generator/app.py

from __future__ import annotations
import re
from urllib.parse import urlsplit, urlunsplit, urlencode
from datetime import datetime, timezone
import time
import pandas as pd
import streamlit as st
from streamlit_gsheets import GSheetsConnection


SOURCE_TO_MEDIUMS = {
    "google": ["organic", "cpc", "paid", "shopping", "video", "remarketing"],
    "bing": ["organic", "cpc", "paid", "shopping", "remarketing"],
    "duckduckgo": ["organic", "cpc", "paid"],
    "yahoo": ["organic", "cpc", "paid"],
    "facebook": ["paid-social", "organic-social", "video", "content", "remarketing", "referral"],
    "instagram": ["paid-social", "organic-social", "video", "content", "shopping"],
    "linkedin": ["paid-social", "organic-social", "content", "video"],
    "twitter": ["paid-social", "organic-social", "content"],
    "youtube": ["video", "paid-social", "organic-social", "content", "remarketing"],
    "tiktok": ["video", "paid-social", "content", "remarketing"],
    "pinterest": ["paid-social", "organic-social", "shopping", "content"],
    "snapchat": ["paid-social", "video", "remarketing"],
    "reddit": ["paid-social", "community", "content", "remarketing"],
    "quora": ["paid-social", "content"],
    "amazon": ["shopping", "cpc", "paid", "referral", "remarketing"],
    "etsy": ["shopping", "referral", "content"],
    "ebay": ["shopping", "referral"],
    "shopify": ["referral", "internal", "content"],
    "walmart": ["shopping", "cpc", "paid", "referral"],
    "target": ["shopping", "cpc", "paid", "referral"],
    "brevo": ["email", "sms", "content", "internal"],
    "hubspot": ["email", "sms", "content", "internal"],
    "medium": ["content", "referral", "organic"],
    "discord": ["community", "referral", "content"],
    "google-shopping": ["shopping", "cpc", "paid"],
    "meta": ["paid-social", "organic-social", "video", "content", "remarketing"],
    "whatsapp": ["sms", "community", "referral"],
    "telegram": ["sms", "community", "referral"],
}

MEDIUM_TO_CAMPAIGNS = {
    "organic": ["brand", "education", "how-to", "seo-content", "content-hub", "announcement", "press", "community", "ugc"],
    "cpc": ["brand", "prospecting", "retargeting", "remarketing", "launch", "product-launch", "new-arrival", "feature-release",
            "promo", "sale", "flash-sale", "holiday", "seasonal", "clearance", "bundle", "starter-kit", "lead-gen"],
    "paid": ["brand", "prospecting", "retargeting", "remarketing", "launch", "product-launch", "new-arrival", "feature-release",
             "promo", "sale", "flash-sale", "holiday", "seasonal", "clearance", "bundle", "starter-kit", "lead-gen"],
    "shopping": ["product-launch", "new-arrival", "promo", "sale", "flash-sale", "holiday", "seasonal", "clearance", "bundle", "starter-kit"],
    "paid-social": ["brand", "prospecting", "retargeting", "remarketing", "launch", "product-launch", "new-arrival", "feature-release",
                    "promo", "sale", "flash-sale", "holiday", "seasonal", "giveaway", "contest", "lead-gen", "lead-nurture", "reengagement", "winback"],
    "organic-social": ["brand", "launch", "product-launch", "new-arrival", "feature-release", "announcement", "community", "ugc",
                       "giveaway", "contest", "education", "how-to"],
    "email": ["brand", "promo", "sale", "flash-sale", "holiday", "seasonal", "member-exclusive", "loyalty", "vip", "lead-nurture",
              "reengagement", "winback", "abandoned-cart", "abandoned-browse", "post-purchase", "education", "how-to", "webinar-series", "event-series"],
    "sms": ["promo", "sale", "flash-sale", "holiday", "seasonal", "member-exclusive", "loyalty", "vip", "reengagement", "winback",
            "abandoned-cart", "post-purchase"],
    "content": ["content-hub", "seo-content", "education", "how-to", "announcement", "press", "survey", "feedback", "community", "ugc"],
    "community": ["community", "ugc", "education", "how-to", "event-series", "webinar-series", "referral-program"],
    "affiliate": ["affiliate-program", "referral-program", "promo", "sale"],
    "referral": ["referral-program", "partner", "community", "ugc", "content-hub"],
    "partner": ["partner", "referral-program", "affiliate-program"],
    "video": ["brand", "launch", "product-launch", "feature-release", "education", "how-to", "promo"],
    "audio": ["podcast-series", "brand", "education", "how-to"],
    "event": ["event-series", "event", "lead-gen", "brand", "community"],
    "webinar": ["webinar-series", "lead-gen", "lead-nurture", "education"],
    "podcast": ["podcast-series", "brand", "education", "how-to"],
    "print": ["brand", "promo", "sale", "event", "lead-gen"],
    "direct-mail": ["brand", "promo", "sale", "winback", "lead-gen"],
    "qr": ["brand", "promo", "event", "lead-gen"],
    "internal": ["internal", "member-exclusive", "loyalty", "education"],
    "remarketing": ["retargeting", "remarketing", "winback", "abandoned-cart", "abandoned-browse"],
    # Legacy/optional mediums you may keep:
    "push": ["promo", "sale", "flash-sale", "holiday", "seasonal", "abandoned-cart", "post-purchase"],
    "transactional-email": ["post-purchase", "abandoned-cart", "abandoned-browse"],
    "sponsored": ["content-hub", "seo-content", "press", "announcement", "promo"],
    "influencer": ["influencer-program", "ugc", "launch", "product-launch", "promo", "giveaway"],
}

CAMPAIGN_TO_CONTENT = {
    "brand": ["hero", "primary", "secondary", "cta", "cta-primary", "cta-secondary", "button", "text-link", "image", "video", "static", "logo"],
    "prospecting": ["hero", "primary", "secondary", "cta", "cta-primary", "button", "video", "short-video", "carousel", "static"],
    "retargeting": ["hero", "primary", "cta", "cta-primary", "offer", "discount", "free-shipping", "limited-time", "countdown", "video", "static"],
    "remarketing": ["hero", "primary", "cta", "offer", "discount", "free-shipping", "limited-time", "countdown", "video", "static"],
    "launch": ["hero", "primary", "announcement", "new", "video", "short-video", "carousel", "static"],
    "product-launch": ["hero", "primary", "new", "best-seller", "featured", "video", "short-video", "carousel", "static"],
    "new-arrival": ["hero", "primary", "new", "featured", "carousel", "image", "video", "static"],
    "feature-release": ["hero", "primary", "how-it-works", "demo", "video", "short-video", "static"],
    "promo": ["hero", "primary", "offer", "discount", "free-shipping", "limited-time", "countdown", "button", "video", "static"],
    "sale": ["hero", "primary", "offer", "discount", "limited-time", "countdown", "button", "video", "static"],
    "flash-sale": ["hero", "primary", "offer", "discount", "limited-time", "countdown", "button", "video", "static"],
    "holiday": ["hero", "primary", "offer", "discount", "free-shipping", "limited-time", "countdown", "video", "static"],
    "seasonal": ["hero", "primary", "offer", "discount", "featured", "video", "static"],
    "clearance": ["hero", "primary", "offer", "discount", "limited-time", "countdown", "video", "static"],
    "bundle": ["hero", "primary", "comparison", "offer", "discount", "video", "static"],
    "starter-kit": ["hero", "primary", "education", "how-it-works", "comparison", "offer", "video", "static"],
    "upsell": ["primary", "secondary", "comparison", "offer", "discount", "button", "static"],
    "cross-sell": ["primary", "secondary", "comparison", "offer", "button", "static"],
    "loyalty": ["hero", "member-exclusive", "vip", "offer", "discount", "free-shipping", "reminder"],
    "vip": ["vip", "member-exclusive", "offer", "discount", "free-shipping"],
    "member-exclusive": ["member-exclusive", "offer", "discount", "free-shipping", "limited-time"],
    "referral-program": ["offer", "discount", "cta", "cta-primary", "how-it-works", "reminder"],
    "affiliate-program": ["offer", "discount", "cta", "cta-primary", "logo"],
    "influencer-program": ["influencer", "creator", "ugc", "video", "short-video", "review", "testimonial"],
    "giveaway": ["offer", "cta", "cta-primary", "limited-time", "countdown", "story", "reel", "short-video"],
    "contest": ["offer", "cta", "cta-primary", "limited-time", "countdown", "story", "reel", "short-video"],
    "lead-gen": ["hero", "primary", "cta", "cta-primary", "offer", "button"],
    "lead-nurture": ["education", "how-to", "tutorial", "faq", "reminder", "follow-up", "copy-short", "copy-long"],
    "reengagement": ["reminder", "offer", "discount", "limited-time", "countdown", "copy-short", "copy-long"],
    "winback": ["offer", "discount", "limited-time", "countdown", "reminder", "copy-short", "copy-long"],
    "abandoned-cart": ["reminder", "offer", "discount", "free-shipping", "limited-time", "copy-short"],
    "abandoned-browse": ["reminder", "featured", "offer", "discount", "copy-short"],
    "post-purchase": ["education", "how-to", "setup-guide", "review", "ugc", "follow-up"],
    "education": ["education", "how-to", "tutorial", "faq", "setup-guide", "troubleshooting", "demo"],
    "how-to": ["how-to", "tutorial", "setup-guide", "faq", "video", "short-video"],
    "demo": ["demo", "how-it-works", "video", "short-video"],
    "webinar-series": ["webinar", "education", "cta", "cta-primary", "reminder", "follow-up"],
    "event-series": ["event", "cta", "cta-primary", "reminder", "follow-up", "print", "qr"],
    "podcast-series": ["podcast", "audio", "education", "cta", "cta-primary"],
    "content-hub": ["education", "how-to", "comparison", "featured", "review"],
    "seo-content": ["education", "how-to", "comparison", "review"],
    "announcement": ["announcement", "new", "hero", "primary"],
    "press": ["announcement", "logo", "review"],
    "survey": ["survey", "cta", "cta-primary"],
    "feedback": ["feedback", "cta", "cta-primary"],
    "community": ["community", "ugc", "creator", "story", "reel"],
    "ugc": ["ugc", "creator", "testimonial", "review", "video", "short-video"],
    "test": ["test", "version-a", "version-b", "version-c", "variant-1", "variant-2", "variant-3", "headline-1", "headline-2", "headline-3"],
    "experiment": ["test", "version-a", "version-b", "version-c", "variant-1", "variant-2", "variant-3", "headline-1", "headline-2", "headline-3"],
    "internal": ["internal", "education", "how-to", "setup-guide"],
}

TERMS_GLOBAL = [
    "sunstone+brand","sunstone+products","brand+welder","brand+kit","brand+chain",
    "permanent+jewelry","permanent+jewelry+kit","permanent+jewelry+welder",
    "permanent+jewelry+training","permanent+jewelry+certification",
    "starter+kit","professional+kit","beginner+kit","advanced+kit",
    "mobile+artist","studio+artist","popup+artist","event+artist",
    "small+business","solo+artist","scaling+business","new+artist",
    "experienced+artist","repeat+customer","pj+pro+member","membership","subscription",
    "chain+by+the+inch","jump+rings","welding+machine","pulse+arc+welder","laser+welder",
    "precision+welder","welding+settings","auto+settings","safety+equipment","darkening+lens",
    "stylus","accessories","consumables","education","training","certification","course",
    "how+to","tutorial","setup+guide","troubleshooting","best+for+beginners","best+for+professionals",
    "comparison","alternative","upgrade","replacement","price+focused","investment","financing","roi",
    "b2b","b2c","direct+to+consumer","wholesale","event+sales","in+person","online","us+based","trusted+brand"
]

# =========================
# HELPERS
# =========================
def strip_query(url: str) -> str:
    parts = urlsplit((url or "").strip())
    return urlunsplit((parts.scheme, parts.netloc, parts.path, "", ""))


def is_valid_url(url: str) -> bool:
    return bool(re.match(r"^https?://", (url or "").strip(), re.I))


def build_url(base_url: str, params: dict) -> str:
    return strip_query(base_url) + "?" + urlencode(params, safe="+-")


def format_term(value: str) -> str:
    value = (value or "").strip().lower()
    value = re.sub(r"\s+", "+", value)
    return value


def current_sig(base_url, source, medium, campaign, content, term, notes):
    return (
        strip_query(base_url),
        source,
        medium,
        campaign,
        content or "",
        term or "",
        (notes or "").strip(),
    )


# =========================
# PAGE CONFIG
# =========================
st.set_page_config(
    page_title="Sunstone UTM Builder",
    page_icon="🔗",
    layout="wide",
)

# =========================
# STYLING
# =========================
st.markdown(
    """
    <style>
        :root {
            --sunstone-bg: #F7F5F1;
            --sunstone-surface: #FFFFFF;
            --sunstone-surface-soft: #F2EEE7;
            --sunstone-text: #1F1A17;
            --sunstone-muted: #6F675F;
            --sunstone-border: #E7DED2;
            --sunstone-gold: #C9A86A;
            --sunstone-gold-dark: #A8874E;
            --sunstone-shadow: 0 8px 24px rgba(31, 26, 23, 0.06);
            --sunstone-radius: 18px;
        }

        /* Radio / checkbox option text */
        [data-baseweb="radio"] label,
        [data-baseweb="checkbox"] label {
            color: #1F1A17 !important;
        }

        /* Selected radio text */
        [data-baseweb="radio"] div {
            color: #1F1A17 !important;
        }

        /* Selected checkbox text */
        [data-baseweb="checkbox"] div {
            color: #1F1A17 !important;
        }

        /* Fix selected label inside Streamlit radio groups */
        .stRadio label {
            color: #1F1A17 !important;
        }

        /* Fix radio label span */
        .stRadio span {
            color: #1F1A17 !important;
        }

        /* Global text color */
        html, body, .stApp {
            background: linear-gradient(180deg, #F7F5F1 0%, #F3EFE8 100%);
            color: var(--sunstone-text) !important;
        }

        /* Main container */
        .block-container {
            padding-top: 2.2rem;
            padding-bottom: 2rem;
            max-width: 1280px;
            color: var(--sunstone-text);
        }

        /* Headings */
        h1, h2, h3 {
            color: var(--sunstone-text) !important;
            letter-spacing: -0.02em;
        }

        /* Labels, captions, markdown text */
        label, .stMarkdown, .stCaption, .stTextInput, .stSelectbox, .stRadio {
            color: var(--sunstone-text) !important;
        }

        /* Input text */
        input, textarea {
            color: var(--sunstone-text) !important;
        }

        /* Dropdown text */
        div[data-baseweb="select"] {
            color: var(--sunstone-text) !important;
        }

        /* Sidebar text */
        [data-testid="stSidebar"] * {
            color: var(--sunstone-text) !important;
        }

        .hero-wrap {
            background: linear-gradient(135deg, #FFFFFF 0%, #F4EFE6 100%);
            border: 1px solid var(--sunstone-border);
            border-radius: 24px;
            padding: 28px 30px 22px 30px;
            box-shadow: var(--sunstone-shadow);
            margin-bottom: 1.5rem;
        }

        .hero-kicker {
            display: inline-block;
            font-size: 0.74rem;
            font-weight: 700;
            letter-spacing: 0.12em;
            text-transform: uppercase;
            color: var(--sunstone-gold-dark);
            margin-bottom: 0.5rem;
        }

        .hero-title {
            font-size: 2.25rem;
            line-height: 1.05;
            font-weight: 700;
            margin: 0 0 0.4rem 0;
        }

        .hero-subtitle {
            color: var(--sunstone-muted);
            font-size: 1rem;
            margin: 0;
            max-width: 820px;
        }

        .section-card {
            background: var(--sunstone-surface);
            border: 1px solid var(--sunstone-border);
            border-radius: var(--sunstone-radius);
            padding: 18px 18px 12px 18px;
            box-shadow: var(--sunstone-shadow);
            height: 100%;
        }

        .mini-card {
            background: rgba(255,255,255,0.78);
            border: 1px solid var(--sunstone-border);
            border-radius: 16px;
            padding: 16px;
            box-shadow: var(--sunstone-shadow);
            height: 100%;
        }

        .section-label {
            font-size: 0.78rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.12em;
            color: var(--sunstone-gold-dark);
            margin-bottom: 0.2rem;
        }

        .section-title {
            font-size: 1.2rem;
            font-weight: 700;
            color: var(--sunstone-text);
            margin-bottom: 0.95rem;
        }

        .status-pill {
            display: inline-block;
            padding: 0.34rem 0.7rem;
            border-radius: 999px;
            font-size: 0.8rem;
            font-weight: 700;
            margin-bottom: 0.65rem;
        }

        .status-success {
            background: rgba(201, 168, 106, 0.16);
            color: #7A5E2D;
            border: 1px solid rgba(201, 168, 106, 0.28);
        }

        .status-warn {
            background: rgba(201, 168, 106, 0.12);
            color: #8B6E3B;
            border: 1px solid rgba(201, 168, 106, 0.22);
        }

        .status-error {
            background: rgba(126, 95, 72, 0.10);
            color: #6E5543;
            border: 1px solid rgba(126, 95, 72, 0.18);
        }

        .result-box {
            background: #FCFBF8;
            border: 1px solid var(--sunstone-border);
            border-radius: 16px;
            padding: 14px;
            min-height: 116px;
        }

        .helper-text {
            color: var(--sunstone-muted);
            font-size: 0.92rem;
        }

        div[data-baseweb="select"] > div,
        div[data-baseweb="input"] > div,
        textarea,
        input {
            border-radius: 14px !important;
        }

        .stTextInput > div > div > input,
        .stTextArea textarea {
            background: #FFFFFF;
        }

        .stButton > button,
        .stDownloadButton > button {
            border-radius: 14px !important;
            border: 1px solid var(--sunstone-gold) !important;
            background: linear-gradient(180deg, #D8B678 0%, #C9A86A 100%) !important;
            color: #1F1A17 !important;
            font-weight: 700 !important;
            padding: 0.7rem 1rem !important;
            box-shadow: 0 6px 18px rgba(201, 168, 106, 0.24);
        }

        .stButton > button:hover,
        .stDownloadButton > button:hover {
            border-color: var(--sunstone-gold-dark) !important;
            background: linear-gradient(180deg, #DDBD85 0%, #C39D55 100%) !important;
            color: #1F1A17 !important;
        }

        .stLinkButton a {
            border-radius: 14px !important;
            border: 1px solid var(--sunstone-border) !important;
            background: #FFFFFF !important;
            color: var(--sunstone-text) !important;
            font-weight: 600 !important;
        }

        .stProgress > div > div > div > div {
            background-color: var(--sunstone-gold) !important;
        }

        [data-testid="stSidebar"] {
            background: #FBF9F5;
            border-right: 1px solid var(--sunstone-border);
        }

        [data-testid="stSidebar"] h2, 
        [data-testid="stSidebar"] h3 {
            color: var(--sunstone-text);
        }

        .stAlert {
            border-radius: 14px;
        }

        code {
            color: #6A532A !important;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

# =========================
# STATE
# =========================
if "committed_sig" not in st.session_state:
    st.session_state.committed_sig = None
if "committed_url" not in st.session_state:
    st.session_state.committed_url = ""

# =========================
# CONNECTION
# =========================
conn = st.connection("gsheets", type=GSheetsConnection)

# =========================
# HEADER
# =========================
st.markdown(
    """
    <br>
    <div class="hero-wrap">
        <div class="hero-kicker">Sunstone Marketing Tools</div>
        <div class="hero-title">UTM Builder</div>
    </div>
    """,
    unsafe_allow_html=True,
)

# =========================
# INPUT LAYOUT
# =========================



base_url = st.text_input(
    "Paste the page URL",
    placeholder="https://permanentjewelry.sunstonewelders.com/collections/...",
    label_visibility="visible",
)

if base_url and not is_valid_url(base_url):
    st.error("Base URL must start with http:// or https://")
else:
    st.caption("Existing query parameters will be ignored automatically.")

st.markdown("</div>", unsafe_allow_html=True)


sources = sorted(SOURCE_TO_MEDIUMS.keys())
source = st.selectbox("utm_source", options=[""] + sources, index=0)

allowed_mediums = SOURCE_TO_MEDIUMS.get(source, []) if source else []
medium = st.selectbox("utm_medium", options=[""] + allowed_mediums, index=0)

allowed_campaigns = MEDIUM_TO_CAMPAIGNS.get(medium, []) if medium else []
campaign = st.selectbox("utm_campaign", options=[""] + allowed_campaigns, index=0)

allowed_content = CAMPAIGN_TO_CONTENT.get(campaign, []) if campaign else []
content = st.selectbox("utm_content (optional)", options=[""] + allowed_content, index=0)

left, right = st.columns([9, 1])

with right:
    st.write("")  # spacer for alignment
    term_custom = st.checkbox("Custom utm_term")

with left:
    if term_custom:
        term_raw = st.text_input("utm_term (optional)", placeholder="example keyword phrase")
        term = format_term(term_raw)
        if term_raw and term:
            st.caption(f"Formatted utm_term: `{term}`")
    else:
        term = st.selectbox("utm_term (optional)", options=[""] + TERMS_GLOBAL, index=0)
st.markdown("</div>", unsafe_allow_html=True)

# =========================
# URL + STATUS PREP
# =========================
required_ok = bool(is_valid_url(base_url) and source and medium and campaign)
params = {}

if source:
    params["utm_source"] = source
if medium:
    params["utm_medium"] = medium
if campaign:
    params["utm_campaign"] = campaign
if content:
    params["utm_content"] = content
if term:
    params["utm_term"] = term

preview_url = build_url(base_url, params) if required_ok else ""
notes = ""


notes = st.text_input("Notes (required)", value="")
notes_ok = bool((notes or "").strip())

progress_wrap = st.empty()
progress_bar_wrap = st.empty()
action_feedback = st.empty()

missing = []
if not is_valid_url(base_url):
    missing.append("Base URL")
if not source:
    missing.append("Source")
if not medium:
    missing.append("Medium")
if not campaign:
    missing.append("Campaign")
if not (notes or "").strip():
    missing.append("Notes")

if missing:
    st.caption("Missing: " + ", ".join(missing))


commit = st.button(
    "Generate My URL",
    type="primary",
    use_container_width=True,
    disabled=not (required_ok and notes_ok),
)

if commit:
    try:
        progress_wrap.markdown("**Generating...**")
        progress = progress_bar_wrap.progress(0)

        payload = {
            "submitted_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "base_url": strip_query(base_url),
            "source": source,
            "medium": medium,
            "campaign": campaign,
            "content": content or "",
            "term": term or "",
            "final_url": preview_url,
            "notes": notes.strip(),
        }

        progress.progress(20)

        new_row = pd.DataFrame([payload])

        existing_df = conn.read(worksheet="Sheet1", ttl=0)

        progress.progress(50)

        if existing_df is None or existing_df.empty:
            updated_df = new_row
        else:
            updated_df = pd.concat([existing_df, new_row], ignore_index=True)

        progress.progress(75)

        conn.update(worksheet="Sheet1", data=updated_df)

        progress.progress(100)

        st.session_state.committed_sig = current_sig(
            base_url, source, medium, campaign, content, term, notes
        )
        st.session_state.committed_url = preview_url

    except Exception as e:
        st.error(f"Google Sheets write failed: {e}")

    finally:
        time.sleep(0.15)
        progress_wrap.empty()
        progress_bar_wrap.empty()

    action_feedback.success("URL generated.")
    time.sleep(0.15)
    progress_wrap.empty()
    progress_bar_wrap.empty()

st.markdown("</div>", unsafe_allow_html=True)

current_form_sig = current_sig(base_url, source, medium, campaign, content, term, notes)
show_result = (
    st.session_state.committed_url
    and st.session_state.committed_sig == current_form_sig
)



if show_result:
    st.code(st.session_state.committed_url, language="text")
    st.markdown("</div>", unsafe_allow_html=True)

    result_actions_left, result_actions_right = st.columns([1, 1], gap="small")
    with result_actions_left:
        st.link_button(
            "Open URL",
            st.session_state.committed_url,
            use_container_width=True,
        )
    with result_actions_right:
        st.download_button(
            "Download .txt",
            data=st.session_state.committed_url,
            file_name="utm_link.txt",
            mime="text/plain",
            use_container_width=True,
        )
st.markdown("</div>", unsafe_allow_html=True)