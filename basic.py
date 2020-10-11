from flask import Flask, render_template, request, session, redirect, url_for
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, SelectField
import requests
import json

app = Flask(__name__)

app.config['SECRET_KEY'] = 'my_secret_key'

api_header = {
    'api-key': 'b60192d669b35ccaf0693cb1a0775856'
}


def book_list(api):
    book_list_payload = {}
    book_array = []
    book_list_url = "https://api.scripture.api.bible/v1/bibles/06125adad2d5898a-01/books?include-chapters=" \
                    "false&include-chapters-and-sections=false"
    book_list_response = requests.request("GET", book_list_url, headers=api, data=book_list_payload)
    book_list_response_json = json.loads(book_list_response.text)

    for item in book_list_response_json["data"]:
        book_array.append(item["id"])
    return book_array


def book_chapters(api, b_id):
    payload = {}
    array = []
    url = "https://api.scripture.api.bible/v1/bibles/06125adad2d5898a-01/books/{}/chapters".format(b_id)
    response = requests.request("GET", url, headers=api, data=payload)
    response_json = json.loads(response.text)

    for item in response_json["data"]:
        array.append(item["id"])
    return array


class InfoForm(FlaskForm):

    book_list_selector = SelectField(choices=book_list(api_header))
    submit = SubmitField('Search')


@app.route('/', methods=['GET', 'POST'])
def index():
    form = InfoForm()
    book_data = form.book_list_selector.data

    if form.validate_on_submit():
        return redirect(url_for('book', book_data=book_data))
    return render_template('index.html', form=form)


@app.route('/book')
def book():

    book_id = request.args.get('book_data', None)
    data = book_chapters(api_header,book_id)

    class BookChapter(FlaskForm):

        book_chapter_selector = SelectField(choices=data)
        submit_book_chapter = SubmitField('Search')

    form2 = BookChapter()

    return render_template('book.html', book_id=book_id, data=data, form2=form2)


if __name__ == '__main__':
    app.run(debug=True)
