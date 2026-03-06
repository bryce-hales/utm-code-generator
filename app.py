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

conn = st.connection("gsheets", type=GSheetsConnection)

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


def current_sig(base_url, source, medium, campaign, content, term):
    return (
        strip_query(base_url),
        source,
        medium,
        campaign,
        content or "",
        term or "",
    )


st.set_page_config(
    page_title="UTM Builder",
    page_icon="🔗",
    layout="wide",
    initial_sidebar_state="collapsed",
)

if "generated_sig" not in st.session_state:
    st.session_state.generated_sig = None
if "generated_url" not in st.session_state:
    st.session_state.generated_url = ""
if "has_generated" not in st.session_state:
    st.session_state.has_generated = False

st.markdown(
    """
    <style>
    .stApp {
        background:
            radial-gradient(circle at top left, rgba(124, 58, 237, 0.20), transparent 30%),
            radial-gradient(circle at top right, rgba(59, 130, 246, 0.18), transparent 28%),
            linear-gradient(180deg, #0b1020 0%, #111827 42%, #0f172a 100%);
        color: #e5e7eb;
    }

    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        max-width: 1240px;
    }

    h1, h2, h3, h4, h5, h6, p, label, div {
        font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    }

    .hero-wrap {
        padding: 1.8rem 1.8rem 1.4rem 1.8rem;
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 24px;
        background: linear-gradient(135deg, rgba(17,24,39,0.82), rgba(30,41,59,0.70));
        backdrop-filter: blur(10px);
        box-shadow: 0 24px 80px rgba(0,0,0,0.28);
        margin-bottom: 1.25rem;
    }

    .hero-kicker {
        display: inline-block;
        padding: 0.4rem 0.75rem;
        border-radius: 999px;
        background: rgba(99, 102, 241, 0.14);
        color: #c7d2fe;
        font-size: 0.82rem;
        font-weight: 700;
        letter-spacing: 0.02em;
        margin-bottom: 0.9rem;
    }

    .hero-title {
        font-size: 2.25rem;
        font-weight: 800;
        line-height: 1.05;
        margin: 0 0 0.65rem 0;
        color: #f8fafc;
    }

    .hero-sub {
        color: #cbd5e1;
        font-size: 1.02rem;
        line-height: 1.65;
        margin-bottom: 0;
        max-width: 820px;
    }

    .metric-row {
        display: grid;
        grid-template-columns: repeat(3, minmax(0, 1fr));
        gap: 1rem;
        margin: 1rem 0 1.35rem 0;
    }

    .metric-card {
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 20px;
        background: rgba(255,255,255,0.04);
        padding: 1rem 1rem 0.9rem 1rem;
    }

    .metric-label {
        font-size: 0.82rem;
        color: #94a3b8;
        margin-bottom: 0.3rem;
    }

    .metric-value {
        font-size: 1.15rem;
        font-weight: 700;
        color: #f8fafc;
    }

    div[data-testid="stVerticalBlock"] div:has(> div > .builder-card) {
        margin-bottom: 0;
    }

    .builder-card {
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 24px;
        background: linear-gradient(180deg, rgba(17,24,39,0.85), rgba(15,23,42,0.75));
        padding: 1.2rem 1.2rem 1rem 1.2rem;
        box-shadow: 0 18px 50px rgba(0,0,0,0.22);
    }

    .section-title {
        font-size: 1.08rem;
        font-weight: 800;
        color: #f8fafc;
        margin-bottom: 0.25rem;
    }

    .section-sub {
        font-size: 0.92rem;
        color: #94a3b8;
        margin-bottom: 0.95rem;
    }

    div[data-baseweb="select"] > div,
    div[data-baseweb="input"] > div,
    .stTextInput > div > div,
    .stSelectbox > div > div,
    .stTextArea > div > div {
        border-radius: 14px !important;
    }

    .stTextInput input,
    .stSelectbox div[data-baseweb="select"] input {
        color: #f8fafc !important;
    }

    .stTextInput label,
    .stSelectbox label,
    .stRadio label {
        color: #e2e8f0 !important;
        font-weight: 600 !important;
    }

    .stRadio [role="radiogroup"] {
        gap: 0.5rem;
    }

    .stButton > button {
        border-radius: 16px !important;
        padding: 0.82rem 1.15rem !important;
        font-weight: 800 !important;
        font-size: 0.98rem !important;
        border: 1px solid rgba(255,255,255,0.08) !important;
        background: linear-gradient(135deg, #8b5cf6, #3b82f6) !important;
        color: white !important;
        box-shadow: 0 14px 30px rgba(59,130,246,0.26);
    }

    .stDownloadButton > button,
    .stLinkButton a {
        border-radius: 14px !important;
    }

    .result-shell {
        border: 1px solid rgba(255,255,255,0.09);
        border-radius: 24px;
        padding: 1.2rem;
        background: linear-gradient(180deg, rgba(15,23,42,0.82), rgba(17,24,39,0.72));
        box-shadow: 0 18px 50px rgba(0,0,0,0.20);
    }

    .url-box {
        background: #020617;
        border: 1px solid rgba(148,163,184,0.22);
        color: #e2e8f0;
        padding: 1rem;
        border-radius: 16px;
        font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
        font-size: 0.92rem;
        overflow-wrap: anywhere;
        margin-top: 0.8rem;
        margin-bottom: 0.6rem;
    }

    .status-pill {
        display: inline-block;
        padding: 0.35rem 0.65rem;
        border-radius: 999px;
        font-size: 0.8rem;
        font-weight: 700;
        margin-bottom: 0.8rem;
    }

    .status-ready {
        background: rgba(34,197,94,0.12);
        color: #86efac;
    }

    .status-waiting {
        background: rgba(250,204,21,0.12);
        color: #fde68a;
    }

    .status-missing {
        background: rgba(248,113,113,0.12);
        color: #fca5a5;
    }

    .footer-note {
        color: #94a3b8;
        font-size: 0.9rem;
        margin-top: 1rem;
    }

    @media (max-width: 900px) {
        .metric-row {
            grid-template-columns: 1fr;
        }

        .hero-title {
            font-size: 1.8rem;
        }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="hero-wrap">
        <div class="hero-kicker">Marketing Utility</div>
        <div class="hero-title">Build polished UTM links in seconds</div>
        <p class="hero-sub">
            Create clean, structured campaign URLs with a much nicer workflow. Pick your source, medium,
            campaign, optional content, and term, then generate a ready-to-use final link.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

with st.sidebar:
    st.markdown("### Preferences")
    term_default_mode = st.radio(
        "utm_term mode",
        options=["Dropdown", "Custom"],
        horizontal=True,
        index=0,
    )
    st.caption("Source → Medium → Campaign → Content is hard-locked to keep your naming clean.")

sources = sorted(SOURCE_TO_MEDIUMS.keys())

top_a, top_b, top_c = st.columns(3, gap="large")
with top_a:
    st.markdown(
        """
        <div class="metric-card">
            <div class="metric-label">Validation</div>
            <div class="metric-value">Smart field gating</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
with top_b:
    st.markdown(
        """
        <div class="metric-card">
            <div class="metric-label">Formatting</div>
            <div class="metric-value">Clean query handling</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
with top_c:
    st.markdown(
        """
        <div class="metric-card">
            <div class="metric-label">Result</div>
            <div class="metric-value">One-click final URL</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

left, right = st.columns([1.05, 0.95], gap="large")

with left:
    st.markdown(
        """
        <div class="builder-card">
            <div class="section-title">Base page</div>
            <div class="section-sub">Paste the destination page. Existing query parameters will be ignored.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    base_url = st.text_input(
        "Destination URL",
        placeholder="https://permanentjewelry.sunstonewelders.com/collections/...",
        label_visibility="visible",
    )

    if base_url and not is_valid_url(base_url):
        st.error("Please enter a valid URL that starts with http:// or https://")

    st.markdown("<div style='height: 0.75rem;'></div>", unsafe_allow_html=True)

    st.markdown(
        """
        <div class="builder-card">
            <div class="section-title">Campaign inputs</div>
            <div class="section-sub">Each selection unlocks the next one so your naming stays consistent.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    source = st.selectbox("utm_source", options=[""] + sources, index=0)

    allowed_mediums = SOURCE_TO_MEDIUMS.get(source, []) if source else []
    medium = st.selectbox("utm_medium", options=[""] + allowed_mediums, index=0)

    allowed_campaigns = MEDIUM_TO_CAMPAIGNS.get(medium, []) if medium else []
    campaign = st.selectbox("utm_campaign", options=[""] + allowed_campaigns, index=0)

    allowed_content = CAMPAIGN_TO_CONTENT.get(campaign, []) if campaign else []
    content = st.selectbox("utm_content", options=[""] + allowed_content, index=0)

    if term_default_mode == "Custom":
        term_raw = st.text_input("utm_term", placeholder="example keyword phrase")
        term = format_term(term_raw)
        if term_raw and term:
            st.caption(f"Formatted utm_term: `{term}`")
    else:
        term = st.selectbox("utm_term", options=[""] + TERMS_GLOBAL, index=0)

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
current_form_sig = current_sig(base_url, source, medium, campaign, content, term)

with right:
    st.markdown(
        """
        <div class="result-shell">
            <div class="section-title">Preview & result</div>
            <div class="section-sub">Review your generated output and launch it when ready.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    missing = []
    if not is_valid_url(base_url):
        missing.append("Base URL")
    if not source:
        missing.append("Source")
    if not medium:
        missing.append("Medium")
    if not campaign:
        missing.append("Campaign")

    if missing:
        st.markdown('<div class="status-pill status-missing">Incomplete</div>', unsafe_allow_html=True)
        st.caption("Missing required fields: " + ", ".join(missing))
    elif required_ok:
        st.markdown('<div class="status-pill status-ready">Ready to generate</div>', unsafe_allow_html=True)
        st.caption("Your URL structure is valid and ready.")
    else:
        st.markdown('<div class="status-pill status-waiting">Waiting</div>', unsafe_allow_html=True)

    st.markdown("#### Live preview")
    if preview_url:
        st.markdown(f'<div class="url-box">{preview_url}</div>', unsafe_allow_html=True)
    else:
        st.info("Your final URL preview will appear here once the required fields are complete.")

    generate = st.button(
        "Generate my URL",
        type="primary",
        disabled=not required_ok,
        use_container_width=True,
    )

    progress_placeholder = st.empty()
    progress_text_placeholder = st.empty()

    if generate:
        progress_text_placeholder.markdown("**Generating...**")
        progress = progress_placeholder.progress(0)

        for i in range(0, 101, 5):
            time.sleep(0.02)
            progress.progress(i)

        payload = {
            "timestamp_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "base_url": strip_query(base_url),
            "source": source,
            "medium": medium,
            "campaign": campaign,
            "content": content or "",
            "term": term or "",
            "final_url": preview_url,
        }

        new_row = pd.DataFrame([payload])
        existing_df = conn.read(worksheet="Sheet1")

        if existing_df is None or existing_df.empty:
            updated_df = new_row
        else:
            updated_df = pd.concat([existing_df, new_row], ignore_index=True)

        conn.update(
            worksheet="Sheet1",
            data=updated_df
        )

        st.session_state.generated_sig = current_form_sig
        st.session_state.generated_url = preview_url
        st.session_state.has_generated = True

        progress_text_placeholder.empty()
        progress_placeholder.empty()

        st.success("URL generated and uploaded successfully.")
        
show_result = (
    st.session_state.has_generated
    and st.session_state.generated_url
    and st.session_state.generated_sig == current_form_sig
)

st.markdown("<div style='height: 0.5rem;'></div>", unsafe_allow_html=True)

bottom_left, bottom_right = st.columns([0.9, 1.1], gap="large")

with bottom_left:
    st.markdown(
        """
        <div class="builder-card">
            <div class="section-title">Summary</div>
            <div class="section-sub">Quick snapshot of what is currently selected.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.write(f"**Source:** {source or '—'}")
    st.write(f"**Medium:** {medium or '—'}")
    st.write(f"**Campaign:** {campaign or '—'}")
    st.write(f"**Content:** {content or '—'}")
    st.write(f"**Term:** {term or '—'}")

with bottom_right:
    st.markdown(
        """
        <div class="result-shell">
            <div class="section-title">Final result</div>
            <div class="section-sub">Use this once you have generated the finished URL.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if show_result:
        st.markdown(f'<div class="url-box">{st.session_state.generated_url}</div>', unsafe_allow_html=True)
        st.link_button("Open final URL", st.session_state.generated_url, use_container_width=True)
        st.download_button(
            "Download URL as .txt",
            data=st.session_state.generated_url,
            file_name="utm_link.txt",
            mime="text/plain",
            use_container_width=True,
        )
    else:
        st.info("Complete the required inputs, then click Generate my URL.")

st.markdown(
    """
    <div class="footer-note">
        Built for cleaner campaign tracking and a much better user experience.
    </div>
    """,
    unsafe_allow_html=True,
)