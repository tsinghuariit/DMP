from app import app,db
from flask.ext.script import Manager
from flask.ext.migrate import Migrate,MigrateCommand
from app.models import *
from tornado.options import options, define, parse_command_line


app.config.from_object('config_web')
migrate=Migrate(app,db)
manager=Manager(app)
manager.add_command('db',MigrateCommand)

if __name__=='__main__':
    manager.run()