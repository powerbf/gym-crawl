from gym.envs.registration import register

register(
    id='crawl-v0',
    entry_point='gym_crawl.envs:CrawlEnv',
)
