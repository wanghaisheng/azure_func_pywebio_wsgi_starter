from flask import Flask
from pywebio.output import *
from pywebio.input import *
from pywebio.platform.flask import webio_view
from functools import partial
from shared.app import  take_gift

app = Flask(__name__)

@app.route("/route",methods=['GET', 'POST', 'OPTIONS'])
def index():
    return webio_view(partial(take_gift, lang=''))()


@app.route("/route/en",methods=['GET', 'POST', 'OPTIONS'])
def index_en():
    return webio_view(partial(take_gift, lang='en'))()