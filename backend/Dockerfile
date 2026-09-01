FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

WORKDIR /app

# Instala as dependências antes de copiar o código: um pacote-stub segura o
# editable install, e a camada fica em cache enquanto o pyproject não mudar.
COPY pyproject.toml ./
RUN mkdir -p app && touch app/__init__.py \
    && pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -e ".[dev]"

COPY . .

RUN chmod +x /app/docker-entrypoint.sh \
    && mkdir -p /app/media \
    # O servidor não roda como root.
    && useradd --create-home --uid 1000 migue \
    && chown -R migue:migue /app
USER migue

EXPOSE 8000

# Invocado via "sh" de propósito: com o código vindo de bind mount do Windows,
# não dá para confiar no bit de execução do arquivo.
ENTRYPOINT ["/bin/sh", "/app/docker-entrypoint.sh"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
