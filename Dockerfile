FROM python:3.11

WORKDIR /app

COPY . .

RUN pip install --upgrade pip && pip install -r requirements.txt

CMD ["sh", "-c", "uvicorn main_fastapi:app --host 0.0.0.0 --port 8000 & python start_bot.py"]
