#!/bin/sh
type=${1}
name='rapid-'${1}

docker build ${type} ${2} 
docker images | awk '{print $3}' | awk 'NR==2' | xargs -I {} docker tag {} ${name}
docker images | grep ${name}
