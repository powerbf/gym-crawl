import gym
import gym_crawl

env = gym.make("crawl-v0")
env.reset()

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




