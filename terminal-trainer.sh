#!/bin/bash

for script in ./q*.sh; do
    [ -f "$script" ] && bash "$script"
done