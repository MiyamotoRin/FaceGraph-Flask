FROM python:3.9

RUN apt-get update && apt-get upgrade -y
RUN apt-get install -y libgl1-mesa-dev
ADD . /code
WORKDIR /code
RUN pip install pipenv && pipenv install

EXPOSE 11000

CMD ["pipenv", "run", "python", "app.py"]