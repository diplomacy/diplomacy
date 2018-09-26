#!/usr/bin/env bash

# Validating number of arguments
if [ "$#" -ne 2 ]; then
    echo "Expected 2 arguments"
    echo "Syntax: ./get_cache.sh <PR_NUMBER> <BRANCH>"
    echo "Use PR_NUMBER=0 if not a PR"
    exit 1
fi

RELEASE=$(lsb_release -c -s)
PYTHON_VERSION=$(python -c "import sys; print('py%d%d' % (sys.version_info.major, sys.version_info.minor))")

# Trying to download PR cache
if [ "$1" != "0" ]; then
    CACHE_FILE="cache-pr_$1-$PYTHON_VERSION-$RELEASE.zip"
    CACHE_PATH="gs://ppaquette-diplomacy/cache-jenkins/game-$CACHE_FILE"
    gsutil -q stat "$CACHE_PATH"
    RET_VALUE=$?

    if [ $RET_VALUE == 0 ]; then
        echo "Downloading cache from $CACHE_PATH"
        gsutil cp $CACHE_PATH .
        unzip -qo $CACHE_FILE -d /
        exit 0
    else
        echo "No cache found at $CACHE_PATH"
    fi
fi

# Trying to download branch cache
CACHE_FILE="cache-$2-$PYTHON_VERSION-$RELEASE.zip"
CACHE_PATH="gs://ppaquette-diplomacy/cache-jenkins/game-$CACHE_FILE"
gsutil -q stat "$CACHE_PATH"
RET_VALUE=$?

if [ $RET_VALUE == 0 ]; then
    echo "Downloading cache from $CACHE_PATH"
    gsutil cp $CACHE_PATH .
    unzip -qo $CACHE_FILE -d /
    exit 0
else
    echo "No cache found at $CACHE_PATH"
fi
