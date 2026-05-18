from __future__ import annotations

import re
import time
from datetime import datetime, timezone
from urllib.parse import urlencode, urlsplit, urlunsplit

import pandas as pd
import streamlit as st
from streamlit_gsheets import GSheetsConnection

APP_VERSION = "2.0.0"

BUSINESS_UNITS = {"Permanent Jewelry": "pj", "Industrial": "ind", "Dental": "dental", "PJX / Events": "pjx", "Corporate / General": "corp"}
DEPARTMENTS = ["marketing", "ecommerce", "sales", "customer_support", "events", "dealer_team", "leadership", "operations"]

SOURCE_TO_MEDIUMS = {
    "google": ["organic", "cpc", "paid_search", "shopping", "display", "video", "remarketing"],
    "google_ads": ["cpc", "paid_search", "shopping", "display", "video", "remarketing"],
    "google_pmax": ["paid_search", "shopping", "display", "video", "remarketing"],
    "microsoft_ads": ["cpc", "paid_search", "shopping", "remarketing"],
    "bing": ["organic", "cpc", "paid_search"],
    "meta": ["paid_social", "organic_social", "video", "remarketing", "referral"],
    "facebook": ["paid_social", "organic_social", "video", "remarketing", "referral"],
    "instagram": ["paid_social", "organic_social", "video", "shopping", "referral"],
    "tiktok": ["paid_social", "organic_social", "video", "shopping", "referral"],
    "tiktok_shop": ["shopping", "paid_marketplace", "affiliate", "referral"],
    "pinterest": ["paid_social", "organic_social", "shopping", "referral"],
    "linkedin": ["paid_social", "organic_social", "sales_outreach", "content", "referral"],
    "youtube": ["video", "paid_social", "organic_social", "content", "remarketing"],
    "hubspot": ["email", "sms", "workflow", "sales_outreach", "internal"],
    "shopify_email": ["email", "workflow"],
    "salesforce": ["sales_outreach", "internal", "email"],
    "microsoft_teams": ["internal", "sales_outreach", "support"],
    "outlook": ["email", "sales_outreach", "support"],
    "email_signature": ["email", "sales_outreach", "support"],
    "customer_support": ["support", "email", "internal"],
    "sales_team": ["sales_outreach", "email", "internal"],
    "amazon": ["shopping", "paid_marketplace", "cpc", "referral", "remarketing"],
    "amazon_ads": ["paid_marketplace", "cpc", "shopping", "remarketing"],
    "etsy": ["shopping", "paid_marketplace", "referral", "content"],
    "shopify": ["internal", "referral", "content"],
    "pjx": ["event", "qr", "email", "sales_outreach", "referral"],
    "regfox": ["event", "email", "referral"],
    "trade_show": ["event", "qr", "print", "sales_outreach"],
    "qr_code": ["qr", "print", "event", "direct_mail"],
    "direct_mail": ["direct_mail", "qr"],
    "dealer": ["partner", "referral", "sales_outreach"],
    "partner": ["partner", "referral", "affiliate"],
    "influencer": ["influencer", "affiliate", "organic_social", "paid_social"],
    "chatgpt": ["agentic", "referral", "content"],
    "perplexity": ["agentic", "referral", "content"],
    "gemini": ["agentic", "referral", "content"],
    "copilot": ["agentic", "referral", "internal"],
}

OBJECTIVES = ["brand_awareness", "prospecting", "retargeting", "product_launch", "starter_kits", "chain_connectors", "marketplace_push", "promo", "lead_gen", "lead_nurture", "event_registration", "sales_enablement", "dealer_recruitment", "support_resource", "user_manual", "data_sheet", "troubleshooting", "post_purchase", "seo_content", "education", "how_to", "comparison", "answer_engine", "agentic_visibility", "community", "ugc", "internal", "training", "reporting"]
CONTENT_OPTIONS = ["hero", "primary_cta", "secondary_cta", "text_link", "button", "image", "video", "short_video", "carousel", "static_ad", "product_card", "collection_tile", "landing_page_form", "register_button", "qr_code", "sales_signature", "proposal_link", "quote_link", "support_article", "manual_link", "data_sheet", "setup_guide", "faq", "comparison", "offer", "discount", "free_shipping", "variant_a", "variant_b", "internal_link"]
TERM_PRESETS = ["permanent+jewelry", "permanent+jewelry+kit", "permanent+jewelry+welder", "permanent+jewelry+training", "zapp+plus+2", "zp2", "pj+pro", "starter+kit", "chain+by+the+inch", "jump+rings", "charms", "connectors", "mobile+artist", "studio+artist", "new+artist", "experienced+artist", "pjx", "event+registration", "dealer+application", "support+resource", "user+manual", "data+sheet", "amazon", "etsy", "tiktok+shop", "answer+engine", "agentic+search"]
LOG_COLUMNS = ["submitted_at_utc", "app_version", "business_unit", "department", "base_url", "source", "medium", "campaign_objective", "campaign_name_raw", "campaign", "content", "term", "final_url", "notes"]


def slugify(value: str, separator: str = "-") -> str:
    value = (value or "").strip().lower().replace("&", " and ")
    return re.sub(r"[^a-z0-9]+", separator, value).strip(separator)


def clean_url(url: str) -> str:
    parts = urlsplit((url or "").strip())
    return urlunsplit((parts.scheme, parts.netloc, parts.path, "", ""))


def is_valid_url(url: str) -> bool:
    return bool(re.match(r"^https?://", (url or "").strip(), re.I))


def build_url(base_url: str, params: dict[str, str]) -> str:
    return clean_url(base_url) + "?" + urlencode({k: v for k, v in params.items() if v}, safe="+_-")


def build_campaign(date_value, unit_label: str, objective: str, campaign_name: str) -> str:
    return f"{date_value.strftime('%Y%m%d')}_{BUSINESS_UNITS.get(unit_label, 'corp')}_{objective}_{slugify(campaign_name)}"


def log_to_sheet(row: dict[str, str]) -> tuple[bool, str]:
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        existing = conn.read(worksheet="Sheet1", ttl=0)
        new_row = pd.DataFrame([row], columns=LOG_COLUMNS)
        if existing is None or existing.empty:
            updated = new_row
        else:
            for column in LOG_COLUMNS:
                if column not in existing.columns:
                    existing[column] = ""
            updated = pd.concat([existing[LOG_COLUMNS], new_row], ignore_index=True)
        conn.update(worksheet="Sheet1", data=updated)
        return True, "Logged to Google Sheets."
    except Exception as exc:
        return False, f"URL generated, but Google Sheets logging failed: {exc}"


st.set_page_config(page_title="Sunstone UTM Builder", page_icon="🔗", layout="wide")
st.markdown("""
<style>
:root{--bg:#F8F4F1;--surface:#fff;--soft:#F3EAF1;--text:#211B20;--muted:#6F646C;--border:#E8DCE4;--accent:#6F4A73;--accent-dark:#4B304F;--shadow:0 14px 32px rgba(33,27,32,.08)}
html,body,.stApp{background:radial-gradient(circle at top left,#fff 0%,var(--bg) 42%,#F5EDF2 100%)!important;color:var(--text)!important}.block-container{max-width:1240px;padding-top:2rem;padding-bottom:2.5rem}h1,h2,h3,label,.stMarkdown,.stCaption{color:var(--text)!important}
.pj-hero{background:linear-gradient(135deg,#fff 0%,var(--soft) 100%);border:1px solid var(--border);border-radius:28px;padding:30px;margin-bottom:1.2rem;box-shadow:var(--shadow)}.pj-kicker{color:var(--accent);font-size:.75rem;font-weight:800;letter-spacing:.13em;text-transform:uppercase}.pj-title{font-size:clamp(2rem,4vw,3.1rem);line-height:1;font-weight:850;margin:.35rem 0 .7rem}.pj-subtitle{color:var(--muted);max-width:860px;font-size:1.03rem}.section-card{background:rgba(255,255,255,.9);border:1px solid var(--border);border-radius:20px;padding:18px;box-shadow:var(--shadow);margin-bottom:1rem}.section-label{font-size:.76rem;font-weight:800;letter-spacing:.12em;text-transform:uppercase;color:var(--accent);margin-bottom:.4rem}
div[data-baseweb="select"]>div,div[data-baseweb="input"]>div,textarea,input{border-radius:14px!important}.stButton>button,.stDownloadButton>button{border-radius:14px!important;border:1px solid var(--accent)!important;background:linear-gradient(180deg,#7F5684 0%,#6F4A73 100%)!important;color:#fff!important;font-weight:800!important;padding:.72rem 1rem!important;box-shadow:0 8px 20px rgba(111,74,115,.22)!important}.stLinkButton a{border-radius:14px!important;border:1px solid var(--border)!important;background:#fff!important;color:var(--text)!important;font-weight:700!important}[data-testid="stSidebar"]{background:#FBF8FA!important;border-right:1px solid var(--border)}.stAlert{border-radius:14px}code{color:var(--accent-dark)!important}
</style>
""", unsafe_allow_html=True)

for key, default in {"committed_sig": None, "committed_url": ""}.items():
    if key not in st.session_state:
        st.session_state[key] = default

with st.sidebar:
    st.subheader("UTM standard")
    st.markdown("""
**Campaign format:** `yyyymmdd_unit_objective_campaign-name`

Examples:
- `20260518_pj_product_launch_zp2-luxe`
- `20260518_pjx_event_registration_early-access`
- `20260518_ind_support_resource_laser-data-sheet`

Rules: lowercase only, underscores between tracking parts, hyphens inside names, plus signs inside keyword terms.
""")
    st.caption(f"App version {APP_VERSION}")

st.markdown("""
<div class="pj-hero">
  <div class="pj-kicker">Sunstone internal tool</div>
  <div class="pj-title">UTM Builder</div>
  <div class="pj-subtitle">Create standardized tracking links for marketing, ecommerce, sales, customer support, marketplaces, events, and internal sharing.</div>
</div>
""", unsafe_allow_html=True)

with st.expander("View field guidance"):
    st.markdown("**utm_source** is where the click starts. **utm_medium** is the channel type. **utm_campaign** is generated from date, business unit, objective, and campaign name. **utm_content** identifies the asset or placement. **utm_term** is optional for keywords, audiences, or meaningful grouping.")

left, right = st.columns([1.15, .85], gap="large")

with left:
    st.markdown('<div class="section-card"><div class="section-label">Destination and campaign</div>', unsafe_allow_html=True)
    base_url = st.text_input("Paste the destination URL", placeholder="https://permanentjewelry.sunstonewelders.com/collections/...")
    if base_url and not is_valid_url(base_url):
        st.error("Base URL must start with http:// or https://")
    elif base_url:
        st.caption("Existing query parameters will be ignored automatically.")
    business_unit_label = st.selectbox("Business unit", list(BUSINESS_UNITS.keys()))
    department = st.selectbox("Department", DEPARTMENTS)
    campaign_date = st.date_input("Campaign date", value=datetime.now().date())
    objective = st.selectbox("Campaign objective", OBJECTIVES, index=OBJECTIVES.index("product_launch"))
    campaign_name_raw = st.text_input("Campaign name", placeholder="zp2 luxe launch, pjx early access, support manual download")
    manual_campaign = st.checkbox("Advanced: manually override utm_campaign")
    if manual_campaign:
        campaign = slugify(st.text_input("Manual utm_campaign", placeholder="20260518_pj_product_launch_zp2-luxe"), "_")
    elif campaign_name_raw:
        campaign = build_campaign(campaign_date, business_unit_label, objective, campaign_name_raw)
        st.caption(f"Generated utm_campaign: `{campaign}`")
    else:
        campaign = ""
    st.markdown("</div>", unsafe_allow_html=True)

with right:
    st.markdown('<div class="section-card"><div class="section-label">Tracking fields</div>', unsafe_allow_html=True)
    source = st.selectbox("utm_source", [""] + sorted(SOURCE_TO_MEDIUMS.keys()))
    medium = st.selectbox("utm_medium", [""] + (SOURCE_TO_MEDIUMS.get(source, []) if source else []))
    content = st.selectbox("utm_content", [""] + CONTENT_OPTIONS)
    if st.checkbox("Use custom utm_content"):
        content = slugify(st.text_input("Custom utm_content", placeholder="hero cta, sales deck link, variant a"), "_")
    if st.checkbox("Use custom utm_term"):
        term = slugify(st.text_input("Custom utm_term", placeholder="keyword phrase or audience segment"), "+")
        if term:
            st.caption(f"Formatted utm_term: `{term}`")
    else:
        term = st.selectbox("utm_term", [""] + TERM_PRESETS)
    st.markdown("</div>", unsafe_allow_html=True)

notes = st.text_input("Notes (required)", placeholder="What is this link for, who is using it, or where will it be placed?")
params = {"utm_source": source, "utm_medium": medium, "utm_campaign": campaign, "utm_content": content, "utm_term": term}
preview_url = build_url(base_url, params) if is_valid_url(base_url) and source and medium and campaign else ""

missing = []
if not is_valid_url(base_url): missing.append("Base URL")
if not source: missing.append("Source")
if not medium: missing.append("Medium")
if not campaign: missing.append("Campaign")
if not notes.strip(): missing.append("Notes")

if missing:
    st.caption("Missing: " + ", ".join(missing))
if preview_url:
    st.markdown("**Preview**")
    st.code(preview_url, language="text")

current_sig = (clean_url(base_url), source, medium, campaign, content or "", term or "", notes.strip())

if st.button("Generate and log URL", type="primary", use_container_width=True, disabled=bool(missing)):
    progress = st.progress(0)
    payload = {
        "submitted_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "app_version": APP_VERSION,
        "business_unit": BUSINESS_UNITS.get(business_unit_label, "corp"),
        "department": department,
        "base_url": clean_url(base_url),
        "source": source,
        "medium": medium,
        "campaign_objective": objective,
        "campaign_name_raw": campaign_name_raw.strip(),
        "campaign": campaign,
        "content": content or "",
        "term": term or "",
        "final_url": preview_url,
        "notes": notes.strip(),
    }
    progress.progress(45)
    logged, message = log_to_sheet(payload)
    progress.progress(100)
    time.sleep(.15)
    progress.empty()
    st.session_state.committed_sig = current_sig
    st.session_state.committed_url = preview_url
    st.success("URL generated and logged.") if logged else st.warning(message)

if st.session_state.committed_url and st.session_state.committed_sig == current_sig:
    st.markdown("### Final URL")
    st.code(st.session_state.committed_url, language="text")
    left_action, right_action = st.columns(2)
    with left_action:
        st.link_button("Open URL", st.session_state.committed_url, use_container_width=True)
    with right_action:
        st.download_button("Download .txt", st.session_state.committed_url, file_name="utm_link.txt", mime="text/plain", use_container_width=True)
