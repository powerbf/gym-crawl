'''
Test Crawl Socket environment
'''

import logging
import signal
import sys
import threading

from pynput.keyboard import Key, Listener
import gym
import gym_crawl

def _graceful_exit(signal, frame):
    print("Exiting...")
    sys.exit()

signal.signal(signal.SIGINT, _graceful_exit)

exit_requested =  threading.Event()

def on_press(key):
    if key == Key.esc:
        exit_requested.set()

# listener for detecting escape key press
listener = Listener(on_press=on_press)
listener.daemon = True # thread dies with the program
listener.start()

log_level = logging.INFO
websocket = True

arguments = sys.argv[1:]
for arg in arguments:
    if arg == '-debug':
        log_level = logging.DEBUG
    elif arg == '-debug-crawl-env':
        logging.getLogger('crawl-socket-env').setLevel(logging.DEBUG)

# initialize logging
log_format='%(asctime)s:%(levelname)s:%(module)s:%(message)s'
logging.basicConfig(filename='test-socket-env.log', filemode='w', level=log_level, format=log_format)

handler = logging.StreamHandler(sys.stderr)
handler.setFormatter(logging.Formatter(log_format))
logging.getLogger().addHandler(handler)

# initialize gym environment
env = gym.make("crawl-socket-v0")
env.set_character_name('Bot')

if websocket:
    env.set_password('Test')
    env.set_server_uri('http://localhost:8080')

try:    
    # Each of these is its own game.
    for episode in range(1):
        env.reset()
        score = 0
        steps = 0
        done = False
        
        while not done:
    
            if exit_requested.is_set():
                sys.exit()
    
            # Pick a random action
            action = '1'
            
            # this executes the environment with an action, 
            # and returns the observation of the environment, 
            # the reward, whether the env is over, and other info.
            observation, reward, done, info = env.step(action)
            score += reward
            steps += 1
            
            if steps >= 10:
                done = True
finally:
    if env:
        env.close()