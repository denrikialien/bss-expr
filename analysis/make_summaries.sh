#!/bin/bash

rm *.csv
python ../src/summary.py ../robustness-single/ single robustness-single.csv
python ../src/summary.py ../robustness-multi-u/ multi-u robustness-multi-u.csv
python ../src/summary.py ../basedist-single/ single basedist-single.csv
python ../src/summary.py ../basedist-multi-u/ multi-u basedist-multi-u.csv
python ../src/summary.py ../mobilerate-single/ single mobilerate-single.csv
python ../src/summary.py ../mobilerate-multi-u/ multi-u mobilerate-multi-u.csv