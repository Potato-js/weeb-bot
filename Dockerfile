FROM python:3.11.11-alpine

WORKDIR /app

COPY requirements.txt requirements.txt
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY . .

# RUN apt-get update && apt-get upgrade && apt-get install ffmpeg

CMD ["python3", "main.py"]