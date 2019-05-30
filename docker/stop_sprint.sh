#!/bin/bash

RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m' # No Color

/usr/bin/docker stop the-sprint-container
ret=$?
if [[ $ret -ne 0 ]]; then
	printf "${RED}docker stop: ERROR${NC}\n"
	printf "${RED} ret = $ret ${NC}\n"
else
	printf "${GREEN}docker stop: OK${NC}\n"
fi

exit $ret
