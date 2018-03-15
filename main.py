##http://flask.pocoo.org/docs/0.12/quickstart/#a-minimal-application

from flask import Flask
from flask import render_template
from flask import request
from src import Airyards


app = Flask('__main__')

## add below to ini file ------------------------------------------
app.config['DB_COMMANDS'] = ['wipe database', 'full data replace']
app.config['SB_COMMANDS'] = ['reception leaders 2017']


@app.route('/stats/')
def hold2():
    return "Get ready for some stats!"


@app.route('/hello/<name>')
def hello(name = None):
    return render_template('hello.html', name = name)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/index/sandbox', methods=['GET', 'POST'])
def sandbox():
    if request.method == 'GET':
        print('Running GET')
        return render_template('sandbox.html',
                               command_list = app.config['SB_COMMANDS'],
                               ran = 0,
                               ran_commands = None)
    else:
        ran = 0
        command = str(request.form.get('command'))
        print('Using {} command'.format(command))
        if command == 'reception leaders 2017':
            return render_template('sandbox_rec_leaders.html')
        try:
            ran = 1
        except Exception as e:
            ran = -1
            raise Exception(msg)
        return _sandbox(command_list = app.config['SB_COMMANDS'],
                            ran = ran,
                            ran_commands=[command])


@app.route('/index/sandbox/sandbox_rec_leaders', methods=['GET', 'POST'])
def sandbox_rec_leaders():
    if request.method == 'GET':
        print('Running GET')
        return render_template('sandbox_rec_leaders.html')

    else:
        ran = 0
        command = str(request.form.get('command'))
        print('Using {} command'.format(command))
        try:
            ran = 1
        except Exception as e:
            ran = -1
            raise Exception(msg)
        return _sandbox_rec_leaders(command_list = app.config['SB_COMMANDS'],
                            ran = ran,
                            ran_commands=[command])




@app.route('/index/update_data', methods=['GET', 'POST'])
def update_data():
    if request.method == 'GET':
        print('Running GET')
        return render_template('update_data.html',
                               command_list = app.config['DB_COMMANDS'],
                               ran = 0,
                               ran_commands = None)
    else:
        ran = 0
        command = str(request.form.get('command'))
        print('Using {} command'.format(command))
        try:
            if command == 'wipe database':
                Airyards.Airyards().wipe_airyards_table()
            if command == 'full data replace':
                Airyards.Airyards().wipe_airyards_table()
                for i in range(2009,2018):
                    print(str(i))
                    Airyards.Airyards(i).update_airyards_table()
                    print('year {} done'.format(str(i)))
            ran = 1
        except Exception as e:
            msg = 'Command {} errored. ERR - {}'.format(command, str(e))
            print(msg)
            ran = -1
            raise Exception(msg)
        return _update_data(command_list = app.config['DB_COMMANDS'],
                            ran = ran,
                            ran_commands=[command])


@app.route('/_get_sandbox_rec_leaders_pivot')
def _get_sandbox_rec_leaders_pivot():
    return(Airyards.Airyards().sandbox_reception_leaders())


def _update_data(command_list, ran, ran_commands):
   return render_template('update_data.html',
                          command_list = command_list,
                          ran = ran,
                          ran_commands = ran_commands)


def _sandbox(command_list, ran, ran_commands):
   return render_template('sandbox.html',
                          command_list = command_list,
                          ran = ran,
                          ran_commands = ran_commands)


def _sandbox_rec_leaders(command_list, ran, ran_commands):
   return render_template('sandbox_rec_leaders.html',
                          command_list = command_list,
                          ran = ran,
                          ran_commands = ran_commands)


if __name__ == '__main__':
    app.run(
        host="0.0.0.0",
        port=int("8080"),
        debug=True
    )

