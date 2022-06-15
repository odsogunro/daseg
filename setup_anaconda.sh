#!/bin/bash

set -eou pipefail

# DAMI NOTE: 
# cudatoolkit and pytorch is backwards compatible
# https://pytorch.org/get-started/previous-versions/
if [[ "$OSTYPE" == "darwin"* ]]; then
  # conda install pytorch torchvision -c pytorch=1.6
  # conda install pytorch torchvision -c pytorch
  conda install pytorch==1.6.0 torchvision -c pytorch
else
  # conda install pytorch torchvision cudatoolkit=10.1 -c pytorch=1.6
  # conda install pytorch torchvision cudatoolkit=10.2 -c pytorch
  conda install pytorch==1.6.0 torchvision cudatoolkit=10.1 -c pytorch
fi

conda install numpy matplotlib pandas nltk tqdm jupyterlab pytest
