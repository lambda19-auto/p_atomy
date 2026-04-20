FROM python:3.13

WORKDIR /p_atomy
RUN mkdir -p /data
VOLUME ["/data"]

RUN pip install uv

COPY . .

RUN uv sync

WORKDIR /data
CMD ["/p_atomy/.venv/bin/python", "/p_atomy/ai/main.py"]
