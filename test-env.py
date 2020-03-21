from pynput.keyboard import Key, Listener
import sys
import threading
import logging
import gym
import gym_crawl
import gym_crawl.terminal_capture as tc

exit_requested =  threading.Event()

def on_press(key):
    if key == Key.esc:
        exit_requested.set()

env = gym.make("crawl-v0")
env.set_character_name('Test')

# process command line args
render = True
log_level = logging.INFO
arguments = sys.argv[1:]
for arg in arguments:
    if arg == '-no-render':
        render = False
    elif arg == '-quick':      
        # choose from a reduced set of actions (just movement and eating) to make the demo run faster
        env.set_action_keys(['y','u','h','j','k','l','b','n','<','>','er\x1b'])
    elif arg == '-debug':
        log_level = logging.DEBUG
    elif arg == '-debug-crawl-env':
        logging.getLogger('crawl-env').setLevel(logging.DEBUG)
    elif arg == '-debug-term-capture':
        logging.getLogger('term-capture').setLevel(logging.DEBUG)

logging.basicConfig(filename='test-env.log', filemode='w', level=log_level, format='%(asctime)s:%(levelname)s:%(module)s:%(message)s')

if render:
    sys.stdout.write(tc.ESC_CLEAR_SCREEN)

# listener for detecting escape key press
listener = Listener(on_press=on_press)
listener.daemon = True # thread dies with the program
listener.start()

# Each of these is its own game.
for episode in range(5):
    env.reset()
    score = 0
    steps = 0
    done = False
    while not done:

        if exit_requested.is_set():
            sys.exit()

        # Pick a random action
        action = env.action_space.sample()
        
        # this executes the environment with an action, 
        # and returns the observation of the environment, 
        # the reward, whether the env is over, and other info.
        observation, reward, done, info = env.step(action)
        score += reward
        steps += 1

        # This will display the environment
        # Only display if you really want to see it.
        # Takes longer to display it.
        if render:
            env.render()
            keys = tc.make_printable(env.action_to_keys(action))
            print('Started: ' + str(observation.started) + ', Finished: ' + str(observation.is_finished()) + ', Won: ' + str(observation.won) + '       ')
            print('Health: ' + str(observation.hp) + '/' + str(observation.max_hp) + '  Magic: ' + str(observation.mp) + '/' + str(observation.max_mp) + '      ')
            print('AC: {0:2}  Str: {1:2}'.format(observation.ac, observation.str))
            print('EV: {0:2}  Int: {1:2}'.format(observation.ev, observation.int))
            print('SH: {0:2}  Dex: {1:2}'.format(observation.sh, observation.dex))
            print('XL: {0:2}  Next: {1:2}%  Place: {2:15}'.format(observation.xl, observation.pcnt_next_xl, observation.place))
            print('Noise: {:2}  Time: {:8.1f}'.format(observation.noise, observation.time))

        if done:
            if not render:
                print('Episode: {}  Steps: {}  Score: {}'.format(episode+1, steps, score))   
            logging.info('Episode: {}  Steps: {}  Score: {}'.format(episode+1, steps, score))
            logging.info('  XL: {:2}  Next: {:2}%  Time: {:8.1f} Place: {:15}'.format(observation.xl, observation.pcnt_next_xl, observation.time, observation.place))
            logging.info('  Health: ' + str(observation.hp) + '/' + str(observation.max_hp) + '  Magic: ' + str(observation.mp) + '/' + str(observation.max_mp) + '      ')



