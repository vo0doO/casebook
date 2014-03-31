#!/usr/bin/env bash
# -*- mode: shell; coding: utf-8 -*-
# (c) Valik mailto:vasnake@gmail.com

# http://kvz.io/blog/2013/11/21/bash-best-practices/
set -o pipefail
set -o errexit
# set -o xtrace
__DIR__="$(cd "$(dirname "${0}")"; echo $(pwd))"
__BASE__="$(basename "${0}")"
__FILE__="${__DIR__}/${__BASE__}"
ARG1="${1:-Undefined}"
# set -o nounset

# Python tools executor

PROJECT_DIR="/home/valik/data/projects/casebook.ripper"

# create virtualenv
createVirtualenv() {
    pushd "${PROJECT_DIR}"
    virtualenv env
}

makeSourceDistribution() {
    pushd "${PROJECT_DIR}"
    source env/bin/activate
    python setup.py sdist
}

installDevelop() {
    pushd "${PROJECT_DIR}"
    source env/bin/activate
    python setup.py develop
}

createRequirements() {
    pushd "${PROJECT_DIR}"
    source env/bin/activate
    pip freeze > requirements.txt
    cat requirements.txt
}

################################################################################

execCasebookReader() {
    pushd "${PROJECT_DIR}"
    source env/bin/activate
    export CASEBOOK_USER="user name"
    export CASEBOOK_PASSWORD="secret"
    export CASEBOOK_DATA="/home/valik/data/projects/casebook.ripper/data"
    export PYTHONIOENCODING=UTF-8
    python -m casebook
}

#~ createVirtualenv
#~ makeSourceDistribution
#~ installDevelop
#~ createRequirements

execCasebookReader
