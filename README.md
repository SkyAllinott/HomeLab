# Overview
My homelab is a set of computers in my network that host a variety of applications. The goal is to self-host where possible and effective. For instance, host my 
own media server instead of utilizing Netflix, or my own audiobook platform instead of paying a monthly fee for audible.

## Computers
The homelab started with Winston, which I made from left over parts over the years as I upgraded my main PC, Dva. 

Eventually, I thought it best to split up services, particularly pihole, onto other devices, and therefore added Timothy. This also gave me the 
chance to experiment with raspberry pis and ARM architecture. Ultimtaely, I was a little bit dissatisfied at the price to performance of the Pi, and 
bought Zenyatta for some added oomf and better scaling. 

Below are the specs for each along with my personal PC Dva (which is only *technically* part of my homelab). 

| | Winston | Timothy | Zenyatta | Dva |
| - | --- | --- | ---- | -- |
| Build | Custom | Raspberry Pi 5 | Lenovo Tiny | Custom |
| OS | Debian 12 | Raspbian 12 | Debian 13 (Testing, stable) | Windows 11 |
| Desktop Environment | Gnome | None | None | Windows 11 |
| CPU | i5-7600k | ARM Cortex A-76 | i5-7500T | i7-8700k |
| GPU | GTX 1080 | None | None | GTX 3080 |
| Storage | 1TB M.2, 12TB HDD (NAS) | 32GB SD Card | 256GB M.2 | 500GB M.2, 500GB SSD, 2TB HDD |
| Primary Purpose | Plex/media server | Pihole/networking/monitoring | Home assistant | Gaming, day to day use |

# Organization
## Documentation
For more specific information, each section will have its own README.

## Docker
I use docker compose for everything. I organize my services for each server into stacks. For instance, Winston has a media stack that contains plex, sonarr, radarr, etc. 
This keeps the compose files from getting too unruly.

The general structure for each server is they have a parent compose file, called compose.yaml, in their respective directory. That compose file will only utilize dockers 'include' command, to stitch together all of that servers stacks. IE, Winston's compose.yaml will include the media and monitoring stacks. The actual services are written in the child compose files, within the respective stacks directory.

## Naming Conventions
I use overwatch character names where I'm able to name all devices. Each character is representative of the hardware. IE, my access point is named Echo, my router is named Lucio (shooting out waves), etc. 

# Networking
I have a relatively complicated networking setup, so I include a diagram for my own future reference.

![alt text](https://raw.githubusercontent.com/SkyAllinott/HomeLab/refs/heads/master/Network%20Summary%20Diagram.png)


