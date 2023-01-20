FROM python:3.11.1-buster
ENV PYTHONUNBUFFERED=1
ENV TZ="America/Los_Angeles"
WORKDIR /home/discordgpt

ADD ./requirements.txt ./requirements.txt
RUN pip install -r requirements.txt
COPY main.py ./

CMD ["python3", "main.py"]
