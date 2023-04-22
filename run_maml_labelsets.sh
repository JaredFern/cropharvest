#!/usr/bin/bash
python benchmarks/deep_learning.py --labelset consolidated --data_folder /projects/tir6/strubell/data/cropharvest/
python benchmarks/deep_learning.py --labelset coarse --data_folder /projects/tir6/strubell/data/cropharvest/
python benchmarks/deep_learning.py --labelset hierarchical --data_folder /projects/tir6/strubell/data/cropharvest/
