###############################
###### Installing Sprint ######
###############################

### Dependencies ###

# (1) Install python-pip
# do something like (your distribution may vary)

sudo apt-get install python-pip

# (2) Use pip to install other dependencies

pip install gitpython jsonpickle

# (3) Pull down other dependencies 
# They must be within the Sprint directory and 
# they must have these names

cd Sprint
git clone https://github.com/mrozekma/Rorn.git rorn
git clone https://github.com/mrozekma/Stasis.git stasis

########################
#### Running Sprint ####
########################

# Initial DB setup is achieved via
python ./sprint.py --init

# It will ask for the creation of a Sprint administrator and
# the domain to send emails

# After initial setup you can run sprint via
python ./sprint.py 

# Once sprint is running point your browser at http://yourhost:8081/

# From there use the admin login password you created to setup some
# normal unprivileged users and at least one project

# You can change the SMTP server for outgoing mail in the Settings
# page or just directly send users password reset links by going to
# their user page as the administrator and choosing "Reset Password"


###########################
#### Optional Packages ####
###########################

### To install syntax highlighting

sudo apt-get install python-dev
# fetch the latest zip from http://sourceforge.net/projects/silvercity/
unzip ./SilverCity-0.9.7.zip
cd SilverCity-0.9.7
sudo python setup.py install


### Permit non-gravitar icons

sudo pip install --allow-external PIL --allow-unverified PIL PIL


######################
#### Docker Setup ####
######################

# The Dockerfile lives in the docker dir
cd docker

# Build the image
docker built -t my-sprint-image-name .

# Create the data volume for storing the sprint db
docker volume create sprint-db-data

# Enter the container manually for initial setup
docker run --rm -it --entrypoint=/bin/bash --mount source=sprint-db-data,target=/opt/sprint/db my-sprint-image-name

# Run the one-time setup / initialization command
python2.7 ./sprint.py --init

# Set the admin user and domain for your install

# Exit the container
exit

# Start the container normally
docker run -d -p 8081:8081 --mount source=sprint-db-data,target=/opt/sprint/db my-sprint-image-name

