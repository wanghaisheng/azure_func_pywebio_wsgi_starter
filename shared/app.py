from flask import Flask
from pywebio.output import *
from pywebio.input import *

def take_gift(lang):
    lang = lang or 'en'
    gift = select('Which gift you want?', ['keyboard', 'ipad'])
    put_text("HHHHHHHHHHHH")

