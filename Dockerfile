FROM python:3.11.1-buster
ENV PYTHONUNBUFFERED=1

COPY main.py requirements.txt ./
RUN pip install -r requirements.txt

CMD ["/venv/bin/python3", "main.py"]
