from flask import Flask

app = Flask("msbdemo")

@app.route("/")
def hello():
    return "If you are seeing this, the multi-stage build succeeded"
