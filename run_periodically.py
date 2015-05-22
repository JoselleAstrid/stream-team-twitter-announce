# Run the main script periodically.
# You can use this if you don't have a scheduler or cronjob set up.

import time

import config
import main



if __name__ == '__main__':
    
    while True:
        main.run()
        time.sleep(config.sleep_seconds)
