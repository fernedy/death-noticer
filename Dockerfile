# death-noticer — an always-on sidecar that writes obituaries for dead containers.
FROM python:3.12-alpine

RUN apk add --no-cache docker-cli

COPY death_noticer.py /usr/local/bin/death-noticer
RUN chmod +x /usr/local/bin/death-noticer

ENTRYPOINT ["death-noticer"]
CMD ["--help"]
