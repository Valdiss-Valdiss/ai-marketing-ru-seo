#!/usr/bin/env python3
"""
Generate SEO Audit Markdown Report — AI Marketing Claude Code Skills
Creates professional Markdown report.
"""

import sys
import os
from datetime import datetime
from urllib.parse import urlparse


def escape_md(text):
    """Escape markdown special characters."""
    if not isinstance(text, str):
        text = str(text)
    return (text
            .replace("\\", "\\\\")
            .replace("*", "\\*")
            .replace("_", "\\_")
            .replace("#", "\\#")
            .replace("[", "\\[")
            .replace("]", "\\]")
            .replace("(", "\\(")
            .replace(")", "\\)")
            .replace("|", "\\|")
            .replace("`", "\\`")
            .replace(">", "\\>")
            .replace("<", "\\<"))


def truncate(text, length=80):
    """Truncate text and add ellipsis."""
    if not text:
        return ""
    text = str(text)
    if len(text) > length:
        return text[:length] + "..."
    return text


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


def generate_recommendations_md(google_breakdown, yandex_breakdown, url, analysis):
    """Generate recommendations section."""
    from urllib.parse import urlparse

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

    rec_data = {
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

    def build_rec_list(items):
        if not items:
            return "1. Нет рекомендаций — всё в порядке!\n"
        result = ""
        for system, name, score, max_val, current in items:
            template_key = name.lower().replace(" ", "_").replace("/", "_")
            template = recommendations_templates.get(template_key, {
                "title": f"Исправить {name}",
                "desc": f"Проблема: {current}",
                "code": None
            })
            code_line = (" `" + template["code"] + "`") if template["code"] else ""
            result += f"1. **{template['title']}** — {template['desc']}{code_line}\n"
        return result

    if not critical and not high and not medium:
        return """### Критические (Исправить немедленно

1. ✅ Нет критических рекомендаций — всё в порядке!
"""

    md = ""
    if critical:
        md += "### Критические (Исправить немедленно)\n\n"
        md += build_rec_list(critical)
        md += "\n"

    if high:
        md += "### Высокий приоритет (Этот месяц)\n\n"
        md += build_rec_list(high)
        md += "\n"

    if medium:
        md += "### Средний приоритет (Этот квартал)\n\n"
        md += build_rec_list(medium)
        md += "\n"

    return md


def generate_md_report(url, analysis):
    """Generate complete Markdown report."""
    scores = analysis.get("scores", {})
    google_score = scores.get("google_seo", 0)
    google_max = scores.get("google_seo_max", 20)
    google_breakdown = scores.get("google_seo_breakdown", {})

    yandex_score = scores.get("yandex_seo", 0)
    yandex_max = scores.get("yandex_seo_max", 20)
    yandex_breakdown = scores.get("yandex_seo_breakdown", {})

    combined_score = scores.get("seo_combined", 0)
    date_str = datetime.now().strftime("%d %m %Y, %H:%M:%S")

    parsed = urlparse(url)
    domain = parsed.netloc

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

    def build_breakdown_table(items, total_score, total_max):
        rows = "| Фактор | Баллы | Макс | Текущее | Статус |\n"
        rows += "|--------|-------|------|---------|--------|\n"
        for name, data in items:
            score = data.get("score", 0)
            max_val = data.get("max", 1)
            current = data.get("current", "—")
            icon, status_text = get_status_icon_and_text(score, max_val)
            current_escaped = escape_md(truncate(str(current), 50))
            name_escaped = escape_md(name)
            rows += f"| {name_escaped} | {score} | {max_val} | {current_escaped} | {icon} {status_text} |\n"
        icon, status_text = get_status_icon_and_text(total_score, total_max)
        rows += f"| **ИТОГО** | **{total_score}** | **{total_max}** | — | {icon} {status_text} |\n"
        return rows

    google_table = build_breakdown_table(google_items, google_score, google_max)
    yandex_table = build_breakdown_table(yandex_items, yandex_score, yandex_max)

    yandex_data = analysis.get("yandex", {})
    yandex_metrics = yandex_data.get("yandex_metrics_installed", False)
    yandex_verification = yandex_data.get("yandex_verification", "")
    has_turbo = yandex_data.get("has_turbo_pages", False)
    yml_feed = yandex_data.get("yml_feed", "")

    yandex_spec = f"""| Элемент | Статус |
|---------|--------|
| Яндекс.Метрика | {"Да" if yandex_metrics else "Нет"} |
| Верификация в Вебмастере | {"Да" if yandex_verification else "Нет"} |
| Турбо-страницы | {"Да" if has_turbo else "Нет"} |
| YML-фид | {"Найден" if yml_feed else "Отсутствует"} |
"""

    recommendations = generate_recommendations_md(google_breakdown, yandex_breakdown, url, analysis)

    md = f"""# SEO-аудит — {domain}

**Дата:** {date_str}
**URL:** {url}

---

## SEO Score

| Система | Баллы | Макс |
|---------|-------|------|
| Google | {google_score} | {google_max} |
| Яндекс | {yandex_score} | {yandex_max} |
| **Комбинированный** | **{combined_score}** | **{google_max}** |

**Вес:** Яндекс 70%, Google 30% (для России)
**Формула:** Google × 0.30 + Яндекс × 0.70

---

## Детализация Google Score

{google_table}

**Механизм расчёта:** Google Score — сумма баллов по 8 факторам (от 0 до Макс). Максимум = 20.

---

## Детализация Яндекс Score

{yandex_table}

**Механизм расчёта:** Яндекс Score — сумма баллов по 8 факторам (от 0 до Макс). Максимум = 20. Для Яндекс критичны коммерческие маркеры (телефоны, email, адреса, ИНН/ОГРН).

---

## Yandex-специфика

{yandex_spec}
---

## Приоритизированные рекомендации

{recommendations}

---

## Хотите радикально повысить эффективность бизнеса?

Мы внедряем передовые инструменты ИИ для кратного роста прибыли. Напишите нам!

**[Хочу увеличить прибыль](https://open4.dev/#contact)**

---

*Отчёт сгенерирован Искуственным интеллектом. ИИ может ошибаться.*
"""

    return md


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 generate_seo_md.py <url>")
        sys.exit(1)

    url = sys.argv[1]
    if not url.startswith("http"):
        url = "https://" + url

    output_dir = os.environ.get("OPENCODE_WORKING_DIR", os.getcwd())

    from analyze_page import analyze
    print(f"Analyzing: {url}")
    result = analyze(url)

    if result.get("status") == "error":
        print(f"Error: {result.get('message')}")
        sys.exit(1)

    analysis = result.get("analysis", {})
    md = generate_md_report(url, analysis)

    os.makedirs(output_dir, exist_ok=True)
    filename = get_timestamp_filename(url, "SEO-AUDIT") + ".md"
    filepath = os.path.join(output_dir, filename)

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(md)

    print(f"Markdown report saved to: {filepath}")
    return filepath


if __name__ == "__main__":
    main()