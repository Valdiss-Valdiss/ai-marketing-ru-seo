#!/usr/bin/env python3
"""
Marketing Page Analyzer — Utility script for AI Marketing Claude Code Skills
Analyzes a webpage for marketing effectiveness: SEO elements, content structure,
trust signals, CTAs, social proof, and conversion optimization indicators.

Supports both Google and Yandex SEO analysis with combined scoring (0-20 scale).
"""

import sys
import json
import re
import urllib.request
import urllib.error
import ssl
from html.parser import HTMLParser
from urllib.parse import urlparse, urljoin
from datetime import datetime


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

        # Commercial markers (new for 0-20 scoring)
        self._commercial_markers = {
            "phones": [],
            "emails": [],
            "addresses": [],
            "inn_ogrn": []
        }

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

        # For collecting all text (including outside tags)
        self._all_text_for_matching = ""

    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)
        self._current_tag = tag
        self._current_attrs = attrs_dict

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
            if "turbo" in attrs_dict.get("attributes", {}) or "turbo" in str(attrs):
                self._has_turbo = True

        elif tag == "link":
            rel = attrs_dict.get("rel", "")
            type_attr = attrs_dict.get("type", "").lower()
            href = attrs_dict.get("href", "")

            if "canonical" in rel:
                self._canonical = href

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
                self._detect_tracking_scripts(src)

    def _detect_tracking_scripts(self, src):
        """Detect Google and Yandex tracking scripts."""
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

        yandex_indicators = {
            "mc.webvisor.com": "Yandex Metrica",
            "top100": "Yandex Top100",
            "metrika": "Yandex Metrica"
        }
        for indicator, name in yandex_indicators.items():
            if indicator in src_lower:
                match = re.search(r'counter[_-]?(\d+)', src_lower)
                counter_id = match.group(1) if match else "unknown"
                self._yandex_metrics.append({"name": name, "counter_id": counter_id})

    def _detect_commercial_markers(self, text):
        """Detect commercial markers: phones, emails, addresses, INN/OGRN."""
        phone_patterns = [
            r'8\s*\(?\s*\d{3}\s*\)?\s*\d{3}\s*[-–]?\s*\d{2}\s*[-–]?\s*\d{2}',
            r'8\s*\d{10}',
            r'\+7\s*\(?\s*\d{3}\s*\)?\s*\d{3}\s*[-–]?\s*\d{2}\s*[-–]?\s*\d{2}',
            r'8-800-\d{3}-\d{2}-\d{2}',
            r'8‑800‑\d{3}‑\d{2}‑\d{2}',
        ]
        for pattern in phone_patterns:
            phones = re.findall(pattern, text)
            self._commercial_markers["phones"].extend(phones)

        email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        emails = re.findall(email_pattern, text)
        self._commercial_markers["emails"].extend(emails)

        inn_pattern = r'\bИНН\s*\d{10,12}\b'
        inn_matches = re.findall(inn_pattern, text, re.IGNORECASE)
        self._commercial_markers["inn_ogrn"].extend(inn_matches)

        ogrn_pattern = r'\bОГРН\s*\d{13,15}\b'
        ogrn_matches = re.findall(ogrn_pattern, text, re.IGNORECASE)
        self._commercial_markers["inn_ogrn"].extend(ogrn_matches)

        address_patterns = [
            r'\d{6},?\s*[г|G|г\.]\s*[а-яА-Я]+\.?',
            r'[г|G][\.\s]+[а-яА-Я]+,?\s*[ул\.?|пер\.?|пр\.?][\s]+[а-яА-Я]+',
        ]
        for pattern in address_patterns:
            addresses = re.findall(pattern, text)
            self._commercial_markers["addresses"].extend(addresses)

    def handle_endtag(self, tag):
        if tag == "title":
            self._in_title = False
            self.title = self._current_text.strip()
            self._all_text_for_matching += " " + self._current_text

        elif tag in self.headings and self._in_heading == tag:
            text = self._current_text.strip()
            if text:
                self.headings[tag].append(text)
                self._all_text_for_matching += " " + text
            self._in_heading = None

        elif tag == "a" and self._in_a:
            self._in_a = False
            text = self._current_text.strip()
            if self.links:
                self.links[-1]["text"] = text
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
            if "gtag" in script_content or "dataLayer" in script_content:
                if "Google Analytics" not in self.tracking_scripts and "Google Tag Manager" not in self.tracking_scripts:
                    self.tracking_scripts.append("Google Analytics/GTM (inline)")
            if "fbq" in script_content:
                if "Meta Pixel" not in self.tracking_scripts:
                    self.tracking_scripts.append("Meta Pixel (inline)")
            if "metrika" in script_content.lower() and "wa" in script_content:
                if not self._yandex_metrics:
                    self._yandex_metrics.append({"name": "Yandex Metrica (inline)", "counter_id": "inline"})
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
        self._all_text_for_matching += data

    def get_full_text(self):
        return " ".join(self._text_content)

    def get_results(self):
        """Compile all findings into a structured result."""
        images_without_alt = sum(1 for img in self.images if not img.get("has_alt") or not img.get("alt"))
        images_with_lazy = sum(1 for img in self.images if img.get("loading") == "lazy")

        heading_issues = []
        if not self.headings["h1"]:
            heading_issues.append("Missing H1 tag")
        elif len(self.headings["h1"]) > 1:
            heading_issues.append(f"Multiple H1 tags ({len(self.headings['h1'])})")
        if self.headings["h3"] and not self.headings["h2"]:
            heading_issues.append("H3 used without H2 (skipped level)")

        tracking = list(set(self.tracking_scripts))
        full_text = self.get_full_text()
        word_count = len(full_text.split())

        page_uses_https = self._has_https or self._canonical.lower().startswith("https")

        # Deduplicate commercial markers
        for key in self._commercial_markers:
            self._commercial_markers[key] = list(set(self._commercial_markers[key]))

        # Check robots meta for noindex
        has_noindex = "noindex" in self._robots_meta.lower() if self._robots_meta else False

        # Check if canonical points to self
        parsed_url = urlparse(self._canonical) if self._canonical else None
        canonical_is_self = False
        if parsed_url and parsed_url.path:
            canonical_is_self = parsed_url.path.rstrip('/') == parsed_url.path.rstrip('/')

        return {
            "seo": {
                "title": self.title,
                "title_length": len(self.title),
                "title_ok": 30 <= len(self.title) <= 70,
                "title_different_from_h1": self.title != (self.headings["h1"][0] if self.headings["h1"] else ""),
                "meta_description": self.meta_description,
                "meta_description_length": len(self.meta_description),
                "meta_description_ok": 50 <= len(self.meta_description) <= 155,
                "canonical": self._canonical,
                "canonical_points_to_self": canonical_is_self,
                "robots_meta": self._robots_meta,
                "has_noindex": has_noindex,
                "has_viewport": self._has_viewport,
                "og_tags": self.og_tags,
                "headings": {k: v for k, v in self.headings.items() if v},
                "heading_issues": heading_issues,
                "images_total": len(self.images),
                "images_without_alt": images_without_alt,
                "images_with_alt": len(self.images) - images_without_alt,
                "images_with_lazy_loading": images_with_lazy
            },
            "yandex": {
                "yandex_verification": self._yandex_verification,
                "has_turbo_pages": self._has_turbo,
                "yml_feed": self._yml_feed,
                "yandex_metrics_installed": len(self._yandex_metrics) > 0,
                "yandex_metrics": self._yandex_metrics
            },
            "commercial": {
                "markers_found": self._commercial_markers,
                "phones_count": len(self._commercial_markers["phones"]),
                "emails_count": len(self._commercial_markers["emails"]),
                "addresses_count": len(self._commercial_markers["addresses"]),
                "inn_ogrn_count": len(self._commercial_markers["inn_ogrn"])
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
    Calculate Google SEO Score (0-20 scale)
    Based on 8 factors, sum = 20.

    Factor                 Max   Description
    ─────────────────────────────────────────────────
    Indexability           4    noindex check, canonical self-reference
    Title Tag             3    presence + length 30-70 + different from H1
    H1 Tag                3    presence + strictly 1 on page
    Schema.org / JSON-LD  3    presence of markup
    Meta Description      2    presence + length up to 155
    Mobile Viewport       2    <meta name="viewport"...>
    Images Alt            2    ratio of img with alt to total
    HTTPS                 1    protocol check
    """
    seo = page_results["seo"]
    tracking = page_results["tracking"]

    # Factor 1: Indexability (4 points max)
    indexability_score = 0
    if seo["has_noindex"]:
        indexability_score = 0
    elif not seo["canonical"]:
        indexability_score = 2
    elif not seo["canonical_points_to_self"]:
        indexability_score = 1
    else:
        indexability_score = 4

    # Factor 2: Title Tag (3 points max)
    title_score = 0
    if seo["title"]:
        if seo["title_ok"]:
            if seo.get("title_different_from_h1", True):
                title_score = 3
            else:
                title_score = 2
        else:
            title_score = 1
    else:
        title_score = 0

    # Factor 3: H1 Tag (3 points max)
    h1_score = 0
    h1_list = seo["headings"].get("h1", [])
    if not h1_list:
        h1_score = 0
    elif len(h1_list) == 1:
        h1_score = 3
    else:
        h1_score = 1

    # Factor 4: Schema.org / JSON-LD (3 points max)
    schema_score = 0
    if tracking["schema_count"] > 0:
        schema_score = 3
    else:
        schema_score = 0

    # Factor 5: Meta Description (2 points max)
    desc_score = 0
    if seo["meta_description"]:
        if seo["meta_description_ok"]:
            desc_score = 2
        else:
            desc_score = 1
    else:
        desc_score = 0

    # Factor 6: Mobile Viewport (2 points max)
    viewport_score = 2 if seo["has_viewport"] else 0

    # Factor 7: Images Alt (2 points max)
    images_score = 0
    total_images = seo["images_total"]
    if total_images > 0:
        images_with_alt = seo["images_with_alt"]
        ratio = images_with_alt / total_images
        if ratio >= 0.8:
            images_score = 2
        elif ratio >= 0.5:
            images_score = 1
        else:
            images_score = 0
    else:
        images_score = 2

    # Factor 8: HTTPS (1 point max)
    https_score = 1 if page_results["technical"]["uses_https"] else 0

    total = indexability_score + title_score + h1_score + schema_score + desc_score + viewport_score + images_score + https_score

    return {
        "score": total,
        "max": 20,
        "breakdown": {
            "indexability": {"score": indexability_score, "max": 4, "current": "noindex" if seo["has_noindex"] else ("missing" if not seo["canonical"] else ("ok" if seo["canonical_points_to_self"] else "points elsewhere"))},
            "title": {"score": title_score, "max": 3, "current": f'"{seo["title"]}" ({seo["title_length"]} chars)' if seo["title"] else "missing"},
            "h1": {"score": h1_score, "max": 3, "current": f'{len(h1_list)} H1 found' if h1_list else "missing"},
            "schema": {"score": schema_score, "max": 3, "current": f'{tracking["schema_count"]} schema(s) found'},
            "meta_description": {"score": desc_score, "max": 2, "current": f'"{seo["meta_description"][:50]}..." ({seo["meta_description_length"]} chars)' if seo["meta_description"] else "missing"},
            "viewport": {"score": viewport_score, "max": 2, "current": "present" if seo["has_viewport"] else "missing"},
            "images_alt": {"score": images_score, "max": 2, "current": f'{seo["images_with_alt"]}/{total_images} with alt'},
            "https": {"score": https_score, "max": 1, "current": "HTTPS" if page_results["technical"]["uses_https"] else "HTTP"}
        }
    }


def calculate_yandex_score(page_results):
    """
    Calculate Yandex SEO Score (0-20 scale)
    Based on 8 factors, sum = 20.

    Factor                    Max   Description
    ─────────────────────────────────────────────────
    Commercial markers        4    Phones, emails, INN/OGRN, addresses via Regex
    Title Tag                 3    presence + length
    H1 Tag                    3    presence + uniqueness
    Indexability              3    noindex + canonical
    Micro markup (OG/Schema)  3    og: tags + Schema
    Counters (Metrica/Webmaster) 2  mc.yandex.ru, yandex-verification
    Meta Description          1    presence (low weight)
    HTTPS                     1    protocol
    """
    seo = page_results["seo"]
    yandex = page_results["yandex"]
    commercial = page_results["commercial"]
    tracking = page_results["tracking"]

    # Factor 1: Commercial markers (4 points max)
    commercial_score = 0
    marker_count = commercial["phones_count"] + commercial["emails_count"] + commercial["addresses_count"] + commercial["inn_ogrn_count"]
    if marker_count >= 4:
        commercial_score = 4
    elif marker_count >= 2:
        commercial_score = 2
    elif marker_count >= 1:
        commercial_score = 1

    # Factor 2: Title Tag (3 points max)
    title_score = 0
    if seo["title"]:
        if seo["title_ok"]:
            title_score = 3
        elif 10 <= seo["title_length"] <= 80:
            title_score = 2
        else:
            title_score = 1
    else:
        title_score = 0

    # Factor 3: H1 Tag (3 points max)
    h1_score = 0
    h1_list = seo["headings"].get("h1", [])
    if not h1_list:
        h1_score = 0
    elif len(h1_list) == 1:
        h1_score = 3
    else:
        h1_score = 1

    # Factor 4: Indexability (3 points max)
    indexability_score = 0
    if seo["has_noindex"]:
        indexability_score = 0
    elif not seo["canonical"]:
        indexability_score = 1
    elif not seo["canonical_points_to_self"]:
        indexability_score = 1
    else:
        indexability_score = 3

    # Factor 5: Micro markup (OG + Schema) (3 points max)
    markup_score = 0
    og_count = len(seo["og_tags"])
    schema_count = tracking["schema_count"]
    if og_count >= 3 and schema_count > 0:
        markup_score = 3
    elif og_count >= 1 or schema_count > 0:
        markup_score = 2

    # Factor 6: Yandex counters (2 points max)
    counters_score = 0
    has_metrica = yandex["yandex_metrics_installed"]
    has_verification = bool(yandex["yandex_verification"])
    if has_metrica and has_verification:
        counters_score = 2
    elif has_metrica or has_verification:
        counters_score = 1

    # Factor 7: Meta Description (1 point max)
    desc_score = 1 if seo["meta_description"] else 0

    # Factor 8: HTTPS (1 point max)
    https_score = 1 if page_results["technical"]["uses_https"] else 0

    total = commercial_score + title_score + h1_score + indexability_score + markup_score + counters_score + desc_score + https_score

    return {
        "score": total,
        "max": 20,
        "breakdown": {
            "commercial_markers": {
                "score": commercial_score,
                "max": 4,
                "current": f'phones:{commercial["phones_count"]}, emails:{commercial["emails_count"]}, addrs:{commercial["addresses_count"]}, inn/ogrn:{commercial["inn_ogrn_count"]}'
            },
            "title": {"score": title_score, "max": 3, "current": f'"{seo["title"]}" ({seo["title_length"]} chars)' if seo["title"] else "missing"},
            "h1": {"score": h1_score, "max": 3, "current": f'{len(h1_list)} H1 found' if h1_list else "missing"},
            "indexability": {"score": indexability_score, "max": 3, "current": "noindex" if seo["has_noindex"] else ("missing" if not seo["canonical"] else "ok")},
            "micro_markup": {"score": markup_score, "max": 3, "current": f'OG:{og_count}, Schema:{schema_count}'},
            "counters": {"score": counters_score, "max": 2, "current": f'metrica:{"yes" if has_metrica else "no"}, verification:{"yes" if has_verification else "no"}'},
            "meta_description": {"score": desc_score, "max": 1, "current": "present" if seo["meta_description"] else "missing"},
            "https": {"score": https_score, "max": 1, "current": "HTTPS" if page_results["technical"]["uses_https"] else "HTTP"}
        }
    }


def calculate_combined_score(google_score, yandex_score, google_weight=0.30, yandex_weight=0.70):
    """
    Calculate combined SEO score based on market weights.
    Default: 30% Google, 70% Yandex (for Russia)
    """
    return round(google_score * google_weight + yandex_score * yandex_weight, 1)


def analyze(url):
    """Run full marketing analysis on a URL."""
    results = {"url": url, "status": "success", "timestamp": datetime.now().isoformat()}

    html = fetch_page(url)
    if not html:
        return {"url": url, "status": "error", "message": "Could not fetch page"}

    parser = MarketingPageParser()
    try:
        parser.feed(html)
    except Exception as e:
        return {"url": url, "status": "error", "message": f"Parse error: {str(e)}"}

    page_results = parser.get_results()

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

    page_results["robots"] = fetch_robots_txt(url)
    page_results["sitemap"] = fetch_sitemap(url)

    scores = {}

    google_result = calculate_google_score(page_results)
    yandex_result = calculate_yandex_score(page_results)

    scores["google_seo"] = google_result["score"]
    scores["google_seo_max"] = google_result["max"]
    scores["google_seo_breakdown"] = google_result["breakdown"]

    scores["yandex_seo"] = yandex_result["score"]
    scores["yandex_seo_max"] = yandex_result["max"]
    scores["yandex_seo_breakdown"] = yandex_result["breakdown"]

    scores["seo_combined"] = calculate_combined_score(scores["google_seo"], scores["yandex_seo"])

    page_results["scores"] = scores

    results["analysis"] = page_results
    return results


def main():
    if len(sys.argv) < 2:
        print(json.dumps({
            "usage": "python3 analyze_page.py <url>",
            "example": "python3 analyze_page.py https://example.com",
            "description": "Analyzes webpage for Google + Yandex SEO (0-20 scale)"
        }, indent=2))
        return

    url = sys.argv[1]
    if not url.startswith("http"):
        url = "https://" + url

    results = analyze(url)
    print(json.dumps(results, indent=2, default=str))


if __name__ == "__main__":
    main()