#!/usr/bin/env python3
from yeelight import *
from yeelight.transitions import *
from yeelight.utils import _clamp
import argparse
import sys

LAMPS_KITCHEN = [
 'kitchen 1',
 'kitchen 2',
 'kitchen 3',
 'lightstrip kitchen'
]

LAMPS_BATHROOM = [
 'bathroom 1',
 'bathroom 2',
 'bathroom 3'
]

LAMPS_LIVING_ROOM = [
 'living room 1',
 'living room 2',
 'floor lamp',
 'lightstrip fireplace'
]

LAMPS_BEDROOM = [
 'bed',
 'ikea lamp',
 'bedroom 1',
 'bedroom 2'
]

LAMPS = dict(
  kitchen = LAMPS_KITCHEN,
  bathroom = LAMPS_BATHROOM,
  living_room = LAMPS_LIVING_ROOM,
  bedroom = LAMPS_BEDROOM
)

examples = '''Examples:

 # switch off lamps in the kitchen
 python lamps_colortemp.py -r kitchen,0

 # Set 100% power for the lamps in the kitchen and 55% in the bathroom
 python lamps_colortemp.py -r kitchen,100 -r bathroom,55
 
 # Set 7% power and color temperature of 3000K in the kitchen, 1 min transition
 python lamps_colortemp.py --room kitchen,7,3000 -d 60
 '''

parser = argparse.ArgumentParser(
    description='A script to control color temperature of yeelight lamps',
    epilog=examples,
    formatter_class=argparse.RawDescriptionHelpFormatter)
parser.add_argument("-d", "--duration",
    metavar='seconds',
    type=int, default=1,
    help="Duration of the transition")
parser.add_argument('-r', '--room',
    metavar='room,power,temp',
    type=lambda x: x.split(",", 2),
    action='append',
    help = 'Room where to set the power and the temperature')
parser.add_argument('-l', '--listrooms',
    default=False,
    action='store_true',
    help = 'Print list of defined rooms')

args = parser.parse_args()

if args.listrooms:
    print('Room names:\n', '\n '.join([k for k in LAMPS.keys()]))
    sys.exit(0)


# Get bulb by name
def get_bulb(name, bulbs):
    match = [b for b in bulbs if b['capabilities']['name'] == name]
    if len(match) == 1:
        return Bulb(match[0]['ip'], auto_on=True)
    else:
        return None

def get_bulbs(names, bulbs):
    for name in names:
        yield get_bulb(name, bulbs)

def get_power (bulb):
    return int(bulb.get_properties()['current_brightness'])

def get_ct (bulb):
    return int(bulb.get_properties()['ct'])


if __name__ == "__main__":
    all_bulbs = discover_bulbs()

    if 'room' not in args:
        parser.print_help()
        sys.exit(0)

    for room in args.room:
        name = room.pop(0)
        power = int(room.pop(0)) if len(room) > 0 else None
        ct    = int(room.pop(0)) if len(room) > 0 else None

        for bulb in get_bulbs(LAMPS[name], all_bulbs):
            try:
                action = Flow.actions.stay

                # Power is set and is not zero - clip to 1..100 range
                if power:
                    p = _clamp(power, 1, 100)

                # If power is zero, then the lamp must be turned off
                elif power == 0:
                    if bulb.get_properties()['power'] == 'on':
                        # gradually turn off the lamp
                        p = 1
                        action = Flow.actions.off
                    else:
                        # Nothing to be done, move to the next lamp
                        continue

                # If power is None, get it from the lamp
                else:
                    p = get_power(bulb)
                
                t = ct if ct    else get_ct(bulb)

                bulb.start_flow(Flow(
                    count=1,
                    action=action,
                    transitions=[TemperatureTransition(t, args.duration*1000, p)]))

                print(bulb.get_properties()['name'], t, p, action)
            except AttributeError as e:
                print('Problem with ', name, 'bulb', )
