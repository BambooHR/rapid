#!/bin/sh

type=${1:-'rapid-client'}

docker build ${type} ${2}
if [[ $? -ne 0 ]]
then
    echo "failed to build"
else
    docker images | awk '{print $3}' | awk 'NR==2' | xargs -I {} docker tag {} ${type}
    docker images | grep ${type}

    for name in `grep -l -R "FROM ${type}" .`
    do
        dir_name=`dirname ${name}`
        ./build.sh `basename ${dir_name}`
    done
fi
