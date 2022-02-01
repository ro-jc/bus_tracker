from flask import (
        Blueprint, flash, g, redirect, render_template, request, url_for
)
from werkzeug.exceptions import abort

from bus_tracker.auth import conductor_login_required
from bus_tracker.db import get_db
from bus_tracker.__init__ import routes

import pickle
import datetime


bp = Blueprint('conductor', __name__, url_prefix='/conductor')


@bp.route('/update', methods=('GET', 'POST'))
@conductor_login_required
def update():
    error = None
    db = get_db()
    crs = db.cursor(dictionary=True)
    conductor_id = g.user['userid']
    crs.execute(f"SELECT * FROM bus WHERE conductor_id={conductor_id}")
    record = crs.fetchone()

    if request.method == 'POST':
        update_seat = True if 'seat' in request.form else False
        update_stop = True if 'stop' in request.form else False
        
        if update_seat:
            crs.execute("UPDATE bus SET seat_available="
                        f"CASE WHEN seat_available=1 THEN 0 ELSE 1 END WHERE conductor_id={conductor_id}")
            db.commit()

        if update_stop:
            time = datetime.datetime.now().strftime('%T')

            if record['stop_index'] >= len(routes[record['route']]) - 1:
                error = "You seem to have crossed the last stop. Stop reset to having crossed the first one."
                stop_index = 0
            else:
                stop_index = record['stop_index'] + 1
            crs.execute(f"UPDATE bus SET stop_index={stop_index}, stop_time='{time}' WHERE conductor_id={conductor_id}")
            db.commit()

            return redirect(url_for("conductor.update"))

    if error is not None:
        flash(error)

    return render_template('conductor/update.html', record=record, route=routes[record['route']])