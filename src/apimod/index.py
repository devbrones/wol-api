##
# @mainpage index.py, The home of our API
#
# @section description_main Description and Copyright notice.
# 
# This file is the main application that runs the wol-api. In this application we declare
# all the possible API calls that can be made with this api while it is active. 
#
# Copyright (c) 2021, 2022 Tibroness. Under the GNU General public license 2.0.
# 
# This file is part of wol-api.
#
# This file is free software: you can redistribute it and/or modify it under the
# terms of the GNU General Public License as published by the Free Software Foundation,
# ether version 2 of the License, or (at your option) any later version.
#
# This program is distrobuted in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A 
# PARTICULAR PURPOSE. See the GNU General Public License for more details.
#
# You should have recieved a copy of the GNU General Public License along with this 
# program. If not, see <https://www.gnu.org/licenses/>.
#
# @section notes_main Notes
# - This application is still bery early in its production, please handle the product at your own risk
#

##
# @file index.py
#
# @brief The main file where the API functions are declared.
#
# @section description_index 
# This file is the main application that runs the wol-api. In this application we declare
# all the possible API calls that can be made with this api while it is active. 
#
# @section libraries_index Libraries/Modules
# - Flask 
# - os
# - apcnf.py
# - psycopg2
# - psycopg2.extras
# - json 
# - collections
# - requests
# - youtube_dl
# - datetime
# - logging
# - re
# - requests
#
# @section todo_index ToDo
# - Change the API landing page (/api/)
#
# @section author_index Author(s)
# - Created by Tibroness (https://github.com/devbrones) as per request by Madiator (https://github.com/kodxana)
# - Modified by Tibroness (https://github.com/devbrones)

from flask import Flask, jsonify, request, send_from_directory, render_template, abort
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import os
from apcnf import *
import psycopg2
import psycopg2.extras
import json
import collections
import requests
import youtube_dl
from datetime import datetime, timezone
import logging
import re
import requests
from v1 import *
from v2 import *

# thanks https://gist.github.com/codsane/25f0fd100b565b3fce03d4bbd7e7bf33
def commitCount(u, r):
	return re.search('\d+$', requests.get('https://api.github.com/repos/{}/{}/commits?per_page=1'.format(u, r)).links['last']['url']).group()
print(commitCount("devbrones", "wol-api"))
app = Flask(__name__)

limiter = Limiter(
            app,
            key_func=get_remote_address,
            default_limits=["200 per day", "50 per hour"]
        )

debug = 0
# Set up logging

logging.basicConfig(filename='apilog.log', level=logging.DEBUG, format=f'%(asctime)s %(levelname)s %(name)s %(threadName)s : %(message)s')
app.logger.info("NEW SESSION ___________________________________________________")


# check if the error report file exists and create it otherwise
if os.path.isfile("error-reports"):
    app.logger.info("file error-reports exists")
else:
    app.logger.info("file error-reports does not exist, creating")
    os.mknod('error-reports')

# connect to the database
#con = psycopg2.connect(user=Config().postgun,
#                       password=Config().postgpw,
#                       host=Config().postghost,
#                       port=Config().postgport,
#                       database=Config().postdbname)
#app.logger.info("connected to database")
# create a cursor
#cursor = con.cursor()
# print details of pgsql into log
app.logger.info("PostgreSQL server details")
app.logger.info(str(str(con.get_dsn_parameters()) + "\n"))



@app.route("/api/")
def ret_ok():
    """! Returns the Documentation webpage.

    This function literally does nothing but that.

    @param None None
    @return     The API documentation in pdf.
    Raises:
        200 OK
    """
    
    return send_from_directory("../../docs/wol-docs/latex/", 'refman.pdf')

@app.route("/api/is-online")
def ison():
    version = request.args.get('v')
    if version == "1":
        return isonline_v1()
    elif version == "2":
        return isonline_v2()
    else:
        return("invalid api version")

@app.route("/api/report-error", methods=['GET'])
@limiter.limit("5 per hour")
def error_report():
    version = request.args.get('v')
    t = request.args.get("errtype")
    v = request.args.get("errvalue")
    if version == "1":
        print("version 1 requested")
        return error_report_v1(request.method, t, v)
    elif version == "2":
        print("version 2 requested")
        return error_report_v2(request.method, t, v)

@app.route("/api/get-lbry-channel", methods=['GET'])
def getc():
    version = request.args.get('v')
    if version == "1":
        return getlch_v1(str(request.args.get('url')))
    elif version == "2":
        return getlch_v2(str(request.args.get('url')))
    else:
        return getlch_v1(str(request.args.get('url')))

@app.route("/api/get-lbry-video", methods=['GET'])
def getv():
    version = request.args.get('v')
    if version == "1":
        return getlurl_v1(str(request.args.get('url')))
    elif version == "2":
        return getlurl_v2(str(request.args.get('url')))
    else:
        return getlurl_v1(str(request.args.get('url')))

@app.route("/api/db-count/", methods=['GET'])
def getdb():
    version = request.args.get('v')
    if version == "1":
        return getdbcount_v1(request.args.get('type'))
    elif version == "2":
        return getdbcount_v2(request.args.get('type'))
    else:
        return getdbcount_v1(request.args.get('type'))

@app.route("/api/demo/", methods=['GET'])
def demo():
    version = request.args.get('v')
    if version == "1":
        return demo_v1()
    elif version == "2":
        return demo_v2()
    else:
        return demo_v1()


@app.route("/api/submit-video", methods=['GET', 'POST'])
@limiter.limit("5 per hour", methods=['POST'])
def submit():
    version = request.args.get('v')
    if version == "1":
        return submv_v1(request.method, request.get_json())
    elif version == "2":
        return submv_v2(request.method, request.form)
    else:
        return submv_v1(request.method, request.get_json())

if __name__ == "__main__":
    app.run()
