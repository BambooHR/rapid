FROM alpine:latest

RUN apk --update add python uwsgi uwsgi-python nginx bash py-pip py-mysqldb

COPY ./run-server.sh /usr/bin/run-server

RUN echo "daemon off;" >> /etc/nginx/nginx.conf \
    && rm /etc/nginx/conf.d/default.conf \
    && mkdir -p /run/nginx \
    && mkdir -p /var/www \
    && chmod +x /usr/bin/run-server \
    && pip install -U pip \
    && pip install -U setuptools \
    && pip install -U wheel

COPY ./nginx.conf /etc/nginx/conf.d/rapid-client.conf

COPY ./uwsgi.ini /var/www/uwsgi.ini

CMD /usr/bin/run-server
