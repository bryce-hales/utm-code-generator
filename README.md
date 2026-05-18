# Sunstone UTM Builder

Internal Streamlit app for creating standardized UTM links across marketing, ecommerce, sales, customer support, events, marketplaces, QR codes, agentic search references, and internal sharing.

## What changed in v2.1

- Simplified the main workflow so most users only need to enter a destination URL, choose a link type, and add a plain-English campaign/link name.
- Removed the visible date field. The app now automatically uses the date the URL is generated.
- Moved source, medium, content, and term controls into an **Advanced tracking fields** section.
- Added link-type presets for marketing campaigns, paid ads, social posts, sales outreach, customer support, events/QR codes, marketplaces, internal links, and SEO/agentic references.
- Improved readability by forcing light input fields, stronger text contrast, more top spacing below the Streamlit header, and neutral Sunstone styling with orange accents instead of PJX purple or gold.
- Added tooltips for custom content and custom term fields.
- Expanded source and medium options and added custom source/custom medium controls for edge cases.

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
- Add notes when helpful so future reporting has context.

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
