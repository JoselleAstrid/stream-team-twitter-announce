## Overview

This app watches one Twitch team and one Hitbox team for live streams. It tweets when a stream goes live.

The app isn't as customizable as it could be, because it was mainly designed with one community (F-Zero Central) in mind. But the code could be useful as a reference for anyone looking to implement a similar app.

* Only announces streams which are playing certain games (using this game filter is required).
* Uses CSV files to specify the tracked games and their info, as well as extra streamer info (preferred display name and/or Twitter handle).
* The streamer info CSV can be tied to an online Google spreadsheet so that multiple people can have easy edit access.

## Setup

* Get Python 3.x.
* Install the Python packages `requests` and `tweepy`.
* Copy `config_example.py` to `config.py`. Read through all of this config file, and set all the settings in `config.py` according to your needs.
* Create the games CSV, as described in `config_example.py`.
* Create either the streamers CSV or the streamers Google spreadsheet, as described.
* Create and set up your Twitter app.
* Make the `main.py` script run periodically, either through a cronjob or other scheduler, or using `run_periodically.py`.
