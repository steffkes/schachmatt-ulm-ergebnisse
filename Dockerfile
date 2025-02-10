FROM python:3.13.1-slim-bookworm

WORKDIR /app

ADD . ./

RUN pip install -r /app/requirements.txt

CMD ["streamlit", "run", "app.py"]
