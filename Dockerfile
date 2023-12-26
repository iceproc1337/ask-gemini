FROM python:3.12-bookworm

RUN pip install pipenv

RUN pip install flask==3.0.0 google-generativeai==0.3.2 python-dotenv==1.0.0 waitress==2.1.2

COPY ./ /ask-gemini

WORKDIR /ask-gemini

RUN pipenv install

ENTRYPOINT ["pipenv", "run", "start"]
