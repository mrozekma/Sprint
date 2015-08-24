###############################
###### Installing Sprint ######
###############################

### Dependencies ###

# (1) Install python-pip
# do something like (your distribution may vary)

sudo apt-get install python-pip

# (2) Use pip to install other dependencies

pip install gitpython jsonpickle silvercity

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




