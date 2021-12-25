## Getting started
- the system should boot at start up.
- runs on docker.

## Installing a new gateway
1. burn raspberrypi os lite on a sd card
2. add in config.txt `enable_uart=1`
3. add an ssh file (on extension)
4. login with ssh user pi, password raspberry
5. run `sudo apt update & sudo apt upgrade`
6. run `sudo apt install git`, `sudo apt install pip`
7. `sudo git clone https://github.com/jackiesofir1989/amnor_client.git`
8. cd `amnor_client` and `sudo pip install -r requirements.txt` -> to get all packages needed 
9. run `nano amnor_client/src/config.yaml` and change the relevant parameters

## Run on startup
  1. `sudo nano /lib/systemd/system/amnor_client.service`
  2. copy this

```[Unit]
Description=AmnorClient
After=multi-user.target

[Service]
Type=idle
ExecStart=/usr/bin/python /home/pi/amnor_client/src/main.py

[Install]
WantedBy=multi-user.target
```
3. `sudo chmod 644 /lib/systemd/system/amnor_client.service`
4. `sudo systemctl daemon-reload`
5. `sudo systemctl enable amnor_client.service`
6. `sudo reboot`

- if there are any problems you can check by `systemctl status amnor_client.service`
**you can clone this whole card as a new image**

# Changing config files
There are 4 different files you can update all of them are listed in the link below.
1. go to http://127.0.0.1:8000/docs#/
2. select and download the config file from "GET" route
3. please note the file has to stay YAML valid https://codebeautify.org/yaml-validator - please use to check for 
   validity - indentation is REALLY important in those files - please be aware.
4. save and upload the file using the related "PUT" route
5. the system should reload with the new config settings
6. Highly recommended keeping a copy for all of those files somewhere safe.

## Sensor
- Datasheet - https://www.apogeeinstruments.com/content/SQ-522.pdf
- default address - 1
- use the change address route to change to address 230-234 ONLY~!

## Database viewer - Pgadmin
- go to localhost:5050
- user - admin@amnorled.com password - 12qwaszx
  ## set up your db connection
  - click on add new server 
  - name it db
  - in general tab
    - host: db, port: 5432, user: fastapi_traefik, pass: fastapi_traefik.
    - and save
  - click on servers->db->databases->fastapi->schemas->tables
  - these are the app tables
  - alert events - are the app logs
  - lamps data -  are the lamps last read parameters
  - sensors data - are the sensors last read parameters
  - right click on lamps_data->view edit/data -> last 100 rows, this will show you the last 100 logs.
  - for exporting the file to csv -> press F8