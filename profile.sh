#!/bin/bash

mprof run python3 -m memory_profiler test-env.py ; mprof plot
