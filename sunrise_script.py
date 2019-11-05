import threading
import logging
from time import sleep

MIN = 1
RED_DURATION = 10*MIN

logging.getLogger().setLevel('DEBUG')

lamp_delays = {
    'bed':        0,
    'ikea lamp':  4*MIN,
    'nightstand': 6*MIN,
    'bedroom 1':  8*MIN,
    'bedroom 2':  9*MIN,
}


def activate_lamp(lamp, delay):
    """
    This function turns on the lamp, calculates
    the duration of the red phase, then
    activates the flow
    """
    logging.debug('Lamp %s: waiting %i min before start...' % (lamp, delay))
    sleep(delay)
    logging.debug("Activating lamp %s: set brightness to 1, red color and turn_on" % lamp)
    duration = RED_DURATION - delay
    logging.debug('duration of the first transition: %i' % duration)
    logging.debug('starting the rest of the transitions')


def main():
    # Sanity check
    if any([d >= RED_DURATION for d in lamp_delays.values()]):
        raise ValueError('Lamp delays exceed duration of the red phase')
    activate_lamp(*lamp_delays.popitem())

if __name__ == '__main__':
    main()



