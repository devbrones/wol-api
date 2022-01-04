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
import logging

# jumbo
app = Flask(__name__)

# set up logging

logging.basicConfig(filename='apilog.log', level=logging.DEBUG, format=f'%(asctime)s %(levelname)s %(name)s %(threadName)s : %(message)s')
app.logger.info("NEW SESSION ___________________________________________________")


# check if the error report file exists and create it otherwise
if os.path.isfile("./error-reports"):
    app.logger.info("file error-reports exists")
else:
    app.logger.info("file error-reports does not exist, creating")
    os.mknod('./error-reports')

#debug

app.logger.info(Config().postgun)

#/debug

# connect to the database
con = psycopg2.connect(user=Config().postgun,
                       password=Config().postgpw,
                       host="127.0.0.1",
                       port="5432",
                       database=Config().postdbname)
# create a cursor
cursor = con.cursor()
# print details of pgsql into log
app.logger.info("PostgreSQL server details")
app.logger.info(str(str(con.get_dsn_parameters()) + "\n"))



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
    
    dat = request.get_json()

    if "error-report-value" in dat:
        with open("./error-reports", "a") as errep:
            errep.write(str(request.get_json()) + "\n")
            return '', 204
    else:
        dat = ""
        return '', 400

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
    
    # set up our most important baddies 
    dt =str(datetime.now(timezone.utc))
    urla = str(request.args.get('url'))

    # check if the search request exists in the database and if so return a jsonified structure
    # of the data.
    # else create the entry and scan lbrys api and add to resp cols.

    cursor.execute("select exists(select * from information_schema.tables where table_name='dataof_all')")

    if bool(cursor.fetchone()[0]):
        # if the table dataof_all exists then check if entry for urla exists, if so return
        # a json dictionary of said entry
        cursor.execute("SELECT * FROM dataof_all WHERE yturl = %s;", (urla,))
        #debug
        app.logger.info("table exists")
        if bool(cursor.fetchone()):
            cur2 = con.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            app.logger.info("entry exists")
            cur2.execute("SELECT * FROM dataof_all WHERE yturl = %s;", (urla,))
            res = cur2.fetchone()
            return jsonify(res)

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
                else:
                    lbryurl = ""
                # lbry url end

                # NEW: lbry channel return
                
                ydl_opts = {
                }
                video = "https://youtube.com/watch?v=" + urla
                with youtube_dl.YoutubeDL(ydl_opts) as ydl:
                    info_dict = ydl.extract_info(video, download=False)
                    ytchan = info_dict.get('channel_id', None)

                r = requests.get("https://api.odysee.com/yt/resolve?channel_ids=" + ytchan)
                if r.status_code == 200:
                    lut = r.json()
                    lbrych = lut['data']['channels'][ytchan]
                    #debug
                else:
                    lbrych = ""
                

                # end lcr

                return_object = {
                   'yt-url':urla,
                   'yt-title':yttitle,
                   'lbry-url':lbryurl,
                   'lbry-chn':lbrych,
                   'dtstamp':dt
                   }
                if bool(lbryurl):
                    # if there is a lbry url
                    cursor.execute("insert into dataof_all(yturl, yttitle, lbryurl, lbrych, dtstamp) values (%s,%s,%s,%s,%s);",(urla,yttitle,lbryurl,lbrych,dt,))
                    con.commit()
                    return jsonify(return_object)    
                else:
                    
                #cursor.execute("insert into dataof_all(id, yturl, yttitle, lbryurl, lbrytitle, dtstamp) values (%s,%s,%s,%s,%s,%s);"())
                    return jsonify(return_object)    

            except psycopg2.DatabaseError as error:
                app.logger.warning("last call could not be completed, cleaning up. %s",(error,))
                con.rollback()
    else:
        app.logger.warning("no table found, creating")
        cursor.execute(str("""CREATE TABLE dataof_all(
                           id int GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
                           yturl text,
                           yttitle text,
                           lbryurl text,
                           lbrych text,
                           dtstamp text);"""))
        con.commit()

        return "internal server error"

if __name__ == "__main__":
    app.run()
