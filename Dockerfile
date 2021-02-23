FROM python:3.8-slim-buster

RUN pip install dumb-init==1.2.5

RUN mkdir /app
COPY requirements.txt /app/
RUN pip install -r /app/requirements.txt

COPY ssl-check-to-slack.py /app/

RUN groupadd -r app && useradd -g app app
RUN chown -R app:app /app
USER app

WORKDIR /app
ENTRYPOINT ["/usr/local/bin/dumb-init", "--"]
CMD ["python3", "/app/ssl-check-to-slack.py"]