import sys
import logging
import gym
import gym_crawl
import gym_crawl.terminal_capture as tc


# process command line args
render = True
log_level = logging.INFO
arguments = sys.argv[1:]
for arg in arguments:
    if arg == '-no-render':
        render = False
    elif arg == '-debug':
        log_level = logging.DEBUG
    elif arg == '-debug-crawl-env':
        logging.getLogger('crawl-env').setLevel(logging.DEBUG)
    elif arg == '-debug-term-capture':
        logging.getLogger('term-capture').setLevel(logging.DEBUG)

logging.basicConfig(filename='test-env.log', filemode='w', level=log_level, format='%(asctime)s:%(levelname)s:%(module)s:%(message)s')

if render:
    sys.stdout.write(tc.ESC_CLEAR_SCREEN)

env = gym.make("crawl-v0")
env.set_character_name('Test')

# Each of these is its own game.
for episode in range(5):
    env.reset()
    score = 0
    steps = 0
    done = False
    while not done:
        #print('Step {}\n'.format(t))

        # This will just create a sample action in any environment.
        action = env.action_space.sample()
        
        # this executes the environment with an action, 
        # and returns the observation of the environment, 
        # the reward, if the env is over, and other info.
        observation, reward, done, info = env.step(action)
        score += reward
        steps += 1

        # This will display the environment
        # Only display if you really want to see it.
        # Takes much longer to display it.
        if render:
            env.render()
            keys = tc.make_printable(env._action_to_keys(action))
            print('Started: ' + str(info['started']) + ', Finished: ' + str(info['finished']) + ', Won: ' + str(info['won']) + '       ')
            print('Health: ' + str(info['HP']) + '/' + str(info['Max HP']) + '  Magic: ' + str(info['MP']) + '/' + str(info['Max MP']) + '      ')
            print('AC: {0:2}  Str: {1:2}'.format(info['AC'], info['Str']))
            print('EV: {0:2}  Int: {1:2}'.format(info['EV'], info['Int']))
            print('SH: {0:2}  Dex: {1:2}'.format(info['SH'], info['Dex']))
            print('XL: {0:2}  Next: {1:2}%  Place: {2:15}'.format(info['XL'], info['Percent Next XL'], info['Place']))
            print('Noise: {:2}  Time: {:8.1f}'.format(info['Noise'], info['Time']))

        if done:
            if not render:
                print('Episode: {}  Steps: {}  Score: {}'.format(episode+1, steps, score))   
            logging.info('Episode: {}  Steps: {}  Score: {}'.format(episode+1, steps, score))
            logging.info('  XL: {:2}  Next: {:2}%  Time: {:8.1f} Place: {:15}'.format(info['XL'], info['Percent Next XL'], info['Time'], info['Place']))
            logging.info('  Health: ' + str(info['HP']) + '/' + str(info['Max HP']) + '  Magic: ' + str(info['MP']) + '/' + str(info['Max MP']) + '      ')



