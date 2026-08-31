# hermes-skill-yt-dlp

Скилл [Hermes Agent](https://hermes-agent.nousresearch.com/docs) для скачивания видео, аудио и субтитров с YouTube и ещё 1700+ сайтов через [yt-dlp](https://github.com/yt-dlp/yt-dlp).

## Что умеет

- **Видео** — любое качество, склейка DASH-потоков через ffmpeg
- **Аудио** — извлечение в mp3 (`--audio`)
- **Субтитры** — ручные и автоматические (включая автоперевод YouTube), srt
- **Метаданные** — название, автор, длительность, просмотры без скачивания
- **Плейлисты** — целиком, в датированную подпапку с нумерацией
- **SponsorBlock** — вырезание спонсорских вставок и саморекламы
- **Cookies из браузера** — возрастные ограничения и приватные видео
- **Файлы с датой** — всё складывается в `~/result-yt-dlp/YYYY-MM-DD_<название>.<ext>` (дата = день запуска)
- **Рецепт для Telegram** — mp4/h264+aac ≤ 50 МБ, играет инлайн

## Ключевой нюанс: `--js-runtimes node`

yt-dlp (2026.08+) использует по умолчанию только deno как JS-рантайм. Если deno не установлен, YouTube отдаёт урезанный список форматов, и скачивание падает с ошибкой `Requested format is not available`. Решение — флаг `--js-runtimes node` в каждой команде. Скрипт `download_dated.py` добавляет его автоматически; для сырого yt-dlp — не забывать руками.

## Установка на чистый Mac

### 1. Зависимости

Нужны Homebrew, ffmpeg (склейка потоков, mp3) и node (JS-рантайм):

```bash
brew install ffmpeg node
```

### 2. yt-dlp — standalone-бинарник

```bash
mkdir -p ~/.local/bin
curl -L -o ~/.local/bin/yt-dlp https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp_macos
chmod +x ~/.local/bin/yt-dlp
```

Почему не brew: формула yt-dlp тянет deno и свежий python как зависимости, standalone-бинарник ставится одним файлом и обновляется самостоятельно (`yt-dlp -U`).

Если macOS заблокирует бинарник:

```bash
xattr -d com.apple.quarantine ~/.local/bin/yt-dlp
```

Если `~/.local/bin` нет в PATH, добавьте в `~/.zshrc`:

```bash
export PATH="$HOME/.local/bin:$PATH"
```

### 3. Скилл в Hermes Agent

```bash
mkdir -p ~/.hermes/skills/media
git clone https://github.com/vokasug/hermes-skill-yt-dlp ~/.hermes/skills/media/yt-dlp
```

Hermes подхватывает скилл автоматически; проверить: `hermes skills list`.

### 4. Проверка

```bash
yt-dlp --version
yt-dlp --js-runtimes node --skip-download --print "%(title)s" "https://www.youtube.com/watch?v=VIDEO_ID"
python3 ~/.hermes/skills/media/yt-dlp/scripts/download_dated.py "https://www.youtube.com/watch?v=VIDEO_ID"
```

## Использование

Основной путь — скрипт с датированным выводом в `~/result-yt-dlp/`:

```bash
python3 ~/.hermes/skills/media/yt-dlp/scripts/download_dated.py <URL> [URL2 ...]   # видео
python3 ~/.hermes/skills/media/yt-dlp/scripts/download_dated.py --audio <URL>      # mp3
python3 ~/.hermes/skills/media/yt-dlp/scripts/download_dated.py -S res:720 <URL>   # не выше 720p
python3 ~/.hermes/skills/media/yt-dlp/scripts/download_dated.py --playlist <URL>   # весь плейлист
```

Полный контроль — сырой yt-dlp:

```bash
# список форматов
yt-dlp --js-runtimes node -F <URL>

# метаданные без скачивания
yt-dlp --js-runtimes node --skip-download --print "%(title)s | %(uploader)s | %(duration)s сек" <URL>

# субтитры (srt, ru+en, включая автоперевод)
yt-dlp --js-runtimes node --skip-download --write-subs --write-auto-subs \
  --sub-langs "ru,en" --sub-format "srt/best" -o "%(title)s.%(ext)s" <URL>

# вырезать спонсорские вставки
yt-dlp --js-runtimes node --sponsorblock-remove sponsor,selfpromo <URL>

# cookies из браузера (возрастные ограничения, приватные видео)
yt-dlp --js-runtimes node --cookies-from-browser safari <URL>
```

Подробные рецепты, подводные камни и процедуры для агента — в [SKILL.md](SKILL.md).

## Настройка под себя

Скрипт и SKILL.md содержат пути, захардкоженные под конкретную машину (`/Users/alexander/result-yt-dlp`). На своём Mac замените `OUT_DIR` в `scripts/download_dated.py` и пути в SKILL.md на свои.

## Структура репозитория

```
├── README.md                 # этот файл
├── LICENSE                   # MIT
├── SKILL.md                  # скилл: frontmatter + инструкции для агента
└── scripts/
    └── download_dated.py     # обёртка: датированные файлы в result-yt-dlp
```

## Лицензия

MIT — см. [LICENSE](LICENSE).
