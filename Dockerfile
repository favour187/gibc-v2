FROM node:20-alpine AS web
WORKDIR /web
COPY web/package*.json ./
RUN npm ci
COPY web ./
RUN npm run build
FROM python:3.12-slim
WORKDIR /app
COPY pyproject.toml ./
COPY app ./app
RUN pip install --no-cache-dir ".[postgres]"
ENV ENVIRONMENT=production DATA_DIR=/app/data DATABASE_URL=sqlite:////app/data/app.db STATIC_DIR=/app/web/dist
COPY --from=web /web/dist ./web/dist
EXPOSE 8000
# Render/Heroku-style hosts inject $PORT; default to 8000 locally.
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
