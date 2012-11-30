from flask import Flask, render_template
import os
from collections import deque
app = Flask(__name__)

BEGIN_SIZE = END_SIZE = 20
def read_some(fn):
    if not os.path.exists(fn):
        return ''
    with open(fn) as f:
        begin = []
        end = deque(maxlen=END_SIZE)
        i = 0
        for i, line in enumerate(f):
            if i < BEGIN_SIZE:
                begin.append(line)
            else:
                end.append(line)
        missing = i+1-BEGIN_SIZE-END_SIZE
        pad = ['[... {0} lines ...]\n'.format(missing)] if len(end) == END_SIZE else []
        return ''.join(begin+pad+list(end)).decode('utf8')

class DuctTapeConfiguration:
    def __init__(self, task_name, conf_name):
        self.task_name = task_name
        self.conf_name = conf_name
        exit = task_name+'/'+conf_name+'/ducttape_exit_code.txt'
        if os.path.exists(exit):
            with open(exit) as f:
                self.exit_code = int(f.read())
        else:
            self.exit_code = None

    @property
    def stdout(self):
        return read_some(self.task_name+'/'+self.conf_name+'/ducttape_stdout.txt')

    @property
    def stderr(self):
        return read_some(self.task_name+'/'+self.conf_name+'/ducttape_stderr.txt')

class DuctTapeTask:
    def __init__(self, task_name):
        self.configurations = {}
        has_link = set() # 
        for d in os.listdir(task_name):
            if os.path.exists(task_name+'/'+d+'/'+'ducttape_stdout.txt'):
                if os.path.islink(task_name+'/'+d):
                    real_d = os.path.basename(os.path.realpath(task_name+'/'+d))
                    has_link.add(real_d)
                self.configurations[d] = DuctTapeConfiguration(task_name, d)
        # Remove aliases
        if len(self.configurations) > 1:
            for d in has_link:
                del self.configurations[d]

class DuctTapeWorkflow:
    def __init__(self):
        self.tasks = {}
        for d in os.listdir('.'):
            if os.path.exists(d+'/Baseline.baseline'):
                self.tasks[d] = DuctTapeTask(d)

@app.route('/task/<task_name>/<conf_name>')
def task(task_name, conf_name):
    configuration = DuctTapeConfiguration(task_name, conf_name)
    return render_template('task.html', configuration=configuration)

@app.route('/')
def index():
    workflow = DuctTapeWorkflow()
    return render_template('index.html', workflow=workflow)

if __name__ == '__main__':
    app.run(host='0.0.0.0')
