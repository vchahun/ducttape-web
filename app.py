from flask import Flask, render_template, request
import socket
import os
import re
import random
from collections import deque, defaultdict
app = Flask(__name__)

BEGIN_SIZE = END_SIZE = 20
def read_some(fn):
    if request.args.get('filter'):
        try:
            filter_re = re.compile(request.args['filter'])
        except Exception:
            filter_re = re.compile('')
    else:
        filter_re = re.compile('')
    if not os.path.exists(fn):
        return ''
    with open(fn) as f:
        begin = []
        end = deque(maxlen=END_SIZE)
        n_lines = 0
        for i, line in enumerate(f):
            if not filter_re.search(line): continue
            if n_lines < BEGIN_SIZE:
                begin.append(line)
            else:
                end.append(line)
            n_lines += 1
        missing = n_lines-len(begin)-len(end)
        pad = ['[... {0} lines ...]\n'.format(missing)] if missing > 0 else []
        return ''.join(begin+pad+list(end)).decode('utf8')

class DuctTapeConfiguration:
    def __init__(self, task_name, conf_name):
        self.task_name = task_name
        self.conf_name = conf_name
        self.aliases = set()
        exit = task_name+'/'+conf_name+'/ducttape_exit_code.txt'
        if os.path.exists(exit):
            with open(exit) as f:
                self.exit_code = int(f.read())
        else:
            self.exit_code = None
        invalidated = task_name+'/'+conf_name+'/ducttape.INVALIDATED'
        self.invalidated = os.path.exists(invalidated)

    @property
    def status(self):
        return ('invalidated' if self.invalidated
                else 'running' if self.exit_code is None 
                else 'succeeded' if self.exit_code == 0 else 'failed')

    @property
    def stdout(self):
        return read_some(self.task_name+'/'+self.conf_name+'/ducttape_stdout.txt')

    @property
    def stderr(self):
        return read_some(self.task_name+'/'+self.conf_name+'/ducttape_stderr.txt')

class DuctTapeTask:
    def __init__(self, task_name):
        self.configurations = {}
        links = defaultdict(list) # real path -> [path]
        for d in os.listdir(task_name):
            #if d.endswith('.LOCK'):
            #    self.configurations[d[:-5]] = DuctTapeConfiguration(task_name, d[:-5])
            if os.path.exists(task_name+'/'+d+'/'+'ducttape_stdout.txt'):
                if os.path.islink(task_name+'/'+d):
                    real_d = os.path.basename(os.path.realpath(task_name+'/'+d))
                    links[real_d].append(d)
                else:
                    links[d].append(d)
                self.configurations[d] = DuctTapeConfiguration(task_name, d)

        # remove aliases
        for real_d, names in links.iteritems():
            canonical_name = max(names, key=lambda name: (len(name.split('.')), name != 'Baseline.baseline'))
            for name in names:
                if name != canonical_name:
                    self.configurations[canonical_name].aliases.add(name)
                    del self.configurations[name]

class DuctTapeWorkflow:
    def __init__(self):
        self.tasks = {}
        for d in os.listdir('.'):
            if os.path.exists(d+'/Baseline.baseline'):
                self.tasks[d] = DuctTapeTask(d)

@app.route('/task/<task_name>/<conf_name>')
def task(task_name, conf_name):
    configuration = DuctTapeConfiguration(task_name, conf_name)
    return render_template('task.html', configuration=configuration, filter=request.args.get('filter', ''))

@app.route('/')
def index():
    workflow = DuctTapeWorkflow()
    return render_template('index.html', workflow=workflow)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=random.randint(1000, 10000))
