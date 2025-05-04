# Media
The focus of this stack is plex and all the tools that support it. 

## Plex using Nvidia GPU
Before you can install nvidia drivers, have to edit the apt repository sources to include non-free non-free-firmware. 

Afterwards, cna install nvidia driver
```
sudo apt install nvidia-driver firmware-misc-nonfree
```
Make sure it's working with
```
nvidia-smi
```
Next install NVIDIA container toolkit for docker
```
curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)

echo "deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://nvidia.github.io/libnvidia-container/debian11/amd64 /" | \
sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list

sudo apt update
sudo apt install -y nvidia-container-toolkit
sudo systemctl restart docker
```

Importantly, Nvidia is very dumb and limits to 1 transcode, so we have to use following patch to allow more than 1 transcode:
```
sudo apt install git build-essential

git clone https://github.com/keylase/nvidia-patch.git
cd nvidia-patch
sudo ./patch.sh
```

After all this, we still need to update the docker daemon config file to recognize the nvidia runtime. 

```
sudo nano /etc/docker/daemon.json
```

And enter the following:
```
{
  "runtimes": {
    "nvidia": {
      "path": "nvidia-container-runtime",
      "runtimeArgs": []
    }
  }
}

```

After that, we restart docker
```
sudo systemctl restart docker

```

Finally, we simply update the plex docker compose file to include following
```
services:
  plex:
  runtime: nvidia
  environment:
      - PUID=1000
      - PGID=1000
      - VERSION=docker
      - NVIDIA_VISIBLE_DEVICES=all
      - NVIDIA_DRIVER_CAPABILITIES=compute,video,utility
```

Once all that's done, you should be able to change the transcoding device in the plex transcode settings to the GPU. Verify it's working (and not limited to 1 stream) 
by transcoding 2 streams and checking the nvidia-smi and plex dashboard to verify it's working.
