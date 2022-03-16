from flask import Flask
from pywebio.output import *
from pywebio.input import *
from pywebio.platform.flask import webio_view
import os
from functools import partial
from shared.app import  take_gift

app = Flask(__name__)

# if __name__ == "__main__":

app.add_url_rule('/', 'webio_view', webio_view(partial(take_gift, lang='')),
                    methods=['GET', 'POST', 'OPTIONS'])
app.add_url_rule('/en', 'webio_view_en', webio_view(partial(take_gift, lang='en')),
                    methods=['GET', 'POST', 'OPTIONS'])


# if (os.environ.get('PORT')):
#     port = int(os.environ.get('PORT'))
# else:
#     port = 5000

    
# app.run(host='0.0.0.0', port=port)
