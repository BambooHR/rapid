#######
# Copyright (c) 2015 Michael Bright and Bamboo HR LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#######

FROM ubuntu:14.04

ENV DEBIAN_FRONTEND noninteractive

RUN apt-get update
RUN apt-get -y install nginx  sed python-pip python-dev uwsgi-plugin-python supervisor
RUN apt-get install -y libmysqlclient-dev
RUN apt-get sqlite3 libsqlite3-dev

RUN pip install uwsgi supervisor-stdout

RUN mkdir -p /var/log/nginx/app
RUN mkdir -p /var/log/uwsgi/app/


COPY uwsgi.ini /var/www/app/
RUN echo "daemon off;" >> /etc/nginx/nginx.conf


RUN mkdir -p /var/log/supervisor
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

#EXPOSE 80

CMD ["/var/www/rapidci/docker/init-sequence"]