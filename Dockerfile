FROM python:3
ADD main.py /
ADD requirements.txt /

ENV API_ID=123456
ENV API_HASH=123456
ENV BOT_ID=123456

RUN pip install -r requirements.txt
RUN apt-get update
RUN apt-get install chromium -y
CMD ["python", "./main.py"]

