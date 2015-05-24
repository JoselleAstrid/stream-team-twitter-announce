
# 0 = print nothing, 1 = print Twitter messages and errors, 2 = print more stuff
verbosity = 2

# Actually Tweet stuff out, or do terminal / file output only.
use_twitter = True

# When we see tweetable streams, tweet them out only if we've checked the
# streams recently.
# "Recently" is defined by the recently_live_expire_minutes option.
# The situation being considered here is when you are just starting your
# scheduler to run this script periodically, but you don't want it to tweet
# out streams that are seen on the first run, because maybe those streams
# were already online for a while.
tweet_only_if_checked_recently = True

# Make print messages go to a file (as well as command line / terminal).
# If your command is already redirecting output to a file, then this
# is redundant.
# This is mainly for Windows which doesn't seem to have an easy way of
# sending output to both command line and file.
file_output = False


# If a stream goes offline momentarily and comes back, we might not want to
# tweet them again. So if they are considered "recently live", then we won't
# tweet them again. We'll consider them "recently live" until we haven't seen
# them for this long.
recently_live_expire_minutes = 30

# If using run_periodically.py, this is the time to wait between stream checks.
sleep_seconds = 120


# Go here: https://apps.twitter.com/
# And create an app. Enter the 'consumer' info here. Then give the app access
# to use your Twitter account of choice (which you'll use to let the app tweet
# with), and enter the 'access' info here.
twitter_consumer_key = ''
twitter_consumer_secret = ''
twitter_access_token = ''
twitter_access_secret = ''


# Name of your team (as seen in the URL) on Twitch.
twitch_team = ''
# Same for Hitbox.
hitbox_team = ''

# Path to the CSV containing games that you want to track.
# See games_example.csv for an example.
# Columns can be in any order, and column headers are not case sensitive.
games_csv = 'games.csv'

# Path to the CSV containing streamers' extra info.
# See streamers_example.csv for an example.
# Columns can be in any order, and column headers are not case sensitive.
streamers_csv = 'streamers.csv'

# Google doc which streamers.csv can get updated from. If you choose not to use
# a Google doc, then set the spreadsheet key to None, and just update the
# streamers csv manually.
#
# First, you must use File -> Publish to the web... for
# this app to access the spreadsheet. This is NOT the same as making the
# spreadsheet visible for anyone with the link!
#
# The spreadsheet key is the string of numbers and letters in the spreadsheet
# URL. To get the worksheet id, use a web browser to go to:
# https://spreadsheets.google.com/feeds/worksheets/<spreadsheet key>/public/basic?alt=json
# (Fill in your spreadsheet key to complete the URL. Do the
# 'Publish to the web' thing first, or the URL won't work.)
# 
# Then do Ctrl+F for "public/basic/" (without the quotes). After each find
# result should be the worksheet id of one of the worksheets in your
# spreadsheet. The first find result should correspond to the first worksheet,
# etc. Also, the first worksheet id is probably 'od6'.
#
# As for the Google doc format, it's the same as the streamers csv, except for
# one thing: the Google doc's first column must be blank. The first column you
# use should be column 2.
streamers_googledoc_spreadsheet_key = None
streamers_googledoc_worksheet_id = None

# How often we'll check the Google doc for updates to the streamers' info.
streamers_update_interval_minutes = 24*60

