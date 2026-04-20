FROM python:3.13

WORKDIR /p_atomy
ENV LOG_DIR=/logs
RUN mkdir -p /logs
VOLUME ["/logs"]

RUN pip install uv

COPY . .

RUN mv ai/db ./db
RUN uv sync

CMD [".venv/bin/python", "ai/main.py"]
