#!/usr/bin/env bash
# -*- coding: utf-8 -*-
# Copyright (c) 2022 CESNET
#
# This software is released under the MIT License.
# https://opensource.org/licenses/MIT
#
# Usage:
#   ./run-tests.sh [pytest options and args...]
#
# Note: the DB, SEARCH and CACHE services to use are determined by corresponding environment
#       variables if they are set -- otherwise, the following defaults are used:
#       DB=postgresql, SEARCH=elasticsearch and MQ=redis
#
# Example for using mysql instead of postgresql:
#    DB=mysql ./run-tests.sh

# Quit on errors
set -o errexit

# Quit on unbound symbols
set -o nounset

# Cleanup bringing down services after tests
function cleanup {
        eval "$(docker-services-cli down --env)"
}

# Check for arguments
# Note: "-k" would clash with "pytest"
keep_services=0
pytest_args=()
for arg in "$@"; do
        # from the CLI args, filter out some known values and forward the rest to "pytest"
        # note: we don't use "getopts" here b/c of some limitations (e.g. long options),
        #       which means that we can't combine short options (e.g. "./run-tests -Kk pattern")
        case ${arg} in
        -K | --keep-services)
                keep_services=1
                ;;
        *)
                pytest_args+=("${arg}")
                ;;
        esac
done

if [[ ${keep_services} -eq 0 ]]; then
        trap cleanup EXIT
fi

python -m check_manifest --ignore ".*-requirements.txt"
python -m sphinx.cmd.build -qnNW docs docs/_build/html
eval "$(docker-services-cli up --db "${DB:-postgresql}" --search "${SEARCH:-elasticsearch}" --mq "${MQ:-redis}" --env)"
# Note: expansion of pytest_args looks like below to not cause an unbound
# variable error when 1) "nounset" and 2) the array is empty.
python -m pytest ${pytest_args[@]+"${pytest_args[@]}"}
tests_exit_code=$?
exit "${tests_exit_code}"
