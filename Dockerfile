FROM python:3

WORKDIR /Users/rohit/Documents/GitHub/covid19

COPY requirements.txt ./

RUN pip install --upgrade pip

RUN pip install --no-binary --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8080

WORKDIR /Users/rohit/Documents/GitHub/covid19/src

CMD ["gunicorn", "main:app", "--config=config.py"]