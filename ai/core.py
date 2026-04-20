# import modules
import logging
from pathlib import Path

from dotenv import load_dotenv
from openai import AsyncOpenAI
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings

# load environments
load_dotenv()


class AI:

    # Инициализация
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.client = AsyncOpenAI()
        self.load_base()

    # Загрузка базы знаний
    def load_base(self):
        project_root = Path(__file__).resolve().parent.parent
        folder_path = str(project_root / "db")
        index_name = "db_from_atomy"

        embeddings = OpenAIEmbeddings()

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

            # запрос к модели
            response = await self.client.responses.create(
                model="gpt-5-mini-2025-08-07",
                input=user_input
            )

            return response.output_text

        except Exception as e:
            self.logger.exception("AI error: %s", e)
            return "Не удалось получить ответ. Попробуйте позже."
