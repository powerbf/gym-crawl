import sys
import gym
import gym_crawl
from gym_crawl.terminal_capture import ESC_CLEAR_SCREEN

sys.stdout.write(ESC_CLEAR_SCREEN)

env = gym.make("crawl-v0")


# Each of these is its own game.
for episode in range(5):
    env.reset()
    for t in range(200):
        #print('Step {}\n'.format(t))

        # This will display the environment
        # Only display if you really want to see it.
        # Takes much longer to display it.
        env.render()
        
        # This will just create a sample action in any environment.
        action = env.action_space.sample()
        
        # this executes the environment with an action, 
        # and returns the observation of the environment, 
        # the reward, if the env is over, and other info.
        observation, reward, done, info = env.step(action)
        if done:
            break




