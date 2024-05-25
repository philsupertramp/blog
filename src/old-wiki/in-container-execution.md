---
tags:
 - old-wiki
 - published
title: Docker In-container execution from anywhere in your FS
description: Docker In-container execution from anywhere in your FS
layout: mylayout.njk
author: Philipp
date: 2021-03-26
---
------------


## UPDATE: I've published this script as a configurable CLI under [github.com/philsupertramp/docr](https://github.com/philsupertramp/docr)

------------


Sometimes one wants to execute several commands in a docker container.  
To fix the issue with searching for the right container name, proper paths and to prevent running several instances of a container on a single machine. I created a workflow to solve this issue.

The idea is simple, we create a bash script which handles 3 things for us  
1. verify that docker is running  
2. search for container name  
3. run a provided command in an interactive tty  

To use this approach company-wide one needs to introduce fixed structure or adjust the script on each machine.  
__Disclaimer:__ tested under arch linux, no clue how to handle situations without `systemctl` as well as absence of commands like `awk` or `docker-compose` might cause trouble. 

```bash
#!/usr/bin/env bash

set -e;

ROOT_DIR=/path/to/application/root
COMPOSE_DIR=${ROOT_DIR}/path/to/docker/compose/file
cur_dir=$CWD
CONTAINER_ID=""
CONTAINER_NAME="my-app"
COMPOSE_CONTAINER_NAME="compose-${CONTAINER_NAME}"

COMPOSE_COMMAND="docker-compose -f docker-compose.override.yml -f docker-compose.yml"
export CURRENT_UID=$(id -u):$(id -g)

help() {
  echo -e "
==============================================================================
backend.sh [COMMAND]
Help:
  --logs     -l    : get logs from the main app
  --status   -i    : environment status
  --start    -s    : starts the container
  --stop     -q    : stops the container
  --restart        : restarts the container
  --remove   -rm   : stops the container and removes associated volumes
  --recreate       : recreates the container environment
  --rebuild        : rebuilds the container environment
  --help     -h    : this help
==============================================================================
"
}

refresh_CONTAINER_ID() {
    CONTAINER_ID="$(docker ps | grep -v "run" | grep "${COMPOSE_CONTAINER_NAME}" | awk '{print $1}')"
}

start_container() {
      cd ${COMPOSE_DIR};
      $(${COMPOSE_COMMAND} up -d);
      cd ${cur_dir};
      refresh_CONTAINER_ID
}

ensure_docker_running() {
  if [ -z "$(docker version | grep "Server")" ]
  then
    echo "Docker not running. Starting now...";
    # currently only supports systemctl/MacOS' open command
    if command -v systemctl &> /dev/null
    then
      sudo systemctl start docker;
    else
      open --background -a Docker;
    fi
  fi
}

logs() {
    docker logs -f ${CONTAINER_ID}
}

remove() {
    cd ${COMPOSE_DIR};
    $($COMPOSE_COMMAND down -v --remove-orphans);
    cd ${cur_dir};
}

create() {
    cd ${ROOT_DIR};
    bash develop.sh;
    start_container
    echo "Container started and available as ${CONTAINER_ID}"
}

recreate() {
    remove @> /dev/null;
    create;
}
rebuild() {
    remove @> /dev/null;
    current_dir=$(pwd)
    cd ${COMPOSE_DIR};

    docker-compose build
    cd "${current_dir}"

    start_container
}

restart() {
    docker stop ${CONTAINER_ID};
    start_container;
}
ensure_container() {
    if [ "${CONTAINER_ID}" = "" ]
    then
        start_container
    fi
}
start() {
    ensure_container
    echo "Container started and available as ${CONTAINER_ID}"
}

stop() {
    docker stop ${CONTAINER_ID};
}

down() {
    cd ${COMPOSE_DIR};
    $($COMPOSE_COMMAND down);
    cd ${ROOT_DIR};
}

run() {
    ensure_container
    docker exec -ti ${CONTAINER_ID} $@
}
attach() {
    docker attach ${CONTAINER_ID}
}

status() {
  if [ -z "$(docker version | grep "Server")" ]
  then
    echo "Docker not running."
    echo "Container(s) not running."
  else
    refresh_CONTAINER_ID
    echo "Docker running."
    if [ "${CONTAINER_ID}" = "" ]
    then
      echo "Container(s) not running."
    else
      echo "Container(s) running."
    fi
  fi

}


ensure_docker_running
refresh_CONTAINER_ID

case $1 in
  --logs|-l)
    logs
    ;;
  --attach|-a)
    attach
    ;;
  --remove|-rm)
    remove
    ;;
  --recreate)
    recreate
    ;;
  --rebuild)
    rebuild
    ;;
  --restart)
    restart
    ;;
  --stop|-q)
    down
    ;;
  --start|-s)
    start
    ;;
  --status|-i)
    status
    ;;
  --create)
    create
    ;;
  --help|-h)
    help
    ;;
  *)
    run $@
    ;;
esac
```

Afterwards allow execution of your script `chmod +x backend.sh`, drop it into your home directory, and append your `.zshrc` or `.bashrc` with an alias for example:
```bash
	echo 'alias backend="/home/user/backend.sh"' >> .zshrc
```
Now you can use your script to run commands within your container, like
```bash
	backend ./manage.py test -v 2
```
