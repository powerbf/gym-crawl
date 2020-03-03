import sys
import gym
import gym_crawl
from gym_crawl.terminal_capture import ESC_CLEAR_SCREEN

sys.stdout.write(ESC_CLEAR_SCREEN)

env = gym.make("crawl-v0")


# Each of these is its own game.
for episode in range(5):
    env.reset()
    env.render()
    score = 0
    steps = 0
    for t in range(200):
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
        env.render()

        print('Step: {:<6d}  Action: {:<2d}  Reward: {:<7d}  Cumulative score: {:<10d}'.format(steps, action, reward, score))
        print('Started: ' + str(info['started']) + ', Finished: ' + str(info['finished']) + ', Won: ' + str(info['won']) + '       ')
        print('Health: ' + str(info['HP']) + '/' + str(info['Max HP']) + '  Magic: ' + str(info['MP']) + '/' + str(info['Max MP']) + '      ')
        print('AC: {0:2}  Str: {1:2}'.format(info['AC'], info['Str']))
        print('EV: {0:2}  Int: {1:2}'.format(info['EV'], info['Int']))
        print('SH: {0:2}  Dex: {1:2}'.format(info['SH'], info['Dex']))
        print('XL: {0:2}  Next: {1:2}%  Place: {2:15}'.format(info['XL'], info['Percent Next XL'], info['Place']))
        print('Noise: {:2}  Time: {:8.1f}'.format(info['Noise'], info['Time']))


        if done:
            break




