from __future__ import annotations

import re
import time
from datetime import datetime, timezone
from urllib.parse import urlencode, urlsplit, urlunsplit

import pandas as pd
import streamlit as st
from streamlit_gsheets import GSheetsConnection

APP_VERSION = "2.1.3"

BUSINESS_UNITS = {
    "Permanent Jewelry": "pj",
    "Industrial": "ind",
    "Dental": "dental",
    "PJX / Events": "pjx",
    "Corporate / General": "corp",
}

BUSINESS_UNIT_LABELS = {
    "Permanent Jewelry": "Permanent Jewelry - PJ products, chains, kits, training",
    "Industrial": "Industrial - welders, lasers, technical resources",
    "Dental": "Dental - dental welding products and resources",
    "PJX / Events": "PJX / Events - expo, registration, QR codes",
    "Corporate / General": "Corporate / General - internal or company-wide links",
}

DEPARTMENTS = ["marketing", "ecommerce", "sales", "customer_support", "events", "dealer_team", "operations", "leadership", "training", "product"]
DEPARTMENT_LABELS = {
    "marketing": "Marketing - campaigns, ads, email, social",
    "ecommerce": "Ecommerce - site, product pages, marketplaces",
    "sales": "Sales - quotes, follow-ups, outreach",
    "customer_support": "Customer Support - help docs, manuals, replies",
    "events": "Events - PJX, trade shows, QR codes",
    "dealer_team": "Dealer Team - partner/dealer outreach",
    "operations": "Operations - internal resources",
    "leadership": "Leadership - internal/company-wide sharing",
    "training": "Training - classes, onboarding, education",
    "product": "Product - product resources or launch support",
}

SOURCE_TO_MEDIUMS = {
    "google": ["organic", "cpc", "paid_search", "shopping", "display", "video", "remarketing"],
    "google_ads": ["cpc", "paid_search", "shopping", "display", "video", "remarketing"],
    "google_pmax": ["paid_search", "shopping", "display", "video", "remarketing"],
    "google_shopping": ["shopping", "cpc", "paid_search"],
    "google_search_console": ["organic", "seo"],
    "microsoft_ads": ["cpc", "paid_search", "shopping", "remarketing"],
    "bing": ["organic", "cpc", "paid_search"],
    "yahoo": ["organic", "cpc", "paid_search"],
    "duckduckgo": ["organic", "cpc", "paid_search"],
    "meta": ["paid_social", "organic_social", "video", "remarketing", "referral"],
    "facebook": ["paid_social", "organic_social", "video", "remarketing", "referral"],
    "instagram": ["paid_social", "organic_social", "video", "shopping", "referral"],
    "tiktok": ["paid_social", "organic_social", "video", "shopping", "referral"],
    "tiktok_shop": ["shopping", "paid_marketplace", "affiliate", "referral"],
    "pinterest": ["paid_social", "organic_social", "shopping", "referral"],
    "linkedin": ["paid_social", "organic_social", "sales_outreach", "content", "referral"],
    "youtube": ["video", "paid_social", "organic_social", "content", "remarketing"],
    "reddit": ["paid_social", "organic_social", "community", "referral"],
    "hubspot": ["email", "sms", "workflow", "sales_outreach", "internal"],
    "shopify_email": ["email", "workflow"],
    "klaviyo": ["email", "sms", "workflow"],
    "salesforce": ["sales_outreach", "internal", "email"],
    "microsoft_teams": ["internal", "sales_outreach", "support"],
    "outlook": ["email", "sales_outreach", "support"],
    "email_signature": ["email", "sales_outreach", "support"],
    "customer_support": ["support", "email", "internal"],
    "sales_team": ["sales_outreach", "email", "internal"],
    "amazon": ["shopping", "paid_marketplace", "cpc", "referral", "remarketing"],
    "amazon_ads": ["paid_marketplace", "cpc", "shopping", "remarketing"],
    "etsy": ["shopping", "paid_marketplace", "referral", "content"],
    "walmart": ["shopping", "paid_marketplace", "cpc", "referral"],
    "ebay": ["shopping", "paid_marketplace", "referral"],
    "shopify": ["internal", "referral", "content"],
    "website": ["internal", "referral", "content"],
    "blog": ["content", "organic", "referral"],
    "pjx": ["event", "qr", "email", "sales_outreach", "referral"],
    "regfox": ["event", "email", "referral"],
    "trade_show": ["event", "qr", "print", "sales_outreach"],
    "qr_code": ["qr", "print", "event", "direct_mail"],
    "print": ["print", "qr", "direct_mail"],
    "direct_mail": ["direct_mail", "qr"],
    "packaging_insert": ["print", "qr", "post_purchase"],
    "dealer": ["partner", "referral", "sales_outreach"],
    "distributor": ["partner", "referral", "sales_outreach"],
    "partner": ["partner", "referral", "affiliate"],
    "affiliate": ["affiliate", "referral", "paid_social"],
    "influencer": ["influencer", "affiliate", "organic_social", "paid_social"],
    "chatgpt": ["agentic", "referral", "content"],
    "perplexity": ["agentic", "referral", "content"],
    "gemini": ["agentic", "referral", "content"],
    "copilot": ["agentic", "referral", "internal"],
    "manual_entry": ["internal", "direct", "support", "sales_outreach", "referral"],
}

SOURCE_LABELS = {key: key.replace("_", " ").title() for key in SOURCE_TO_MEDIUMS}
SOURCE_LABELS.update({
    "hubspot": "HubSpot - email, workflow, form, CRM",
    "sales_team": "Sales team - rep outreach or quote follow-up",
    "customer_support": "Customer support - help reply or ticket",
    "qr_code": "QR code - scan from print/event/package",
    "microsoft_teams": "Microsoft Teams - internal team sharing",
    "manual_entry": "Manual entry - use when none of the above fit",
})

ALL_MEDIUMS = sorted({medium for mediums in SOURCE_TO_MEDIUMS.values() for medium in mediums} | {"affiliate", "agentic", "audio", "community", "content", "cpc", "direct", "direct_mail", "display", "email", "event", "influencer", "internal", "organic", "organic_social", "paid_marketplace", "paid_search", "paid_social", "partner", "podcast", "post_purchase", "print", "qr", "referral", "remarketing", "sales_outreach", "seo", "shopping", "sms", "support", "video", "webinar", "workflow"})
MEDIUM_LABELS = {key: key.replace("_", " ").title() for key in ALL_MEDIUMS}
MEDIUM_LABELS.update({
    "email": "Email - campaign, reply, or newsletter",
    "support": "Support - customer help or ticket reply",
    "sales_outreach": "Sales outreach - rep email, quote, follow-up",
    "qr": "QR - scanned QR code",
    "paid_search": "Paid search - Google/Bing search ads",
    "paid_social": "Paid social - paid social ads",
    "agentic": "Agentic - AI/search assistant reference",
})

OBJECTIVES = ["other", "brand_awareness", "prospecting", "retargeting", "product_launch", "starter_kits", "chain_connectors", "marketplace_push", "promo", "lead_gen", "lead_nurture", "event_registration", "sales_enablement", "dealer_recruitment", "support_resource", "user_manual", "data_sheet", "troubleshooting", "post_purchase", "seo_content", "education", "how_to", "comparison", "answer_engine", "agentic_visibility", "community", "ugc", "internal", "training", "reporting"]
OBJECTIVE_LABELS = {key: key.replace("_", " ").title() for key in OBJECTIVES}
OBJECTIVE_LABELS.update({
    "other": "Other - use when the exact campaign/goal is unknown",
    "promo": "Promo - discount, sale, special offer",
    "sales_enablement": "Sales enablement - sales follow-up/resource",
    "support_resource": "Support resource - help article/resource",
    "event_registration": "Event registration - registration/sign-up link",
    "marketplace_push": "Marketplace push - Amazon/Etsy/TikTok Shop/etc.",
})

CONTENT_OPTIONS = ["primary_cta", "secondary_cta", "button", "text_link", "hero", "image", "video", "short_video", "carousel", "static_ad", "product_card", "collection_tile", "landing_page_form", "register_button", "qr_code", "sales_signature", "proposal_link", "quote_link", "support_article", "manual_link", "data_sheet", "setup_guide", "faq", "comparison", "offer", "discount", "free_shipping", "version_a", "version_b", "internal_link", "other"]
CONTENT_LABELS = {key: key.replace("_", " ").title() for key in CONTENT_OPTIONS}
CONTENT_LABELS.update({"": "No content tag - optional", "primary_cta": "Primary CTA - main button/link", "sales_signature": "Sales signature - rep email signature", "qr_code": "QR code - scanned QR placement", "other": "Other - placement is unknown or not listed"})

TERM_PRESETS = ["", "permanent+jewelry", "permanent+jewelry+kit", "permanent+jewelry+welder", "permanent+jewelry+training", "zapp+plus+2", "zp2", "pj+pro", "starter+kit", "chain+by+the+inch", "jump+rings", "charms", "connectors", "mobile+artist", "studio+artist", "new+artist", "experienced+artist", "pjx", "event+registration", "dealer+application", "support+resource", "user+manual", "data+sheet", "amazon", "etsy", "tiktok+shop", "answer+engine", "agentic+search", "other"]
TERM_LABELS = {"": "No term tag - optional", "other": "Other - segment/keyword unknown or not listed"}

LINK_TYPE_PRESETS = {
    "Marketing campaign": dict(unit="Permanent Jewelry", department="marketing", source="hubspot", medium="email", objective="promo", content="primary_cta"),
    "Paid ad": dict(unit="Permanent Jewelry", department="marketing", source="google_ads", medium="paid_search", objective="prospecting", content="static_ad"),
    "Social post": dict(unit="Permanent Jewelry", department="marketing", source="instagram", medium="organic_social", objective="community", content="image"),
    "Sales outreach": dict(unit="Permanent Jewelry", department="sales", source="sales_team", medium="sales_outreach", objective="other", content="sales_signature"),
    "Customer support": dict(unit="Permanent Jewelry", department="customer_support", source="customer_support", medium="support", objective="other", content="support_article"),
    "Event or QR code": dict(unit="PJX / Events", department="events", source="qr_code", medium="qr", objective="event_registration", content="qr_code"),
    "Marketplace": dict(unit="Permanent Jewelry", department="ecommerce", source="amazon", medium="shopping", objective="marketplace_push", content="product_card"),
    "Internal link": dict(unit="Corporate / General", department="operations", source="microsoft_teams", medium="internal", objective="other", content="internal_link"),
    "SEO / agentic reference": dict(unit="Permanent Jewelry", department="marketing", source="chatgpt", medium="agentic", objective="agentic_visibility", content="text_link"),
    "Other / not sure": dict(unit="Corporate / General", department="operations", source="manual_entry", medium="internal", objective="other", content="other"),
}
LINK_TYPE_LABELS = {
    "Marketing campaign": "Marketing campaign - email, launch, promo, nurture",
    "Paid ad": "Paid ad - Google, Meta, Microsoft, marketplace ads",
    "Social post": "Social post - unpaid post, story, reel, community share",
    "Sales outreach": "Sales outreach - quote, follow-up, rep email",
    "Customer support": "Customer support - ticket reply, manual, help resource",
    "Event or QR code": "Event or QR code - booth, flyer, registration, scan",
    "Marketplace": "Marketplace - Amazon, Etsy, Walmart, TikTok Shop",
    "Internal link": "Internal link - Teams, training, employee resource",
    "SEO / agentic reference": "SEO / agentic reference - search, AI answer, content refs",
    "Other / not sure": "Other / not sure - use when nothing else fits",
}
NON_MARKETING_DEPARTMENTS = {"sales", "customer_support", "dealer_team", "operations", "leadership", "training", "product"}

CREATOR_QUERY_KEYS = ["teams_user_email", "teams_login_hint", "teams_user_id", "teams_tenant_id", "teams_display_name"]
LOG_COLUMNS = ["submitted_at_utc", "app_version", "business_unit", "department", "link_type", "creator_email", "creator_name", "creator_teams_user_id", "creator_tenant_id", "creator_source", "base_url", "source", "medium", "campaign_objective", "campaign_name_raw", "campaign", "content", "term", "final_url", "notes"]


def get_query_value(key: str) -> str:
    value = st.query_params.get(key, "")
    if isinstance(value, list):
        return value[0] if value else ""
    return str(value or "").strip()


def get_creator_context() -> dict[str, str]:
    email = get_query_value("teams_user_email") or get_query_value("teams_login_hint")
    display_name = get_query_value("teams_display_name")
    user_id = get_query_value("teams_user_id")
    tenant_id = get_query_value("teams_tenant_id")
    source = "microsoft_teams_context" if any([email, display_name, user_id, tenant_id]) else "not_available"
    return {"creator_email": email, "creator_name": display_name, "creator_teams_user_id": user_id, "creator_tenant_id": tenant_id, "creator_source": source}


def term_label(value: str) -> str:
    return TERM_LABELS.get(value, value.replace("+", " ").title())


def slugify(value: str, separator: str = "-") -> str:
    value = (value or "").strip().lower().replace("&", " and ")
    return re.sub(r"[^a-z0-9]+", separator, value).strip(separator)


def clean_url(url: str) -> str:
    parts = urlsplit((url or "").strip())
    return urlunsplit((parts.scheme, parts.netloc, parts.path, "", ""))


def is_valid_url(url: str) -> bool:
    return bool(re.match(r"^https?://", (url or "").strip(), re.I))


def build_url(base_url: str, params: dict[str, str]) -> str:
    return clean_url(base_url) + "?" + urlencode({key: value for key, value in params.items() if value}, safe="+_-")


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


def set_default(key: str, value: str) -> None:
    if key not in st.session_state:
        st.session_state[key] = value


def index_of(options: list[str], value: str) -> int:
    return options.index(value) if value in options else 0


st.set_page_config(page_title="Sunstone UTM Builder", page_icon="🔗", layout="wide")
st.markdown("""
<style>
:root{--bg:#F8F5F0;--surface:#FFFFFF;--surface2:#F2ECE5;--text:#171514;--muted:#625C56;--border:#DED6CC;--accent:#FF8200;--accent-dark:#C65F00;--shadow:0 16px 36px rgba(23,21,20,.08)}
html,body,.stApp{background:linear-gradient(180deg,#fff 0%,var(--bg) 100%)!important;color:var(--text)!important}
[data-testid="stHeader"]{background:#0E1117!important}.block-container{max-width:1180px!important;padding-top:4.25rem!important;padding-bottom:2.5rem!important}h1,h2,h3,p,li,label,.stMarkdown,.stCaption{color:var(--text)!important}code{background:#F1EEE9!important;color:#222!important;border-radius:6px;padding:.15rem .35rem}.pj-hero{background:var(--surface);border:1px solid var(--border);border-radius:24px;padding:26px 28px;margin-bottom:1.15rem;box-shadow:var(--shadow)}.pj-kicker{color:var(--accent-dark);font-size:.72rem;font-weight:850;letter-spacing:.12em;text-transform:uppercase}.pj-title{font-size:clamp(2rem,4vw,3rem);line-height:1;font-weight:850;margin:.35rem 0 .6rem;color:var(--text)}.pj-subtitle{color:var(--muted)!important;max-width:850px;font-size:1rem}.section-card{background:rgba(255,255,255,.96);border:1px solid var(--border);border-radius:20px;padding:18px;box-shadow:var(--shadow);margin-bottom:1rem}.section-label{font-size:.74rem;font-weight:850;letter-spacing:.12em;text-transform:uppercase;color:var(--accent-dark);margin-bottom:.5rem}.small-note{color:var(--muted);font-size:.9rem;margin-top:.35rem;line-height:1.45}
div[data-baseweb="select"]>div,div[data-baseweb="input"]>div,textarea,input{background:#fff!important;color:var(--text)!important;border-color:var(--border)!important;border-radius:12px!important}div[data-baseweb="select"] *,div[data-baseweb="input"] *,textarea,input{color:var(--text)!important}input::placeholder,textarea::placeholder{color:#9B948B!important;opacity:1!important}div[data-baseweb="popover"],div[data-baseweb="menu"],ul[role="listbox"]{background:#fff!important;border:1px solid var(--border)!important;border-radius:12px!important;box-shadow:0 18px 40px rgba(23,21,20,.16)!important}div[data-baseweb="popover"] *,div[data-baseweb="menu"] *,ul[role="listbox"] *{color:var(--text)!important}li[role="option"],[role="option"]{background:#fff!important;color:var(--text)!important}li[role="option"]:hover,[role="option"]:hover,[role="option"][aria-selected="true"],[data-highlighted="true"]{background:var(--surface2)!important;color:var(--text)!important}.stCheckbox label span,.stRadio label span{color:var(--text)!important}.stButton>button,.stDownloadButton>button{border-radius:999px!important;border:1px solid var(--accent)!important;background:var(--accent)!important;color:#fff!important;font-weight:850!important;padding:.72rem 1.2rem!important;box-shadow:0 8px 18px rgba(255,130,0,.22)!important}.stButton>button:hover,.stDownloadButton>button:hover{background:var(--accent-dark)!important;border-color:var(--accent-dark)!important;color:#fff!important}[data-testid="stSidebar"]{background:#FBF8F4!important;border-right:1px solid var(--border)}.stAlert{border-radius:14px}
</style>
""", unsafe_allow_html=True)

for key, default in {"committed_sig": None, "committed_url": ""}.items():
    set_default(key, default)

creator = get_creator_context()

with st.sidebar:
    st.subheader("UTM standard")
    st.markdown("""**Required:** URL + campaign/link name.

The app fills in most tracking fields based on the use case. Use Advanced tracking only when you need to adjust the details.

**Campaign format**

`yyyymmdd_unit_objective_campaign-name`

Use `other` when the real campaign is unknown.""")
    if creator["creator_email"] or creator["creator_name"]:
        st.divider()
        st.caption(f"Creator: {creator['creator_name'] or creator['creator_email']}")
        if creator["creator_email"] and creator["creator_name"]:
            st.caption(creator["creator_email"])
    st.caption(f"App version {APP_VERSION}")

st.markdown("""<div class="pj-hero"><div class="pj-kicker">Sunstone internal tool</div><div class="pj-title">UTM Builder</div><div class="pj-subtitle">Create clean, standardized tracking links without making every team decode marketing jargon first.</div></div>""", unsafe_allow_html=True)

left, right = st.columns([1.05, .95], gap="large")
with left:
    st.markdown('<div class="section-card"><div class="section-label">Quick setup</div>', unsafe_allow_html=True)
    base_url = st.text_input("Link destination", placeholder="Paste the page people should land on, like https://permanentjewelry.sunstonewelders.com/...", help="The page someone should land on after clicking the link.")
    st.markdown('<div class="small-note">This is the final page the link should send people to. Existing tracking in the URL will be replaced.</div>', unsafe_allow_html=True)
    link_type = st.selectbox("Use case", list(LINK_TYPE_PRESETS.keys()), key="link_type", format_func=lambda value: LINK_TYPE_LABELS.get(value, value), help="Pick the closest match. It only sets defaults, and you can still edit details below.")
    st.markdown('<div class="small-note">Choose the closest reason for making this link. The app will prefill the tracking fields from this choice.</div>', unsafe_allow_html=True)
    if st.session_state.get("_last_link_type") != link_type:
        preset = LINK_TYPE_PRESETS[link_type]
        st.session_state.business_unit = preset["unit"]
        st.session_state.department = preset["department"]
        st.session_state.source_select = preset["source"]
        st.session_state.medium_select = preset["medium"]
        st.session_state.objective = preset["objective"]
        st.session_state.content_select = preset["content"]
        st.session_state._last_link_type = link_type
    campaign_name_raw = st.text_input("Campaign or link name", placeholder="Short name people recognize, like dealer follow up or support manual", help="A short, plain-English name. The app formats it automatically.")
    st.markdown('<div class="small-note">Do not worry about formatting. Type a simple name and the app will clean it up.</div>', unsafe_allow_html=True)
    notes = st.text_input("Notes (optional)", placeholder="Example: sent by sales reps after demo calls")
    st.markdown(f'<div class="small-note">Date will be added automatically: <strong>{datetime.now().date().strftime("%Y/%m/%d")}</strong></div>', unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

with right:
    st.markdown('<div class="section-card"><div class="section-label">Standard fields</div>', unsafe_allow_html=True)
    unit_options = list(BUSINESS_UNITS.keys())
    business_unit_label = st.selectbox("Business area", unit_options, key="business_unit", index=index_of(unit_options, st.session_state.get("business_unit", "Permanent Jewelry")), format_func=lambda value: BUSINESS_UNIT_LABELS.get(value, value), help="Which part of Sunstone this link mainly supports.")
    department = st.selectbox("Team using the link", DEPARTMENTS, key="department", index=index_of(DEPARTMENTS, st.session_state.get("department", "marketing")), format_func=lambda value: DEPARTMENT_LABELS.get(value, value.replace("_", " ").title()), help="Which internal team is creating or mainly using this link.")
    if department in NON_MARKETING_DEPARTMENTS and st.session_state.get("_last_department") != department:
        st.session_state.objective = "other"
    st.session_state._last_department = department
    objective = st.selectbox("Goal or campaign bucket", OBJECTIVES, key="objective", index=index_of(OBJECTIVES, st.session_state.get("objective", "other")), format_func=lambda value: OBJECTIVE_LABELS.get(value, value.replace("_", " ").title()), help="This becomes part of the campaign name. Use Other when the exact marketing campaign is unknown.")
    if objective == "other":
        st.caption("Using `other` keeps the link standardized even when the exact campaign is unknown.")
    st.markdown("</div>", unsafe_allow_html=True)

with st.expander("Advanced tracking fields", expanded=False):
    st.markdown('<div class="small-note">Most users can leave these alone. Use this section when you know the exact channel, placement, keyword, audience, or asset.</div>', unsafe_allow_html=True)
    source_options = sorted(SOURCE_TO_MEDIUMS.keys())
    use_custom_source = st.checkbox("Use custom source", help="Use this only when the click starts somewhere not listed.")
    if use_custom_source:
        source = slugify(st.text_input("Click source (utm_source)", placeholder="Where the click starts, like dealer_portal or printed_catalog"), "_")
        medium_options = ALL_MEDIUMS
    else:
        if st.session_state.get("source_select") not in source_options:
            st.session_state.source_select = "hubspot"
        source = st.selectbox("Click source (utm_source)", source_options, key="source_select", format_func=lambda value: SOURCE_LABELS.get(value, value.replace("_", " ").title()), help="Where the click starts, such as HubSpot, sales team, QR code, Google Ads, Amazon, or customer support.")
        medium_options = SOURCE_TO_MEDIUMS.get(source, ALL_MEDIUMS)
    use_custom_medium = st.checkbox("Use custom medium", help="Use this only when the channel type is not listed.")
    if use_custom_medium:
        medium = slugify(st.text_input("Channel type (utm_medium)", placeholder="What kind of channel is it, like email, support, qr, or sales_outreach"), "_")
    else:
        if st.session_state.get("medium_select") not in medium_options:
            st.session_state.medium_select = medium_options[0]
        medium = st.selectbox("Channel type (utm_medium)", medium_options, key="medium_select", format_func=lambda value: MEDIUM_LABELS.get(value, value.replace("_", " ").title()), help="The channel type, such as email, support, paid search, QR, sales outreach, or shopping.")
    content_choice = st.selectbox("Clicked item or placement (utm_content)", [""] + CONTENT_OPTIONS, key="content_select", format_func=lambda value: CONTENT_LABELS.get(value, value.replace("_", " ").title()), help="Optional. Identifies the exact button, placement, QR code, image, or asset clicked.")
    custom_content = st.text_input("Custom clicked item or placement (optional)", placeholder="Examples: email-header, hero-button, booth-qr, sales-signature", help="Use this when you need a more specific placement than the dropdown. It answers: which button, image, QR code, link, or asset was clicked?")
    content = slugify(custom_content, "_") if custom_content else content_choice
    term_choice = st.selectbox("Audience, keyword, or product focus (utm_term)", TERM_PRESETS, format_func=term_label, help="Optional. Use for a keyword, audience, customer segment, product focus, or internal grouping.")
    custom_term = st.text_input("Custom audience, keyword, or product focus (optional)", placeholder="Examples: new artists, starter kit buyers, laser prospects", help="Use this for the keyword, audience, segment, product focus, or search phrase. Spaces become plus signs.")
    term = slugify(custom_term, "+") if custom_term else term_choice

if base_url and not is_valid_url(base_url):
    st.error("Destination URL must start with http:// or https://")

campaign_date = datetime.now().date()
campaign = build_campaign(campaign_date, business_unit_label, objective, campaign_name_raw) if campaign_name_raw else ""
params = {"utm_source": source, "utm_medium": medium, "utm_campaign": campaign, "utm_content": content, "utm_term": term}
preview_url = build_url(base_url, params) if is_valid_url(base_url) and source and medium and campaign else ""
missing = []
if not is_valid_url(base_url):
    missing.append("Link destination")
if not campaign_name_raw:
    missing.append("Campaign or link name")
if not source:
    missing.append("Click source")
if not medium:
    missing.append("Channel type")
if missing:
    st.caption("Missing: " + ", ".join(missing))
if preview_url:
    st.markdown("### Preview")
    st.code(preview_url, language="text")

current_sig = (clean_url(base_url), source, medium, campaign, content or "", term or "", notes.strip())
if st.button("Generate and log URL", type="primary", use_container_width=True, disabled=bool(missing)):
    progress = st.progress(0)
    payload = {"submitted_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"), "app_version": APP_VERSION, "business_unit": BUSINESS_UNITS.get(business_unit_label, "corp"), "department": department, "link_type": link_type, **creator, "base_url": clean_url(base_url), "source": source, "medium": medium, "campaign_objective": objective, "campaign_name_raw": campaign_name_raw.strip(), "campaign": campaign, "content": content or "", "term": term or "", "final_url": preview_url, "notes": notes.strip()}
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
