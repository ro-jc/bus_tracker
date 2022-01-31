import functools
from mysql.connector import IntegrityError

from flask import (
        Blueprint, flash, g, redirect, render_template, request, session, url_for
    )
from werkzeug.security import check_password_hash, generate_password_hash

from bus_tracker.db import get_db

bp = Blueprint('auth', __name__, url_prefix='/auth')

@bp.route('/login', methods=('GET', 'POST'))
def login():
    if request.method == 'POST':
        user_id = request.form['userid']
        password = request.form['password']
        db = get_db()
        crs = db.cursor(dictionary=True)
        error = None
        crs.execute(
            f"SELECT * FROM conductor WHERE userid = {user_id}"
        )
        user = crs.fetchone()
        crs.execute(f"SELECT * FROM bus WHERE conductor_id={user_id}")
        if not crs.fetchone():
            error = "You are not assigned to a bus. Please ask admin to update if this is a mistake."

        if user is None:
            error = 'Incorrect id'
        elif not check_password_hash(user['password'], password):
            error = 'Incorrect password'

        if error is None:
            session.clear()
            session['user_id'] = 'C' + str(user['userid']) #convert uid to string and prefix with 'C' to identify as conductor
            return redirect(url_for('conductor.update'))
        else:
            flash(error)

    return render_template('auth/login.html', admin=False)

@bp.route('/adminlogin', methods=('GET', 'POST'))
def adminlogin():
    if request.method == 'POST':
        user_id = request.form['userid']
        password = request.form['password']
        db = get_db()
        crs = db.cursor(dictionary=True)
        error = None
        crs.execute(
            f"SELECT * FROM admin WHERE userid = {user_id}"
        )
        user = crs.fetchone()

        if user is None:
            error = 'Incorrect id'
        elif not check_password_hash(user['password'], password):
            error = 'Incorrect password'

        if error is None:
            session.clear()
            session['user_id'] = 'A' + str(user['userid']) #convert uid to string and prefix with 'A' to identify as admin
            return redirect(url_for('admin.home'))  
        else:
            flash(error)

    return render_template('auth/login.html', admin=True)

@bp.before_app_request
def load_logged_in_user():
    user_id = session.get('user_id')

    if user_id is None:
        g.user = None
    else:
        crs = get_db().cursor(dictionary=True)
        if user_id[0]=='C':
            admin = False
            crs.execute(
                f'SELECT * FROM conductor WHERE userid = {user_id[1:]}'
            )
        else:
            admin = True
            crs.execute(
                f'SELECT * FROM admin WHERE userid = {user_id[1:]}'
            )
        g.user = crs.fetchone()
        g.user['admin']=admin

@bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('search'))

def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for('auth.login')) 
        return view(**kwargs)
    return wrapped_view

#making sure no sneaky conductors try to access the admin portal/pages.....
def admin_login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None or not g.user.get('admin',False):
            return redirect(url_for('auth.adminlogin')) 

        return view(**kwargs)

    return wrapped_view