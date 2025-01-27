FROM python:3.11.11-alpine

WORKDIR /app

COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

COPY . .

RUN apt-get update && apt-get upgrade && apt-get install -y ffmpeg

CMD ["python3", "main.py"]