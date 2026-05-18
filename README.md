# Sunstone UTM Builder

Internal Streamlit app for creating standardized UTM links across marketing, ecommerce, sales, customer support, events, marketplaces, QR codes, agentic search references, and internal sharing.

## What changed in v2.1.3

- Fixed dropdown readability so open menu options use a light background and readable dark text.
- Replaced UTM-heavy labels with plainer field names like **Use case**, **Link destination**, **Business area**, **Team using the link**, and **Goal or campaign bucket**.
- Added short helper text under key fields so non-marketing users understand what to enter without being over-explained to.
- Added descriptive dropdown labels that explain what each option means while preserving clean UTM values behind the scenes.
- Added Microsoft Teams creator tracking via Teams context URL parameters.
- Logs creator email, display name, Teams user ID, tenant ID, and creator source to Google Sheets when the app is opened from Teams.
- Updated the Teams manifest template so the Teams tab passes user context into the Streamlit app URL.
- Kept advanced tracking available for power users while making the default workflow easier for sales, support, operations, and other teams.

## Current workflow

Most users only need to fill out:

1. Link destination
2. Use case
3. Campaign or link name
4. Notes, optional

The app fills in the tracking structure based on the selected use case. Advanced tracking is available for users who need to adjust the exact source, medium, content, or term.

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
20260518_pj_other_support-manual-follow-up
```

Naming rules:

- Use lowercase values.
- Use underscores between UTM structure parts.
- Use hyphens inside campaign and content names.
- Use plus signs inside keyword terms.
- Use `other` when the exact marketing campaign or objective is unknown.
- Add notes when helpful so future reporting has context.

## Creator tracking in Microsoft Teams

The Teams app package passes Teams context into the hosted Streamlit URL using query parameters:

```text
teams_user_email
teams_login_hint
teams_user_id
teams_tenant_id
teams_display_name
```

The Streamlit app logs those values as:

```text
creator_email
creator_name
creator_teams_user_id
creator_tenant_id
creator_source
```

This is intended for crediting who created a UTM link. It should not be treated as secure authentication or permission control. For security-sensitive identity, use Microsoft Entra ID / Teams SSO token validation.

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
- The Teams context fields are for attribution/logging, not secure proof of identity.
- The manifest currently points privacy and terms URLs to `/privacy` and `/terms` on the hosted app domain. Change those to approved company URLs if those pages are not available.
