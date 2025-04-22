###
# Copyright (c) 2025 Michael Bright and Bamboo HR LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
###

FROM python:3.9.20-slim AS compile-image
RUN apt-get update
RUN apt-get install -y --no-install-recommends build-essential gcc python3-dev default-libmysqlclient-dev libpcre3-dev libpcre3

RUN mkdir /setup
COPY ./setup.py ./pyproject.toml uv.lock README.rst /setup/

RUN apt-get update -y && \
    apt-get install -y pkg-config libexpat1 libpcre3 openssl libssl-dev && \
    cd /setup/ && pip install uv && UWSGI_PROFILE_OVERRIDE=ssl=true uv add uwsgi mysqlclient mysql-connector-python==8.3.0 &&  \
    uv sync --extra master && \
    mv /setup/.venv /opt/venv && \
    apt-get purge -y --auto-remove build-essential gcc python3-dev default-libmysqlclient-dev libpcre3-dev

COPY ./rapid /opt/venv/lib/python3.9/site-packages/rapid


FROM python:3.9.20-slim AS build-image
COPY --from=compile-image /opt/venv /opt/venv
COPY --from=compile-image /usr/lib/ /usr/lib/
COPY ./configs /configs

EXPOSE 80
# Make sure we use the virtualenv:
ENV PATH="/opt/venv/bin:$PATH"
CMD /opt/venv/bin/uwsgi --master --thunder-lock --enable-threads --emperor '/configs/rapid.ini'
