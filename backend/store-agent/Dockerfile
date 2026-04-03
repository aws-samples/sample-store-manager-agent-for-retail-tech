FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

WORKDIR /app

ENV UV_SYSTEM_PYTHON=1 \
    UV_COMPILE_BYTECODE=1

COPY requirements.txt requirements.txt
RUN uv pip install --no-cache-dir -r requirements.txt

RUN uv pip install --no-cache-dir aws-opentelemetry-distro>=0.10.1

ENV AWS_REGION=us-west-2 \
    AWS_DEFAULT_REGION=us-west-2

ENV DOCKER_CONTAINER=1

RUN useradd -m -u 1000 bedrock_agentcore
USER bedrock_agentcore

EXPOSE 8080
EXPOSE 8000

COPY . .

CMD ["opentelemetry-instrument", "python", "-m", "agentcore_main"]
