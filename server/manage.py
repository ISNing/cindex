from flask_script import Manager

from App.init import create_app, init_first_run

app = create_app()

manager = Manager(app)


@manager.command
def first_run():
    init_first_run()


if __name__ == '__main__':
    manager.run()
