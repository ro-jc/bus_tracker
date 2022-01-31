from flask import (
        Blueprint, flash, g, redirect, render_template, request, session, url_for
    )
from bus_tracker.db import get_db
from bus_tracker.__init__ import stop_list, routes

import mysql.connector
import pickle


bp = Blueprint('search', __name__)

@bp.route('/', methods=('GET', 'POST'))
def search():
    results = []
    if request.method == 'POST':
        current_stop = request.form['current_stop'].title()
        destination = request.form['destination'].title()
        stops = []
        for i in routes.values():
            for j in i:
                stops.append(j)
        print(current_stop in stops)
        
        #create a dictionary with routes which have the stops as keys and the indexes of their stops as values
        #and just keys for query and indexes for filtering the result after
        route_index = dict()
        for key in routes:
            if current_stop in routes[key]:
                route_index[key] = routes[key].index(current_stop)

        if len(route_index) >= 1:
            crs = get_db().cursor(dictionary=True)
            if len(route_index) == 1:
                crs.execute("SELECT registration, route, type, stop_index, stop_time, seat_available"
                            f" FROM bus WHERE route = '{next(iter(route_index))}'")
            else:
                crs.execute("SELECT registration, route, type, stop_index, stop_time, seat_available"
                            f" FROM bus WHERE route in {tuple(route_index)}")
            
            #check if bus has already passed the stop before adding to the result set
            print(results)
            for record in crs.fetchall():
                route_name = record['route']
                print(routes[route_name][route_index[route_name]+1:])
                if not destination or destination in routes[route_name][route_index[route_name]+1:]:
                    if record['stop_index'] < route_index[route_name]:
                        record['current_stop'] = routes[route_name][record['stop_index']]
                        record['stop_time'] = str(record['stop_time'])[:-3]
                        record['seat_available'] = 'free seats' if  record['seat_available'] else 'no free seats'
                        results.append(record)

    return render_template('search/search.html', buses=results, stop_list=stop_list)