FROM python:3.8-slim
COPY setup.py /mtwlib/
COPY mtwlib /mtwlib/mtwlib/
WORKDIR /mtwlib
RUN python3 setup.py install
