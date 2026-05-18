from __future__ import annotations

import argparse
import json
import re
import zipfile
from pathlib import Path
from urllib.parse import urlparse

APP_VERSION = "2.0.0"
ROOT = Path(__file__).resolve().parents[1]
TEAMS_DIR = ROOT / "teams"
DIST_DIR = ROOT / "dist"


def sanitize_base_url(url: str) -> str:
    parsed = urlparse(url.strip().rstrip("/"))
    if parsed.scheme != "https" or not parsed.netloc:
        raise ValueError("APP_BASE_URL must be a full HTTPS URL, such as https://utm-builder.example.com")
    return f"{parsed.scheme}://{parsed.netloc}{parsed.path}".rstrip("/")


def render_manifest(app_base_url: str, microsoft_app_id: str) -> dict:
    app_base_url = sanitize_base_url(app_base_url)
    domain = urlparse(app_base_url).netloc
    template = (TEAMS_DIR / "manifest.template.json").read_text(encoding="utf-8")
    replacements = {
        "{{APP_VERSION}}": APP_VERSION,
        "{{MICROSOFT_APP_ID}}": microsoft_app_id,
        "{{APP_BASE_URL}}": app_base_url,
        "{{APP_DOMAIN}}": domain,
    }
    for token, value in replacements.items():
        template = template.replace(token, value)
    return json.loads(template)


def write_icon(path: Path, color: tuple[int, int, int, int], accent: tuple[int, int, int, int]) -> None:
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError as exc:
        raise SystemExit("Install Pillow first: pip install Pillow") from exc

    image = Image.new("RGBA", (192, 192), color)
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((18, 18, 174, 174), radius=42, fill=accent)
    draw.text((55, 67), "UTM", fill=(255, 255, 255, 255))
    image.save(path)


def build_package(app_base_url: str, microsoft_app_id: str, output: Path) -> Path:
    DIST_DIR.mkdir(exist_ok=True)
    work_dir = DIST_DIR / "teams-package"
    work_dir.mkdir(exist_ok=True)

    manifest = render_manifest(app_base_url, microsoft_app_id)
    (work_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    write_icon(work_dir / "color.png", (255, 255, 255, 0), (111, 74, 115, 255))
    write_icon(work_dir / "outline.png", (255, 255, 255, 0), (75, 48, 79, 255))

    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as zf:
        for file_name in ["manifest.json", "color.png", "outline.png"]:
            zf.write(work_dir / file_name, arcname=file_name)
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the Microsoft Teams app package for the UTM Builder.")
    parser.add_argument("--app-base-url", required=True, help="Hosted HTTPS URL for the Streamlit app.")
    parser.add_argument("--microsoft-app-id", default="00000000-0000-0000-0000-000000000000", help="Microsoft app ID. Replace before final admin approval when available.")
    parser.add_argument("--output", default=str(DIST_DIR / "sunstone-utm-builder-teams.zip"))
    args = parser.parse_args()

    output = build_package(args.app_base_url, args.microsoft_app_id, Path(args.output))
    print(f"Created {output}")


if __name__ == "__main__":
    main()
