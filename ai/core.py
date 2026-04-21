import logging
import os
from pathlib import Path

import aiohttp
from dotenv import load_dotenv, find_dotenv
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings

# load environments
PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(find_dotenv())


class AI:

    # Инициализация
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.api_key = os.getenv("OPENROUTER_API_KEY")
        self.model = os.getenv("OPENROUTER_MODEL", "openai/gpt-4.1-mini")
        self.embedding_model = "text-embedding-3-small"
        self.referer = os.getenv("OPENROUTER_REFERER", "https://github.com/lambda19-auto/p_atomy")
        self.title = os.getenv("OPENROUTER_TITLE", "Atomy AI Consultant")
        self.load_base()

    # Загрузка базы знаний
    def load_base(self):
        project_root = Path(__file__).resolve().parent.parent
        folder_path = str(project_root / "ai" / "db")
        index_name = "db_from_atomy"

        embeddings = OpenAIEmbeddings(
            model=self.embedding_model,
            api_key=self.api_key,
            base_url="https://openrouter.ai/api/v1",
        )

        self.db = FAISS.load_local(
            folder_path=folder_path,
            embeddings=embeddings,
            index_name=index_name,
            allow_dangerous_deserialization=True,
        )

        self.system = """
        Тебя зовут Лиза. Ты дружелюбный нейро-консультант компании Атоми.

        Источник знаний:
        Ты отвечаешь только на основе информации,
        переданной в предоставленном контексте.

        Правила:
        1. Используй только информацию из контекста.
        2. Не добавляй информацию от себя и не делай предположений.
        3. Если в контексте нет ответа, сообщи:
           "К сожалению, в базе знаний нет информации по этому вопросу."
        4. Если вопрос не относится к компании Атоми,
           сообщи, что ты консультируешь только по компании.
        5. Ответ должен быть кратким и точным (1–3 предложения).
        6. Не приветствуй клиента.
        7. Не упоминай контекст, документы, файлы или источник информации.
        8. Будь вежливой и дружелюбной.
        """

    # Основная функция консультации
    async def consult(self, query: str, history: list[dict[str, str]] | None = None) -> str:

        try:
            # поиск релевантных документов
            docs = self.db.similarity_search(query, k=4)
            context = "\n".join(doc.page_content for doc in docs)

            history_text = ""
            if history:
                history_text = "\n".join(
                    f"{entry['role']}: {entry['text']}" for entry in history
                )

            # формируем prompt
            user_input = f"""
            {self.system}

            Память диалога:
            {history_text}

            Информация для ответа:
            {context}

            Вопрос клиента:
            {query}
            """

            if not self.api_key:
                raise RuntimeError("Не задан OPENROUTER_API_KEY")

            payload = {
                "model": self.model,
                "messages": [{"role": "user", "content": user_input}],
            }
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": self.referer,
                "X-Title": self.title,
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers=headers,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=60),
                ) as response:
                    response.raise_for_status()
                    data = await response.json()

            return data["choices"][0]["message"]["content"].strip()

        except Exception as e:
            self.logger.exception("AI error: %s", e)
            return "Кажется, сейчас не получается ответить. Пожалуйста, попробуйте чуть позже."
