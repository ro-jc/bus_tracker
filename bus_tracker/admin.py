import pickle
import getpass
import click

from werkzeug.security import generate_password_hash, check_password_hash
from flask import (
        Blueprint, flash, g, redirect, render_template, request, url_for
)
from flask.cli import with_appcontext

from bus_tracker.auth import admin_login_required
from bus_tracker.db import get_db
from bus_tracker.__init__ import stop_list, routes


bp = Blueprint('admin', __name__, url_prefix='/admin')


@bp.route('/')
@admin_login_required
def home():
    return render_template('admin/home.html')


@bp.route('/conductor', methods=('GET', 'POST'))
@admin_login_required
def conductor():
    record=''
    if request.method == 'POST':
        name = request.form['name']
        password = request.form['password']
        db = get_db()
        crs = db.cursor(dictionary=True)
        error = None
        '''
        if x is None:
            error = 'blah blah blah'
        flash(error)
        '''
        if error is None:
            crs.execute(
                f"INSERT INTO conductor (name, password) VALUES ('{name}', '{generate_password_hash(password)}')"
            )
            db.commit()

        crs.execute("SELECT * FROM conductor ORDER BY userid DESC LIMIT 1")
        record = crs.fetchone()
        #else condition in case there was a new record added before this one could be read off the database
        record['password'] = password if check_password_hash(record['password'], password) else "intermediate write"

    return render_template('admin/conductor_driver.html', conductor=True, record=record)


@bp.route('/bus', methods=('GET', 'POST'))
@admin_login_required
def bus():
    record=''
    action=''
    if request.method == 'POST':
        registration = request.form['registration'].upper()
        conductor_id = request.form['conductor_id']
        driver_id = request.form['driver_id']
        route = request.form['route'].upper()
        bus_type = request.form['type']
        stop_index = request.form['stop_index']
        stop_time = '00:00:00'
        seat_available = 1
        db = get_db()
        crs = db.cursor(dictionary=True)
        error = None

        if route not in routes:
            error = 'Route is not in defined. Please add it first'

        if error is None:
            crs.execute(f"SELECT * FROM bus WHERE registration='{registration}'")
            record = crs.fetchone()

            if record is None:
                action="Added"
                updated_record = (registration, int(conductor_id), int(driver_id), route, bus_type, stop_index, stop_time, seat_available)
                try:
                    crs.execute(
                        f"INSERT INTO bus VALUES {updated_record}"
                    )
                    db.commit()
                    crs.execute(f"SELECT * FROM bus WHERE registration='{registration}'")
                    record = crs.fetchone()
                except Exception as e:
                    print(e)
                    flash(str(e))
            else:
                action="Edited"
                new_record = dict(record)
                for key in record:
                    if request.form.get(key,None):
                        if request.form[key]==record[key]:
                            new_record.pop(key)
                        else:
                            new_record[key]=request.form[key]
                    else:
                        new_record.pop(key)

                if route in routes or route=='':
                    query_param = ''
                    #build query by adding  which attributes to update
                    for param_set in new_record.items():
                        #handle integer and string cases
                        if type(param_set[1])==int:
                            query_param += f"{param_set[0]}={param_set[1]}, "
                        else:
                            query_param += f"{param_set[0]}='{param_set[1]}', "

                    crs.execute(f"UPDATE bus SET {query_param[:-2]} WHERE registration='{registration}'")
                    db.commit()
                    crs.execute(f"SELECT * FROM bus WHERE registration='{registration}'")
                    record = crs.fetchone()

        if error is not None:
            flash(error)

    return render_template('admin/bus.html', record=record, action=action, route_name_list=routes.keys())


@bp.route('/route', methods=('GET','POST'))
@admin_login_required
def route():
    global routes
    route=''
    route_name=''
    done=0
    if request.method == 'POST':
        route_name = request.form['route_name'].upper()
        route = request.form.get('route', '')

        if route != '':
            route = route.replace(', ',',').split(sep=',')
            route = [stop.strip() for stop in route if stop and not stop.isspace()]
            routes[route_name] = route

            with open("instance/routes.dat", "wb+") as f:
                pickle.dump(routes, f)
                f.seek(0)
                routes = pickle.load(f)
                print(routes[route_name])
            done=1
            
        else:     
            route = routes[route_name] if route_name in routes else ''
        route = str(route)[1:-1].replace("'","")

    return render_template('admin/route.html', route=route, route_name=route_name, done=done, route_name_list=routes.keys())


@bp.route('/driver', methods=('GET','POST'))
@admin_login_required
def driver():
    record=''
    if request.method == 'POST':
        error = None
        name = request.form['name']
        db = get_db()
        crs = db.cursor(dictionary=True)
        '''
        if name is None:
            error = 'Name is required'
        flash(error)
        '''
        if error is None:
            crs.execute(
                f"INSERT INTO driver (name) VALUES ('{name}')"
            )
            db.commit()
        crs.execute("SELECT * FROM driver ORDER BY userid DESC LIMIT 1")
        record = crs.fetchone()

    return render_template('admin/conductor_driver.html', conductor=False, record=record)


@bp.route('/remove', methods=('GET','POST'))
@admin_login_required
def remove():
    global routes
    error=None
    done = False
    value = ''
    record = dict()
    options = []

    table_name = request.args.get('table')
    if table_name:
        if table_name == 'route' or 'Route':
            options = list(routes.keys())
        elif table_name == 'bus' or 'Bus':
            db = get_db()
            crs = db.cursor(dictionary=True)
            crs.execute("SELECT registration from bus")
            options = [record['registration'] for record in crs.fetchall()]
        else:
            db = get_db()
            crs = db.cursor(dictionary=True)
            crs.execute(f"SELECT userid from {table_name.lower()}")
            options = [record['userid'] for record in crs.fetchall()]

    if request.method == 'POST':
        value = request.form['id']
        if table_name != 'route' or 'Route':
            if table_name == 'bus':
                crs.execute(f"SELECT * FROM bus WHERE registration='{value}'")
                record = crs.fetchone()
                crs.execute(f"DELETE FROM bus WHERE registration='{value}'")
            elif table_name == 'conductor':
                crs.execute(f"SELECT * FROM conductor WHERE userid='{value}'")
                record = crs.fetchone()
                crs.execute(f"DELETE FROM conductor WHERE userid={value}")
            else:
                crs.execute(f"SELECT * FROM driver WHERE userid='{value}'")
                record = crs.fetchone()
                crs.execute(f"DELETE FROM driver WHERE userid={value}")
            db.commit()
            done = True
        else:
            record = {value: routes.pop(value, None)}
            record = {} if not record[value] else record
            with open("instance/routes.dat", "wb+") as f:
                pickle.dump(routes, f)
                f.seek(0)
                routes = pickle.load(f)
            done=True

        if record == {}:
            done = False
            error = "Record does not exist, please recheck the value you entered"

    if error is not None:
        flash(error)

    return render_template('admin/remove.html', table_name=table_name.lower(), options=options, record=record, done=done)



@bp.route('/table')
@admin_login_required
def table():
    table_name = request.args.get('table_name') if request.args.get('table_name') else 'bus'

    if table_name in ('driver', 'bus'):
        db = get_db()
        crs = db.cursor(dictionary=True)
        crs.execute(f"SELECT * FROM {table_name}")
        table = crs.fetchall()
    elif table_name == 'conductor':
        db = get_db()
        crs = db.cursor(dictionary=True)
        crs.execute(f"SELECT userid, name FROM conductor")
        table = crs.fetchall()
    else:
        table = [{'Route Name': route_name, 'Route': routes[route_name]} for route_name in routes] 

    return render_template("admin/table.html", table=table, table_name=table_name)


@click.command('add-admin')
@with_appcontext
def add_admin_command():
    name = input("Admin name: ")
    password = getpass.getpass()
    db = get_db()
    crs = db.cursor()
    crs.execute(f"INSERT INTO admin (name, password) VALUES ('{name}', '{generate_password_hash(password)}')")
    db.commit()
    print(f"Admin {name} added")