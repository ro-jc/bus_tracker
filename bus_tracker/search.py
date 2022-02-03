from flask import (
        Blueprint, flash, g, redirect, render_template, request, session, url_for
    )
from bus_tracker.db import get_db
from bus_tracker.__init__ import stop_list, routes

import mysql.connector
import pickle


bp = Blueprint('search', __name__, url_prefix="/search")


@bp.route('/bus', methods=('GET', 'POST'))
def bus():
    results = []
    if request.method == 'POST':
        current_stop = request.form['current_stop'].lower()
        destination = request.form['destination'].lower()
        
        #create a dictionary with routes which have the route names as keys and the indexes of the current stop if exists as values
        #will use keys for query and indexes for filtering the result after depending on where the destination comes
        route_indexes = dict()
        for key in routes:
            if current_stop in [stop.lower() for stop in routes[key]]:
                route_indexes[key] = [stop.lower() for stop in routes[key]].index(current_stop)
        
        crs = get_db().cursor(dictionary=True)
        crs.execute("SELECT registration, route, type, stop_index, stop_time, seat_available"
                    f" FROM bus WHERE route in {tuple(route_indexes)}")
            
        #check if bus has already passed the stop before adding to the result set
        for record in crs.fetchall():
            route_name = record['route']
            route_index = route_indexes[route_name]
            if not destination or destination in [stop.lower() for stop in routes[route_name][route_index+1:]]:
                if record['stop_index'] < route_indexes[route_name]:
                    record['current_stop'] = routes[route_name][record['stop_index']]
                    record['gap'] = [stop.lower() for stop in routes[route_name]].index(current_stop) - record['stop_index']
                    record['stop_time'] = str(record['stop_time'])[:-3]
                    record['seat_available'] = 'free seats' if  record['seat_available'] else 'no free seats'
                    results.append(record)

    return render_template('search/bus.html', buses=results, stop_list=stop_list)


@bp.route('/route', methods=('GET','POST'))
def route():
    mod_routes = {}
    if request.method == 'POST':
        stop1 = request.form['stop1'].lower()
        stop2 = request.form['stop2'].lower()
        route_name = request.form['route_name'].upper()

        #check if query is with route_name or stops
        if route_name != '':
            mod_routes = {route_name: routes[route_name]} if route_name in routes else {}
        else:
            mod_routes = {route_name: route for route_name, route in routes.items()
                if stop1 in [stop.lower() for stop in route] and stop2 in [stop.lower() for stop in route]}

    return render_template('search/route.html', routes=mod_routes, stop_list=stop_list, route_name_list = routes.keys())