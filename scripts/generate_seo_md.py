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


def generate_recommendations_md(google_breakdown, yandex_breakdown):
    """Generate recommendations section."""
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
            "code": '<title>AI-автоматизация | Команда AI 24/7 | Brand</title>'
        },
        "h1": {
            "title": "Добавить H1 с ключевым словом",
            "desc": "Ровно один H1 на странице с основным ключевым словом.",
            "code": "<h1>AI-автоматизация бизнеса</h1>"
        },
        "schema": {
            "title": "Добавить Schema.org разметку",
            "desc": "Organization, FAQPage, Service для усиления E-E-A-T.",
            "code": None
        },
        "meta_description": {
            "title": "Добавить Meta Description",
            "desc": "140-160 символов с CTA и ключевыми словами.",
            "code": '<meta name="description" content="...">'
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
            code_line = f" \\`{template['code']}\\`" if template["code"] else ""
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

    def build_breakdown_table(items):
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
        return rows

    google_table = build_breakdown_table(google_items)
    yandex_table = build_breakdown_table(yandex_items)

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

    recommendations = generate_recommendations_md(google_breakdown, yandex_breakdown)

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

    from analyze_page import analyze
    print(f"Analyzing: {url}")
    result = analyze(url)

    if result.get("status") == "error":
        print(f"Error: {result.get('message')}")
        sys.exit(1)

    analysis = result.get("analysis", {})
    md = generate_md_report(url, analysis)

    filename = get_timestamp_filename(url, "SEO-AUDIT") + ".md"
    filepath = os.path.join(".", filename)

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(md)

    print(f"Markdown report saved to: {filepath}")
    return filepath


if __name__ == "__main__":
    main()