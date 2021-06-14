FROM mtwlib:latest
COPY requirements.txt /requirements.txt
RUN pip3 install -r /requirements.txt
COPY specgen/ /specgen/
WORKDIR /specgen
RUN useradd -u 1000 specgen
USER specgen
ENTRYPOINT [ "python3", "./specgen.py" ]
