# Sunstone UTM Builder

Streamlit app for creating standardized UTM tracking links for marketing, ecommerce, sales, customer support, events, marketplaces, QR codes, AI/search references, and internal sharing.

## Overview

The app creates clean UTM URLs using a consistent naming structure. Users can choose a use case, enter a destination URL, add a campaign or link name, and optionally adjust advanced tracking fields.

## Current Workflow

Most links can be created with four fields:

1. Link destination
2. Use case
3. Campaign or link name
4. Notes, optional

The app fills in the tracking structure based on the selected use case. Advanced tracking fields are available for source, medium, content, and term values.

## UTM Standard

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
- Use `other` when the exact campaign or objective is unknown.
- Add notes when helpful for future reporting context.

## Microsoft Teams Creator Tracking

The Microsoft Teams app package can pass Teams context into the hosted Streamlit URL using query parameters:

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

These values are intended for attribution and reporting. They are not a replacement for secure authentication or permission control. Security-sensitive identity validation should use Microsoft Entra ID or Teams SSO token validation.

## Run Locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Google Sheets Logging

The app expects a Streamlit Google Sheets connection named `gsheets` and a worksheet named `Sheet1`.

If Google Sheets logging fails, the app still generates the final UTM URL and displays the logging error instead of blocking link creation.

## Microsoft Teams App Package

The Teams package wraps a hosted HTTPS version of the Streamlit app as a personal tab.

Build the package with:

```bash
python teams/package-teams-app.py --app-base-url https://your-hosted-app.example.com --microsoft-app-id YOUR-MICROSOFT-APP-ID
```

The generated package is saved as:

```text
dist/sunstone-utm-builder-teams.zip
```

Package details:

- `validDomains` is generated from the hosted app URL.
- The manifest uses `color.png`, `outline.png`, and `manifest.json` in the app package.
- The default Microsoft app ID is a placeholder and should be replaced when a registered app ID is available.
- Teams context fields are used for attribution and logging.
- Privacy and terms URLs default to `/privacy` and `/terms` on the hosted app domain.
