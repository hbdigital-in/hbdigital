"""
HBDigital Website Test Suite
Tests the index.html for structural integrity, SEO schema, content correctness,
AI Visibility implementation, links, images, and JavaScript.
"""

import re
import json
import os
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

HTML_FILE = os.path.join(os.path.dirname(__file__), "index.html")

# -- helpers -----------------------------------------------------------------

def read_html():
    with open(HTML_FILE, "r", encoding="utf-8") as f:
        return f.read()

PASS  = "PASS"
FAIL  = "FAIL"
results = []

def check(name, condition, detail=""):
    status = PASS if condition else FAIL
    results.append((status, name, detail))
    icon = "OK" if condition else "!!"
    detail_str = f"  → {detail}" if detail else ""
    print(f"  [{icon}] {name}{detail_str}", flush=True)
    return condition

def section(title):
    print(f"\n{'-'*60}")
    print(f"  {title}")
    print(f"{'-'*60}")

# -- load file ----------------------------------------------------------------

try:
    html = read_html()
except FileNotFoundError:
    print(f"ERROR: Cannot find {HTML_FILE}")
    sys.exit(1)

html_lower = html.lower()

# -----------------------------------------------------------------------------
# GROUP 1: Required Sections
# -----------------------------------------------------------------------------
section("GROUP 1 — Required Sections (IDs)")

required_ids = [
    ("hero",                    "#hero"),
    ("proof-strip",             "#proof-strip"),
    ("how-customers-find-you",  "#how-customers-find-you  (NEW AI section)"),
    ("services",                "#services"),
    ("who-i-help",              "#who-i-help"),
    ("pricing",                 "#pricing"),
    ("work",                    "#work"),
    ("about",                   "#about"),
    ("faq",                     "#faq"),
    ("contact",                 "#contact"),
]

for id_, label in required_ids:
    check(f"Section id='{id_}'", f'id="{id_}"' in html, label)

# -----------------------------------------------------------------------------
# GROUP 2: Nav Links → Matching IDs
# -----------------------------------------------------------------------------
section("GROUP 2 — Nav Links Point to Existing Sections")

nav_links = re.findall(r'<ul[^>]*class="nav-links"[^>]*>(.*?)</ul>', html, re.DOTALL)
if nav_links:
    nav_html = nav_links[0]
    nav_hrefs = re.findall(r'href="(#[^"]+)"', nav_html)
    for href in nav_hrefs:
        section_id = href.lstrip("#")
        check(f"Nav href='{href}' has matching id", f'id="{section_id}"' in html)
else:
    check("Nav links found", False, "Could not parse nav-links ul")

# -----------------------------------------------------------------------------
# GROUP 3: JSON-LD Schema
# -----------------------------------------------------------------------------
section("GROUP 3 — JSON-LD Schema Validity & Completeness")

schema_match = re.search(
    r'<script\s+type="application/ld\+json">(.*?)</script>',
    html, re.DOTALL
)
schema_valid = False
schema_data = None

if schema_match:
    try:
        schema_data = json.loads(schema_match.group(1))
        schema_valid = True
        check("JSON-LD parses as valid JSON", True)
    except json.JSONDecodeError as e:
        check("JSON-LD parses as valid JSON", False, str(e))
else:
    check("JSON-LD block found in <head>", False)

if schema_valid and schema_data:
    graph = schema_data.get("@graph", [])

    # Find LocalBusiness node
    lb = next((n for n in graph if "LocalBusiness" in str(n.get("@type", ""))), None)
    check("@graph contains LocalBusiness node", lb is not None)

    if lb:
        check("LocalBusiness.name = 'HB Digital'",
              lb.get("name") == "HB Digital",
              f"Got: {lb.get('name')}")
        check("LocalBusiness.telephone present",
              bool(lb.get("telephone")),
              lb.get("telephone", "MISSING"))
        check("LocalBusiness.address present",
              bool(lb.get("address")))
        check("LocalBusiness.url present",
              bool(lb.get("url")))
        check("LocalBusiness.areaServed is a list",
              isinstance(lb.get("areaServed"), list))
        check("LocalBusiness.founder present",
              bool(lb.get("founder")))

        catalog = lb.get("hasOfferCatalog", {})
        services = catalog.get("itemListElement", [])
        service_names = [
            s.get("itemOffered", {}).get("name", "")
            for s in services
        ]
        check("6 services defined in catalog",
              len(services) == 6,
              f"Found {len(services)}")
        check("'AI Visibility Setup' service in catalog",
              any("AI Visibility" in n for n in service_names),
              f"Services: {service_names}")

    # Find FAQPage node
    faq_node = next((n for n in graph if n.get("@type") == "FAQPage"), None)
    check("@graph contains FAQPage node", faq_node is not None)

    if faq_node:
        questions = faq_node.get("mainEntity", [])
        check("FAQPage has 9+ questions",
              len(questions) >= 9,
              f"Found {len(questions)}")
        ai_qs = [q.get("name","") for q in questions
                 if "chatgpt" in q.get("name","").lower()
                 or "ai" in q.get("name","").lower()]
        check("FAQPage includes AI-related questions",
              len(ai_qs) >= 2,
              f"AI questions: {len(ai_qs)}")

    # Find WebSite node
    ws = next((n for n in graph if n.get("@type") == "WebSite"), None)
    check("@graph contains WebSite node", ws is not None)

# -----------------------------------------------------------------------------
# GROUP 4: Meta Tags & SEO
# -----------------------------------------------------------------------------
section("GROUP 4 — Meta Tags & SEO")

desc_match = re.search(r'<meta\s+name="description"\s+content="([^"]+)"', html)
check("Meta description present",
      bool(desc_match),
      desc_match.group(1)[:80] + "…" if desc_match else "MISSING")

if desc_match:
    desc = desc_match.group(1)
    check("Meta description mentions AI/ChatGPT",
          "chatgpt" in desc.lower() or "ai" in desc.lower(),
          desc[:80])
    check("Meta description mentions price",
          "5,999" in desc or "₹" in desc)

og_title = re.search(r'property="og:title"\s+content="([^"]+)"', html)
check("og:title present", bool(og_title))
if og_title:
    check("og:title mentions AI or Google",
          "ai" in og_title.group(1).lower() or "google" in og_title.group(1).lower(),
          og_title.group(1))

check("Canonical URL present", '<link rel="canonical"' in html)
check("geo.region meta tag present", 'name="geo.region"' in html)
check("geo.placename meta tag present", 'name="geo.placename"' in html)

# -----------------------------------------------------------------------------
# GROUP 5: AI Visibility Content
# -----------------------------------------------------------------------------
section("GROUP 5 — AI Visibility Content")

check("'How customers find you' section present",
      'id="how-customers-find-you"' in html)
check("discovery-grid CSS class present",
      'class="discovery-grid"' in html)
check("'AI chatbot' card present",
      'ask an AI chatbot' in html or 'AI chatbot' in html)
check("'Yellow Pages' analogy present",
      'Yellow Pages' in html)
check("'Only local agency' claim present",
      'only local agency' in html.lower())
check("AI Visibility Setup service card present",
      'AI Visibility Setup' in html)
check("ai-card-features list present",
      'class="ai-card-features"' in html)
check("NEW badge on AI Visibility in Growth pricing",
      'pkg-new-badge' in html)
check("AI Visibility add-on standalone card present",
      'ai-addon-card' in html)
check("AI Visibility in Growth pkg-items",
      'AI Visibility Setup' in html and 'pkg-new-badge' in html)
check("AI Visibility standalone price ₹4,999",
      '₹4,999' in html)

# FAQ AI questions
ai_faq_count = len(re.findall(r'ChatGPT|Gemini|AI assistant|AI chatbot|AI Visibility',
                               html, re.IGNORECASE))
check("Multiple AI mentions in FAQ section",
      ai_faq_count >= 8,
      f"Found {ai_faq_count} AI-related mentions in HTML")

check("AI Visibility in contact form dropdown",
      'ai-visibility' in html or 'AI Visibility Setup' in html)

# -----------------------------------------------------------------------------
# GROUP 6: Phone Number & Contact Consistency
# -----------------------------------------------------------------------------
section("GROUP 6 — Phone Number & Contact Consistency")

phone_correct = "+91 88502 81560"
phone_double  = "+91 +91"
check("No double '+91 +91' in HTML",
      phone_double not in html,
      "Found duplicate prefix!" if phone_double in html else "OK")

phone_occurrences = html.count(phone_correct)
check(f"Phone '{phone_correct}' appears in HTML",
      phone_occurrences >= 1,
      f"Found {phone_occurrences} times")

wa_number = "918850281560"
wa_links = re.findall(r'wa\.me/(\d+)', html)
wrong_wa = [n for n in wa_links if n != wa_number]
check("All wa.me links use correct number",
      len(wrong_wa) == 0,
      f"Wrong numbers: {wrong_wa}" if wrong_wa else f"{len(wa_links)} links all correct")

check("Email hello@hbdigital.in present",
      "hello@hbdigital.in" in html)
check("Formspree action URL present",
      "formspree.io/f/" in html)

# -----------------------------------------------------------------------------
# GROUP 7: No Placeholder / Draft Text
# -----------------------------------------------------------------------------
section("GROUP 7 — No Placeholder or Draft Text")

placeholders = [
    "[placeholder]", "YOUR_FORM_ID", "XXXXXXXXXX",
    "TODO", "FIXME", "your@email.com", "example.com",
]
for p in placeholders:
    check(f"No '{p}' in HTML", p not in html)

# -----------------------------------------------------------------------------
# GROUP 8: Images
# -----------------------------------------------------------------------------
section("GROUP 8 — Image Files Exist on Disk")

img_srcs = re.findall(r'<img[^>]+src="([^"]+)"', html)
base_dir = os.path.dirname(HTML_FILE)

for src in img_srcs:
    if src.startswith("http"):
        continue  # skip external
    img_path = os.path.join(base_dir, src.lstrip("/"))
    check(f"Image '{src}' exists on disk",
          os.path.isfile(img_path),
          "MISSING" if not os.path.isfile(img_path) else "OK")

# Check alt attributes on all img tags
img_tags = re.findall(r'<img[^>]+>', html)
imgs_without_alt = [t for t in img_tags if 'alt=' not in t]
check("All <img> tags have alt attributes",
      len(imgs_without_alt) == 0,
      f"{len(imgs_without_alt)} images missing alt" if imgs_without_alt else "OK")

# -----------------------------------------------------------------------------
# GROUP 9: JavaScript
# -----------------------------------------------------------------------------
section("GROUP 9 — JavaScript Checks")

check("toggleFaq() function defined",
      "function toggleFaq(" in html)
check("Navbar scroll handler present",
      "addEventListener('scroll'" in html)
check("Mobile nav toggle handler present",
      "navToggle" in html)
check("No onclick references to undefined functions",
      all(fn in html for fn in re.findall(r"onclick=\"(\w+)\(", html)))

# Check all onclick="fnName(...)" functions are defined
onclick_fns = set(re.findall(r'onclick="(\w+)\(', html))
for fn in onclick_fns:
    check(f"onclick function '{fn}()' is defined in <script>",
          f"function {fn}(" in html)

# -----------------------------------------------------------------------------
# GROUP 10: External Link Safety
# -----------------------------------------------------------------------------
section("GROUP 10 — External Link Safety")

ext_links = re.findall(r'<a[^>]+href="https?://[^"]*"[^>]*>', html)
missing_noopener = [
    l for l in ext_links
    if 'target="_blank"' in l and 'noopener' not in l
]
check("All target=_blank links have rel=noopener",
      len(missing_noopener) == 0,
      f"{len(missing_noopener)} unsafe links" if missing_noopener else "OK")

check("Google Analytics tag present",
      "googletagmanager.com/gtag/js" in html)

# -----------------------------------------------------------------------------
# SUMMARY
# -----------------------------------------------------------------------------
print(f"\n{'='*60}")
total  = len(results)
passed = sum(1 for r in results if r[0] == PASS)
failed = sum(1 for r in results if r[0] == FAIL)

print(f"  TOTAL: {total}  |  PASSED: {passed}  |  FAILED: {failed}")
print(f"{'='*60}")

if failed:
    print(f"\n  FAILURES:")
    for status, name, detail in results:
        if status == FAIL:
            detail_str = f"  --> {detail}" if detail else ""
            print(f"    FAIL: {name}{detail_str}")

print()
sys.exit(0 if failed == 0 else 1)
