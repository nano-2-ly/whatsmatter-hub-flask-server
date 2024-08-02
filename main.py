from flask import Flask
import requests


app = Flask(__name__)

@app.route('/local/api')
def home():
    headers = {"Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJiY2E5MWY1OTJjZDg0ZmU0YTRiMWRjYTJiZWI5ZWQ4MSIsImlhdCI6MTcyMjUwMTI3NSwiZXhwIjoyMDM3ODYxMjc1fQ.TpTXTBFyuOwQY5mOVuLy4MTUGfCkZ3ZVFh7xHnprW5I"}
    response = requests.get("http://192.168.1.195:8123/api/", headers=headers)
    return str(response.json())

@app.route('/local/api/states')
def state():
    headers = {"Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJiY2E5MWY1OTJjZDg0ZmU0YTRiMWRjYTJiZWI5ZWQ4MSIsImlhdCI6MTcyMjUwMTI3NSwiZXhwIjoyMDM3ODYxMjc1fQ.TpTXTBFyuOwQY5mOVuLy4MTUGfCkZ3ZVFh7xHnprW5I"}
    response = requests.get("http://192.168.1.195:8123/api/states", headers=headers)
    return str(response.json())

if __name__ == '__main__':
    app.run(debug=True)