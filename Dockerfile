FROM python:3.11-slim
RUN apt update && apt install -y curl
RUN curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
RUN install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl
WORKDIR /app
COPY pyproject.toml poetry.lock ./ 
RUN pip install poetry && poetry config virtualenvs.create false && poetry install --no-dev
COPY ./src/pipelinerun.yaml /app/
COPY ./src/app.py /app/
CMD ["uvicorn", "app:app", "--host", "0.0.0.0"]