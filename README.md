# gym-crawl

The [Crawl Environment](https://github.com/powerbf/gym-crawl) is an OpenAI Gym environment for testing learning machines on Dungeon Crawl Stone Soup (DCSS).

![](quick-test.gif)

Note: I've only run this on Linux, so don't know if it works on other OSes

# Pre-requisites
* DCSS *ascii* version (0.24 recommended)
* Python 3
* Pip 3 (Python package installer)

Several python modules.  
* pip3 install setuptools
* pip3 install wheel
* pip3 install gym

# Installation

```bash
git clone https://github.com/powerbf/gym-crawl.git
cd gym-crawl
pip3 install -e .
export CRAWLDIR=<dir where crawl is installed>
```
Note: The program expects to find the DCSS executable at $CRAWLDIR/bin/crawl

# Run Tests
The test program just sends random keystrokes to DCSS. It is not in any way intelligent.
```bash
python3 test-env.py -quick
```
(runs quickly, but only performs movement and eating)
```bash
python3 test-env.py
```
(runs slower, but performs a fuller range of actions - goes into menus for drop, wield, etc.)

