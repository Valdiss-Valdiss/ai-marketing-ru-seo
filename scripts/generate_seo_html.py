#!/usr/bin/env python3
"""
Generate SEO Audit HTML Report — AI Marketing Claude Code Skills
Creates professional HTML report with open4.dev styling.
"""

import sys
import json
import os
from datetime import datetime
from urllib.parse import urlparse


def extract_keywords(h1_list, h2_list, title):
    """Извлекает ключевые слова из заголовков и title."""
    stop_words = {'для', 'все', 'наши', 'компания', 'наш', 'это', 'и', 'в', 'по', 'с', 'не', 'что', 'как', 'где', 'когда', 'зачем', 'это', '—', '-', '|', '/', '\\', '\u2014', '\u2013'}
    all_words = []
    for text in h1_list + h2_list + [title]:
        if not text:
            continue
        words = text.lower().split()
        all_words.extend([
            w.strip('.,!?:;()[]{}"\'/\\') 
            for w in words 
            if len(w) > 4 and w.lower() not in stop_words
        ])
    result = list(set(all_words))[:5]
    return result


def detect_business_type(schema_types, url):
    """Определяет тип бизнеса по Schema.org и URL."""
    schema_str = ' '.join(schema_types).lower()
    url_lower = url.lower()

    if any(x in schema_str for x in ['localbusiness', 'store', 'retail', 'shop', 'postaladdress']):
        return "e-commerce"
    if any(x in schema_str for x in ['professionalservice', 'service']):
        return "services"
    if any(x in schema_str for x in ['softwareapplication', 'webapplication']):
        return "saas"
    if any(x in url_lower for x in ['/shop/', '/catalog/', '/store/', '/tovary/', '/products/']):
        return "e-commerce"
    if any(x in url_lower for x in ['/service/', '/uslugi/', '/services/']):
        return "services"
    return "general"


def generate_title_recommendation(current_title, domain, keywords, business_type):
    """Генерирует рекомендуемый Title на основе анализа."""
    if not current_title:
        primary_keyword = keywords[0] if keywords else "Главная"
        return f"<title>{primary_keyword} | {domain}</title>"
    
    title_stripped = current_title.strip()
    
    if len(title_stripped) < 45:
        if keywords:
            return f"<title>{title_stripped} — {keywords[0]} в {domain.replace('www.', '')}</title>"
        return f"<title>{title_stripped} | {domain}</title>"
    
    if len(title_stripped) > 70:
        return f"<title>{title_stripped[:60]}... | {domain}</title>"
    
    return f"<title>{title_stripped} | {domain}</title>"


def generate_meta_recommendation(current_meta, keywords, business_type):
    """Генерирует рекомендуемый Meta Description на основе анализа."""
    if not current_meta:
        kw = ', '.join(keywords[:3]) if keywords else 'описание'
        return f"<meta name='description' content='[Ваше краткое описание с ключевыми словами: {kw}]'>"
    
    meta_stripped = current_meta.strip()
    if len(meta_stripped) < 100:
        suffix = ""
        if keywords:
            suffix = f" {keywords[0].capitalize()}."
        return f"<meta name='description' content='{meta_stripped}{suffix}'>"
    
    if len(meta_stripped) > 160:
        return f"<meta name='description' content='{meta_stripped[:155]}...'>"
    
    return f"<meta name='description' content='{meta_stripped}'>"


def generate_h1_recommendation(h1_list, keywords, business_type):
    """Генерирует рекомендуемый H1 на основе анализа."""
    if h1_list and h1_list[0]:
        return f"<h1>{h1_list[0]}</h1>"

    if keywords:
        primary_keyword = keywords[0].capitalize()
        return f"<h1>{primary_keyword}</h1>"

    return "<h1>[Основной заголовок страницы]</h1>"


def build_recommendations_data(url, analysis):
    """
    Единый источник всех рекомендаций на основе анализа.
    Используется и для Section 03, и для Section 04.
    """
    seo = analysis.get("seo", {})
    tracking = analysis.get("tracking", {})
    content = analysis.get("content", {})
    
    current_title = seo.get("title", "")
    current_meta = seo.get("meta_description", "")
    h1_list = content.get("h1", [])
    h2_list = content.get("h2", [])
    schema_types = tracking.get("schema_types", [])
    domain = urlparse(url).netloc
    
    keywords = extract_keywords(h1_list, h2_list, current_title)
    business_type = detect_business_type(schema_types, url)
    
    title_recommended = generate_title_recommendation(current_title, domain, keywords, business_type)
    meta_recommended = generate_meta_recommendation(current_meta, keywords, business_type)
    h1_recommended = generate_h1_recommendation(h1_list, keywords, business_type)
    
    return {
        "url": url,
        "domain": domain,
        "business_type": business_type,
        "keywords": keywords,
        "current": {
            "title": current_title,
            "meta_description": current_meta,
            "h1": h1_list,
            "h2": h2_list,
        },
        "recommended": {
            "title": title_recommended,
            "meta_description": meta_recommended,
            "h1": h1_recommended,
        }
    }


def get_score_color(score, max_score):
    """Return color class based on score percentage."""
    percentage = (score / max_score) * 100 if max_score > 0 else 0
    if percentage >= 70:
        return "success"
    elif percentage >= 40:
        return "warning"
    else:
        return "danger"


def escape_html(text):
    """Escape HTML special characters."""
    if not isinstance(text, str):
        text = str(text)
    return (text
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
            .replace("'", "&#39;"))


def truncate(text, length=50):
    """Truncate text and add ellipsis."""
    if not text:
        return ""
    text = str(text)
    if len(text) > length:
        return text[:length] + "..."
    return text


def format_current(current):
    """Format current value for display."""
    if not current:
        return "—"
    current_str = str(current)
    if len(current_str) > 80:
        return current_str[:80] + "..."
    return current_str


def get_status_icon_and_text(score, max_score):
    """Return status icon and text based on score ratio."""
    if max_score == 0:
        return "❌", "Не пройдено"
    ratio = score / max_score
    if ratio >= 0.8:
        return "✅", "Хорошо"
    elif ratio >= 0.5:
        return "⚠️", "Требует работы"
    else:
        return "❌", "Не пройдено"


def get_timestamp_filename(url, prefix="SEO-AUDIT"):
    """Generate filename with timestamp."""
    parsed = urlparse(url)
    domain = parsed.netloc.replace(".", "-")
    timestamp = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    return f"{prefix}-{domain}-{timestamp}"


def generate_checklist_section(analysis, url):
    """Generate Section 3: On-Page SEO Checklist with subsections."""
    seo = analysis.get("seo", {})
    google_breakdown = analysis.get("scores", {}).get("google_seo_breakdown", {})
    yandex_breakdown = analysis.get("scores", {}).get("yandex_seo_breakdown", {})

    rec_data = build_recommendations_data(url, analysis)

    title = seo.get("title", "")
    title_length = seo.get("title_length", 0)
    meta_desc = seo.get("meta_description", "")
    meta_desc_length = seo.get("meta_description_length", 0)
    h1_list = analysis.get("content", {}).get("h1", [])
    h2_list = analysis.get("content", {}).get("h2", [])
    images_total = seo.get("images_total", 0)
    images_without_alt = seo.get("images_without_alt", 0)
    has_viewport = seo.get("has_viewport", False)
    og_tags = seo.get("og_tags", {})
    schema_count = analysis.get("tracking", {}).get("schema_count", 0)
    uses_https = analysis.get("technical", {}).get("uses_https", False)
    canonical = seo.get("canonical", "")
    canonical_self = seo.get("canonical_points_to_self", False)
    yandex_metrics = analysis.get("yandex", {}).get("yandex_metrics_installed", False)
    yandex_verification = analysis.get("yandex", {}).get("yandex_verification", "")
    has_turbo = analysis.get("yandex", {}).get("has_turbo_pages", False)

    def get_status_class(score, max_val):
        if max_val == 0:
            return "status-fail"
        ratio = score / max_val
        if ratio >= 0.7:
            return "status-pass"
        elif ratio >= 0.4:
            return "status-warn"
        else:
            return "status-fail"

    def get_icon_for_check(status_class):
        if status_class == "status-pass":
            return "✅"
        elif status_class == "status-warn":
            return "⚠️"
        else:
            return "❌"

    html = ""

    title_score = google_breakdown.get("title", {}).get("score", 0)
    title_max = google_breakdown.get("title", {}).get("max", 3)
    title_status = get_status_class(title_score, title_max)
    title_icon = get_icon_for_check(title_status)
    title_recommended = rec_data["recommended"]["title"]
    title_current = title if title else "(отсутствует)"
    has_keyword_in_title = any(kw.lower() in title.lower() for kw in rec_data["keywords"]) if title else False
    domain = rec_data["domain"]

    html += f'''<h4 style="margin: 0 0 15px; color: var(--tp-primary);">Title Tag</h4>
                            <div class="table-scroll-wrapper">
                                <table class="check-table">
                                    <thead>
                                        <tr>
                                            <th>Параметр</th>
                                            <th>Текущее</th>
                                            <th>Рекомендуемое</th>
                                            <th>Статус</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        <tr>
                                            <td>Текст</td>
                                            <td class="current-cell">{escape_html(truncate(title_current, 60))}</td>
                                            <td>{escape_html(truncate(title_recommended, 60))}</td>
                                            <td class="{title_status}">{title_icon}</td>
                                        </tr>
                                        <tr>
                                            <td>Длина</td>
                                            <td class="current-cell">{title_length} симв.</td>
                                            <td>50-60 симв.</td>
                                            <td class="{title_status}">{title_icon}</td>
                                        </tr>
                                        <tr>
                                            <td>Ключевое слово</td>
                                            <td class="current-cell">{"найдено" if has_keyword_in_title else "—"}</td>
                                            <td>{escape_html(rec_data["keywords"][0]) if rec_data["keywords"] else "определить из H1/H2"}</td>
                                            <td class="{"status-pass" if has_keyword_in_title else "status-fail"}">{"✅" if has_keyword_in_title else "❌"}</td>
                                        </tr>
                                        <tr>
                                            <td>Бренд в конце</td>
                                            <td class="current-cell">{"да" if domain in title else "—"}</td>
                                            <td>{escape_html(domain)}</td>
                                            <td class="{"status-pass" if domain in title else "status-fail"}">{"✅" if domain in title else "❌"}</td>
                                        </tr>
                                    </tbody>
                                </table>
                            </div>

    '''

    meta_score = google_breakdown.get("meta_description", {}).get("score", 0)
    meta_max = google_breakdown.get("meta_description", {}).get("max", 2)
    meta_status = get_status_class(meta_score, meta_max)
    meta_icon = get_icon_for_check(meta_status)
    meta_recommended = rec_data["recommended"]["meta_description"]
    meta_current = meta_desc if meta_desc else "(отсутствует)"
    has_cta_in_meta = any(cta in meta_desc.lower() for cta in ['оставьте', 'заказать', 'купить', 'подробнее', 'свяжитесь', 'напишите']) if meta_desc else False

    html += f'''<h4 style="margin: 25px 0 15px; color: var(--tp-primary);">Meta Description</h4>
                            <div class="table-scroll-wrapper">
                                <table class="check-table">
                                    <thead>
                                        <tr>
                                            <th>Параметр</th>
                                            <th>Текущее</th>
                                            <th>Рекомендуемое</th>
                                            <th>Статус</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        <tr>
                                            <td>Текст</td>
                                            <td class="current-cell">{"(пусто)" if not meta_desc else escape_html(truncate(meta_current, 60))}</td>
                                            <td>{escape_html(truncate(meta_recommended, 60))}</td>
                                            <td class="{meta_status}">{meta_icon}</td>
                                        </tr>
                                        <tr>
                                            <td>Длина</td>
                                            <td class="current-cell">{meta_desc_length} симв.</td>
                                            <td>140-160 симв.</td>
                                            <td class="{meta_status}">{meta_icon}</td>
                                        </tr>
                                        <tr>
                                            <td>CTA</td>
                                            <td class="current-cell">{"да" if has_cta_in_meta else "—"}</td>
                                            <td>"Оставьте заявку!"</td>
                                            <td class="{"status-pass" if has_cta_in_meta else "status-fail"}">{"✅" if has_cta_in_meta else "❌"}</td>
                                        </tr>
                                    </tbody>
                                </table>
                            </div>

    '''

    h1_score_g = google_breakdown.get("h1", {}).get("score", 0)
    h1_max_g = google_breakdown.get("h1", {}).get("max", 3)
    h1_status = get_status_class(h1_score_g, h1_max_g)
    h1_icon = get_icon_for_check(h1_status)
    h1_current = h1_list[0] if h1_list else "(отсутствует)"
    h1_recommended = rec_data["recommended"]["h1"]
    has_h1_keyword = any(kw.lower() in h1_current.lower() for kw in rec_data["keywords"]) if h1_current != "(отсутствует)" else False

    html += f'''<h4 style="margin: 25px 0 15px; color: var(--tp-primary);">Иерархия заголовков</h4>
                            <div class="table-scroll-wrapper">
                                <table class="check-table">
                                    <thead>
                                        <tr>
                                            <th>Элемент</th>
                                            <th>Текущее</th>
                                            <th>Рекомендуемое</th>
                                            <th>Статус</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        <tr>
                                            <td>H1</td>
                                            <td class="current-cell">{escape_html(truncate(h1_current, 60))}</td>
                                            <td>{escape_html(truncate(h1_recommended, 60))}</td>
                                            <td class="{h1_status}">{h1_icon}</td>
                                        </tr>
                                        <tr>
                                            <td>H2</td>
                                            <td class="current-cell">{" найдено".join(map(str, [len(h2_list)])) if h2_list else "(не найдены)"}</td>
                                            <td>Логическая структура под H1</td>
                                            <td class="status-fail">❌</td>
                                        </tr>
                                        <tr>
                                            <td>Всего заголовков</td>
                                            <td class="current-cell">{len(h1_list) + len(h2_list)}</td>
                                            <td>≥3-5 для структуры</td>
                                            <td class="status-fail">❌</td>
                                        </tr>
                                    </tbody>
                                </table>
                            </div>

    '''

    img_score = google_breakdown.get("images_alt", {}).get("score", 0)
    img_max = google_breakdown.get("images_alt", {}).get("max", 2)
    img_status = get_status_class(img_score, img_max)
    img_icon = get_icon_for_check(img_status)
    img_without_alt_pct = int((images_without_alt / images_total * 100) if images_total > 0 else 0)

    html += f'''<h4 style="margin: 25px 0 15px; color: var(--tp-primary);">Оптимизация изображений</h4>
                            <div class="table-scroll-wrapper">
                                <table class="check-table">
                                    <thead>
                                        <tr>
                                            <th>Параметр</th>
                                            <th>Текущее</th>
                                            <th>Рекомендуемое</th>
                                            <th>Статус</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        <tr>
                                            <td>Всего изображений</td>
                                            <td class="current-cell">{images_total}</td>
                                            <td>—</td>
                                            <td class="status-warn">⚠️</td>
                                        </tr>
                                        <tr>
                                            <td>Без alt</td>
                                            <td class="current-cell">{images_without_alt} ({img_without_alt_pct}%)</td>
                                            <td>0</td>
                                            <td class="{img_status}">{img_icon}</td>
                                        </tr>
                                        <tr>
                                            <td>WebP формат</td>
                                            <td class="current-cell">Не используется</td>
                                            <td>Да</td>
                                            <td class="status-fail">❌</td>
                                        </tr>
                                        <tr>
                                            <td>Lazy loading</td>
                                            <td class="current-cell">{seo.get("images_with_lazy_loading", 0)}</td>
                                            <td>Для внеэкранных</td>
                                            <td class="status-fail">❌</td>
                                        </tr>
                                    </tbody>
                                </table>
                            </div>

    '''

    https_score_g = google_breakdown.get("https", {}).get("score", 0)
    https_max_g = google_breakdown.get("https", {}).get("max", 1)
    https_status = get_status_class(https_score_g, https_max_g)
    https_icon = get_icon_for_check(https_status)
    https_current = "HTTPS" if uses_https else "HTTP"

    html += f'''<h4 style="margin: 25px 0 15px; color: var(--tp-primary);">Технические факторы</h4>
                            <div class="table-scroll-wrapper">
                                <table class="check-table">
                                    <thead>
                                        <tr>
                                            <th>Параметр</th>
                                            <th>Текущее</th>
                                            <th>Рекомендуемое</th>
                                            <th>Статус</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        <tr>
                                            <td>HTTPS</td>
                                            <td class="current-cell">{https_current}</td>
                                            <td>Обязательно для SEO</td>
                                            <td class="{https_status}">{https_icon}</td>
                                        </tr>
                                        <tr>
                                            <td>Canonical</td>
                                            <td class="current-cell">{escape_html(truncate(canonical, 50) if canonical else "(отсутствует)")}</td>
                                            <td>Указывает на себя</td>
                                            <td class="{"status-pass" if canonical_self else "status-fail"}">{"✅" if canonical_self else "❌"}</td>
                                        </tr>
                                        <tr>
                                            <td>Viewport</td>
                                            <td class="current-cell">{"present" if has_viewport else "отсутствует"}</td>
                                            <td>Для мобильных</td>
                                            <td class="{"status-pass" if has_viewport else "status-fail"}">{"✅" if has_viewport else "❌"}</td>
                                        </tr>
                                        <tr>
                                            <td>Schema.org</td>
                                            <td class="current-cell">{schema_count} схем</td>
                                            <td>Organization, FAQPage</td>
                                            <td class="status-fail">❌</td>
                                        </tr>
                                        <tr>
                                            <td>Яндекс.Метрика</td>
                                            <td class="current-cell">{"установлена" if yandex_metrics else "нет"}</td>
                                            <td>Обязательно для Яндекс</td>
                                            <td class="{"status-pass" if yandex_metrics else "status-fail"}">{"✅" if yandex_metrics else "❌"}</td>
                                        </tr>
                                        <tr>
                                            <td>Верификация Яндекс</td>
                                            <td class="current-cell">{"да" if yandex_verification else "нет"}</td>
                                            <td>Через Вебмастер</td>
                                            <td class="{"status-pass" if yandex_verification else "status-fail"}">{"✅" if yandex_verification else "❌"}</td>
                                        </tr>
                                    </tbody>
                                </table>
                            </div>

    '''

    return html


def generate_recommendations_section(google_breakdown, yandex_breakdown, url, analysis):
    """Generate Section 4: Prioritized Recommendations."""
    rec_data = build_recommendations_data(url, analysis)

    def get_recommendations():
        critical = []
        high = []
        medium = []

        all_factors = []
        seen_names = set()
        for name, data in google_breakdown.items():
            all_factors.append(("Google", name, data))
            seen_names.add(name)
        for name, data in yandex_breakdown.items():
            if name not in seen_names:
                all_factors.append(("Яндекс", name, data))
                seen_names.add(name)

        for system, name, data in all_factors:
            score = data.get("score", 0)
            max_val = data.get("max", 1)
            current = data.get("current", "—")
            ratio = score / max_val if max_val > 0 else 0

            if score == 0 and max_val >= 3:
                critical.append((system, name, score, max_val, current))
            elif score == 0 and max_val < 3:
                high.append((system, name, score, max_val, current))
            elif 0 < score < max_val and ratio < 0.5:
                high.append((system, name, score, max_val, current))
            elif 0 < score < max_val and ratio >= 0.5:
                medium.append((system, name, score, max_val, current))

        return critical, high, medium

    critical, high, medium = get_recommendations()

    recommendations_templates = {
        "https": {
            "title": "Установить HTTPS",
            "desc": "Перенаправить HTTP на HTTPS, обновить canonical. Без HTTPS сайт не получит высокие позиции в Яндекс.",
            "code": "301 redirect HTTP → HTTPS"
        },
        "title": {
            "title": "Улучшить Title Tag",
            "desc": "Минимум 50-60 символов с ключевыми словами и названием бренда.",
            "code": rec_data["recommended"]["title"]
        },
        "h1": {
            "title": "Добавить H1 с ключевым словом",
            "desc": "Ровно один H1 на странице с основным ключевым словом.",
            "code": rec_data["recommended"]["h1"]
        },
        "schema": {
            "title": "Добавить Schema.org разметку",
            "desc": f"Рекомендуемые типы: LocalBusiness, Store, Service. Найдены: {', '.join(rec_data.get('keywords', ['—'])[:3])}",
            "code": None
        },
        "meta_description": {
            "title": "Добавить Meta Description",
            "desc": "140-160 символов с CTA и ключевыми словами.",
            "code": rec_data["recommended"]["meta_description"]
        },
        "images_alt": {
            "title": "Alt тексты для изображений",
            "desc": "Добавить описательные alt к изображениям для Яндекс.Картинки.",
            "code": '<img alt="описание изображения">'
        },
        "commercial_markers": {
            "title": "Добавить коммерческие маркеры",
            "desc": "Телефоны, email, адреса, ИНН/ОГРН для Яндекс.",
            "code": None
        },
        "counters": {
            "title": "Установить Яндекс.Метрику",
            "desc": "Для анализа поведенческих факторов — критичных для Яндекс.",
            "code": None
        },
        "indexability": {
            "title": "Исправить Indexability",
            "desc": "Проверить canonical и robots.txt.",
            "code": None
        },
        "micro_markup": {
            "title": "Расширить микроразметку",
            "desc": "Добавить Schema.org помимо OG тегов.",
            "code": None
        },
        "viewport": {
            "title": "Проверить viewport",
            "desc": "Убедиться в наличии meta viewport для мобильных.",
            "code": '<meta name="viewport" content="width=device-width, initial-scale=1">'
        }
    }

    def build_priority_items(items, priority_class):
        html = ""
        for system, name, score, max_val, current in items:
            template_key = name.lower().replace(" ", "_").replace("/", "_")
            template = recommendations_templates.get(template_key, {
                "title": f"Исправить {name}",
                "desc": f"Проблема: {current}",
                "code": None
            })

            code_html = f'<p style="margin-top: 8px;"><code>{escape_html(template["code"])}</code></p>' if template["code"] else ""
            html += f'''
                                <div class="priority-item {priority_class}">
                                    <h4>{escape_html(template["title"])}</h4>
                                    <p>{escape_html(template["desc"])}</p>
                                    <p style="margin-top: 8px; color: var(--tp-secondary);">Текущее: {escape_html(truncate(str(current), 60))} ({score}/{max_val})</p>
                                    {code_html}
                                </div>
            '''
        return html

    critical_html = build_priority_items(critical, "critical")
    high_html = build_priority_items(high, "high")
    medium_html = build_priority_items(medium, "medium")

    if not critical_html and not high_html and not medium_html:
        no_recs = '''
                                <div class="priority-item" style="border-color: var(--success);">
                                    <h4 style="color: var(--success);">Всё в порядке!</h4>
                                    <p>Критических проблем не обнаружено. Продолжайте мониторить SEO-метрики.</p>
                                </div>
        '''
        critical_html = no_recs

    html = f'''
                            <div class="priority-section">
                                <h4 class="priority-title critical">Критические (исправить немедленно)</h4>
                                {critical_html}
                            </div>

                            <div class="priority-section">
                                <h4 class="priority-title high">Высокий приоритет (этот месяц)</h4>
                                {high_html}
                            </div>

                            <div class="priority-section">
                                <h4 class="priority-title medium">Средний приоритет (этот квартал)</h4>
                                {medium_html}
                            </div>
    '''

    return html


def generate_html_report(url, analysis):
    """Generate complete HTML report."""
    scores = analysis.get("scores", {})
    google_score = scores.get("google_seo", 0)
    google_max = scores.get("google_seo_max", 20)
    google_breakdown = scores.get("google_seo_breakdown", {})

    yandex_score = scores.get("yandex_seo", 0)
    yandex_max = scores.get("yandex_seo_max", 20)
    yandex_breakdown = scores.get("yandex_seo_breakdown", {})

    combined_score = scores.get("seo_combined", 0)
    timestamp = analysis.get("timestamp", datetime.now().isoformat())
    date_str = datetime.now().strftime("%d %m %Y, %H:%M:%S")

    parsed = urlparse(url)
    domain = parsed.netloc

    google_formula = f"{google_score}×0.30 + {yandex_score}×0.70 = {combined_score}"

    google_items = [
        ("Indexability (Robots/Canonical)", google_breakdown.get("indexability", {})),
        ("Title Tag", google_breakdown.get("title", {})),
        ("H1 Tag", google_breakdown.get("h1", {})),
        ("Schema.org / JSON-LD", google_breakdown.get("schema", {})),
        ("Meta Description", google_breakdown.get("meta_description", {})),
        ("Mobile Viewport", google_breakdown.get("viewport", {})),
        ("Images Alt", google_breakdown.get("images_alt", {})),
        ("HTTPS", google_breakdown.get("https", {})),
    ]

    yandex_items = [
        ("Коммерческие маркеры", yandex_breakdown.get("commercial_markers", {})),
        ("Title Tag", yandex_breakdown.get("title", {})),
        ("H1 Tag", yandex_breakdown.get("h1", {})),
        ("Indexability (Robots/Canonical)", yandex_breakdown.get("indexability", {})),
        ("Микроразметка (OG/Schema)", yandex_breakdown.get("micro_markup", {})),
        ("Счётчики (Метрика/Вебмастер)", yandex_breakdown.get("counters", {})),
        ("Meta Description", yandex_breakdown.get("meta_description", {})),
        ("HTTPS", yandex_breakdown.get("https", {})),
    ]

    def build_table_rows(items, total_score, total_max):
        rows = ""
        for name, data in items:
            score = data.get("score", 0)
            max_val = data.get("max", 1)
            current = data.get("current", "—")
            icon, status_text = get_status_icon_and_text(score, max_val)
            score_color_class = get_score_color(score, max_val)

            current_formatted = escape_html(format_current(current))
            name_escaped = escape_html(name)

            rows += f"""
                                        <tr>
                                            <td>{name_escaped}</td>
                                            <td class="score-cell {score_color_class}">{score}</td>
                                            <td class="max-cell">{max_val}</td>
                                            <td class="current-cell">{current_formatted}</td>
                                            <td class="status-cell">{icon} {status_text}</td>
                                        </tr>
            """
        # Add TOTAL row
        total_icon, total_status = get_status_icon_and_text(total_score, total_max)
        total_color_class = get_score_color(total_score, total_max)
        rows += f"""
                                        <tr class="total-row">
                                            <td><strong>ИТОГО</strong></td>
                                            <td class="score-cell {total_color_class}"><strong>{total_score}</strong></td>
                                            <td class="max-cell"><strong>{total_max}</strong></td>
                                            <td class="current-cell">—</td>
                                            <td class="status-cell"><strong>{total_icon} {total_status}</strong></td>
                                        </tr>
        """
        return rows

    google_rows = build_table_rows(google_items, google_score, google_max)
    yandex_rows = build_table_rows(yandex_items, yandex_score, yandex_max)

    checklist_section = generate_checklist_section(analysis, url)
    recommendations_section = generate_recommendations_section(google_breakdown, yandex_breakdown, url, analysis)

    html = f"""<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>SEO-аудит — {escape_html(domain)}</title>
    <meta name="description" content="SEO-аудит сайта {escape_html(domain)}">
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@100..900&family=Poppins:ital,wght@0,100;0,200;0,300;0,400;0,500;0,600;0,700;0,800;0,900;1,100;1,200;1,300;1,400;1,500;1,600;1,700;1,800;1,900&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css">
    <style>
        :root {{
            --tp-primary: #1a1a1a;
            --tp-secondary: #666666;
            --tp-accent: #ff6b35;
            --tp-accent-2: #f7b731;
            --tp-white: #ffffff;
            --tp-black: #000000;
            --tp-gray: #f5f5f5;
            --tp-gray-2: #e0e0e0;
            --tp-text: #333333;
            --tp-text-light: #666666;
            --tp-bg: #ffffff;
            --tp-bg-alt: #f9f9f9;
            --tp-transition: all 0.3s ease;
            --tp-radius: 8px;
            --success: #00C853;
            --danger: #FF1744;
            --warning: #FFB300;
        }}

        *, *::before, *::after {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        html {{
            scroll-behavior: smooth;
        }}

        body {{
            font-family: 'Outfit', 'Poppins', sans-serif;
            font-size: 16px;
            line-height: 1.6;
            color: var(--tp-text);
            background-color: var(--tp-bg);
            overflow-x: hidden;
        }}

        a {{
            text-decoration: none;
            color: inherit;
            transition: var(--tp-transition);
        }}

        ul {{
            list-style: none;
        }}

        img {{
            max-width: 100%;
            height: auto;
            display: block;
        }}

        button {{
            border: none;
            background: none;
            cursor: pointer;
            font-family: inherit;
        }}

        .container {{
            max-width: 1600px;
            margin: 0 auto;
            padding: 0 30px;
        }}

        /* Header */
        .tp-header {{
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            z-index: 1000;
            padding: 15px 0;
            background-color: var(--tp-white);
            box-shadow: 0 2px 20px rgba(0, 0, 0, 0.1);
            transition: var(--tp-transition);
        }}

        .tp-header-inner {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            position: relative;
        }}

        .tp-header-logo {{
            flex-shrink: 0;
            z-index: 1002;
        }}

        .tp-header-logo img {{
            width: 120px;
            max-width: 120px;
            height: auto;
        }}

        /* Main Menu (Desktop by default) */
        .tp-main-menu {{
            position: absolute;
            left: 50%;
            transform: translateX(-50%);
        }}

        .tp-nav-menu {{
            display: flex;
            gap: 60px;
            align-items: center;
        }}

        .tp-nav-menu .nav-links {{
            position: relative;
            font-weight: 500;
            font-size: 15px;
            color: var(--tp-primary);
            padding: 10px 0;
            text-decoration: none;
            transition: color 0.3s ease;
        }}

        .tp-nav-menu .nav-links::after {{
            content: '';
            position: absolute;
            bottom: 0;
            left: 0;
            width: 100%;
            height: 2px;
            background-color: var(--tp-accent);
            transform: scaleX(0);
            transform-origin: right;
            transition: transform 0.3s ease;
        }}

        .tp-nav-menu .nav-links:hover {{
            color: var(--tp-accent);
        }}

        .tp-nav-menu .nav-links:hover::after {{
            transform: scaleX(1);
            transform-origin: left;
        }}

        .tp-header-action {{
            display: flex;
            align-items: center;
            gap: 20px;
            flex-shrink: 0;
        }}

        /* Menu Toggle (hamburger) */
        .tp-menu-toggle {{
            width: 40px;
            height: 30px;
            position: relative;
            display: none;
            flex-direction: column;
            justify-content: space-between;
            z-index: 1002;
        }}

        .tp-menu-toggle span {{
            display: block;
            width: 100%;
            height: 2px;
            background-color: var(--tp-primary);
            position: absolute;
            left: 0;
            transition: var(--tp-transition);
        }}

        .tp-menu-toggle span:nth-child(1) {{ top: 0; }}
        .tp-menu-toggle span:nth-child(2) {{ top: 50%; transform: translateY(-50%); }}
        .tp-menu-toggle span:nth-child(3) {{ top: 100%; transform: translateY(-100%); }}

        .tp-menu-toggle::before,
        .tp-menu-toggle::after {{
            content: '';
            position: absolute;
            top: 50%;
            left: 0;
            width: 100%;
            height: 2px;
            background-color: var(--tp-primary);
            transform: translateY(-50%) rotate(0deg);
            transition: transform 0.3s ease;
            pointer-events: none;
        }}

        .tp-menu-toggle.active span {{
            opacity: 0;
        }}

        .tp-menu-toggle.active::before {{
            transform: translateY(-50%) rotate(45deg);
        }}

        .tp-menu-toggle.active::after {{
            transform: translateY(-50%) rotate(-45deg);
        }}

        /* Buttons */
        .tp-btn {{
            position: relative;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            padding: 14px 30px;
            background-color: var(--tp-primary);
            color: var(--tp-white);
            font-weight: 600;
            font-size: 13px;
            text-transform: uppercase;
            letter-spacing: 1px;
            border-radius: var(--tp-radius);
            overflow: hidden;
            transition: var(--tp-transition);
            white-space: nowrap;
        }}

        .tp-btn:hover {{
            background-color: var(--tp-accent);
            color: var(--tp-white);
            transform: translateY(-2px);
            box-shadow: 0 10px 30px rgba(255, 107, 53, 0.3);
        }}

        .tp-btn-accent {{
            background-color: var(--tp-accent);
        }}

        .tp-btn-accent:hover {{
            background-color: var(--tp-primary);
        }}

        /* Mobile Backdrop */
        .mobile-menu-backdrop {{
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background-color: rgba(0, 0, 0, 0.5);
            z-index: 1000;
            opacity: 0;
            visibility: hidden;
            transition: opacity 0.3s ease, visibility 0.3s ease;
        }}

        .mobile-menu-backdrop.active {{
            opacity: 1;
            visibility: visible;
        }}

        /* Hero Section */
        .tp-hero {{
            position: relative;
            min-height: 40vh;
            display: flex;
            align-items: center;
            justify-content: center;
            background: linear-gradient(135deg, #f5f5f5 0%, #ffffff 100%);
            overflow: hidden;
            padding: 120px 0 60px;
        }}

        .tp-hero-bg {{
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            overflow: hidden;
        }}

        .tp-hero-shape {{
            position: absolute;
            border-radius: 50%;
            opacity: 0.1;
        }}

        .tp-hero-shape-1 {{
            width: clamp(200px, 50vw, 600px);
            height: clamp(200px, 50vw, 600px);
            background: linear-gradient(135deg, var(--tp-accent), var(--tp-accent-2));
            top: clamp(-50px, -10vw, -200px);
            right: clamp(-20px, -8vw, -100px);
            animation: float 15s ease-in-out infinite;
        }}

        .tp-hero-shape-2 {{
            width: clamp(120px, 35vw, 400px);
            height: clamp(120px, 35vw, 400px);
            background: linear-gradient(135deg, #667eea, #764ba2);
            bottom: clamp(-30px, -8vw, -100px);
            left: clamp(-20px, -8vw, -100px);
            animation: float 12s ease-in-out infinite reverse;
        }}

        .tp-hero-shape-3 {{
            width: clamp(80px, 18vw, 200px);
            height: clamp(80px, 18vw, 200px);
            background: linear-gradient(135deg, var(--tp-accent-2), #ff6b35);
            top: 50%;
            left: 20%;
            animation: float 10s ease-in-out infinite;
        }}

        @keyframes float {{
            0%, 100% {{ transform: translate(0, 0) rotate(0deg); }}
            33% {{ transform: translate(30px, -30px) rotate(10deg); }}
            66% {{ transform: translate(-20px, 20px) rotate(-5deg); }}
        }}

        .tp-hero-content {{
            position: relative;
            z-index: 10;
            text-align: center;
        }}

        .tp-hero-subtitle {{
            display: inline-block;
            font-size: 14px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 3px;
            color: var(--tp-accent);
            margin-bottom: 20px;
            padding: 10px 25px;
            background-color: rgba(255, 107, 53, 0.1);
            border-radius: 30px;
        }}

        .tp-hero-title {{
            font-size: clamp(40px, 8vw, 80px);
            font-weight: 800;
            line-height: 1.1;
            color: var(--tp-primary);
            margin-bottom: 20px;
        }}

        .tp-hero-description {{
            font-size: 18px;
            color: var(--tp-text-light);
            margin-bottom: 10px;
            line-height: 1.8;
        }}

        .tp-hero-date {{
            font-size: 14px;
            color: var(--tp-secondary);
        }}

        /* Score Cards */
        .scores-section {{
            padding: 60px 0;
            background-color: var(--tp-bg);
        }}

        .scores-grid {{
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 30px;
            max-width: 900px;
            margin: 0 auto;
        }}

        .score-card {{
            position: relative;
            padding: 40px 30px;
            background-color: var(--tp-white);
            border-radius: var(--tp-radius);
            box-shadow: 0 10px 40px rgba(0, 0, 0, 0.1);
            text-align: center;
            transition: var(--tp-transition);
        }}

        .score-card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 20px 50px rgba(0, 0, 0, 0.15);
        }}

        .score-card.google {{ border-top: 4px solid var(--warning); }}
        .score-card.yandex {{ border-top: 4px solid var(--tp-accent); }}
        .score-card.total {{ border-top: 4px solid var(--tp-primary); }}

        .score-card-label {{
            font-size: 12px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 2px;
            color: var(--tp-text-light);
            margin-bottom: 15px;
        }}

        .score-card-value {{
            font-size: 56px;
            font-weight: 800;
            line-height: 1;
            margin-bottom: 5px;
        }}

        .score-card.google .score-card-value {{ color: var(--warning); }}
        .score-card.yandex .score-card-value {{ color: var(--tp-accent); }}
        .score-card.total .score-card-value {{ color: var(--tp-primary); }}

        .score-card-max {{
            font-size: 16px;
            color: var(--tp-text-light);
        }}

        .score-card-formula {{
            margin-top: 15px;
            font-size: 11px;
            color: var(--tp-secondary);
            font-family: monospace;
        }}

        /* Accordion */
        .tp-sections {{
            padding: 80px 0 100px;
            background-color: var(--tp-bg-alt);
        }}

        .services-accordion {{
            max-width: 1400px;
            margin: 0 auto;
        }}

        .services-accordion-item {{
            border-bottom: 1px solid var(--tp-gray-2);
            margin-bottom: 0;
        }}

        .services-accordion-item:nth-child(odd) {{
            background-color: var(--tp-bg);
        }}

        .services-accordion-item:nth-child(even) {{
            background-color: var(--tp-bg-alt);
        }}

        .services-accordion-item.active .services-accordion-toggle {{
            background-color: var(--tp-accent);
            color: var(--tp-white);
        }}

        .services-accordion-header {{
            display: flex;
            align-items: center;
            padding: 25px 0;
            cursor: pointer;
            transition: var(--tp-transition);
        }}

        .services-accordion-header:hover {{
            color: var(--tp-accent);
        }}

        .services-accordion-number {{
            font-size: 48px;
            font-weight: 800;
            color: var(--tp-gray-2);
            line-height: 1;
            margin-right: 30px;
            font-family: 'Outfit', sans-serif;
            opacity: 0.7;
            min-width: 70px;
            text-align: left;
        }}

        .services-accordion-title {{
            flex: 1;
            display: flex;
            align-items: center;
            gap: 15px;
        }}

        .services-accordion-title i {{
            font-size: 24px;
            color: var(--tp-accent);
        }}

        .services-accordion-title h3 {{
            font-size: 20px;
            font-weight: 700;
            color: var(--tp-primary);
            margin: 0;
        }}

        .services-accordion-toggle {{
            width: 40px;
            height: 40px;
            display: flex;
            align-items: center;
            justify-content: center;
            background-color: var(--tp-white);
            border-radius: 50%;
            color: var(--tp-primary);
            font-size: 14px;
            transition: all 0.3s ease;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
        }}

        .services-accordion-content {{
            max-height: 0;
            overflow: hidden;
            transition: max-height 0.5s ease;
        }}

        .services-accordion-item.active .services-accordion-content {{
            max-height: 10000px;
        }}

        .services-accordion-body {{
            padding: 0 0 40px 90px;
            padding-right: 40px;
        }}

        /* Table Scroll Wrapper */
        .table-scroll-wrapper {{
            overflow-x: auto;
            -webkit-overflow-scrolling: touch;
            margin-bottom: 8px;
        }}

        .table-scroll-wrapper::after {{
            display: none;
        }}

        @media (max-width: 767px) {{
            .table-scroll-wrapper::after {{
                content: "Поверните экран для лучшего просмотра таблицы";
                display: block;
                text-align: center;
                font-size: 11px;
                color: var(--tp-text-light);
                padding: 8px 0;
                font-style: italic;
            }}
        }}

        /* Tables */
        .check-table {{
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 20px;
            min-width: 600px;
        }}

        .check-table th {{
            text-align: left;
            font-size: 11px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 1px;
            color: var(--tp-text-light);
            padding: 12px 15px;
            border-bottom: 2px solid #e0e0e0;
            background-color: var(--tp-bg);
            white-space: normal;
            word-wrap: break-word;
        }}

        .check-table td {{
            padding: 14px 15px;
            border-bottom: 1px solid #f0f0f0;
            font-size: 14px;
            white-space: normal;
            word-wrap: break-word;
        }}

        .check-table tr:last-child td {{
            border-bottom: none;
        }}

        .check-table tr:hover td {{
            background-color: rgba(255, 107, 53, 0.03);
        }}

        .score-cell {{
            font-family: monospace;
            font-weight: 700;
            text-align: center;
            white-space: nowrap;
        }}

        .score-cell.success {{ color: var(--success); }}
        .score-cell.warning {{ color: var(--warning); }}
        .score-cell.danger {{ color: var(--danger); }}

        .max-cell {{
            font-family: monospace;
            color: var(--tp-secondary);
            text-align: center;
            white-space: nowrap;
        }}

        .current-cell {{
            font-family: monospace;
            color: var(--tp-secondary);
            font-size: 13px;
            max-width: 300px;
            word-wrap: break-word;
        }}

        .status-cell {{
            font-weight: 600;
            white-space: nowrap;
        }}

        /* Status classes for checklist */
        .status-pass {{ color: var(--success); font-weight: 600; }}
        .status-fail {{ color: var(--danger); font-weight: 600; }}
        .status-warn {{ color: var(--warning); font-weight: 600; }}

        /* Description under table */
        .calculation-description {{
            font-size: 13px;
            color: var(--tp-text-light);
            line-height: 1.6;
            padding: 15px 0;
            border-top: 1px dashed var(--tp-gray-2);
            margin-top: 10px;
        }}

        /* Priority Items */
        .priority-section {{
            margin-bottom: 25px;
        }}

        .priority-section:last-child {{
            margin-bottom: 0;
        }}

        .priority-title {{
            font-size: 16px;
            font-weight: 700;
            margin-bottom: 12px;
            padding-left: 10px;
        }}

        .priority-title.critical {{ color: var(--danger); }}
        .priority-title.high {{ color: var(--tp-accent); }}
        .priority-title.medium {{ color: var(--warning); }}

        .priority-item {{
            padding: 16px 20px;
            margin-bottom: 10px;
            background: var(--tp-white);
            border-radius: var(--tp-radius);
            border-left: 4px solid;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.05);
        }}

        .priority-item.critical {{ border-color: var(--danger); }}
        .priority-item.high {{ border-color: var(--tp-accent); }}
        .priority-item.medium {{ border-color: var(--warning); }}

        .priority-item h4 {{
            margin: 0 0 8px;
            font-size: 15px;
            font-weight: 600;
            color: var(--tp-primary);
        }}

        .priority-item p {{
            margin: 0;
            font-size: 13px;
            color: var(--tp-text-light);
        }}

        .priority-item code {{
            background: var(--tp-gray);
            padding: 2px 6px;
            border-radius: 4px;
            font-size: 12px;
            color: var(--tp-accent);
        }}

        /* CTA Section */
        .cta-section {{
            padding: 80px 20px;
            background: linear-gradient(135deg, var(--tp-primary) 0%, #2a2a2a 100%);
            text-align: center;
        }}

        .cta-section h2 {{
            font-size: clamp(24px, 4vw, 36px);
            font-weight: 700;
            color: var(--tp-white);
            margin-bottom: 20px;
            line-height: 1.3;
        }}

        .cta-section p {{
            font-size: 18px;
            color: rgba(255, 255, 255, 0.8);
            margin-bottom: 30px;
            max-width: 600px;
            margin-left: auto;
            margin-right: auto;
        }}

        .cta-section .tp-btn {{
            font-size: 14px;
            padding: 18px 40px;
        }}

        /* Footer */
        .tp-footer {{
            padding: 40px 0;
            background-color: var(--tp-bg-alt);
            text-align: center;
            border-top: 1px solid var(--tp-gray-2);
        }}

        .tp-footer p {{
            font-size: 14px;
            color: var(--tp-text-light);
        }}

        /* Responsive - Mobile Menu */
        @media (max-width: 1200px) {{
            .container {{
                max-width: 100%;
                padding: 0 20px;
            }}

            .services-accordion {{
                max-width: 100%;
            }}
        }}

        @media (max-width: 991px) {{
            .tp-menu-toggle {{
                display: flex !important;
            }}

            .tp-header-action .tp-btn {{
                display: none;
            }}

            .tp-main-menu {{
                position: fixed;
                top: 0;
                right: 0;
                left: auto;
                width: 320px;
                max-width: 100%;
                height: 100vh;
                background-color: var(--tp-white);
                clip-path: inset(0 0 0 100%);
                transition: clip-path 0.3s ease;
                z-index: 1001;
                box-shadow: -5px 0 20px rgba(0, 0, 0, 0.1);
                transform: none;
            }}

            .tp-main-menu.active {{
                clip-path: inset(0 0 0 0);
            }}

            .tp-nav-menu {{
                display: flex !important;
                flex-direction: column;
                gap: 0;
                padding-top: 100px;
                height: 100%;
            }}

            .tp-nav-menu .nav-links {{
                font-size: 18px;
                padding: 15px 0;
                border-bottom: 1px solid rgba(0, 0, 0, 0.1);
                display: block;
            }}

            .scores-grid {{
                grid-template-columns: 1fr;
            }}

            .services-accordion-number {{
                font-size: 32px;
                margin-right: 15px;
                min-width: 50px;
            }}

            .services-accordion-body {{
                padding-left: 0;
            }}

            .score-card-value {{
                font-size: 42px;
            }}

            .cta-section h2 {{
                font-size: 24px;
            }}

            .cta-section p {{
                font-size: 16px;
            }}
        }}

        @media (max-width: 767px) {{
            .tp-hero {{
                padding: 100px 0 50px;
            }}

            .tp-hero-title {{
                font-size: 32px;
            }}

            .services-accordion-header {{
                flex-wrap: wrap;
                padding: 20px 0;
            }}

            .services-accordion-number {{
                font-size: 28px;
                width: 100%;
                margin-bottom: 10px;
            }}

            .services-accordion-title {{
                flex: 1;
            }}

            .table-scroll-wrapper::after {{
                display: block;
            }}

            .check-table {{
                font-size: 12px;
            }}

            .check-table th, .check-table td {{
                padding: 10px 8px;
            }}
        }}
    </style>
</head>
<body>
    <!-- Header -->
    <header class="tp-header" id="header-sticky">
        <div class="mobile-menu-backdrop" id="mobile_backdrop"></div>
        <div class="container">
            <div class="tp-header-inner">
                <div class="tp-header-logo">
                    <a href="https://open4.dev/">
                        <img src="https://open4.dev/images/open4_logo_small.png" alt="open4">
                    </a>
                </div>

                <nav class="tp-main-menu" id="main_menu">
                    <ul class="tp-nav-menu">
                        <li><a href="https://open4.dev/index.html" class="nav-links">Main</a></li>
                        <li><a href="https://open4.dev/work.html" class="nav-links">Work</a></li>
                        <li><a href="https://open4.dev/services.html" class="nav-links">Services</a></li>
                    </ul>
                </nav>

                <div class="tp-header-action">
                    <a href="https://open4.dev/#contact" class="tp-btn">
                        <span>Let's Talk</span>
                    </a>
                    <button class="tp-menu-toggle" id="menu_toggle" aria-label="Toggle menu">
                        <span></span>
                        <span></span>
                        <span></span>
                    </button>
                </div>
            </div>
        </div>
    </header>

    <!-- Hero Section -->
    <section class="tp-hero">
        <div class="tp-hero-bg">
            <div class="tp-hero-shape tp-hero-shape-1"></div>
            <div class="tp-hero-shape tp-hero-shape-2"></div>
            <div class="tp-hero-shape tp-hero-shape-3"></div>
        </div>
        <div class="container">
            <div class="tp-hero-content">
                <span class="tp-hero-subtitle">SEO-аудит</span>
                <h1 class="tp-hero-title">{escape_html(domain)}</h1>
                <p class="tp-hero-description">Комплексный анализ для Google и Яндекс</p>
                <p class="tp-hero-date">{date_str}</p>
            </div>
        </div>
    </section>

    <!-- Score Cards -->
    <section class="scores-section">
        <div class="container">
            <div class="scores-grid">
                <div class="score-card google">
                    <div class="score-card-label">Google</div>
                    <div class="score-card-value">{google_score}</div>
                    <div class="score-card-max">/ {google_max}</div>
                </div>
                <div class="score-card yandex">
                    <div class="score-card-label">Яндекс</div>
                    <div class="score-card-value">{yandex_score}</div>
                    <div class="score-card-max">/ {yandex_max}</div>
                </div>
                <div class="score-card total">
                    <div class="score-card-label">Итого</div>
                    <div class="score-card-value">{combined_score}</div>
                    <div class="score-card-max">/ 20</div>
                    <div class="score-card-formula">{google_formula}</div>
                </div>
            </div>
        </div>
    </section>

    <!-- Accordion Sections -->
    <section class="tp-sections">
        <div class="container">
            <div class="services-accordion">

                <!-- Детализация Google -->
                <div class="services-accordion-item active">
                    <div class="services-accordion-header">
                        <span class="services-accordion-number">&nbsp;01</span>
                        <div class="services-accordion-title">
                            <i class="fa-brands fa-google"></i>
                            <h3>Детализация Google Score</h3>
                        </div>
                        <span class="services-accordion-toggle"><i class="fas fa-minus"></i></span>
                    </div>
                    <div class="services-accordion-content">
                        <div class="services-accordion-body">
                            <div class="table-scroll-wrapper">
                                <table class="check-table">
                                    <thead>
                                        <tr>
                                            <th>Фактор</th>
                                            <th>Баллы</th>
                                            <th>Макс</th>
                                            <th>Текущее</th>
                                            <th>Статус</th>
                                        </tr>
                                    </thead>
                                    <tbody>
{google_rows}
                                    </tbody>
                                </table>
                            </div>
                            <div class="calculation-description">
                                <strong>Механизм расчёта:</strong> Google Score — это сумма баллов по 8 факторам (от 0 до Макс). Максимальный возможный балл = 20. Чем выше оценка, тем лучше сайт оптимизирован для Google. Критические факторы: Indexability (если страница закрыта от индексации, остальные факторы не имеют значения) и Schema.org (влияет на Rich Results).
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Детализация Яндекс -->
                <div class="services-accordion-item">
                    <div class="services-accordion-header">
                        <span class="services-accordion-number">&nbsp;02</span>
                        <div class="services-accordion-title">
                            <i class="fa-brands fa-yandex"></i>
                            <h3>Детализация Яндекс Score</h3>
                        </div>
                        <span class="services-accordion-toggle"><i class="fas fa-plus"></i></span>
                    </div>
                    <div class="services-accordion-content">
                        <div class="services-accordion-body">
                            <div class="table-scroll-wrapper">
                                <table class="check-table">
                                    <thead>
                                        <tr>
                                            <th>Фактор</th>
                                            <th>Баллы</th>
                                            <th>Макс</th>
                                            <th>Текущее</th>
                                            <th>Статус</th>
                                        </tr>
                                    </thead>
                                    <tbody>
{yandex_rows}
                                    </tbody>
                                </table>
                            </div>
                            <div class="calculation-description">
                                <strong>Механизм расчёта:</strong> Яндекс Score — это сумма баллов по 8 факторам (от 0 до Макс). Максимальный возможный балл = 20. Для Яндекс критичны коммерческие маркеры (телефоны, email, адреса, ИНН/ОГРН) — это фундаментальный сигнал качества бизнеса. Также важны счётчики Метрики и верификация в Вебмастере.
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Чеклист On-Page SEO -->
                <div class="services-accordion-item">
                    <div class="services-accordion-header">
                        <span class="services-accordion-number">&nbsp;03</span>
                        <div class="services-accordion-title">
                            <i class="fa-solid fa-clipboard-check"></i>
                            <h3>Чеклист On-Page SEO</h3>
                        </div>
                        <span class="services-accordion-toggle"><i class="fas fa-plus"></i></span>
                    </div>
                    <div class="services-accordion-content">
                        <div class="services-accordion-body">
{checklist_section}
                        </div>
                    </div>
                </div>

                <!-- Приоритизированные рекомендации -->
                <div class="services-accordion-item">
                    <div class="services-accordion-header">
                        <span class="services-accordion-number">&nbsp;04</span>
                        <div class="services-accordion-title">
                            <i class="fa-solid fa-list-check"></i>
                            <h3>Приоритизированные рекомендации</h3>
                        </div>
                        <span class="services-accordion-toggle"><i class="fas fa-plus"></i></span>
                    </div>
                    <div class="services-accordion-content">
                        <div class="services-accordion-body">
{recommendations_section}
                        </div>
                    </div>
                </div>

            </div>
        </div>
    </section>

    <!-- CTA Section -->
    <section class="cta-section">
        <div class="container">
            <h2>Хотите радикально повысить эффективность бизнеса?</h2>
            <p>Мы внедряем передовые инструменты ИИ для кратного роста прибыли. Напишите нам!</p>
            <a href="https://open4.dev/#contact" class="tp-btn tp-btn-accent">
                <span>Хочу увеличить прибыль</span>
            </a>
        </div>
    </section>

    <!-- Footer -->
    <footer class="tp-footer">
        <div class="container">
            <p>Отчёт сгенерирован Искуственным интеллектом. ИИ может ошибаться.</p>
        </div>
    </footer>

    <!-- JavaScript for menu and accordion -->
    <script>
        document.addEventListener('DOMContentLoaded', function() {{
            var menuToggle = document.getElementById('menu_toggle');
            var mainMenu = document.getElementById('main_menu');
            var mobileBackdrop = document.getElementById('mobile_backdrop');

            if (menuToggle && mainMenu) {{
                menuToggle.addEventListener('click', function() {{
                    mainMenu.classList.toggle('active');
                    mobileBackdrop.classList.toggle('active');
                    menuToggle.classList.toggle('active');
                }});
            }}

            if (mobileBackdrop) {{
                mobileBackdrop.addEventListener('click', function() {{
                    mainMenu.classList.remove('active');
                    mobileBackdrop.classList.remove('active');
                    menuToggle.classList.remove('active');
                }});
            }}

            var accordionHeaders = document.querySelectorAll('.services-accordion-header');
            accordionHeaders.forEach(function(header) {{
                header.addEventListener('click', function() {{
                    var item = header.parentElement;
                    var content = item.querySelector('.services-accordion-content');
                    var toggle = header.querySelector('.services-accordion-toggle i');

                    item.classList.toggle('active');

                    if (item.classList.contains('active')) {{
                        toggle.classList.remove('fa-plus');
                        toggle.classList.add('fa-minus');
                    }} else {{
                        toggle.classList.remove('fa-minus');
                        toggle.classList.add('fa-plus');
                    }}
                }});
            }});
        }});
    </script>
</body>
</html>"""

    return html


def add_css_tooltips(html):
    """Add CSS title tooltips to factor names in tables."""
    tooltips = {
        "Indexability (Robots/Canonical)": "Проверяет, может ли поисковик просканировать страницу. Без этого сайт вообще не попадает в индекс.",
        "Title Tag": "Заголовок страницы в поиске. Должен содержать ключевое слово и быть 50-60 символов. Влияет на кликабельность в выдаче.",
        "H1 Tag": "Главный заголовок страницы. Должен быть ровно один на странице и содержать ключевое слово. Ключевой фактор для SEO.",
        "Schema.org / JSON-LD": "Структурированные данные — помогают поисковикам понимать тип контента. Влияют на Rich Snippets в выдаче.",
        "Meta Description": "Краткое описание страницы под заголовком в поиске. Влияет на CTR, но не на ранжирование напрямую.",
        "Mobile Viewport": "Адаптивность для мобильных устройств. Google использует mobile-first индексацию — без этого фактора сайт теряет позиции.",
        "Images Alt": "Alt-тексты для изображений — описывают картинки для поисковиков и скрин-ридеров. Помогают в Image Search.",
        "HTTPS": "Защищённое соединение. Google учитывает HTTPS как фактор ранжирования с 2014 года.",
        "Коммерческие маркеры": "Телефоны, email, адреса, ИНН — сигналы для Яндекс, что это реальный бизнес. Критичны для коммерческих запросов.",
        "Микроразметка (OG/Schema)": "Open Graph теги для соцсетей + Schema.org для поисковиков. Помогает корректно показывать контент в превью.",
        "Счётчики (Метрика/Вебмастер)": "Яндекс.Метрика — для анализа поведенческих факторов. Верификация — подтверждение прав на сайт.",
    }

    for factor, tooltip in tooltips.items():
        html = html.replace(
            f'<td>{factor}</td>',
            f'<td title="{tooltip}">{factor}</td>'
        )

    return html


def main():
    if len(sys.argv) < 2:
        print(json.dumps({
            "usage": "python3 generate_seo_html.py <url> [--output-dir <dir>]",
            "example": "python3 generate_seo_html.py https://comandos.ai",
            "description": "Generate SEO audit HTML report with open4.dev styling"
        }, indent=2))
        sys.exit(1)

    url = sys.argv[1]
    if not url.startswith("http"):
        url = "https://" + url

    output_dir = os.environ.get("OPENCODE_WORKING_DIR", os.getcwd())
    for i, arg in enumerate(sys.argv[2:], start=2):
        if arg == "--output-dir" and i + 1 < len(sys.argv):
            output_dir = sys.argv[i + 1]

    os.makedirs(output_dir, exist_ok=True)

    from analyze_page import analyze
    print(f"Analyzing: {url}")
    result = analyze(url)

    if result.get("status") == "error":
        print(f"Error: {result.get('message')}")
        sys.exit(1)

    analysis = result.get("analysis", {})
    html = generate_html_report(url, analysis)
    html = add_css_tooltips(html)

    filename = get_timestamp_filename(url, "SEO-AUDIT") + ".html"
    filepath = os.path.join(output_dir, filename)

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"HTML report saved to: {filepath}")
    return filepath


if __name__ == "__main__":
    main()