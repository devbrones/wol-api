from flask import Flask, jsonify, request
import os
from apcnf import *
import psycopg2
import json
import collections


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
    return "ok!200!\n<h1>The API is active</h1>\n<p>Watch-on-LBRY API Version 1.0+c22 by Devbrones https://tibroness.org</p>"

@app.route("/api/is-online")
def isonline():
    online = {"online":True}
    return jsonify(online)

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

    # check if the url consists only of integers, and if so append ''

    urla = str("yt_" + request.args.get('url'))

    # check if the search request exists in the database and if so return a jsonified structure
    # of the data.
    # else create the table and scan lbrys api and add to resp cols.

    cursor.execute("select exists(select * from information_schema.tables where table_name=%s)", (urla,))

    if bool(cursor.fetchone()[0]):
        # if the search request exists in the database, select it and return the values as
        # a json dictionary

        cursor.execute(str("SELECT * FROM " + str(urla)))
        rows = cursor.fetchall()
        rowarr = []
        for row in rows:
            d = collections.OrderedDict()
            d['yttitle'] = row[0]
            d['lbryurl'] = row[1]
            d['lbrytitle'] = row[2]
            rowarr.append(d)
        return jsonify(rowarr)

    else:

       # else create a table with the name urla (ex. yt_dQw4w9WgXcQ) and append proper values
       # that we get from lbry api

        try:
            cursor.execute("select exists(select * from information_schema.tables where table_name=%s)", (urla,))

            if bool(cursor.fetchone()[0]):
                # select the url table
                cursor.execute(str("SELECT * FROM " + str(urla)))
                con.commit()
                print(str("SELECT * FROM " + str(urla)))
            else:
                cursor.execute(str("CREATE TABLE " + str(urla) + "(yttitle text, lbryurl text, lbrytitle text);"))
                con.commit()
                # select the url table
                cursor.execute(str("SELECT * FROM " + str(urla)))
                print(str("SELECT * FROM " + str(urla)))

                # the following is the response format from the odysee api
                # (https://api.odysee.com/yt/resolve?video_ids=YOUTUBEURL)

                #{
                #  "sucess": true,
                #  "error": null,
                #  "data": {
                #    "videos": {
                #      "YOUTUBEURL": "LBRYURL"
                #    {,
                #    "channels":null
                #  }
                #}

                # we now need to feed these values into their respective columns which for
                # us would be lbryurl and potentially lbrytitle
                # the other values will be fetched using some movie magic i guess!



        except psycopg2.DatabaseError as error:
            print("Log | N | last call could not be completed, cleaning up. %s",(error,))
            con.rollback()

        # fetch result

        record = cursor.fetchone()
        print(record)
        if record == None:
            record = "Null"
        # cursor.close()
        return_object = {'yttitle':ytt, 'lbryurl':urlb, 'lbrytitle':lbt}
        return jsonify(return_object)
if __name__ == "__main__":
    app.run()
