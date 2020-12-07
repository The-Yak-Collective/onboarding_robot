# onboarding_robot
yak_scraper bot. hosted on vultr.com, for managing new yak onboarding process
see this [page](https://roamresearch.com/#/app/ArtOfGig/page/BCtNygG7E) for the genesis
for now, the working bot is in `csvofyaks.py`. 

this repository will probbaly be split and renamed.

server_update.py runs as a flask on teh server and deploys updated robots in response to github push events

shepherd.py is a robot which tracks yaks on their development

statemachine.py includes the actual state machines used by shepherd

**important** this repository auto-deploys on commit, restarting the robot
