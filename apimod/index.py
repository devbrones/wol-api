from flask import Flask, jsonify, request
import os
from config import *
import psycopg2

# jumbo
app = Flask(__name__)

# check if the error report file exists and create it otherwise
if os.path.isfile("/home/rex/projects/wol-api/error-reports"):
    print("Log | N | file error-reports exists")
else:
    print("Log | N | file error-reports does not exist, creating")
    os.mknod('/home/rex/projects/wol-api/error-reports')

#debug
print(Config().postgun)
#/&debug

# connect to the database
con = psycopg2.connect(user=Config().postgun,
                       password=Config().postgpw,
                       host="127.0.0.1",
                       port="5432",
                       database=Config().postdbname)
# create a cursor
cursor = con.cursor()
# print details of pgsql into log
print("PostgreSQL server details")
print(con.get_dsn_parameters(), "\n")



@app.route("/api/")
def ret_ok():
    return "ok!200!\n<h1>The API is active</h1>\n<p>Watch-on-LBRY API Version 1.0.10 by Devbrones https://tibroness.org</p>"

@app.route("/api/is-online")
def isonline():
    return """[{"online":"true"}]"""

@app.route("/api/report-error", methods=['POST'])
def error_report():
    # report an error by sending a POST request to http://madinator.com/api/
    with open("/home/rex/projects/wol-api/error-reports", "a") as errep:
        errep.write(str(request.get_json()))
        return '', 204

@app.route("/api/get-lbry-url", methods=['GET'])
def getlurl():
    # database management goes here, it will read the db for (request.args.get('url'))
    # and if it is found it returns url, otherwise it would be wise to query the LBRY
    # API and get the new url and store to db
    # db structure ex:
    # [
    #   {
    #   'yt-url':'dQw4w9WgXcQ',
    #   'yt-title':'Rick Astley - Never Gonna Give You Up (Official Music Video)',
    #   'lbry-url':'example_url',
    #   'lbry-title':'pickle rick funny '
    #   }
    # ]

    # select the url table
    cursor.execute("SELECT url();")
    # fetch result


    return request.args.get('url')
