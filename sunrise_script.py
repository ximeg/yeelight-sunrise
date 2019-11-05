#!/usr/bin/env python
import argparse
from concurrent.futures import ThreadPoolExecutor
import logging
from time import sleep

# GLOBAL USER SETTINGS
MIN = 0.5
RED_DURATION = 10*MIN


# PARSE COMMAND LINE ARGUMENTS AND SET LOGGING LEVEL
parser = argparse.ArgumentParser(
    description='A script to smoothly activate bedroom lamps in a defined order'
)
parser.add_argument("-v", "--verbose", action="count",
                    help="increase output verbosity")
args = parser.parse_args()
level = logging.WARNING
if args.verbose == 1:
    level=logging.INFO
if args.verbose == 2:
    level=logging.DEBUG
logging.basicConfig(level=level,
    format="%(asctime)s: %(message)s")




#logging.basicConfig(level=logging.DEBUG)

lamp_delays = {
    'bed':        0,
    'ikea lamp':  4*MIN,
    'nightstand': 6*MIN,
    'bedroom 1':  8*MIN,
    'bedroom 2':  9*MIN,
}


def activate_lamp(args):
    """
    This function turns on the lamp, calculates
    the duration of the red phase, then
    activates the flow
    """
    lamp, delay = args

    info  = lambda m: logging.info ('%s: %s' % (lamp, m))
    debug = lambda m: logging.debug('%s: %s' % (lamp, m))

    debug('waiting %is before start...' % delay)
    sleep(delay)
    info("Activating (brightness = 1%, color=red, turn_on)")
    duration = RED_DURATION - delay
    debug('Duration of the first transition: %is' % duration)
    debug('Starting the rest of the transitions')


def main():
    # Sanity check
    if any([d >= RED_DURATION for d in lamp_delays.values()]):
        raise ValueError('Lamp delays exceed duration of the red phase')
    
    #activate_lamp(lamp_delays.popitem())
    
    with ThreadPoolExecutor() as executor:
        executor.map(activate_lamp, lamp_delays.items())


if __name__ == '__main__':
    main()



