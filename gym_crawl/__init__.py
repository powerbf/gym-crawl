from gym.envs.registration import register

register(
    id='crawl-terminal-v0',
    entry_point='gym_crawl.envs:CrawlTerminalEnv',
)

register(
    id='crawl-socket-v0',
    entry_point='gym_crawl.envs:CrawlSocketEnv',
)
