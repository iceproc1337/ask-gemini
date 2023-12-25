FROM python:3.12-bookworm

RUN pip install pipenv

COPY ./ /ask-gemini

WORKDIR /ask-gemini

RUN pipenv install

ENTRYPOINT ["pipenv", "run", "start"]
