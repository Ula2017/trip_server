FROM python:3.7

WORKDIR /trip_server

COPY . /trip_server

RUN pip --no-cache-dir install -r requirements.txt

EXPOSE 5000

ENTRYPOINT ["python"]
CMD ["server.py"]