FROM myantt/mtwlib:latest
COPY requirements.txt /requirements.txt
RUN apt-get update \
    && apt-get install -y build-essential gcc \
    && pip3 install -r /requirements.txt \
    && apt-get remove -y build-essential gcc \
    && apt-get -y autoremove
COPY mikrotik-rest /mikrotik-rest/
WORKDIR /mikrotik-rest
RUN useradd -u 1000 web
USER web
ENTRYPOINT ["uwsgi", "uwsgi.ini"]
EXPOSE 8080
