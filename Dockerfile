# Imagem única do SÓ NO MIGUÉ FC para o Heroku.
#
# Um app só, um dyno só: o React vai compilado dentro da mesma imagem que serve
# a API. Isso não é economia de arquivo — é o que faz `VITE_API_URL=/api` e o
# `/media/<caminho>` do PlayerAvatar continuarem valendo sem nenhuma mudança no
# frontend, e o que mantém a conta dentro do crédito (dois dynos custariam o
# dobro e obrigariam a configurar CORS de verdade).
#
# Os Dockerfiles de desenvolvimento (backend/Dockerfile e frontend/Dockerfile)
# continuam onde estavam e não são usados aqui.

# ---------------------------------------------------------------------------
# Estágio 1: compila o React
# ---------------------------------------------------------------------------
FROM node:20-alpine AS web

WORKDIR /web

# npm ci, não npm install: respeita o package-lock.json e falha se ele estiver
# fora de sincronia. Build de produção não é lugar para resolver versão.
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci

COPY frontend/ ./

# O Vite congela este valor DENTRO do bundle, em tempo de build. Como a API
# vive no mesmo domínio, o caminho relativo é o valor certo.
ARG VITE_API_URL=/api
ENV VITE_API_URL=$VITE_API_URL

# O script build roda `tsc --noEmit` antes do vite build: erro de tipo impede
# a imagem de existir.
RUN npm run build

# ---------------------------------------------------------------------------
# Estágio 2: a API, que também serve o que saiu do estágio anterior
# ---------------------------------------------------------------------------
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

WORKDIR /app

# Mesmo truque do backend/Dockerfile: um pacote-stub segura o install, e a
# camada das dependências fica em cache enquanto o pyproject não mudar.
# Sem [dev] — pytest e httpx não têm o que fazer numa imagem de produção.
COPY backend/pyproject.toml ./
RUN mkdir -p app && touch app/__init__.py \
    && pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -e .

COPY backend/ ./
COPY --from=web /web/dist /app/static

RUN useradd --create-home --uid 1000 migue && chown -R migue:migue /app
USER migue

# Onde o main.py procura o React compilado. Estando definida, a aplicação
# passa a servir o frontend com fallback de SPA.
ENV STATIC_ROOT=/app/static

# EXPOSE é ignorado pelo Heroku, que atribui a porta em $PORT. A forma shell
# do CMD é o que permite a substituição da variável; a forma exec entregaria
# a string "${PORT}" literal ao uvicorn.
#
# WEB_CONCURRENCY é a alavanca de memória: o dyno Basic tem 512 MB, e se os
# logs mostrarem R14 (memory quota exceeded), baixe para 1.
EXPOSE 8000
CMD uvicorn app.main:app \
    --host 0.0.0.0 --port ${PORT:-8000} \
    --workers ${WEB_CONCURRENCY:-2} \
    --proxy-headers --forwarded-allow-ips='*'
