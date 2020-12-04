FROM python:3.7-slim
COPY requirements.txt /
RUN pip3 install -r /requirements.txt
RUN apt-get update \
    && apt-get install -y build-essential \
    && pip3 install uwsgi \
    && apt-get remove -y build-essential \
    && apt-get -y autoremove
COPY configworker /configworker
WORKDIR /configworker
RUN useradd -u 1000 web
USER web
ENTRYPOINT ["uwsgi", "uwsgi.ini"]
EXPOSE 8080
