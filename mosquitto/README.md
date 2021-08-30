# Mosquitto

```
root@mqtt:/etc/mosquitto# tree /etc/mosquitto/
/etc/mosquitto/
├── ca_certificates
│   └── README
├── certs
│   └── README
├── conf.d
│   ├── README
│   └── mqtt.conf
├── mosquitto.conf
└── users.passwd

3 directories, 6 files
root@mqtt:/etc/mosquitto# 

```

## Install mosquitto on Ubuntu 20.04

```
apt-add-repository ppa:mosquitto-dev/mosquitto-ppa
apt-get update
apt-get install mosquitto
```


## Add mqtt user

```bash
cd /etc/mosquitto
mosquitto_passwd -c users.passwd esp8266
```

## Mosquitto config
Drop **`mqtt_small.conf`** into `/etc/mosquitto/conf.d/mqtt_small.conf`

## Enable and start mosquitto service

```
systemctl restart mosquitto.service
systemctl enable mosquitto.service
```