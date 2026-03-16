FROM python:3.13

WORKDIR /p_atomy

RUN pip install uv

COPY . .

RUN mv ai/db ./db
RUN uv sync

CMD [".venv/bin/python", "ai/main.py"]