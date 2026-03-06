# app.py
from __future__ import annotations
import re
from urllib.parse import urlsplit, urlunsplit, urlencode
from datetime import datetime, timezone

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


st.set_page_config(page_title="UTM Builder", page_icon="🔗", layout="wide")
st.title("🔗 UTM Builder (Streamlit)")

if "committed_sig" not in st.session_state:
    st.session_state.committed_sig = None
if "committed_url" not in st.session_state:
    st.session_state.committed_url = ""

with st.sidebar:
    st.header("Settings")
    st.caption("Hard-block: Source → Medium → Campaign → Content. Terms are global.")
    notes_default = st.text_input("Default notes", value="")

col1, col2 = st.columns([1, 1], gap="large")

with col1:
    st.subheader("1) Base URL")
    base_url = st.text_input(
        "Paste the page URL (app will ignore existing query params)",
        placeholder="https://permanentjewelry.sunstonewelders.com/collections/...",
    )
    if base_url and not is_valid_url(base_url):
        st.error("Base URL must start with http:// or https://")

with col2:
    st.subheader("2) UTM Inputs")

    sources = sorted(SOURCE_TO_MEDIUMS.keys())
    source = st.selectbox("utm_source", options=[""] + sources, index=0)

    allowed_mediums = SOURCE_TO_MEDIUMS.get(source, []) if source else []
    medium = st.selectbox("utm_medium", options=[""] + allowed_mediums, index=0)

    allowed_campaigns = MEDIUM_TO_CAMPAIGNS.get(medium, []) if medium else []
    campaign = st.selectbox("utm_campaign", options=[""] + allowed_campaigns, index=0)

    allowed_content = CAMPAIGN_TO_CONTENT.get(campaign, []) if campaign else []
    content = st.selectbox("utm_content (optional)", options=[""] + allowed_content, index=0)

    term_mode = st.radio(
        "utm_term input type",
        options=["Dropdown", "Custom"],
        horizontal=True,
        index=0,
    )

    if term_mode == "Custom":
        term_raw = st.text_input("utm_term (optional)", placeholder="example keyword phrase")
        term = format_term(term_raw)
        if term_raw and term:
            st.caption(f"Formatted utm_term: `{term}`")
    else:
        term = st.selectbox("utm_term (optional)", options=[""] + TERMS_GLOBAL, index=0)

st.divider()

notes = ""
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

c1, c2, c3 = st.columns([1, 2, 1], gap="large")

with c3:
    st.subheader("Append to Google Sheet")
    notes = st.text_input("Notes (required)", value=notes_default)
    notes_ok = bool((notes or "").strip())

    commit = st.button(
        "✅ Commit",
        type="primary",
        disabled=not (required_ok and notes_ok),
    )

    if commit:
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

        new_row = pd.DataFrame([payload])
        existing_df = conn.read(worksheet="Sheet1")

        if existing_df is None or existing_df.empty:
            updated_df = new_row
        else:
            updated_df = pd.concat([existing_df, new_row], ignore_index=True)

        conn.update(worksheet="Sheet1", data=updated_df)

        st.session_state.committed_sig = current_sig(
            base_url, source, medium, campaign, content, term, notes
        )
        st.session_state.committed_url = preview_url

        st.success("Appended to Google Sheet ✅")

current_form_sig = current_sig(base_url, source, medium, campaign, content, term, notes)
show_result = (
    st.session_state.committed_url
    and st.session_state.committed_sig == current_form_sig
)

with c1:
    st.subheader("Status")
    if show_result:
        st.write("✅ Committed")
        st.caption("Result is locked to the latest commit.")
    else:
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
            st.write("❌ Incomplete")
            st.caption("Required: " + ", ".join(missing))
        else:
            st.write("🟡 Ready to commit")
            st.caption("Click Commit to generate and save the result.")

with c2:
    st.subheader("Final URL")
    if show_result:
        st.code(st.session_state.committed_url, language="text")
        st.link_button("Open link", st.session_state.committed_url)
        st.download_button(
            "Download as .txt",
            data=st.session_state.committed_url,
            file_name="utm_link.txt",
            mime="text/plain",
        )
    else:
        st.info("Complete the required fields and click Commit to generate the final URL.")