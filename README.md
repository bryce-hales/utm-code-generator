# Sunstone UTM Builder

Internal Streamlit app for creating standardized UTM links across marketing, ecommerce, sales, customer support, events, marketplaces, QR codes, and internal sharing.

## What changed in v2

- Reworked the visual style to better match the permanent jewelry brand without using the gold accent.
- Added a standard campaign naming format: `yyyymmdd_unit_objective_campaign-name`.
- Added business unit and department fields so links are easier to audit later.
- Expanded UTM sources and mediums for Shopify, HubSpot, sales outreach, customer support, Amazon, Etsy, TikTok Shop, PJX, QR codes, Microsoft Teams, email signatures, and agentic search tools.
- Added campaign objectives, content placements, and term presets that better fit Sunstone workflows.
- Expanded Google Sheets logging fields for clearer reporting.
- Added Microsoft Teams packaging files so the hosted app can be submitted as a Teams personal tab.

## UTM standard

Campaign format:

```text
yyyymmdd_unit_objective_campaign-name
```

Examples:

```text
20260518_pj_product_launch_zp2-luxe
20260518_pjx_event_registration_early-access
20260518_ind_support_resource_laser-data-sheet
```

Naming rules:

- Use lowercase values.
- Use underscores between UTM structure parts.
- Use hyphens inside campaign and content names.
- Use plus signs inside keyword terms.
- Add notes for every generated link so future reporting has context.

## Run locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Google Sheets logging

The app expects a Streamlit Google Sheets connection named `gsheets` and a worksheet named `Sheet1`.

If Google Sheets logging fails, the app still generates the final UTM URL and shows the logging error. This avoids blocking someone from creating a link during a campaign or support workflow.

## Microsoft Teams app package

Teams will not run the Python Streamlit app directly. The Teams package wraps a hosted HTTPS version of the Streamlit app as a personal tab.

1. Deploy the Streamlit app to an HTTPS URL employees can access.
2. Build the Teams package:

```bash
python teams/package-teams-app.py --app-base-url https://your-hosted-app.example.com --microsoft-app-id YOUR-MICROSOFT-APP-ID
```

3. Give IT the generated file:

```text
dist/sunstone-utm-builder-teams.zip
```

Notes for IT review:

- `validDomains` is generated from the hosted app URL.
- The manifest uses `color.png`, `outline.png`, and `manifest.json` in the app package.
- The default Microsoft app ID is a placeholder. Replace it before final approval if your IT process requires a registered app ID.
- The manifest currently points privacy and terms URLs to `/privacy` and `/terms` on the hosted app domain. Change those to approved company URLs if those pages are not available.
