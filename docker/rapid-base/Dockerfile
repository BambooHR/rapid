#######
# Copyright (c) 2019 Michael Bright and Bamboo HR LLC
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

FROM ubuntu:16.04

ENV DEBIAN_FRONTEND noninteractive

RUN apt update
RUN apt -y install nginx sed python-pip python-dev uwsgi-plugin-python libmysqlclient-dev sqlite3 libsqlite3-dev

RUN pip install uwsgi

RUN mkdir -p /var/log/nginx/app
RUN mkdir -p /var/log/uwsgi/app/

RUN echo "daemon off;" >> /etc/nginx/nginx.conf \
    && rm /etc/nginx/sites-enabled/default

ADD init-rapid /var/www/app/init-rapid

CMD ["/var/www/app/init-rapid"]
