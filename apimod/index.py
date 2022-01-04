from flask import Flask, jsonify, request
import os
from apcnf import *
import psycopg2
import psycopg2.extras
import json
import collections
import requests
import youtube_dl
from datetime import datetime, timezone


#dt="1212"

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
    return "ok!200!\n<h1>The API is active</h1>\n<p>Watch-on-LBRY API Version 1.1+c35 by Devbrones https://tibroness.org</p>"

@app.route("/api/is-online")
def isonline():
    online = {"online":True}
    return jsonify(online)

@app.route("/api/report-error", methods=['POST'])
def error_report():
    # report an error by sending a POST request to http://madinator.com/api/
    # this code needs to be adapted to work better with a database rather than json

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
    #   'id':id
    #   'yt-url':'dQw4w9WgXcQ',
    #   'yt-title':'Rick Astley - Never Gonna Give You Up (Official Music Video)',
    #   'lbry-url':'example_url',
    #   'lbry-title':'pickle rick funny '
    #   'dtstamp':datetime
    #   }
    # ]

    dt =str(datetime.now(timezone.utc))
    urla = str(request.args.get('url'))

    # check if the search request exists in the database and if so return a jsonified structure
    # of the data.
    # else create the entry and scan lbrys api and add to resp cols.

    # THIS CODE NEEDS TO BE CHANGED, NOW IT CREATES TABLES NOT ENTRIES!!!!!!

    cursor.execute("select exists(select * from information_schema.tables where table_name='dataof_all')")

    if bool(cursor.fetchone()[0]):
        # if the table dataof_all exists then check if entry for urla exists, if so return
        # a json dictionary of said entry
        cursor.execute("SELECT * FROM dataof_all WHERE yturl = %s;", (urla,))
        #debug
        print("table exists")
        if bool(cursor.fetchone()):
            #debug
            cur2 = con.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            print("entry exists")
            cur2.execute("SELECT * FROM dataof_all WHERE yturl = %s;", (urla,))
            res = cur2.fetchone()
            print(type(res))
            print(res)
            return jsonify(res)

            #for some reason the code seems to fail here without any exceptions so ima give this one a thinker

        else:

        # else create a entry and append proper values
        # that we get from lbry api

            try:
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
                
                # yt title begin
                ydl_opts = {
                }
                video = "https://youtube.com/watch?v=" + urla
                with youtube_dl.YoutubeDL(ydl_opts) as ydl:
                    info_dict = ydl.extract_info(video, download=False)
                    yttitle = info_dict.get('title', None)
                # yt title end

                # lbry url begin
                r = requests.get("https://api.odysee.com/yt/resolve?video_ids=" + urla)
                if r.status_code == 200:
                    lut = r.json()
                    lbryurl = lut['data']['videos'][urla]
                    #debug
                    print(lbryurl)
                else:
                    lbryurl = ""
                # lbry url end

                return_object = {
                   'yt-url':urla,
                   'yt-title':yttitle,
                   'lbry-url':lbryurl,
                   'dtstamp':dt
                   }
                if bool(lbryurl):
                    # if there is a lbry url
                    cursor.execute("insert into dataof_all(yturl, yttitle, lbryurl, dtstamp) values (%s,%s,%s,%s);",(urla,yttitle,lbryurl,dt,))
                    con.commit()
                    return jsonify(return_object)    
                else:
                    
                #cursor.execute("insert into dataof_all(id, yturl, yttitle, lbryurl, lbrytitle, dtstamp) values (%s,%s,%s,%s,%s,%s);"())
                    return jsonify(return_object)    

            except psycopg2.DatabaseError as error:
                print("Log | N | last call could not be completed, cleaning up. %s",(error,))
                con.rollback()
    else:
        cursor.execute(str("""CREATE TABLE dataof_all(
                           id int GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
                           yturl text,
                           yttitle text,
                           lbryurl text,
                           dtstamp text);"""))
        con.commit()

        # do we need to do all above here?


        # _______________

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
