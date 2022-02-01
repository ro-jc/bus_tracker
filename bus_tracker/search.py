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
        stops = []
        for i in routes.values():
            for j in i:
                stops.append(j)
        
        #create a dictionary with routes which have the stops as keys and the indexes of their stops as values
        #and just keys for query and indexes for filtering the result after
        route_index = dict()
        for key in routes:
            if current_stop in [stop.lower() for stop in routes[key]]:
                route_index[key] = [stop.lower() for stop in routes[key]].index(current_stop)

        if len(route_index) >= 1:
            crs = get_db().cursor(dictionary=True)
            if len(route_index) == 1:
                crs.execute("SELECT registration, route, type, stop_index, stop_time, seat_available"
                            f" FROM bus WHERE route = '{next(iter(route_index))}'")
            else:
                crs.execute("SELECT registration, route, type, stop_index, stop_time, seat_available"
                            f" FROM bus WHERE route in {tuple(route_index)}")
            
            #check if bus has already passed the stop before adding to the result set
            for record in crs.fetchall():
                route_name = record['route']
                if not destination or destination in routes[route_name][route_index[route_name]+1:]:
                    if record['stop_index'] < route_index[route_name]:
                        record['current_stop'] = routes[route_name][record['stop_index']]
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
        mod_routes = {route_name: route for route_name, route in routes.items()
            if stop1 in [stop.lower() for stop in route] and stop2 in [stop.lower() for stop in route]}

    return render_template('search/route.html', routes=mod_routes, stop_list=stop_list)