from flask import Flask, render_template, request
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
import requests
import json


app = Flask(__name__)

app.config['SECRET_KEY'] = 'my_secret_key'


class InfoForm(FlaskForm):
    search = StringField('What verse are you looking for?')
    submit = SubmitField('Search')


def book_list():
    api_header = {
        'api-key': 'b60192d669b35ccaf0693cb1a0775856'
    }
    book_list_payload = {}
    book_list_url = "https://api.scripture.api.bible/v1/bibles/06125adad2d5898a-01/books?include-chapters=false&include-chapters-and-sections=false"
    book_list_response = requests.request("GET", book_list_url, headers=api_header, data=book_list_payload)
    book_list_response_text = json.loads(book_list_response.text)
    return book_list_response_text



@app.route('/', methods=['GET', 'POST'])
def index():

    search = False          # initially false so that the if statement doesnt execute
    form = InfoForm()
    response_text = ''      # variable initially empty
    book_list_for_html = book_list()

    if form.validate_on_submit():

        search = form.search.data
        form.search.data = ''


        # url = "https://api.scripture.api.bible/v1/bibles/06125adad2d5898a-01/verses/{}".format(search)
        url = "https://api.scripture.api.bible/v1/bibles/06125adad2d5898a-01/books?include-chapters=false&include-chapters-and-sections=false"

        payload = {}
        headers = {
            'api-key': 'b60192d669b35ccaf0693cb1a0775856'
        }

        response = requests.request("GET", url, headers=headers, data=payload)
        response_text = json.loads(response.text)



    return render_template('index.html', form=form, search=search, response_text=response_text, book_list_for_html=book_list_for_html)


if __name__ == '__main__':
    app.run(debug=True)