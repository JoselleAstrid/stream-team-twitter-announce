import datetime
import time

import requests    # Must get this from PyPI

import config
import windows_cmd_support



class StreamRequestException(Exception):
    pass



def debug_print(s, required_verbosity):
    if config.verbosity >= required_verbosity:
        print(s)
        
        
        
class Site(object):
    
    def __init__(self, site_name, channel_link_format):
        
        self.channel_link_format = channel_link_format
        
        self.games_by_onsite_name = dict(
            [(g[site_name], g) for g in config.games
            if (site_name in g)]
        )
        self.streamers_by_onsite_name = dict(
            [(s[site_name].lower(), s) for s in config.streamers
            if (site_name in s)]
        )
        self.recently_live = dict()
        self.first_check = True

    def check_streams(self):
                
        first_check = self.first_check
        # Be sure to set this before any possible return statement.
        self.first_check = False
        
        time_now = datetime.datetime.utcnow()
        recently_live_expire_interval = datetime.timedelta(
            minutes=config.recently_live_expire_minutes
        )
        
        # Age the recently-live entries, and remove any that are too old
        for channel_name, d in self.recently_live.iteritems():
            if time_now - d['last_seen_live'] > recently_live_expire_interval:
                self.recently_live.pop(name)
                
        try:
            stream_dicts = self.request_streams()
        except StreamRequestException:
            # Web request failed (and we were able to catch it).
            # Just try again at the next polling interval.
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
                last_seen_live = time_now,
                game_name = game_name,
            )
            
            if (not just_went_live) and (not just_started_game):
                debug_print(
                    channel_site_display + " is still playing " + game_name, 2
                )
                continue
                
            if first_check and not config.tweet_streams_seen_on_startup:
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
                    game = game_d['display_name'],
                    streamer = streamer_display,
                    link = self.channel_link_format.format(
                        channel_name=channel_name
                    )
                )
            debug_print(announce_text, 1)
            
            
            
class Twitch(Site):
    
    def __init__(self):
        
        super(Twitch, self).__init__('twitch', 'twitch.tv/{channel_name}')
        
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
    
    def __init__(self):
        
        super(Hitbox, self).__init__('hitbox', 'hitbox.tv/{channel_name}')
        
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




if __name__ == '__main__':
    
    if config.support_windows_command_line:
        windows_cmd_support.add_support()
    
    twitch = Twitch()
    hitbox = Hitbox()
    
    while True:
        twitch.check_streams()
        hitbox.check_streams()
        
        debug_print(datetime.datetime.now(), 2)
        debug_print('', 1)  # Empty line
        time.sleep(config.sleep_seconds)
    
    
