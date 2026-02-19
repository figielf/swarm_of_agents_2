"""
Convert all Markdown files in ./summary to clean HTML in ./summary/html.
Mermaid diagrams are pre-rendered as static <img> tags via mermaid.ink so
they survive copy-paste into Confluence without any plugin requirement.
"""

import re
import textwrap
import base64
from urllib.parse import quote
import markdown
from pathlib import Path

# ── paths ──────────────────────────────────────────────────────────────────
SCRIPT_DIR = Path(__file__).parent
REPO_ROOT   = SCRIPT_DIR.parent
SRC_DIR     = REPO_ROOT / "summary"
DST_DIR     = REPO_ROOT / "summary" / "html"

DST_DIR.mkdir(parents=True, exist_ok=True)

# ── Confluence config ────────────────────────────────────────────────────────
CONFLUENCE_BASE  = "https://rezolvetech.atlassian.net"
CONFLUENCE_SPACE = "RAIL"


def confluence_page_url(title: str) -> str:
    """Build a Confluence display URL from a page title.

    Uses the /wiki/display/{space}/{title} format which Confluence Cloud
    resolves automatically to the live page once it exists.
    """
    slug = quote(title, safe="-_. ")
    # Confluence display URLs use '+' for spaces
    slug = slug.replace(" ", "+")
    return f"{CONFLUENCE_BASE}/wiki/display/{CONFLUENCE_SPACE}/{slug}"


def build_page_url_map(src_dir: Path) -> dict[str, str]:
    """Return {html_filename: confluence_url} for every .md file in src_dir."""
    mapping: dict[str, str] = {}
    for f in src_dir.glob("*.md"):
        md_text = f.read_text(encoding="utf-8")
        title = extract_title(md_text)
        mapping[f.stem + ".html"] = confluence_page_url(title)
    return mapping

# ── per-page HTML template ──────────────────────────────────────────────────
HTML_TEMPLATE = """\
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title}</title>
  <style>
    /* === base === */
    body {{
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto,
                   "Helvetica Neue", Arial, sans-serif;
      font-size: 14px;
      line-height: 1.6;
      color: #172b4d;
      max-width: 960px;
      margin: 32px auto;
      padding: 0 24px;
    }}
    /* === headings === */
    h1 {{ font-size: 2em;   border-bottom: 2px solid #dfe1e6; padding-bottom: 8px;  margin-top: 32px; }}
    h2 {{ font-size: 1.5em; border-bottom: 1px solid #dfe1e6; padding-bottom: 4px;  margin-top: 28px; }}
    h3 {{ font-size: 1.17em; margin-top: 24px; }}
    h4 {{ font-size: 1em;   margin-top: 16px; }}
    /* === tables === */
    table {{
      border-collapse: collapse;
      width: 100%;
      margin: 16px 0;
      font-size: 13px;
    }}
    th, td {{
      border: 1px solid #dfe1e6;
      padding: 8px 12px;
      text-align: left;
      vertical-align: top;
    }}
    th {{
      background-color: #f4f5f7;
      font-weight: 600;
    }}
    tr:nth-child(even) td {{
      background-color: #fafbfc;
    }}
    /* === code === */
    code {{
      font-family: "SFMono-Regular", Consolas, "Liberation Mono", Menlo, monospace;
      font-size: 12px;
      background: #f4f5f7;
      padding: 2px 5px;
      border-radius: 3px;
    }}
    pre {{
      background: #f4f5f7;
      border: 1px solid #dfe1e6;
      border-radius: 4px;
      padding: 16px;
      overflow-x: auto;
      margin: 16px 0;
    }}
    pre code {{
      background: none;
      padding: 0;
      font-size: 12px;
    }}
    /* === mermaid diagram image === */
    .mermaid-img {{
      display: block;
      max-width: 100%;
      border: 1px solid #dfe1e6;
      border-radius: 4px;
      margin: 16px 0;
      background: #f9f9fb;
      padding: 8px;
    }}
    /* === blockquotes / notes === */
    blockquote {{
      border-left: 4px solid #0052cc;
      margin: 16px 0;
      padding: 8px 16px;
      background: #e9f2ff;
      border-radius: 0 4px 4px 0;
    }}
    /* === lists === */
    ul, ol {{ margin: 8px 0 8px 24px; }}
    li {{ margin: 4px 0; }}
    /* === horizontal rule === */
    hr {{ border: none; border-top: 1px solid #dfe1e6; margin: 24px 0; }}
    /* === strong / bold === */
    strong {{ font-weight: 600; color: #172b4d; }}
    /* === links === */
    a {{ color: #0052cc; text-decoration: none; }}
    a:hover {{ text-decoration: underline; }}
  </style>
  <!-- No Mermaid JS needed: diagrams are pre-rendered as static images via mermaid.ink -->
</head>
<body>
{body}
</body>
</html>
"""

# ── helpers ─────────────────────────────────────────────────────────────────

def extract_title(md_text: str) -> str:
    """Return the first H1 heading text, or the filename stem."""
    m = re.search(r"^#\s+(.+)$", md_text, re.MULTILINE)
    return m.group(1).strip() if m else "Document"


def _mermaid_ink_url(diagram_code: str) -> str:
    """Return a mermaid.ink PNG URL for the given diagram source."""
    encoded = base64.urlsafe_b64encode(diagram_code.encode("utf-8")).decode("ascii")
    return f"https://mermaid.ink/img/{encoded}?theme=neutral"


def preprocess_mermaid(md_text: str) -> str:
    """
    Replace ```mermaid ... ``` fences with a placeholder <img> tag so the
    markdown parser does not try to syntax-highlight them.
    Each diagram is rendered as a static image via mermaid.ink.
    """
    counter = [0]
    placeholders: dict[str, str] = {}

    def replacer(match: re.Match) -> str:
        diagram_code = match.group(1).strip()
        key = f"MERMAID_PLACEHOLDER_{counter[0]}_END"
        counter[0] += 1
        img_url = _mermaid_ink_url(diagram_code)
        block = f'<img class="mermaid-img" src="{img_url}" alt="Mermaid diagram" />'
        placeholders[key] = block
        return key

    pattern = re.compile(r"```mermaid\n(.*?)```", re.DOTALL)
    processed = pattern.sub(replacer, md_text)
    return processed, placeholders


def postprocess_placeholders(html: str, placeholders: dict[str, str]) -> str:
    """Substitute placeholders back with their HTML blocks."""
    for key, block in placeholders.items():
        # The markdown library may have wrapped the key in a <p> tag
        html = html.replace(f"<p>{key}</p>", block)
        html = html.replace(key, block)
    return html


def _normalize_anchor(anchor: str) -> str:
    """Collapse consecutive hyphens to a single hyphen in an anchor slug.

    Python's toc extension reduces any run of non-alphanumeric characters to a
    single '-', but Markdown source TOC links (written for GitHub-style slugs)
    use '--' for em-dashes, arrows, and slashes.  Normalizing keeps them in sync.
    """
    return re.sub(r"-{2,}", "-", anchor).strip("-")


def rewrite_md_links(html: str) -> str:
    """Rewrite href="*.md[#anchor]" → href="*.html[#normalized-anchor]"."""
    def _fix(m: re.Match) -> str:
        path    = m.group(1)
        anchor  = m.group(2) or ""          # includes leading '#' when present
        if anchor:
            anchor = "#" + _normalize_anchor(anchor[1:])
        return f'href="{path}.html{anchor}"'

    return re.sub(r'href="([^"]+?)\.md(#[^"]*)??"', _fix, html)


def rewrite_cross_page_links(html: str, page_url_map: dict[str, str]) -> str:
    """Replace .html cross-page hrefs with real Confluence page URLs.

    - Cross-page .html links  → Confluence display URL for that page
      (anchor fragments are dropped — they don't cross pages in Confluence)
    - Same-page anchor links  → kept as-is (work within one Confluence page)
    - External http(s) links  → kept as-is
    """
    def _replace(m: re.Match) -> str:
        href  = m.group(1)
        inner = m.group(2)
        # keep pure anchor and external links unchanged
        if href.startswith("#") or href.startswith("http"):
            return m.group(0)
        # strip anchor fragment to get the target filename
        filename = href.split("#")[0]
        if filename in page_url_map:
            return f'<a href="{page_url_map[filename]}">{inner}</a>'
        # unknown target — fall back to bold text
        return f"<strong>{inner}</strong>"

    return re.sub(r'<a\s+href="([^"]*)"[^>]*>(.*?)</a>', _replace, html, flags=re.DOTALL)


def md_to_html(md_text: str) -> str:
    """
    Convert a Markdown string to an HTML body fragment.
    Uses: tables, fenced_code, toc, smarty extras.
    """
    extensions = [
        "tables",
        "fenced_code",
        "toc",
        "nl2br",
        "pymdownx.superfences",
    ]
    # pymdownx.superfences may conflict with fenced_code — use a minimal set
    safe_extensions = ["tables", "fenced_code", "toc", "sane_lists"]
    try:
        body = markdown.markdown(md_text, extensions=extensions)
    except Exception:
        body = markdown.markdown(md_text, extensions=safe_extensions)
    return body


def convert_file(src: Path, dst: Path, page_url_map: dict[str, str]) -> None:
    md_text = src.read_text(encoding="utf-8")
    title = extract_title(md_text)

    # Pull out mermaid blocks before the markdown parser sees them
    preprocessed, placeholders = preprocess_mermaid(md_text)

    body_html = md_to_html(preprocessed)
    body_html = postprocess_placeholders(body_html, placeholders)
    body_html = rewrite_md_links(body_html)
    body_html = rewrite_cross_page_links(body_html, page_url_map)

    page = HTML_TEMPLATE.format(title=title, body=body_html)
    dst.write_text(page, encoding="utf-8")
    print(f"  ✓  {src.name}  →  {dst.name}")


# ── main ─────────────────────────────────────────────────────────────────────
def main() -> None:
    md_files = sorted(SRC_DIR.glob("*.md"))
    if not md_files:
        print(f"No .md files found in {SRC_DIR}")
        return

    # Pre-scan all .md files to build filename → Confluence URL map
    page_url_map = build_page_url_map(SRC_DIR)
    print("Confluence page URL map:")
    for fname, url in sorted(page_url_map.items()):
        print(f"  {fname} → {url}")
    print()

    print(f"Converting {len(md_files)} file(s): {SRC_DIR} → {DST_DIR}\n")
    for src in md_files:
        dst = DST_DIR / (src.stem + ".html")
        convert_file(src, dst, page_url_map)

    print(f"\nDone. HTML files are in: {DST_DIR}")


if __name__ == "__main__":
    main()
