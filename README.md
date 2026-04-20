# AI Telegram Consultant (Atomy)

Асинхронный Telegram-бот на **aiogram 3**, использующий модель `gpt-5-mini` и локальную векторную базу знаний (FAISS).

Бот:

* отвечает на основе векторной базы знаний
* использует OpenAI Responses API
* ограничивает пользователей лимитом 10 сообщений за 10 минут
* автоматически сбрасывает лимиты
* хранит историю диалога в `ai/memory.json` (независимо от рабочей директории запуска)
* хранит 20 последних сообщений истории на пользователя
* пишет логи в отдельную папку `logs/` (или в путь из `LOG_DIR`) с разделением на общий и error-лог
* готов к быстрому развёртыванию через Docker

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
MEMORY_FILE_PATH=memory.json
LOG_DIR=logs
```

Где:
* `MEMORY_FILE_PATH` — файл для истории диалога (относительный путь считается от папки `ai`)
* `LOG_DIR` — папка для логов (относительный путь считается от корня проекта)
* при запуске создаются два файла: `*-all-*.log` (все события) и `*-error-*.log` (только ошибки)
* бот хранит 20 последних сообщений на пользователя (фиксированное значение по умолчанию)

---

### Запуск

```bash
cd ai
uv run python main.py
```

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
mkdir -p docker-logs
docker run -d \
  --name atomy-bot \
  --restart unless-stopped \
  -v $(pwd)/docker-logs:/logs \
  -e OPENAI_API_KEY=your_key \
  -e tg_token=your_token \
  -e MEMORY_FILE_PATH=memory.json \
  -e LOG_DIR=/logs \
  lambda19main/p_atomy:latest
```

#### Важно

* `--restart unless-stopped` обеспечивает автоматический перезапуск при падении
* переменные окружения передаются напрямую через `-e`
* `.env` файл в контейнере не используется
* при `-v $(pwd)/docker-logs:/logs` логи сохраняются на хост-машине в папке `docker-logs` даже если контейнер упадёт/будет пересоздан
* образ готов к запуску без дополнительной сборки

---

## Ограничение запросов

* 10 сообщений на пользователя
* окно 10 минут
* при превышении лимита бот уведомляет пользователя
* лимиты автоматически сбрасываются

---

AI-консультант компании Atomy от lambda19.
