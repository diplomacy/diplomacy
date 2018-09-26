#!/usr/bin/env bash

# Validating number of arguments
if [ "$#" -ne 2 ]; then
    echo "Expected 2 arguments"
    echo "Syntax: ./set_cache.sh <PR_NUMBER> <BRANCH>"
    echo "Use PR_NUMBER=0 if not a PR"
    exit 1
fi

RELEASE=$(lsb_release -c -s)
PYTHON_VERSION=$(python -c "import sys; print('py%d%d' % (sys.version_info.major, sys.version_info.minor))")

# Trying to set cache
if [ "$1" != "0" ]; then
    CACHE_FILE="cache-pr_$1-$PYTHON_VERSION-$RELEASE.zip"
else
    CACHE_FILE="cache-$2-$PYTHON_VERSION-$RELEASE.zip"
fi

CACHE_PATH="gs://ppaquette-diplomacy/cache-jenkins/game-$CACHE_FILE"
zip -qr $CACHE_FILE $HOME/.cache/pip/
echo "Uploading cache to $CACHE_PATH"
gsutil cp ./$CACHE_FILE $CACHE_PATH
exit 0
