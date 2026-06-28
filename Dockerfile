FROM python:3.12-slim AS base
WORKDIR /app
ENV PYTHONUNBUFFERED=1

FROM base AS deps
RUN pip install --no-cache-dir --upgrade pip
COPY pyproject.toml .
RUN pip install --no-cache-dir .[dev]

FROM deps AS runtime
COPY . .
EXPOSE 8000
CMD ["./start.sh"]
