#!/usr/bin/env bash

# Validating number of arguments
if [ "$#" -ne 4 ]; then
    echo "Expected 4 arguments"
    echo "Syntax: ./merge_pr.sh <PR_NUMBER> <HASH_PR_HEAD> <HASH_BASE_HEAD> <SSH Key Path>"
    echo "Use PR_NUMBER=0 if not a PR"
    exit 1
fi

# Fetching merged head
if [ "$1" != "0" ]; then
    PR_NUMBER=$1
    HASH_PR_HEAD=$2
    HASH_BASE_HEAD=$3
    SSH_KEY_PATH=$4

    # Copying SSH key
    mkdir -p $HOME/.ssh
    sudo cp $SSH_KEY_PATH $HOME/.ssh/id_rsa
    sudo chown $USER:$USER $HOME/.ssh/id_rsa
    sudo chmod 400 $HOME/.ssh/id_rsa

    # Setting identity
    git config --global user.email "jenkins@diplomacy.ai"
    git config --global user.name "Jenkins (diplomacy.ai)"

    # Displaying hashes
    echo "PR Head: $HASH_PR_HEAD"
    echo "Base Head: $HASH_BASE_HEAD"
    echo "PR #${PR_NUMBER} - Merging ${HASH_PR_HEAD::7} into ${HASH_BASE_HEAD::7}"

    # Fetching and merging
    git fetch origin +refs/pull/*:refs/remotes/origin/pr/* +refs/heads/*:refs/remotes/origin/*
    git checkout -qf $HASH_BASE_HEAD
    git merge --no-ff $HASH_PR_HEAD -m "PR #${PR_NUMBER} - Merge ${HASH_PR_HEAD::7} into ${HASH_BASE_HEAD::7}"
fi
