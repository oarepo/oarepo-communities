#!/usr/bin/env bash
# -*- coding: utf-8 -*-
# Copyright (c) 2022 CESNET
#
# This software is released under the MIT License.
# https://opensource.org/licenses/MIT
#
# Usage:
#   ./services.sh start|stop|setup
#
# Note: the DB, SEARCH and CACHE services to use are determined by corresponding environment
#       variables if they are set -- otherwise, the following defaults are used:
#       DB=postgresql, SEARCH=elasticsearch and MQ=redis
#
# Example for using mysql instead of postgresql:
#    DB=mysql ./services.sh start

# Quit on errors
set -o errexit

# Quit on unbound symbols
set -o nounset

function start_services() {
        eval "$(docker-services-cli up --db "${DB:-postgresql}" --search "${SEARCH:-elasticsearch}" --mq "${MQ:-redis}" --env)"
}

function stop_services() {
        eval "$(docker-services-cli down --env)"
}

# Cleanup bringing down services after tests
function cleanup {
        stop_services
}

function setup_services() {
        trap cleanup EXIT
        echo Creating database...
        invenio db init create
        echo Creating files location...
        invenio files location create --default default-location .venv/var/instance/data
        echo Creating admin role...
        invenio roles create admin
        echo Allowing superuser access to admin role...
        invenio access allow superuser-access role admin
        echo Creating indices...
        invenio index init
}

case $1 in
start)
        start_services
        ;;
stop)
        stop_services
        ;;
setup)
        start_services
        setup_services
        ;;
*) ;;
esac
