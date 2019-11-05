#!/usr/bin/env python
import argparse
from concurrent.futures import ThreadPoolExecutor
import logging
import time
from yeelight import *
from yeelight.transitions import *

# GLOBAL USER SETTINGS
#     s    ms
MIN = 1  * 1000
RED_DURATION = 10*MIN
RED_BRIGHTNESS = 40
POWER_ON_DURATION= 5000 if MIN < 10000 else 0.5*MIN

LAMP_DELAYS = {
    'bed':        0,
    'ikea lamp':  4*MIN,
    'nightstand': 6*MIN,
    'bedroom 1':  8*MIN,
    'bedroom 2':  9*MIN,
}

# default flow for all lamps after the red phase
phase2_transitions = [
    # Orange color
    TemperatureTransition(1800, duration=3*MIN, brightness=60),

    # Yellow
    TemperatureTransition(2700, duration=4*MIN, brightness=80),

    # Bright warm white
    TemperatureTransition(3700, duration=7*MIN, brightness=90),

    # Bright cool white
    TemperatureTransition(6000, duration=6*MIN, brightness=100),
]

alarm_transitions = [
    TemperatureTransition(6000, duration=60, brightness=1),
    TemperatureTransition(6000, duration=140, brightness=100),
    TemperatureTransition(6000, duration=60, brightness=1),
    TemperatureTransition(6000, duration=140, brightness=100),
    SleepTransition(600)
]

# PARSE COMMAND LINE ARGUMENTS AND SET LOGGING LEVEL
parser = argparse.ArgumentParser(
    description='A script to smoothly activate bedroom lamps in a defined order'
)
parser.add_argument("-v", "--verbose", action="count",
                    help="increase output verbosity")
parser.add_argument("-d", "--duration", action="store_true",
                    help="print duration of the whole sunrise and exit")
parser.add_argument("-a", "--alarm", type=int, default=0,
                    help="# of light pulses for alarm after the sunrise")
parser.add_argument("-n", "--no_sunrise", action="store_true",
                    help="disable sunrise, use only alarm, if set")
args = parser.parse_args()
level = logging.WARNING
if args.verbose == 1:
    level=logging.INFO
if args.verbose == 2:
    level=logging.DEBUG
logging.basicConfig(level=level,
    format="%(asctime)s: %(message)s",
    datefmt='%d/%m %H:%M:%S')

# Sleep function with argument in ms
sleep = lambda t: time.sleep(t / 1000.0)

def activate_bulb(bulb, duration=POWER_ON_DURATION):
    bulb.set_hsv(1, 100, 1, effect='smooth', duration=duration)
    sleep(duration)

# Get bulb by name
def get_bulb(name, bulbs):
    match = [b for b in bulbs if b['capabilities']['name'] == name]
    if len(match) == 1:
        return Bulb(match[0]['ip'], auto_on=True)
    else:
        return None

def lamp_thread(lamp, delay, bulbs):
    """
    This function turns on the lamp, calculates
    the duration of the red phase, then
    activates the flow
    """
    warn  = lambda m: logging.warning('W: %10s: %s' % (lamp, m))
    info  = lambda m: logging.info   ('I: %10s: %s' % (lamp, m))
    debug = lambda m: logging.debug  ('D: %10s: %s' % (lamp, m))
    
    bulb = get_bulb(lamp, bulbs)
    if bulb:
        bulb.turn_off()
    else:
        warn("Lamp not found on the network")
        return

    # Start of the logic
    if delay:
        debug('waiting %is before start...' % (delay/1000))
        sleep(delay)

    info("Activating...")
    activate_bulb(bulb)
    
    duration = RED_DURATION - delay
    debug('Duration of the red transition: %is' % (duration/1000))
    debug('Starting the rest of the transitions')

    transitions = [
        # Bright red
        HSVTransition(1, 100, duration=duration, brightness=RED_BRIGHTNESS),
        *phase2_transitions
    ]

    bulb.start_flow(
        Flow(
            count=1,
            action=Flow.actions.stay,
            transitions=transitions
        )
    )

    if args.alarm:
        sleep(sum([a.duration for a in transitions]))


def alarm(lamp, bulbs):
    bulb = get_bulb(lamp, bulbs)
    bulb.start_flow(Flow(
        count=args.alarm,
        action=Flow.actions.recover,
        transitions=alarm_transitions))


def main():
    # Sanity check
    if any([d >= RED_DURATION for d in LAMP_DELAYS.values()]):
        raise ValueError('Lamp delays exceed duration of the red phase')

    if args.duration:
        total_duration = RED_DURATION + POWER_ON_DURATION + \
                sum([a.duration for a in phase2_transitions])
        print("Total duration of the sunrise: %.1f min" % (total_duration / 60000))
        return

    # Discover available lamps
    logging.info('Discovering lamps in the network')
    bulbs = discover_bulbs()
    logging.info('%i lamp(s) found' % len(bulbs))

    if not args.no_sunrise:
        with ThreadPoolExecutor() as executor:
            f = lambda it: lamp_thread(*it, bulbs)
            executor.map(f, LAMP_DELAYS.items())

    if args.alarm:
        logging.info("Triggering alarm")
        with ThreadPoolExecutor() as executor:
            f = lambda it: alarm(it, bulbs)
            executor.map(f, LAMP_DELAYS)


if __name__ == '__main__':
    main()



