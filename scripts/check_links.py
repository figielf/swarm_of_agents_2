"""Verify all anchored links in the generated HTML files resolve correctly."""
import re
from pathlib import Path

html_dir = Path(__file__).parent.parent / "summary" / "html"

# Collect all id= attributes per file
ids_by_file = {}
for f in html_dir.glob("*.html"):
    ids_by_file[f.name] = set(re.findall(r'id="([^"]+)"', f.read_text(encoding="utf-8")))

# Check every anchored href in every file
total = 0
broken = []
ok = []
for src_file in sorted(html_dir.glob("*.html")):
    content = src_file.read_text(encoding="utf-8")
    links = re.findall(r'href="([^"#]+\.html)#([^"]+)"', content)
    for target_file, anchor in links:
        total += 1
        if anchor in ids_by_file.get(target_file, set()):
            ok.append((src_file.name, target_file, anchor))
        else:
            broken.append((src_file.name, target_file, anchor))

print(f"Total anchored links checked: {total}")
print(f"  OK:     {len(ok)}")
print(f"  Broken: {len(broken)}")

if broken:
    print("\nBROKEN links:")
    for src, tgt, anchor in broken:
        actual_ids = sorted(ids_by_file.get(tgt, set()))
        # find closest for diagnosis
        close = [x for x in actual_ids if x.startswith(anchor.split("-")[0])][:3]
        print(f"  [{src}] -> {tgt}#{anchor}")
        if close:
            print(f"    actual IDs starting with '{anchor.split('-')[0]}': {close}")
else:
    print("\nAll anchored links resolve correctly.")
