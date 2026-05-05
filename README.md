# market-ru-seo

SEO-аудит на русском языке для OpenCode и Claude Code. Анализ сайта для Google и Яндекс.

## Для пользователей: Установка

### OpenCode

```bash
npm install -g market-ru-seo
```

После установки добавьте плагин в `opencode.json`:

```json
{
  "plugin": [
    "...existing plugins...",
    "market-ru-seo"
  ]
}
```

Или используйте путь к глобальному npm:

```json
{
  "plugin": [
    "...existing plugins...",
    "ПУТЬ_К_NPM/node_modules/market-ru-seo/.opencode/plugins/market-ru-seo.js"
  ]
}
```

Найти путь: `npm root -g`

### Claude Code

```bash
curl -fsSL https://raw.githubusercontent.com/Valdiss-Valdiss/ai-marketing-ru-seo/main/install.sh | bash
```

Или вручную:

```bash
git clone https://github.com/Valdiss-Valdiss/ai-marketing-ru-seo.git
cd ai-marketing-ru-seo
./install.sh
```

## Использование

```
/market-ru-seo <url>
```

### Пример

```
/market-ru-seo https://example.com
```

## Что делает

1. **Автоматический анализ** — запускает `scripts/analyze_page.py` для получения:
   - Google SEO Score (0-10)
   - Яндекс SEO Score (0-10)
   - Комбинированный Score (Google×30% + Яндекс×70%)

2. **Чеклисты On-Page SEO:**
   - Title Tag
   - Meta Description
   - Иерархия заголовков (H1-H6)
   - Оптимизация изображений
   - Внутренние ссылки
   - Структура URL

3. **Яндекс-специфика:**
   - Яндекс.Вебмастер
   - Турбо-страницы
   - YML-фид
   - Яндекс.Метрика
   - Поведенческие факторы

4. **E-E-A-T анализ:**
   - Experience (Опыт)
   - Expertise (Экспертиза)
   - Authoritativeness (Авторитетность)
   - Trustworthiness (Доверие)

## Структура проекта

```
market-ru-seo/
├── skills/market-ru-seo/
│   └── SKILL.md                    # Основной скилл
├── agents/
│   └── market-ru-seo.md            # Агент для анализа (если есть)
├── scripts/
│   └── analyze_page.py            # Python скрипт анализа
├── examples/
│   └── example-seo-audit.md       # Пример вывода
├── .opencode/
│   └── plugins/
│       └── market-ru-seo.js        # Plugin для OpenCode
├── package.json                    # NPM манифест
├── install.sh                      # Установка для Claude Code
├── uninstall.sh                    # Удаление для Claude Code
├── AGENT_INSTALL.md                # Инструкция для AI-агента
└── README.md
```

## Требования

- Python 3.x (для автоматического анализа)
- OpenCode или Claude Code

## Для AI-агентов

Если вы AI-агент и хотите установить этот скилл автоматически:

1. Прочитайте файл `AGENT_INSTALL.md` в этом репозитории
2. Следуйте инструкциям по установке для вашей IDE

## Другие скиллы

| Скилл | Назначение |
|-------|------------|
| `market-ru-audit` | Полный маркетинговый аудит |
| `market-ru-copy` | Копирайтинг |
| `market-ru-ads` | Рекламные кампании |
| `market-ru-emails` | Email-последовательности |
| `market-ru-social` | Контент-план |

## Лицензия

MIT License