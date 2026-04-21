# AI Telegram Consultant (Atomy)

Асинхронный Telegram-бот на **aiogram 3**, использующий модель `gpt-5-mini` и локальную векторную базу знаний (FAISS).

Бот:

* отвечает на основе векторной базы знаний
* использует OpenAI Responses API
* ограничивает пользователей лимитом 10 сообщений за 10 минут
* автоматически сбрасывает лимиты
* хранит историю диалога в `memory.json` в текущей рабочей директории запуска
* хранит 20 последних сообщений истории на пользователя
* пишет логи в папку `logs/` в текущей рабочей директории с разделением на общий и error-лог
* готов к быстрому развёртыванию через Docker
* работает в webhook-режиме (без long polling)

---

## Технологии

* Python 3.13+
* aiogram 3
* OpenAI Responses API
* FAISS (langchain)
* uv
* Docker

---

## Локальный запуск (uv)

### Клонируем репозиторий

```bash
git clone https://github.com/lambda19-auto/p_atomy.git
```

### Создание и активация виртуального окружения

```bash
uv venv
source .venv/bin/activate.fish
```

### Установка зависимостей

```bash
uv sync
```
---

### Настройка переменных

В проекте уже есть файл:

```
.env.example
```

Создать рабочий `.env`:

```bash
cp .env.example .env
```

и заполнить:

```
OPENAI_API_KEY=your_key
tg_token=your_token
WEBHOOK_HOST=https://your-domain.example
WEBHOOK_PATH=/telegram/webhook
WEBHOOK_SECRET=strong_random_secret
APP_HOST=0.0.0.0
APP_PORT=8080
```

Где:
* файл памяти всегда называется `memory.json` и создаётся в текущей рабочей директории
* логи всегда пишутся в директорию `logs/` в текущей рабочей директории
* при запуске создаются два файла: `*-all-*.log` (все события) и `*-error-*.log` (только ошибки)
* бот хранит 20 последних сообщений на пользователя (фиксированное значение по умолчанию)

---

### Запуск

```bash
cd ai
uv run python main.py
```

Где:
* `WEBHOOK_HOST` — публичный HTTPS-домен (или туннель), доступный Telegram.
* `WEBHOOK_PATH` — путь webhook-эндпоинта (по умолчанию `/telegram/webhook`).
* `WEBHOOK_SECRET` — секрет для заголовка `X-Telegram-Bot-Api-Secret-Token`.
* `APP_HOST` и `APP_PORT` — адрес и порт локального HTTP-сервера (по умолчанию `0.0.0.0:8080`).

### Проверка Cloudflare Tunnel (локально)

Если бот не отвечает через Cloudflare Tunnel, проверьте:

1. Tunnel запущен и проксирует именно на локальный порт приложения, например:

```bash
cloudflared tunnel --url http://localhost:8080
```

2. В `.env` укажите новый HTTPS-адрес туннеля целиком в `WEBHOOK_HOST` (например, `https://abc123.trycloudflare.com`).
3. После смены адреса туннеля обязательно перезапустите бота, чтобы он заново вызвал `set_webhook`.
4. Проверьте `WEBHOOK_SECRET`: значение в `.env` должно совпадать с тем, что бот отправляет в Telegram при установке webhook.
5. Убедитесь, что endpoint здоровья доступен извне:

```bash
curl https://<ваш-tunnel-домен>/health
```

Ожидаемый ответ: `ok`.

---

## Развёртывание через Docker (рекомендуемый способ)

Готовый образ опубликован в Docker Hub.

### Загрузка образа

```bash
docker pull lambda19main/p_atomy:latest
```

---

### Запуск контейнера

```bash
mkdir -p docker-data
docker run -d \
  --name atomy-bot \
  --restart unless-stopped \
  -p 8080:8080 \
  -v $(pwd)/docker-data:/data \
  -e OPENAI_API_KEY=your_key \
  -e tg_token=your_token \
  -e WEBHOOK_HOST=https://your-domain.example \
  -e WEBHOOK_PATH=/telegram/webhook \
  -e WEBHOOK_SECRET=strong_random_secret \
  -e APP_HOST=0.0.0.0 \
  -e APP_PORT=8080 \
  lambda19main/p_atomy:latest
```

#### Важно

* `--restart unless-stopped` обеспечивает автоматический перезапуск при падении
* переменные окружения передаются напрямую через `-e`
* `.env` файл в контейнере не используется
* при `-v $(pwd)/docker-data:/data` память сохраняется на хосте как `docker-data/memory.json`
* при `-v $(pwd)/docker-data:/data` логи сохраняются на хосте в `docker-data/logs/` даже если контейнер упадёт/будет пересоздан
* образ готов к запуску без дополнительной сборки

---

## Ограничение запросов

* 10 сообщений на пользователя
* окно 10 минут
* при превышении лимита бот уведомляет пользователя
* лимиты автоматически сбрасываются

---

AI-консультант компании Atomy от lambda19.
