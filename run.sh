#!/bin/bash

# python script to parse csv file, *10 the relevant columns and gen the param
# file
# script also runs solver, takes output and get those rows
# in the csv
./savilerow-1.7.0RC-linux/savilerow -run-solver $@ 
cat *.solution
rm *.solution *.minion *.info *.infor
