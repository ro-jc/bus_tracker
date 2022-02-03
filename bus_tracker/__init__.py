import os
from flask import Flask, redirect, url_for
from pickle import load

stop_list = load(open("instance/stop_list.dat", "rb"))
routes = load(open("instance/routes.dat", "rb"))

def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY='1qfvjfdsakfsaldfiugafgdfb fliufg sldfgvfvw lgefkvgbfiv'
    )

    if test_config is None:
        app.config.from_pyfile('config.py', silent=True)
    else:
        app.config.from_mapping(test_config)

    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    from . import db
    db.init_app(app)

    from . import auth
    app.register_blueprint(auth.bp)

    from . import search
    app.register_blueprint(search.bp)
    @app.route('/')
    def return_to_bus():
        return redirect(url_for("search.bus"))

    from . import admin
    app.register_blueprint(admin.bp)
    app.cli.add_command(admin.add_admin_command)

    from . import conductor
    app.register_blueprint(conductor.bp)
    return app