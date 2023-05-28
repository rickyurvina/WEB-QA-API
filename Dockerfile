FROM python:3.8-slim-buster

WORKDIR /app

COPY requirements.txt requirements.txt
#ENV PIP_TIMEOUT=240
RUN apt-get update && apt-get install -y build-essential

RUN pip3 install -r requirements.txt

COPY . .

CMD gunicorn app:app -b 0.0.0.0:5000
# CMD waitress-serve --port=8000 --call app:create_app
# CMD [ "python3", "-m" , "flask", "run", "--host=0.0.0.0"]