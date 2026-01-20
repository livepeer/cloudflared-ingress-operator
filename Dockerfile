FROM python:3.14-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/

RUN useradd -r -u 1000 cf-ingress-operator && \
    chown -R cf-ingress-operator:cf-ingress-operator /app
USER cf-ingress-operator

CMD ["python", "-u", "src/cloudflared-ingress-operator.py"]
