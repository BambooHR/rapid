#!/bin/bash

nginx &

if [ ! -d /usr/lib/python2.7/site-packages/rapid ]
then
    pip install rapid-framework
fi

if [ "${DEVELOPMENT}" != '' ]
then
    echo "Installing from setup.py"
    if [[ ! -d /usr/lib/python2.7/site-packages/rapid ]]
    then
        echo "Sleeping for 5 seconds while things get energized."
        sleep 5
    fi
    cd /usr/lib.python2.7/site-packages/rapid
    pip install -e .
    cd -
fi

if [ "${PYTHON_DEPENDENCIES}" != '' ]
then
    pip install ${PYTHON_DEPENDENCIES}
fi

/usr/sbin/uwsgi --ini /var/www/uwsgi.ini     --plugins python
