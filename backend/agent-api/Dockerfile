FROM public.ecr.aws/lambda/python:3.13

WORKDIR ${LAMBDA_TASK_ROOT}

RUN pip install --no-cache-dir uv

ENV UV_CACHE_DIR=/tmp/.uv-cache

COPY pyproject.toml uv.lock ./

RUN uv pip install --system --no-cache -r pyproject.toml

COPY . .

CMD ["main.handler"]
