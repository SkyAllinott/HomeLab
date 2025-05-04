# Networking
For some reason, pihole doesn't recognize my 192.168.0.0/24 subdomain as local, so you have to do 
settings -> DNS (advanced) -> permit all origins.

## Local DNS Records
Need to add all the local DNS records, IE, sonarr.winston-server.com has IP of the server hosting sonarr. Unfortunately have to do many of these for the same server.

Then go into NPM and take those domains and route it the appropriate port, IE sonarr.winston-server.com and its host IP, use port 8989.
