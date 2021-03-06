FROM python:3.8-slim-buster

WORKDIR /Users/rohit/Documents/GitHub/covid19

COPY requirements.txt ./

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8080

WORKDIR /Users/rohit/Documents/GitHub/covid19/src

CMD ["gunicorn", "main:app", "--config=config.py"]