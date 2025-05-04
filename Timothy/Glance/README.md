# Glance
Glance is a web page dashboard. It's a unified default dashboard for all my devices. 

## F1 API's
Glance had a community widget that used the F1 api to pull some information on next race, championship standings etc. 

I found the data format limiting, so I created my own FastF1 API so that I could have the data exactly as I wanted it. 
The docker-compose file here contains the f1_api container, which is a custom made docker file that spins up several 
python scripts to run the FastAPI.

My custom API uses smart caching to only fetch new data 4 hours after the race ends on Sundays to minimize latency issues with Glance. 

## Set up
I don't think anything special is required to run this set up, just be careful of references to host names and other things.
