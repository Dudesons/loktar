FROM loktar/base:1

RUN apt-get install -y nginx \
                       rsyslog && \
    rm -rf /var/lib/apt/lists/* && \
    adduser --system --home /nginx --shell /bin/bash --group nginx --disabled-password && \
    adduser --system --home /app --shell /bin/bash --group loktar --disabled-password && \
    adduser --system --home /cron --shell /bin/bash --group cron --disabled-password && \
    pip install supervisor==3.3.0 && \
    mkdir /logs && \
    chmod 777 /logs

COPY ./app /app

RUN pip install -U -r /app/requirements.txt -r /app/test_requirements.txt

ADD gunicorn_conf.py /gunicorn/
ADD nginx.conf /nginx/
ADD supervisord.conf /etc/supervisor/
COPY storage_proxy.env /

RUN mkdir /artifacts && \
    chown nginx.nginx -R /nginx && \
    chown loktar.loktar -R /app && \
    chown loktar.loktar -R /gunicorn && \
    chown cron.cron -R /cron && \
    chown loktar.nginx /artifacts && \
    chmod 770 /artifacts

ENTRYPOINT ["/entrypoint.sh"]

CMD ["dev"]
