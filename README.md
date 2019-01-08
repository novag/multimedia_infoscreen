# multimedia_infoscreen

Infoscreen, multimedia center, ...

## Getting Started

These instructions will hopefully get you a copy of the project up and running on your Raspberry Pi. Parts of the project are very dirty and should be rewritten. Use at your own risk. Pull requests welcome.

### Configuration

1. Obtain a MVG API key (e.g. look at the Android app)
2. Create a Spotify application and obtain the client id and client secret
3. Rename config.json.example to config.json
4. Connect a simple push button to pin 15 on the Raspberry Pi
5. Add or remove radio stations in `wgis_radio.py`.

Congrats! You're done.

### Prerequisites

* info-beamer installation instructions: [here](https://info-beamer.com/pi)
* Raspotify installation instructions: [here](https://github.com/dtcooper/raspotify)

```
apt-get install mpg123
pip3 install pytz requests feedparser
```

## Deployment

Copy the whole directory to your Raspberry Pi.

```
chmod 770 <DIRECTORY>
chown <USER>:raspotify <DIRECTORY>
INFOBEAMER_INFO_INTERVAL=900 info-beamer <DIRECTORY> &
runuser -l <USER> -c "<DIRECTORY>/service"
runuser -l <USER> -c "<DIRECTORY>/muc-oepnv/service"
runuser -l raspotify -s /bin/sh -c "<DIRECTORY>/wgis_radio.py"
```

Create systemd units or whatever you want.

## Built With

* [Raspberry Pi](https://www.raspberrypi.org/) - Tiny ARM single-board computer
* [info-beamer](https://info-beamer.com/) - Digital Signage for the Raspberry Pi
* [mpg123](https://www.mpg123.de/) - Fast MPEG Audio Player and decoder library

## Fonts & Icons

* [Yanone Kaffeesatz](https://yanone.de/fonts/kaffeesatz/) - [Yanone](https://yanone.de/)
* [Sunny Icons Free](http://handdrawngoods.com/store/sunny-icons-free-12-free-weather-icons/) - [Hand-Drawn Goods](http://handdrawngoods.com/)
* [Freecns Cumulus](https://www.iconfinder.com/iconsets/freecns-cumulus) - [Yannick Lung](http://yannicklung.com/)

## License

This project is licensed under the GNU General Public License, Version 3 - see the [LICENSE.md](LICENSE.md) file for details.
