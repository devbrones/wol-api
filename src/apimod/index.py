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
#
# @section todo_index ToDo
# - Change the API landing page (/api/)
#
# @section author_index Author(s)
# - Created by Tibroness (https://github.com/devbrones) as per request by Madiator (https://github.com/kodxana)
# - Modified by Tibroness (https://github.com/devbrones)

from flask import Flask, jsonify, request, send_from_directory, render_template, abort
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

app = Flask(__name__)

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
con = psycopg2.connect(user=Config().postgun,
                       password=Config().postgpw,
                       host=Config().postghost,
                       port=Config().postgport,
                       database=Config().postdbname)
app.logger.info("connected to database")
# create a cursor
cursor = con.cursor()
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
def isonline():
    """! Returns a JSON online object.

    This feature is obsolete but I kept it anyways.

    @param None None
    @return     [{"online":true}]
    Raises:
        200 OK
    """
    
    online = {"online":True}
    return jsonify(online)

@app.route("/api/report-error", methods=['POST'])
def error_report():
    """! Report an error by sending a POST request to /api/report-error
        
    Error reporting function.
    TODO: This code needs to be adapted to work better with a database rather than JSON
    
    @param error-report-type    Can be "exception", "bug", or even "abcdefg"
    @param error-report-value   The error message to be passed to the log, i.e. "Extension did not load."
    @return 204
    
    Raises:
        Error in "error-reports" file.
    
    Examples:
        curl -X POST -H "Content-Type: application/json" -d '{"error-report-type":"exception","error-report-value":"Extension could not read webcontent"}' http://localhost:5000/api/report-error
        
        Writes an error in the above seen JSON format into the "error-reports" file.
    """
    
    dat = request.get_json()

    if "error-report-value" in dat:
        with open("./error-reports", "a") as errep:
            errep.write(str(request.get_json()) + "\n")
            return '', 204
    else:
        dat = ""
        return '', 400

@app.route("/api/get-lbry-channel", methods=['GET'])
def getlch():
    """! Get information about a YouTube Channel.
    
    This function gets information on from odysee's API and saves that data to a database, and eventually returns a JSON Object.
    If an entry for the URL exists then it reads from that database entry.

    @param url  The YouTube URL
    @return A JSON dictionary like this one:
    
    Raises:
        Entry in log. 
        Database functions.
    
    Examples:
        curl http://localhost:5000/api/get-lbry-channel?url=CHANNELID
        Returns: {"dtstamp": TIME_WAS_ADDED,"id":ID,"lbrych":LBRY_CHANNEL_URL,"ytch":null,"yturl":CHANNELID} 
        
            

    """
    
    dt =str(datetime.now(timezone.utc))
    urla = str(request.args.get('url'))
    
    cursor.execute("select exists(select * from information_schema.tables where table_name='dataof_channels')")

    if bool(cursor.fetchone()[0]):
        cursor.execute("SELECT * FROM dataof_channels WHERE yturl = %s;", (urla,))
        #debug
        app.logger.info("table exists - channels")
        if bool(cursor.fetchone()):
            cur2 = con.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            app.logger.info("entry exists")
            cur2.execute("SELECT * FROM dataof_channels WHERE yturl = %s;", (urla,))
            res = cur2.fetchone()
            return jsonify(res)

        else:
            try:
                # NEW: lbry channel return

                r = requests.get("https://api.odysee.com/yt/resolve?channel_ids=" + urla)
                if r.status_code == 200:
                    lut = r.json()
                    print(lut)
                    lbrych = lut['data']['channels'][urla]
                    print(str("ch found, " + str(lbrych)))#debug
                else:
                    lbrych = ""
                

                # end lcr
                """
                video = "https://youtube.com/watch?v=" + urla
                with youtube_dl.YoutubeDL(ydl_opts) as ydl:
                    info_dict = ydl.extract_info(video, download=False)
                    ytch = info_dict.get('uploader_url', None)
                """             
                return_object = {
                   'yt-url':urla,
                   'lbry-chn':lbrych,
                   'dtstamp':dt
                   }
                if bool(lbrych):
                    # if there is a lbry url
                    print("there is a lbry url")
                    cursor.execute("insert into dataof_channels(yturl, lbrych, dtstamp) values (%s,%s,%s);",(urla,lbrych,dt,))
                    con.commit()
                    return jsonify(return_object) 
                else:
                    print("there is no lbry url")
                    return jsonify(return_object), 404        

            except psycopg2.DatabaseError as error:
                app.logger.warning("last call could not be completed, cleaning up. %s",(error,))
                con.rollback()
    else:
        app.logger.warning("no table found, creating")
        cursor.execute(str("""CREATE TABLE dataof_channels(
                           id int GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
                           yturl text,
                           ytch text,
                           lbrych text,
                           dtstamp text);"""))
        con.commit()

        return "internal server error"


@app.route("/api/get-lbry-video", methods=['GET'])
def getlurl():
    """! Get information about a YouTube Video.
    
    This function gets information on from odysee's API and saves that data to a database, and eventually returns a JSON Object.
    If an entry for the URL exists then it reads from that database entry.

    @param url  The YouTube URL
    @return A JSON dictionary like this one: "{"dtstamp":"2022-01-04 23:26:09.752372+00:00","id":2,"lbrych":"@AlphaNerd#8d497e7e96c789364c56aea7a35827d2dc1eea65","lbryurl":"@AlphaNerd#8/how-monero-works-and-why-its-a-better#a","yttitle":"How Monero Works (And Why its a Better Currency Than BTC)","yturl":"QrHsFZBab4U"}"
    
    Raises:
        Entry in log. 
        Database functions.
    
    Examples:
        curl http://localhost:5000/api/get-lbry-video?url=QrHsFZBab4U
        Returns: 
        {
            "dtstamp":"2022-01-04 23:26:09.752372+00:00",
            "id":2,
            "lbryurl":"@AlphaNerd#8/how-monero-works-and-why-its-a-better#a",
            "yttitle":"How Monero Works (And Why its a Better Currency Than BTC)",
            "yturl":"QrHsFZBab4U"
        }
    """
    
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
                    return jsonify(return_object), 404

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
                           dtstamp text);"""))
        con.commit()

        return "internal server error"

@app.route("/api/db-count/", methods=['GET'])
def getdbcount():
    """! Get data amount.
    
    This function gets information on from our database, and returns either a webpage with the data or if specified, a JSON Object with the number of indexed videos and channels.
    If no entries are found it returns 0.

    @param type Specify format, if this is blank it will return in HTML format, if this key has the value "json" a json string will be returned.
    @return Webpage or a JSON dictionary like this one: "{"channel_count":1,"video_count":2}"
    
    Examples:
        curl http://localhost:5000/api/db-count?type=json
        Returns: {"channel_count":1,"video_count":2}
    """
    
    cursor.execute("select exists(select * from information_schema.tables where table_name='dataof_all')")

    if bool(cursor.fetchone()[0]):
        app.logger.info("table dataof_all found")
        # this is a very slow method i know but estimates are sus
        cursor.execute("SELECT count(*) AS exact_count FROM dataof_all")
        countv = cursor.fetchone()[0]
    else:
        countv = 0
    
    cursor.execute("select exists(select * from information_schema.tables where table_name='dataof_channels')")

    if bool(cursor.fetchone()[0]):
        app.logger.info("table dataof_channels found")
        # this is a very slow method i know but estimates are sus
        cursor.execute("SELECT count(*) AS exact_count FROM dataof_channels")
        countc = cursor.fetchone()[0]
    else:
        countc = 0

    if request.args.get('type') == "json": 
        return_object = {'video_count':countv, 'channel_count':countc}
        return jsonify(return_object)
    else:
        return render_template("status.html", vnum=countv, cnum=countc)

@app.route("/api/submit-video", methods=['GET', 'POST'])
def submv():
    """! Submit a request.
    
    This function lets a user submit a request to our server containing a youtube video url and a lbry url.
    The submissions will be manually verified by an admin.

    @param yturl    Youtube URL 
    @param lbryurl  LBRY URL

    @return 204, or a webpage if the method is GET
    
    Raises:
        Database entry.

    Examples:
        curl -X POST -H "Content-Type: application/json" -d '{"yturl":YTURL,"lbryurl":LBRYURL}' http://localhost:5000/api/submit-video
        Returns: 204
    """
    
    if request.method == 'POST':
    
        dt =str(datetime.now(timezone.utc))
        try: 
            cursor.execute("select exists(select * from information_schema.tables where table_name='submissions')")

            if bool(cursor.fetchone()[0]):
                app.logger.info("table submissions found")
                r = request.get_json()
                lbryurl = r['lbryurl']
                yturl = r['yturl']

                if bool(lbryurl):
                    # if there is a lbry url
                    cursor.execute("insert into submissions(yturl, lbryurl, dtstamp) values (%s,%s,%s);",(yturl,lbryurl,dt,))
                    con.commit()
                    return '', 204   
                else:
                    return '', 400
            else:
                app.logger.warning("no table found, creating")
                cursor.execute(str("""CREATE TABLE submissions(
                                   id int GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
                                   yturl text,
                                   lbryurl text,
                                   dtstamp text);"""))
                con.commit()
                return("reload") 

        except psycopg2.DatabaseError as error:
            app.logger.warning("last call could not be completed, cleaning up. %s",(error,))
            con.rollback()
    else:
        return render_template("submit.html")







if __name__ == "__main__":
    app.run()
