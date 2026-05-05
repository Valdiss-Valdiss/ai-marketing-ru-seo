#!/usr/bin/env python3
"""
Marketing Page Analyzer — Utility script for AI Marketing Claude Code Skills
Analyzes a webpage for marketing effectiveness: SEO elements, content structure,
trust signals, CTAs, social proof, and conversion optimization indicators.

Supports both Google and Yandex SEO analysis with combined scoring.
"""

import sys
import json
import re
import urllib.request
import urllib.error
import ssl
from html.parser import HTMLParser
from urllib.parse import urlparse, urljoin


class MarketingPageParser(HTMLParser):
    """Parse HTML and extract marketing-relevant elements."""

    def __init__(self):
        super().__init__()
        self.title = ""
        self.meta_description = ""
        self.meta_keywords = ""
        self.og_tags = {}
        self.headings = {"h1": [], "h2": [], "h3": [], "h4": [], "h5": [], "h6": []}
        self.links = []
        self.images = []
        self.forms = []
        self.buttons = []
        self.scripts = []
        self.schema_data = []
        self.ctas = []
        self.social_links = []
        self.tracking_scripts = []

        # Yandex-specific fields
        self._yandex_verification = ""
        self._has_turbo = False
        self._yml_feed = ""
        self._yandex_metrics = []

        # State tracking
        self._current_tag = None
        self._current_attrs = {}
        self._in_title = False
        self._in_heading = None
        self._in_button = False
        self._in_a = False
        self._current_text = ""
        self._in_script = False
        self._script_type = ""
        self._in_form = False
        self._current_form = {}
        self._form_fields = []
        self._text_content = []
        self._has_viewport = False
        self._canonical = ""
        self._robots_meta = ""
        self._has_https = False

    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)
        self._current_tag = tag
        self._current_attrs = attrs_dict

        # Check for HTTPS
        if tag == "meta" and attrs_dict.get("http-equiv", "").lower() == "upgrade-insecure-requests":
            self._has_https = True

        if tag == "title":
            self._in_title = True
            self._current_text = ""

        elif tag == "meta":
            name = attrs_dict.get("name", "").lower()
            prop = attrs_dict.get("property", "").lower()
            content = attrs_dict.get("content", "")

            if name == "description":
                self.meta_description = content
            elif name == "keywords":
                self.meta_keywords = content
            elif name == "viewport":
                self._has_viewport = True
            elif name == "robots":
                self._robots_meta = content
            elif name == "yandex-verification":
                self._yandex_verification = content
            elif prop.startswith("og:"):
                self.og_tags[prop] = content

        elif tag == "html":
            # Check for turbo-html attribute (Yandex Turbo pages)
            if "turbo" in attrs_dict.get("attributes", {}) or "turbo" in str(attrs):
                self._has_turbo = True

        elif tag == "link":
            rel = attrs_dict.get("rel", "")
            type_attr = attrs_dict.get("type", "").lower()
            href = attrs_dict.get("href", "")

            if "canonical" in rel:
                self._canonical = href

            # Check for YML feed (Yandex Market export)
            if "alternate" in rel and "xml" in type_attr and "yml" in href.lower():
                self._yml_feed = href

        elif tag in self.headings:
            self._in_heading = tag
            self._current_text = ""

        elif tag == "a":
            self._in_a = True
            self._current_text = ""
            href = attrs_dict.get("href", "")
            self.links.append({"href": href, "text": "", "attrs": attrs_dict})
            # Check for social links
            social_platforms = ["twitter.com", "x.com", "facebook.com", "linkedin.com",
                                "instagram.com", "youtube.com", "tiktok.com", "github.com"]
            for platform in social_platforms:
                if platform in href:
                    self.social_links.append({"platform": platform.split(".")[0], "url": href})

        elif tag == "img":
            self.images.append({
                "src": attrs_dict.get("src", ""),
                "alt": attrs_dict.get("alt", ""),
                "has_alt": "alt" in attrs_dict,
                "loading": attrs_dict.get("loading", "")
            })

        elif tag == "button":
            self._in_button = True
            self._current_text = ""

        elif tag == "form":
            self._in_form = True
            self._current_form = {
                "action": attrs_dict.get("action", ""),
                "method": attrs_dict.get("method", "GET").upper()
            }
            self._form_fields = []

        elif tag == "input" and self._in_form:
            self._form_fields.append({
                "type": attrs_dict.get("type", "text"),
                "name": attrs_dict.get("name", ""),
                "placeholder": attrs_dict.get("placeholder", ""),
                "required": "required" in attrs_dict
            })

        elif tag == "script":
            self._in_script = True
            self._script_type = attrs_dict.get("type", "")
            self._current_text = ""
            src = attrs_dict.get("src", "")
            if src:
                self.scripts.append(src)
                # Detect tracking scripts (Google)
                tracking_indicators = {
                    "gtag": "Google Analytics (gtag)",
                    "googletagmanager": "Google Tag Manager",
                    "google-analytics": "Google Analytics",
                    "analytics": "Analytics",
                    "fbevents": "Meta Pixel",
                    "facebook": "Meta/Facebook",
                    "snap.licdn": "LinkedIn Insight Tag",
                    "hotjar": "Hotjar",
                    "fullstory": "FullStory",
                    "mixpanel": "Mixpanel",
                    "amplitude": "Amplitude",
                    "segment": "Segment",
                    "hubspot": "HubSpot",
                    "intercom": "Intercom",
                    "crisp": "Crisp Chat",
                    "drift": "Drift",
                    "tiktok": "TikTok Pixel",
                    "clarity": "Microsoft Clarity"
                }
                src_lower = src.lower()
                for indicator, name in tracking_indicators.items():
                    if indicator in src_lower:
                        self.tracking_scripts.append(name)

                # Detect Yandex Metrica
                yandex_indicators = {
                    "mc.webvisor.com": "Yandex Metrica",
                    "top100": "Yandex Top100",
                    "metrika": "Yandex Metrica"
                }
                for indicator, name in yandex_indicators.items():
                    if indicator in src_lower:
                        # Extract counter ID from URL
                        match = re.search(r'counter[_-]?(\d+)', src_lower)
                        counter_id = match.group(1) if match else "unknown"
                        self._yandex_metrics.append({"name": name, "counter_id": counter_id})

    def handle_endtag(self, tag):
        if tag == "title":
            self._in_title = False
            self.title = self._current_text.strip()

        elif tag in self.headings and self._in_heading == tag:
            text = self._current_text.strip()
            if text:
                self.headings[tag].append(text)
            self._in_heading = None

        elif tag == "a" and self._in_a:
            self._in_a = False
            text = self._current_text.strip()
            if self.links:
                self.links[-1]["text"] = text
            # Detect CTAs
            cta_words = ["sign up", "get started", "try free", "start free", "buy now",
                         "subscribe", "join", "register", "download", "book", "schedule",
                         "request demo", "contact us", "learn more", "see pricing",
                         "start trial", "create account", "claim", "unlock"]
            text_lower = text.lower()
            for cta in cta_words:
                if cta in text_lower:
                    self.ctas.append({"text": text, "href": self.links[-1]["href"], "type": "link"})
                    break

        elif tag == "button" and self._in_button:
            self._in_button = False
            text = self._current_text.strip()
            if text:
                self.buttons.append(text)
                self.ctas.append({"text": text, "type": "button"})

        elif tag == "form" and self._in_form:
            self._in_form = False
            self._current_form["fields"] = self._form_fields
            self._current_form["field_count"] = len(self._form_fields)
            self.forms.append(self._current_form)

        elif tag == "script" and self._in_script:
            self._in_script = False
            script_content = self._current_text
            # Check for inline tracking
            if "gtag" in script_content or "dataLayer" in script_content:
                if "Google Analytics" not in self.tracking_scripts and "Google Tag Manager" not in self.tracking_scripts:
                    self.tracking_scripts.append("Google Analytics/GTM (inline)")
            if "fbq" in script_content:
                if "Meta Pixel" not in self.tracking_scripts:
                    self.tracking_scripts.append("Meta Pixel (inline)")
            # Check for inline Yandex Metrica
            if "metrika" in script_content.lower() and "wa" in script_content:
                if not self._yandex_metrics:
                    self._yandex_metrics.append({"name": "Yandex Metrica (inline)", "counter_id": "inline"})
            # Check for JSON-LD schema
            if self._script_type == "application/ld+json":
                try:
                    schema = json.loads(script_content)
                    if isinstance(schema, list):
                        self.schema_data.extend(schema)
                    else:
                        self.schema_data.append(schema)
                except (json.JSONDecodeError, ValueError):
                    pass

    def handle_data(self, data):
        if self._in_title or self._in_heading or self._in_a or self._in_button or self._in_script:
            self._current_text += data
        self._text_content.append(data)

    def get_full_text(self):
        return " ".join(self._text_content)

    def get_results(self):
        """Compile all findings into a structured result."""
        # Count images without alt text
        images_without_alt = sum(1 for img in self.images if not img.get("has_alt") or not img.get("alt"))
        images_with_lazy = sum(1 for img in self.images if img.get("loading") == "lazy")

        # Analyze heading hierarchy
        heading_issues = []
        if not self.headings["h1"]:
            heading_issues.append("Missing H1 tag")
        elif len(self.headings["h1"]) > 1:
            heading_issues.append(f"Multiple H1 tags ({len(self.headings['h1'])})")
        if self.headings["h3"] and not self.headings["h2"]:
            heading_issues.append("H3 used without H2 (skipped level)")

        # Unique tracking tools
        tracking = list(set(self.tracking_scripts))

        # Full text for word count
        full_text = self.get_full_text()
        word_count = len(full_text.split())

        # Check if page uses HTTPS
        page_uses_https = self._has_https or self._canonical.lower().startswith("https")

        return {
            "seo": {
                "title": self.title,
                "title_length": len(self.title),
                "title_ok": 30 <= len(self.title) <= 60,
                "meta_description": self.meta_description,
                "meta_description_length": len(self.meta_description),
                "meta_description_ok": 120 <= len(self.meta_description) <= 160,
                "canonical": self._canonical,
                "robots_meta": self._robots_meta,
                "has_viewport": self._has_viewport,
                "og_tags": self.og_tags,
                "headings": {k: v for k, v in self.headings.items() if v},
                "heading_issues": heading_issues,
                "images_total": len(self.images),
                "images_without_alt": images_without_alt,
                "images_with_lazy_loading": images_with_lazy
            },
            "yandex": {
                "yandex_verification": self._yandex_verification,
                "has_turbo_pages": self._has_turbo,
                "yml_feed": self._yml_feed,
                "yandex_metrics_installed": len(self._yandex_metrics) > 0,
                "yandex_metrics": self._yandex_metrics
            },
            "content": {
                "word_count": word_count,
                "headings_count": sum(len(v) for v in self.headings.values()),
                "h1": self.headings["h1"],
                "h2": self.headings["h2"]
            },
            "conversion": {
                "ctas": self.ctas[:20],
                "cta_count": len(self.ctas),
                "forms": self.forms,
                "form_count": len(self.forms),
                "buttons": self.buttons[:20]
            },
            "trust": {
                "social_links": self.social_links,
                "social_link_count": len(self.social_links)
            },
            "tracking": {
                "tools_detected": tracking,
                "tools_count": len(tracking),
                "schema_types": [s.get("@type", "Unknown") for s in self.schema_data],
                "schema_count": len(self.schema_data)
            },
            "technical": {
                "total_links": len(self.links),
                "internal_links": 0,
                "external_links": 0,
                "scripts_count": len(self.scripts),
                "uses_https": page_uses_https
            }
        }


def fetch_page(url):
    """Fetch a webpage and return its HTML content."""
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
    }

    req = urllib.request.Request(url, headers=headers)
    try:
        response = urllib.request.urlopen(req, timeout=15, context=ctx)
        return response.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        return None
    except Exception as e:
        return None


def fetch_robots_txt(url):
    """Fetch and parse robots.txt."""
    parsed = urlparse(url)
    robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
    content = fetch_page(robots_url)
    if content:
        has_sitemap = "sitemap:" in content.lower()
        return {"exists": True, "has_sitemap_reference": has_sitemap, "content_preview": content[:500]}
    return {"exists": False}


def fetch_sitemap(url):
    """Check if sitemap.xml exists."""
    parsed = urlparse(url)
    sitemap_url = f"{parsed.scheme}://{parsed.netloc}/sitemap.xml"
    try:
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        req = urllib.request.Request(sitemap_url, headers={"User-Agent": "MarketingBot/1.0"})
        response = urllib.request.urlopen(req, timeout=10, context=ctx)
        content = response.read().decode("utf-8", errors="replace")
        url_count = content.lower().count("<url>") or content.lower().count("<loc>")
        return {"exists": True, "url_count": url_count}
    except:
        return {"exists": False, "url_count": 0}


def calculate_google_score(page_results):
    """
    Calculate Google SEO Score (0-10 scale)
    Based on standard on-page SEO factors.
    """
    score = 10
    seo = page_results["seo"]

    if not seo["title"]:
        score -= 3
    elif not seo["title_ok"]:
        score -= 1

    if not seo["meta_description"]:
        score -= 3
    elif not seo["meta_description_ok"]:
        score -= 1

    if not seo["headings"].get("h1"):
        score -= 2

    if seo["images_without_alt"] > 0:
        score -= min(2, seo["images_without_alt"])

    if seo["heading_issues"]:
        score -= 1

    if not seo["has_viewport"]:
        score -= 1

    return max(0, score)


def calculate_yandex_score(page_results):
    """
    Calculate Yandex SEO Score (0-10 scale)
    Based on Yandex-specific ranking factors.

    Scoring:
    - Title Tag: -2 if missing/poor
    - Meta Description: -0.5 if missing/poor
    - Heading hierarchy: -1 if issues
    - Images without alt: -0.5
    - URL not human-readable: -1
    - No internal links: -1
    - No Yandex tools (Metrica + Verification): -1
    - No Turbo pages: -1
    - No Schema.org: -1
    - No HTTPS: -1

    Total: 10 points max
    """
    score = 10
    seo = page_results["seo"]
    yandex = page_results["yandex"]
    tech = page_results["technical"]

    # Title Tag
    if not seo["title"]:
        score -= 2
    elif not seo["title_ok"]:
        score -= 0.5

    # Meta Description
    if not seo["meta_description"]:
        score -= 0.5
    elif not seo["meta_description_ok"]:
        score -= 0.25

    # Heading hierarchy
    if not seo["headings"].get("h1"):
        score -= 1
    elif seo["heading_issues"]:
        score -= 0.5

    # Images without alt
    if seo["images_without_alt"] > 0:
        score -= min(0.5, seo["images_without_alt"] * 0.25)

    # URL not human-readable (check for Cyrillic, parameters)
    canonical_url = seo.get("canonical", "")
    if canonical_url:
        # Check for Cyrillic characters
        if re.search(r'[\u0400-\u04FF]', canonical_url):
            score -= 0.5
        # Check for excessive parameters
        if "?" in canonical_url and canonical_url.count("&") > 2:
            score -= 0.5
    else:
        score -= 0.5

    # Internal links
    if tech["internal_links"] == 0:
        score -= 1

    # Yandex tools (Metrica + Webmaster verification)
    has_metrica = yandex["yandex_metrics_installed"]
    has_verification = bool(yandex["yandex_verification"])
    if not has_metrica and not has_verification:
        score -= 1
    elif not has_metrica or not has_verification:
        score -= 0.5

    # Turbo pages
    if not yandex["has_turbo_pages"]:
        score -= 1

    # Schema.org
    if page_results["tracking"]["schema_count"] == 0:
        score -= 1

    # HTTPS
    if not tech.get("uses_https", False):
        score -= 1

    return max(0, score)


def calculate_combined_score(google_score, yandex_score, google_weight=0.30, yandex_weight=0.70):
    """
    Calculate combined SEO score based on market weights.
    Default: 30% Google, 70% Yandex (for Russia)
    """
    return round(google_score * google_weight + yandex_score * yandex_weight, 1)


def analyze(url):
    """Run full marketing analysis on a URL."""
    results = {"url": url, "status": "success"}

    html = fetch_page(url)
    if not html:
        return {"url": url, "status": "error", "message": "Could not fetch page"}

    parser = MarketingPageParser()
    try:
        parser.feed(html)
    except Exception as e:
        return {"url": url, "status": "error", "message": f"Parse error: {str(e)}"}

    page_results = parser.get_results()

    # Count internal vs external links
    parsed_url = urlparse(url)
    domain = parsed_url.netloc
    internal = 0
    external = 0
    for link in parser.links:
        href = link.get("href", "")
        if href.startswith("/") or domain in href:
            internal += 1
        elif href.startswith("http"):
            external += 1
    page_results["technical"]["internal_links"] = internal
    page_results["technical"]["external_links"] = external

    # Check robots.txt and sitemap
    page_results["robots"] = fetch_robots_txt(url)
    page_results["sitemap"] = fetch_sitemap(url)

    # Generate marketing scores
    scores = {}

    # SEO Scores (Google + Yandex)
    scores["google_seo"] = calculate_google_score(page_results)
    scores["yandex_seo"] = calculate_yandex_score(page_results)
    scores["seo_combined"] = calculate_combined_score(scores["google_seo"], scores["yandex_seo"])

    # CTA Score
    cta_score = 5
    conv = page_results["conversion"]
    if conv["cta_count"] == 0:
        cta_score = 1
    elif conv["cta_count"] >= 2:
        cta_score = 7
    if conv["cta_count"] >= 4:
        cta_score = 8
    value_ctas = [c for c in conv["ctas"] if len(c.get("text", "")) > 10]
    if value_ctas:
        cta_score = min(10, cta_score + 1)
    scores["cta"] = cta_score

    # Trust Score
    trust_score = 5
    if page_results["trust"]["social_link_count"] >= 3:
        trust_score += 2
    elif page_results["trust"]["social_link_count"] >= 1:
        trust_score += 1
    if page_results["tracking"]["schema_count"] > 0:
        trust_score += 1
    scores["trust"] = min(10, trust_score)

    # Tracking Score
    track_score = 3
    if page_results["tracking"]["tools_count"] >= 3:
        track_score = 9
    elif page_results["tracking"]["tools_count"] >= 2:
        track_score = 7
    elif page_results["tracking"]["tools_count"] >= 1:
        track_score = 5
    scores["tracking"] = track_score

    page_results["scores"] = scores

    # Overall score (average of all scores except combined)
    main_scores = [scores["google_seo"], scores["yandex_seo"], scores["cta"], scores["trust"], scores["tracking"]]
    page_results["overall_score"] = round(sum(main_scores) / len(main_scores), 1)

    results["analysis"] = page_results
    return results


def main():
    if len(sys.argv) < 2:
        print(json.dumps({
            "usage": "python3 analyze_page.py <url>",
            "example": "python3 analyze_page.py https://calendly.com",
            "description": "Analyzes a webpage for marketing effectiveness (Google + Yandex SEO)"
        }, indent=2))
        return

    url = sys.argv[1]
    if not url.startswith("http"):
        url = "https://" + url

    results = analyze(url)
    print(json.dumps(results, indent=2, default=str))


if __name__ == "__main__":
    main()