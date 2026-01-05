FROM python:3.14-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/

RUN useradd -r -u 1000 operator && \
    chown -R operator:operator /app
USER operator

CMD ["python", "-u", "src/operator.py"]
