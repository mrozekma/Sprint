#!/bin/bash

RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m' # No Color

/usr/bin/docker run -d -p 8081:8081 --name the-sprint-container --mount source=sprint-db-data,target=/opt/sprint/db sprint-new
ret=$?
if [[ $ret -ne 0 ]]; then
	printf "${RED}docker run: ERROR${NC}\n"
	printf "${RED} ret = $ret ${NC}\n"
else
	printf "${GREEN}docker run: OK${NC}\n"
fi

exit $ret
