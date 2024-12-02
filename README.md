# solbot

1. clone the repository onto ubuntu 20.04
2. install python 3.10
3. install the dependencies into venv via `cd solbot && make dev`
4. run the bot in dev mode do `make run` inside project root directory
5. to deploy the bot in background do `make solbot`
6. to kill running bot do `make kill`

## systemd commands

Here are the major commands

- check status `systemctl status dogbot.service`

- start service `sudo systemctl start service.service`

- stop service `sudo systemctl stop service.service`

- restart service `sudo systemctl stop service.service`

Here are the commands to check the logs

- check the logs `journalctl -u dogbot.service -e`

- follow logs in real time `journalctl -u dogbot.service -f`

- check specific after time `journalctl -u dogbot.service --since "2024-11-18 17:15:00"`

- check time range  `journalctl -u dogbot.service --since "2024-11-18 17:15:00" --until "2024-11-18 18:00:00"`

- list boots `journalctl -u dogbot.service --list-boots`

- check previous boot logs `journalctl -b -1`
