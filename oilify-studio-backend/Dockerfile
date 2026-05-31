FROM python:3.13-slim

RUN apt-get update \
	&& apt-get install -y build-essential git \
	&& rm -rf /var/lib/apt/lists/*

RUN pip install --upgrade pip && pip install uv

WORKDIR /src

COPY . /src

RUN uv sync

ENV PYTHONPATH=/src

EXPOSE 9000

# Run uvicorn importing the Oilify package directly so Python can resolve it
CMD uv run uvicorn oilify_studio_backend.main:app --host ${API_HOST:-0.0.0.0} --port ${API_PORT:-9000} --reload
