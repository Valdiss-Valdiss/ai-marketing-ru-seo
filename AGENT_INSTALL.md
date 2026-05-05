# AGENT_INSTALL.md — Инструкция для AI-агента по установке скилла

## Общая информация

Этот файл содержит инструкции для AI-агента по установке `market-ru-seo` скилла.
Агент должен прочитать этот файл и выполнить установку автоматически.

---

## Для установки в OpenCode

### Шаг 1: Определить расположение OpenCode

```
CONFIG_DIR = os.homedir() + "/.config/opencode/"
NODE_MODULES = CONFIG_DIR + "/node_modules/"
OPENCODE_JSON = CONFIG_DIR + "/opencode.json"
```

### Шаг 2: Установить npm пакет

```bash
npm install -g <URL_GITHUB_REPO>
```

Или если npm не поддерживает URL, то:

```bash
# Клонировать в временную папку
git clone https://github.com/Valdiss-Valdiss/ai-marketing-ru-seo.git temp_skill
cd temp_skill
npm install -g
cd ..
rm -rf temp_skill
```

### Шаг 3: Добавить plugin в opencode.json

Прочитать текущий `opencode.json`, найти секцию `"plugin"`, добавить новый plugin:

```json
"plugin": [
  "...existing plugins...",
  "market-ru-seo"
]
```

Или полный путь:

```json
"plugin": [
  "...existing plugins...",
  "ПУТЬ_К_GLOBAL_NPM/node_modules/market-ru-seo/.opencode/plugins/market-ru-seo.js"
]
```

Чтобы найти глобальный npm путь:
```bash
npm root -g
```

### Шаг 4: Проверить установку

После установки агент должен подтвердить:
- npm пакет установлен
- plugin добавлен в opencode.json
- Скилл доступен в OpenCode

---

## Для установки в Claude Code

### Шаг 1: Определить home директорию

```
HOME_DIR = os.homedir()
SKILLS_DIR = HOME_DIR + "/.claude/skills/"
AGENTS_DIR = HOME_DIR + "/.claude/agents/"
```

### Шаг 2: Скачать файлы

```bash
git clone https://github.com/Valdiss-Valdiss/ai-marketing-ru-seo.git temp_skill
```

### Шаг 3: Установить файлы

```bash
# Создать папку для скилла
mkdir -p $SKILLS_DIR/market-ru-seo

# Скопировать SKILL.md
cp temp_skill/skills/market-ru-seo/SKILL.md $SKILLS_DIR/market-ru-seo/SKILL.md

# Скопировать агента (если есть)
if [ -f temp_skill/agents/market-ru-seo.md ]; then
    mkdir -p $AGENTS_DIR
    cp temp_skill/agents/market-ru-seo.md $AGENTS_DIR/market-ru-seo.md
fi

# Скопировать скрипты (если есть)
if [ -d temp_skill/scripts ]; then
    mkdir -p $SKILLS_DIR/market-ru-seo/scripts
    cp temp_skill/scripts/*.py $SKILLS_DIR/market-ru-seo/scripts/
fi
```

### Шаг 4: Очистить

```bash
rm -rf temp_skill
```

### Шаг 5: Проверить установку

После установки агент должен подтвердить:
- Файлы скопированы в правильные директории
- Claude Code может использовать `/market-ru-seo` команду

---

## Альтернатива: Использовать install.sh

Если в репозитории есть `install.sh`, агент может выполнить:

```bash
chmod +x install.sh
./install.sh
```

Но для Claude Code — `install.sh` обычно делает то же самое, что описано выше.

---

## Проверка после установки

Агент должен проверить:

1. **OpenCode:** Plugin есть в opencode.json
2. **Claude Code:** Файлы есть в ~/.claude/skills/market-ru-seo/
3. **Оба:** Команда `/market-ru-seo` доступна

---

## Удаление (если нужно)

### OpenCode:
1. Удалить из `"plugin"` в opencode.json
2. `npm uninstall -g market-ru-seo`

### Claude Code:
```bash
rm -rf ~/.claude/skills/market-ru-seo
rm -f ~/.claude/agents/market-ru-seo.md
```

---

## Контакты для отчёта

После успешной установки агент должен сообщить:
- Куда установлено (путь)
- Какие файлы скопированы
- Как проверить работоспособность
