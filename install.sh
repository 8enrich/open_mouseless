#!/bin/bash

mkdir build

cython main.py --embed

mv main.c ./build

gcc -Os $(python3-config --includes) ./build/main.c -o ./build/open_mouseless $(python3-config --ldflags --embed) 
