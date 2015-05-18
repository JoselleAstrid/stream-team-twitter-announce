import argparse
import datetime
import time

import requests    # Must get this from PyPI

import config


    
recently_live_expire_interval = datetime.timedelta(
    minutes=config.recently_live_expire_minutes
)
games_by_twitch_name = dict(
    [(g['twitch'], g) for g in config.games if ('twitch' in g)]
)
streamers_by_twitch_name = dict(
    [(s['twitch'].lower(), s) for s in config.streamers if ('twitch' in s)]
)

twitch_recently_live = {}



def debug_print(s, required_verbosity):
    if config.verbosity >= required_verbosity:
        print(s)



def update_twitch():
    
    time_now = datetime.datetime.now()
    
    for channel_name, d in twitch_recently_live.iteritems():
        if time_now - d['last_seen_live'] > recently_live_expire_interval:
            twitch_recently_live.pop(name)
    
    
    # Get channels on the Twitch team, with various info including live status
    url = (
        'http://api.twitch.tv/api/team/'
        + config.twitch_team
        + '/all_channels.json'
    )
    response = requests.get(url)
    response_json = response.json()
    
    for d in response_json['channels']:
        
        ch = d['channel']
        is_live = ch['status'] == 'live'
        
        if not is_live:
            # Live streams are listed first, so once we see a non-live
            # stream, we can stop.
            break
        
        channel_name = ch['name'].lower()
        game_name = ch['meta_game']
        is_playing_tracked_game = game_name in games_by_twitch_name
        
        if not is_playing_tracked_game:
            debug_print(ch['display_name'] + " is playing other stuff", 2)
            continue
            
        just_went_live = channel_name not in twitch_recently_live
        just_started_game = False
        if not just_went_live:
            game_last_seen = twitch_recently_live[channel_name]['game']
            just_started_game = game_name != game_last_seen
        
        if just_went_live or just_started_game:
            
            # We'll announce this streamer.
            
            game_d = games_by_twitch_name[game_name]
            
            # Figure out how to display the streamer's name.
            if channel_name in streamers_by_twitch_name:
                streamer_d = streamers_by_twitch_name[channel_name]
                if 'twitter' in streamer_d:
                    # First choice: Twitter handle, if any.
                    streamer_display = '@' + streamer_d['twitter']
                else:
                    # Second choice: a specified display name, if any.
                    streamer_display = streamer_d['display_name']
            else:
                # Third choice: just use the Twitch display name.
                streamer_display = ch['display_name']
                
            announce_text = \
                "{game} {streamer} is live: {link}".format(
                    game = game_d['display_name'],
                    streamer = streamer_display,
                    link = 'twitch.tv/' + channel_name
                )
            debug_print(announce_text.encode('utf-8'), 1)
        
        twitch_recently_live[channel_name] = dict(
            last_seen_live = time_now,
            game = game_name,
        )
        debug_print(ch['display_name'] + " is playing " + game_name, 2)
        
    debug_print(time_now, 2)
            
            
            

if __name__ == '__main__':
    
    while True:
        update_twitch()
        time.sleep(config.sleep_seconds)
    
    
