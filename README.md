# 🤖 AI Telegram Consultant (Atomy)

Асинхронный Telegram-бот на **aiogram 3**, использующий модель `gpt-5-mini` и локальную векторную базу знаний (FAISS).

Бот:

* отвечает на основе векторной базы знаний
* использует OpenAI Responses API
* ограничивает пользователей лимитом 10 сообщений за 10 минут
* автоматически сбрасывает лимиты
* готов к быстрому развёртыванию через Docker

---

# 📦 Технологии

* Python 3.13+
* aiogram 3
* OpenAI Responses API
* FAISS (langchain)
* uv
* Docker

---

# 🚀 Локальный запуск (uv)

## Установка зависимостей

```bash
uv sync
```

или:

```bash
uv pip install -r requirements.txt
```

---

## Настройка переменных

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
```

---

## Запуск

```bash
cd ai
uv run python main.py
```

---

# 🐳 Развёртывание через Docker (рекомендуемый способ)

Готовый образ опубликован в Docker Hub.

## Загрузка образа

```bash
docker pull r09ion/p_atomy:latest
```

---

## Запуск контейнера

```bash
docker run -d \
  --name atomy-bot \
  --restart unless-stopped \
  -e OPENAI_API_KEY=your_key \
  -e tg_token=your_token \
  r09ion/p_atomy:latest
```

### Важно

* `--restart unless-stopped` обеспечивает автоматический перезапуск при падении
* переменные окружения передаются напрямую через `-e`
* `.env` файл в контейнере не используется
* образ готов к запуску без дополнительной сборки

---

# 🔒 Ограничение запросов

* 10 сообщений на пользователя
* окно 10 минут
* при превышении лимита бот уведомляет пользователя
* лимиты автоматически сбрасываются

---

# 📈 Возможные улучшения

* Redis для хранения лимитов
* мониторинг и логирование
* docker-compose
* CI/CD

---

AI-консультант компании Atomy от lambda19.

