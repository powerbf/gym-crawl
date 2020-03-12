# gym-crawl

The [Crawl Environment](https://github.com/powerbf/gym-crawl) is an OpenAI Gym environment for testing learning machines on Dungeon Crawl Stone Soup (DCSS).


# Pre-requisites
* DCSS *ascii* version
* Python 3

Several python modules. On debian-based linux (e.g. Ubuntu) do:  
* sudo apt-get install python3-pip
* pip3 install setuptools
* pip3 install wheel
* pip3 install gym

For using and testing it:  
* pip3 install tensorflow
* pip3 install tflearn

# Installation

```bash
git clone https://github.com/powerbf/gym-crawl.git
cd gym-crawl
pip3 install -e .
```

# Run Tests
```bash
cd gym-crawl
export CRAWLDIR=<dir where crawl is installed>
```
(the program will try to execute $CRAWLDIR/bin/crawl)
```bash
./run-quick-test.sh ```
(runs quick, but only performs movement and eating)
```bash
./run-test.sh ```
(runs slowers, but performas a fuller range of actions)


