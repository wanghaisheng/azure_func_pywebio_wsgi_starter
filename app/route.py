from flask import Flask
from pywebio.output import *
from pywebio.input import *
from pywebio.platform.flask import webio_view
# import translators as ts

# Always use relative import for custom module
from functools import partial

app = Flask(__name__)



def take_gift(lang):
    lang = lang or 'en'
    gift = select('Which gift you want?', ['keyboard', 'ipad'])
    put_text("HHHHHHHHHHHH")


@app.route("/",methods=['GET', 'POST', 'OPTIONS'])
def index():
    return webio_view(partial(take_gift, lang=''))()


@app.route("/en",methods=['GET', 'POST', 'OPTIONS'])
def index_en():
    return webio_view(partial(take_gift, lang='en'))()