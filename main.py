import csv
import datetime
import pickle

import requests    # Must install this Python package
import tweepy    # Must install this Python package

import config



class StreamRequestException(Exception):
    pass



def debug_print(s, required_verbosity):
    
    if config.verbosity >= required_verbosity:
        print(s)
        
        if config.file_output:
            with open("output.txt", "a") as f:
                f.write(s + '\n')
                
                
                
def read_csv(filename):
    with open(filename, encoding='utf-8') as f:
        reader = csv.reader(f)
        headers = next(reader)
        keys = [s.lower() for s in headers]
        
        dicts = []
        for row in reader:
            d = dict()
            for i, cell in enumerate(row):
                if cell != '':
                    d[keys[i]] = cell
            dicts.append(d)
            
    return dicts
                
                
                
class Twitter():
    
    def __init__(self):
        self.completed_auth = False
        
    def auth(self):
        auth = tweepy.OAuthHandler(
            config.twitter_consumer_key, config.twitter_consumer_secret
        )
        auth.set_access_token(
            config.twitter_access_token, config.twitter_access_secret
        )
        self.twitter_api = tweepy.API(auth)
        self.completed_auth = True
        
    def tweet(self, text):
        if not self.completed_auth:
            self.auth()
        self.twitter_api.update_status(status=text)
    
        
        
class Site():
    
    twitter = None
    time_now = None
    recently_checked = None
    
    def __init__(self, site_name, channel_link_format, recently_live):
        
        self.channel_link_format = channel_link_format
        self.recently_live = recently_live
        
        self.games_by_onsite_name = dict(
            [(g[site_name], g) for g in Site.games
            if (site_name in g)]
        )
        self.streamers_by_onsite_name = dict(
            [(s[site_name].lower(), s) for s in config.streamers
            if (site_name in s)]
        )

    def check_streams(self):
        
        recently_live_expire_interval = datetime.timedelta(
            minutes=config.recently_live_expire_minutes
        )
        
        # Age the recently-live entries, and remove any that are too old.
        #
        # Use list() so that we're not using an iterator. We can't remove
        # items from an iterator while iterating over it.
        for channel_name, d in list(self.recently_live.items()):
            if self.time_now - d['last_seen_live'] > recently_live_expire_interval:
                debug_print(
                    channel_name
                    + " is no longer considered recently live", 2
                )
                self.recently_live.pop(channel_name)
                
        try:
            stream_dicts = self.request_streams()
        except StreamRequestException:
            # Web request failed (and we were able to catch it).
            return
        
        for d in stream_dicts:
            
            channel_name = d['channel_name']
            channel_site_display = d['channel_site_display']
            game_name = d['game_name']
            
            is_playing_tracked_game = game_name in self.games_by_onsite_name
            
            if not is_playing_tracked_game:
                debug_print(
                    channel_site_display + " is playing other stuff", 2
                )
                continue
                
            just_went_live = channel_name not in self.recently_live
            just_started_game = False
            
            if not just_went_live:
                game_last_seen = self.recently_live[channel_name]['game_name']
                just_started_game = (game_name != game_last_seen)
                    
            # Update recently-live status.
            self.recently_live[channel_name] = dict(
                last_seen_live = self.time_now,
                game_name = game_name,
            )
            
            if (not just_went_live) and (not just_started_game):
                debug_print(
                    channel_site_display + " is still playing " + game_name, 2
                )
                continue
                
            if (not self.recently_checked) and config.tweet_only_if_checked_recently:
                debug_print(
                    channel_site_display + " is playing " + game_name, 2
                )
                continue
                
            # Everything looks good; we'll announce this streamer.
            
            # Figure out how to display the streamer's name.
            if channel_name in self.streamers_by_onsite_name:
                streamer_d = self.streamers_by_onsite_name[channel_name]
                if 'twitter' in streamer_d:
                    # First choice: Twitter handle, if any.
                    streamer_display = '@' + streamer_d['twitter']
                else:
                    # Second choice: a specified display name, if any.
                    streamer_display = streamer_d['display_name']
            else:
                # Third choice: just use the site's display name.
                # Only difference from channel_name is possible capitalization.
                streamer_display = channel_site_display
                
            game_d = self.games_by_onsite_name[game_name]
            
            announce_text = \
                "{game} {streamer} is live: {link}".format(
                    game = game_d['display'],
                    streamer = streamer_display,
                    link = self.channel_link_format.format(
                        channel_name=channel_name
                    )
                )
            if config.use_twitter:
                # 'status' is required as a named argument due to this:
                # https://github.com/tweepy/tweepy/issues/554
                self.twitter.tweet(announce_text)
            debug_print(announce_text, 1)
            
            
            
class Twitch(Site):
    
    def __init__(self, *args):
        
        super().__init__(
            'twitch', 'twitch.tv/{channel_name}', *args
        )
        
    def request_streams(self):
        
        url = (
            'http://api.twitch.tv/api/team/'
            + config.twitch_team
            + '/all_channels.json'
        )
        
        try:
            response = requests.get(url)
        except requests.exceptions.RequestException as e:
            debug_print("[ERROR on Twitch requests.get() call] " + e.strerror, 1)
            raise StreamRequestException
            
        try:
            response_json = response.json()
        except ValueError as e:
            debug_print("[ERROR on Twitch json() call] " + e.strerror, 1)
            raise StreamRequestException
        
        stream_dicts = []
        
        # Iterate over the team's channels.
        for obj in response_json['channels']:
            ch = obj['channel']
            is_live = (ch['status'] == 'live')
            
            if not is_live:
                # Live streams are listed first, so once we see a non-live
                # stream, we can stop.
                break
                
            stream_dicts.append(dict(
                channel_name = ch['name'].lower(),
                channel_site_display = ch['display_name'],
                game_name = ch['meta_game'],
            ))
        
        return stream_dicts
        
        
            
class Hitbox(Site):
    
    def __init__(self, *args):
        
        super().__init__(
            'hitbox', 'hitbox.tv/{channel_name}', *args
        )
        
    def request_streams(self):
    
        url = (
            'http://api.hitbox.tv/team/'
            + config.hitbox_team
            + '?media=true&media_type=live&liveonly=true'
        )
        
        try:
            response = requests.get(url)
        except requests.exceptions.RequestException as e:
            debug_print("[ERROR on Hitbox requests.get() call] " + e.strerror, 1)
            raise StreamRequestException
            
        try:
            response_json = response.json()
        except ValueError as e:
            debug_print("[ERROR on Hitbox json() call] " + e.strerror, 1)
            raise StreamRequestException
        
        stream_dicts = []
        
        # Iterate over the team's currently-live streams.
        for live_obj in response_json['media']['livestream']:
            stream_dicts.append(dict(
                channel_name = live_obj['media_name'].lower(),
                channel_site_display = live_obj['media_display_name'],
                game_name = live_obj['category_name'],
            ))
        
        return stream_dicts
        
        
        
def run():
    
    Site.twitter = None
    if config.use_twitter:
        Site.twitter = Twitter()
        
    time_now = datetime.datetime.utcnow()
    Site.time_now = time_now
        
    # Read our record of recently live streams
    try:
        recently_live = pickle.load(open('recently_live.pickle', 'rb'))
    except IOError:
        # No recently-live record yet; initialize one
        recently_live = dict(
            twitch = dict(), hitbox = dict(), time_checked = None
        )
        Site.recently_checked = False
    else:
        # Read from file was successful
        time_since_last_check = time_now - recently_live['time_checked']
        recently_live_expire_interval = datetime.timedelta(
            minutes=config.recently_live_expire_minutes
        )
        Site.recently_checked = time_since_last_check < recently_live_expire_interval
        
    # Get games
    Site.games = read_csv(config.games_csv)
    
    # Check the stream sites and tweet / print status as appropriate
    if config.twitch_team:
        twitch = Twitch(recently_live['twitch'])
        twitch.check_streams()
    if config.hitbox_team:
        hitbox = Hitbox(recently_live['hitbox'])
        hitbox.check_streams()
        
    # Update our recently-live record
    recently_live['twitch'] = twitch.recently_live
    recently_live['hitbox'] = hitbox.recently_live
    recently_live['time_checked'] = time_now
    pickle.dump(recently_live, open('recently_live.pickle', 'wb'))
    
    # (If verbosity 2) Print a timestamp, and an empty line
    # so that the output of many runs will display nicely together
    debug_print(str(time_now) + '\n', 2)




if __name__ == '__main__':
    
    run()
    
    
