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
import re
import requests

# thanks https://gist.github.com/codsane/25f0fd100b565b3fce03d4bbd7e7bf33
def commitCount(u, r):
	return re.search('\d+$', requests.get('https://api.github.com/repos/{}/{}/commits?per_page=1'.format(u, r)).links['last']['url']).group()

app = Flask(__name__)
con = psycopg2.connect(user=Config().postgun,
                       password=Config().postgpw,
                       host=Config().postghost,
                       port=Config().postgport,
                       database=Config().postdbname)
# create a cursor
cursor = con.cursor()

def isonline_v1():
    """! Returns a JSON online object.

    This feature is obsolete but I kept it anyways.

    @param None None
    @return     [{"online":true}]
    Raises:
        200 OK
    """
    
    online = {"online":True}
    return jsonify(online)

def error_report_v1(dat):
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
    
    #dat = request.get_json()

    if "error-report-value" in dat:
        with open("./error-reports", "a") as errep:
            errep.write(str(dat) + "\n")
            return '', 204
    else:
        dat = ""
        return '', 400

def getlch_v1(urla):
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
    #urla = str(request.args.get('url'))
    
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
                
def getlurl_v1(urla):
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
    #urla = str(request.args.get('url'))

    # check if the search request exists in the database and if so return a jsonified structure
    # of the data.
    # else create the entry and scan lbrys api and add to resp cols.
    
    if not re.match("^([A-z0-9_-]{11})$", urla):
        return jsonify({"error":"invalid url passed"}), 404
    
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
                try:
                    ydl_opts = {
                    }
                    video = "https://youtube.com/watch?v=" + urla
                    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
                        info_dict = ydl.extract_info(video, download=False)
                        yttitle = info_dict.get('title', None)
                except youtube_dl.utils.DownloadError as e:
                    return jsonify({"error":str(e),"error_hr":"No such video was found!"}), 404

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

def getdbcount_v1(type):
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

    if type == "json": 
        return_object = {'video_count':countv, 'channel_count':countc}
        return jsonify(return_object)
    else:
        vers = commitCount("devbrones","wol-api")
        return render_template("status.html", vnum=countv, cnum=countc, ver=vers)

def demo_v1():
    return render_template("demo.html")

def submv_v1(method, r):
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
    
    if method == 'POST':
    
        dt =str(datetime.now(timezone.utc))
        try: 
            cursor.execute("select exists(select * from information_schema.tables where table_name='submissions')")

            if bool(cursor.fetchone()[0]):
                app.logger.info("table submissions found")
                #r = request.get_json()
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
