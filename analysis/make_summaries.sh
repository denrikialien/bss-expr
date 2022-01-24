#!/bin/bash

rm *.csv
python ../src/summary.py ../output-robustness-single/ single robustness-single.csv
python ../src/summary.py ../output-robustness-multi-u/ multi-u robustness-multi-u.csv
python ../src/summary.py ../output-basedist-single/ single basedist-single.csv
python ../src/summary.py ../output-basedist-multi-u/ multi-u basedist-multi-u.csv
python ../src/summary.py ../output-mobilerate-single/ single mobilerate-single.csv
python ../src/summary.py ../output-mobilerate-multi-u/ multi-u mobilerate-multi-u.csv