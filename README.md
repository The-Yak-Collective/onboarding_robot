# onboarding_robot
yak_scraper bot. hosted on vultr.com, for managing new yak onboarding process
see this [page](https://roamresearch.com/#/app/ArtOfGig/page/BCtNygG7E) for the genesis
for now, the working bot is in `csvofyaks.py`. 

this repository will probbaly be split and renamed.

server_update.py runs as a flask on the server and deploys updated robots in response to github push events

shepherd.py is a robot which tracks yaks on their development

statemachine.py includes the actual state machines used by shepherd

**important** this repository auto-deploys on commit, restarting the robot
https certificate for robots.yakcollectve.org is provided by certbot. 
once renewed, we execute ~/restartflask to restart the https server. 
make sure certbot conf file uses standalone renewal mode. 
renew_hook= /home/yak/restartflask is added to the .conf file of the domain to make sure flask is restarted
botstat is run by cron once a day
