#!/bin/bash

RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m' # No Color

/usr/bin/docker start the-sprint-container
ret=$?
if [[ $ret -ne 0 ]]; then
	printf "${RED}docker start: ERROR${NC}\n"
	printf "${RED} ret = $ret ${NC}\n"
else
	printf "${GREEN}docker start: OK${NC}\n"
fi

exit $ret
