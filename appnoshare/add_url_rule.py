from flask import Flask
from pywebio.output import *
from pywebio.input import *
from pywebio.platform.flask import webio_view
import os
from functools import partial

app = Flask(__name__)
def take_gift(lang):
    lang = lang or 'en'
    gift = select('Which gift you want?', ['keyboard', 'ipad'])
    put_text("HHHHHHHHHHHH")


# if __name__ == "__main__":

app.add_url_rule('/noshare', 'webio_view', webio_view(partial(take_gift, lang='')),
                    methods=['GET', 'POST', 'OPTIONS'])
app.add_url_rule('/noshare/en', 'webio_view_en', webio_view(partial(take_gift, lang='en')),
                    methods=['GET', 'POST', 'OPTIONS'])


# if (os.environ.get('PORT')):
#     port = int(os.environ.get('PORT'))
# else:
#     port = 5000

    
# app.run(host='0.0.0.0', port=port)
