#!/bin/bash
#SBATCH --job-name=cropharvest-train
#SBATCH --exclude=tir-0-32,tir-0-36
#SBATCH --nodes=1
#SBATCH --gres=gpu:1
#SBATCH --mem=32GB
#SBATCH --time 1-00:00:00

source activate cropharvest;
python deep_learning.py;
