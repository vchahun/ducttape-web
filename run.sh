#!/usr/bin/env bash

dir=`dirname $0`
if [ ! -d $dir/env ]; then
    wget https://raw.github.com/pypa/virtualenv/master/virtualenv.py -O $dir/virtualenv.py
    python $dir/virtualenv.py env
    . $dir/env/bin/activate
    pip install -r requirements.txt
fi

$dir/env/bin/python $dir/app.py
