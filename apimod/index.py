from flask import Flask, jsonify, request
import os

app = Flask(__name__)

if os.path.isfile("/home/rex/projects/wol-api/error-reports"):
    print("Log | N | file error-reports exists")
else:
    print("Log | N | file error-reports does not exist, creating")
    os.mknod('/home/rex/projects/wol-api/error-reports')

@app.route("/")
def ret_ok():
    return "ok!200!\n<p>The API is active</p>"
@app.route("/is-online")
def isonline():
    return """[{"online":"true"}]"""

@app.route("/report-error", methods=['POST'])
def error_report():
    with open("/home/rex/projects/wol-api/error-reports", "a") as errep:
        errep.write(str(request.get_json()))
        return '', 204

