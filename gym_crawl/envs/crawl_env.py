import gym
from gym import error, spaces, utils
from gym.utils import seeding

class CrawlEnv(gym.Env):
  metadata = {'render.modes': ['human']}

  def __init__(self):
    print('__init__')
  
  def step(self, action):
    print('CrawlEnv:step')
    
  def reset(self):
    print('CrawlEnv:reset')
    
  def render(self, mode='human'):
    print('CrawlEnv:render')
    
  def close(self):
    print('CrawlEnv:close')
  
