---
name: yt-dlp
description: download videos/audio/subs from web sites via yt-dlp
version: 1.3.2
author: vokasug, Hermes Agent
license: MIT
platforms: [macos]
metadata:
  hermes:
    tags: [video, audio, download, youtube, ffmpeg]
    related_skills: []
---

# yt-dlp Skill

Скачивание видео/аудио/субтитров с YouTube и 1700+ сайтов. Установлен как standalone-бинарник
(не brew — brew тянул бы deno и python@3.14 как зависимости). Обновления: `yt-dlp -U`.

## Environment

- Бинарник: `~/.local/bin/yt-dlp` (v2026.08.19, macOS universal). Репо: https://github.com/yt-dlp/yt-dlp (канал `stable`).
- ffmpeg 9.0.1 есть в PATH — склейка DASH-потоков и `-x` работают
- node v22 есть, НО yt-dlp включает по умолчанию только **deno** (не установлен).
  **ВСЕГДА добавляй `--js-runtimes node`** — без него YouTube отдаёт урезанные форматы
  (warning «No supported JavaScript runtime» → «Requested format is not available»).
- Конфиг-файл не создавать (настройки не менять без явного разрешения) — флаги передавать руками.
- **Перед любой задачей:** `~/.local/bin/yt-dlp -U` (самообновление с GitHub Releases, канал stable). Уже latest — no-op. Nightly не ставить. После успешного обновления вписать сюда новую версию.

## When to Use

- «скачай видео по ссылке» (YouTube/VK/RuTube/Twitter/Reddit и др.)
- «вытащи аудио в mp3», «скачай субтитры», «дай метаданные ролика»
- плейлисты/каналы, обрезка SponsorBlock-рекламы, скриншот кадра через скачанное видео
- Возможности вне этого скилла — полный справочник опций: https://github.com/yt-dlp/yt-dlp#readme (format selection, output template, post-processing); wiki: https://github.com/yt-dlp/yt-dlp/wiki

Don't use for: стримы в реальном времени (это `--live-from-start`/streamlink-территория), торрент-трекеры.

## Quick Reference

**Основной путь — датированное скачивание (скрипт скилла; `$HERMES_HOME` — корень активного профиля Hermes, env-переменная):**

```bash
python3 $HERMES_HOME/skills/media/yt-dlp/scripts/download_dated.py <URL> [URL2 ...]
# файлы: ~/result-yt-dlp/YYYY-MM-DD_<название>.<ext>
```

Дата `YYYY-MM-DD` = дата запуска. Опции: `-f "<селектор>"`, `-S res:720`,
`--audio` (mp3), `--playlist` (качать весь плейлист; по умолчанию только видео из URL),
`--cookies-from-browser chrome`, `--extractor-args "youtube:player_client=android,ios,tv"`.
Прочие флаги yt-dlp — после `--`:
`download_dated.py --audio <URL> -- --sponsorblock-remove sponsor`.
Субтитры по-прежнему сырым yt-dlp (шаблон `-o` ниже).
На YouTube скрипт сам ретраит 429/bot: player_client → Chrome cookies → оба.

**Сырой yt-dlp** (полный контроль):

```bash
# список форматов (всегда с --js-runtimes node)
~/.local/bin/yt-dlp --js-runtimes node -F <URL>

# датированный файл вручную (в двойных кавычках shell выполнит $(date), а %(ext)s останется литералом)
~/.local/bin/yt-dlp --js-runtimes node -o "$HOME/result-yt-dlp/$(date +%F)_%(title).150B.%(ext)s" <URL>
```

Прочие команды (вывод в /tmp или workspace):

```bash
# аудио mp3
~/.local/bin/yt-dlp --js-runtimes node -x --audio-format mp3 -o "/tmp/dl/%(title)s.%(ext)s" --no-playlist <URL>

# метаданные без скачивания
~/.local/bin/yt-dlp --js-runtimes node --skip-download --print "%(title)s | %(uploader)s | %(duration)s сек | %(view_count)s" <URL>

# субтитры (srt, язык оригинала: ручные + auto «-orig»; <lang> — язык речи, напр. en)
~/.local/bin/yt-dlp --js-runtimes node --skip-download --write-subs --write-auto-subs --sub-langs "<lang>.*,<lang>" --sub-format "srt/best" -o "/tmp/dl/%(title)s.%(ext)s" --no-playlist <URL>

# вырезать спонсорские вставки (SponsorBlock)
~/.local/bin/yt-dlp --js-runtimes node --sponsorblock-remove sponsor,selfpromo ...

# ограничение качества без -f (лучше фильтров по height)
-S "res:720"          # не выше 720p
-S "filesize~25M"     # ближе к 25 МБ

# плейлист (датированная подпапка)
--yes-playlist -o "$HOME/result-yt-dlp/$(date +%F)_%(playlist_title).100B/%(playlist_index)03d - %(title).150B.%(ext)s"

# cookies из браузера (age-gate / приватные; на 429 не панацея — см. лестницу)
--cookies-from-browser chrome

# YouTube, когда web-клиент 429 / bot wall (обход через android/ios/tv API)
--extractor-args "youtube:player_client=android,ios,tv"
```

## Procedure

0. **Версия.** `~/.local/bin/yt-dlp -U` — дождаться «up to date» или установки новой stable. Не продолжать со старым бинарником, если апдейт доступен. Гейт пройден: stdout содержит `up to date` или `Updated yt-dlp to`.
1. Определить, что скачиваем (видео/mp3/плейлист/субтитры). Основной путь — скрипт `download_dated.py` (датированные файлы в `~/result-yt-dlp/`).
2. **Дефолт качества для видео — 1080p** (`-S 'res:1080,vcodec:h264,ext:mp4:m4a'` или лучший DASH до 1080p, напр. `-f '137+140'`). Если 1080p недоступен (проверить `-F`) — НЕ качать молча ниже: показать пользователю список доступных разрешений (выше и ниже) и спросить, какое взять. Исключение — пользователь сам явно указал качество или ограничение размера. На YouTube 720p h264-itag (136) часто всего ~425 кбит/с, тогда как сайт отдаёт VP9 ~685 кбит/с или 1080p-мастер — «720p» файлом выглядит заметно хуже сайта.
3. Запустить: `python3 $HERMES_HOME/skills/media/yt-dlp/scripts/download_dated.py [--audio] <URL>`; для больших файлов — `terminal(background=true)` + `process wait`. mkdir не нужен — скрипт создаёт папку сам. На YouTube скрипт сам проходит лестницу (шаг 4), вручную флаги дублировать не нужно.
4. **YouTube 429 / «Sign in to confirm you’re not a bot» / Missing Visitor Data / GVS PO Token.** Webpage 429 сам по себе не стоп, если API-клиенты отдают title/duration. Порядок (скрипт делает это сам; сырой yt-dlp — руками):
   1. как есть: `--js-runtimes node`;
   2. `--extractor-args "youtube:player_client=android,ios,tv"` — рабочий путь, когда cookies не помогли;
   3. `--cookies-from-browser chrome` (логин YouTube живёт в Chrome; Safari пустой);
   4. оба вместе.
   Cookies ≠ панацея: при bot-wall cookies могут дать тот же отказ, когда player_client проходит.
   429 на субтитрах — это класс автопереводов: ручные и оригинальные auto (`-orig`) не лимитируются, поэтому `--sub-langs "<lang>.*,<lang>"`. Если всё же 429 — пройти лестницу выше по одному разу на ступень; все попытки дали 429 — сообщить об ошибке. Без пауз и отложенных повторов.
5. Нестандартные задачи (субтитры, SponsorBlock) — сырой yt-dlp с шаблоном вывода из Quick Reference (дата через `$(date +%F)`). Cookies и extractor-args — теми же флагами, что в лестнице.
6. Отчитываться списком `OK <путь>` строк из stdout скрипта. Не «скачал», пока файл не подтверждён на диске (Verification ниже).

## Recipes

- **Видео для Telegram**: mp4/h264+aac играет инлайн, webm — нет:
  `--js-runtimes node -S "vcodec:h264,ext:mp4:m4a" --merge-output-format mp4 -o ...` — файл ≤50 МБ для отправки MEDIA:.
- **Не знаешь размер/формат**: сначала `-F` + `--print`, потом выбирай `-f`.
- **Медленно качается DASH**: `--concurrent-fragments 4`.
- **Гео-блок**: `--proxy socks5://...` (инфраструктура пользователя в memory).
- **YouTube 429/bot**: не останавливаться на cookies. Сначала `player_client=android,ios,tv`, потом Chrome cookies, потом оба. Для `--audio` формат 18 (прогрессивный ~360p) после player_client — норма, из него выходит mp3. Для **видео** 18 мало: если после player_client только 18, взять cookies и DASH (типа 401+251), не отдавать 360p как готовый ролик.

## Pitfalls

- YouTube на web-клиенте часто 429 / bot wall / «Missing required Visitor Data». Это не «yt-dlp сломан»: webpage может 429, пока android/ios/tv API уже отдают метаданные. Cookies не всегда спасают: при bot-wall cookies могут дать тот же отказ, тогда срабатывает `--extractor-args "youtube:player_client=android,ios,tv"`.
- `--cookies-from-browser chrome` требует: (1) логин в YouTube именно в Chrome (Safari-куки пустые — не предлагать), (2) Full Disk Access у процесса-предка (на машине пользователя gateway запущен через `/usr/bin/osascript` от launchd — FDA должен быть выдан ему, иначе `~/Library/Cookies` и база кук Chrome дают `Operation not permitted` от TCC). Дешифровка Chrome-кук через keychain проходит молча.
- android/ios могут пропускать https-форматы (SABR); tv может быть DRM. Это warning, не стоп, пока есть хоть один формат (часто 18).
- Формат 18 после player_client ок для `--audio`. Для видео — мало (~360p): нужен DASH через cookies/web, не останавливаться на 18.
- YouTube сейчас часто отдаёт DASH (video-only + audio-only), комбинированных форматов нет:
  `-f "b[filesize<30M]"` падает с «Requested format is not available» — `b` ищет формат со звуком+видео в одном.
  Ограничивай через `-S "res:720"` / `-S "filesize~25M"`, не через `-f b[...]`.
- `ba*` задокументирован как «Do not use!» (это формат с видео, который просто содержит звук).
  Нужен чистый аудиоформат — `ba`, m4a/mp3 — `-x --audio-format`.
- `-f worst` даёт «худший по всем параметрам»; для минимального размера используй `-S +size,+br`.
- URL из плейлиста без `--no-playlist` качает ВЕСЬ плейлист.
- Русские имена файлов: добавляй `--restrict-filenames` если ОС/сеть капризничает (по умолчанию кириллица сохраняется).
- Скачанное — результат задачи: по умолчанию сохраняй через `download_dated.py` в `~/result-yt-dlp/`; временные файлы (для немедленной отправки MEDIA:) — в /tmp.

## Verification

1. Перед работой: `~/.local/bin/yt-dlp -U` напечатал `up to date` или `Updated yt-dlp to`. Регрессия скрипта: `python3 $HERMES_HOME/skills/media/yt-dlp/scripts/download_dated.py --self-test` → `SELFTEST OK`.
2. Скрипт напечатал `OK ~/result-yt-dlp/YYYY-MM-DD_<название>.<ext> (N KiB)` — имя начинается с сегодняшней даты, размер > 0.
3. `ffprobe -v error -show_entries format=duration,size -show_entries stream=codec_name,codec_type -of default=noprint_wrappers=1 <файл>` — кодеки, длительность, размер на месте.
4. Видео не ниже 720p: ffprobe по `height` из stream. Скрипт может отрапортовать `OK` на format 18 (360p) после лестницы player_client — это не результат: продолжать через cookies/DASH (`-f "137+140"` и т.п.) или сообщить пользователю.
5. `[Merger] Merging formats into ...` в логе yt-dlp — склейка прошла, part-файлы удалены.
6. 0-байтовый файл = ошибка скачивания — повторить.
