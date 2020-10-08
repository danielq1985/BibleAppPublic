from flask import Flask, render_template, request, session
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
    book_list_url = "https://api.scripture.api.bible/v1/bibles/06125adad2d5898a-01/books?include-chapters=false&include-chapters-and-sections=false"
    book_list_response = requests.request("GET", book_list_url, headers=api, data=book_list_payload)
    book_list_response_json = json.loads(book_list_response.text)

    for item in book_list_response_json["data"]:
        book_array.append(item["id"])
    return book_array


def book_chapter(api, book):
    book_chapter_payload = {}
    chapter_array = []
    book_chapter_url = "https://api.scripture.api.bible/v1/bibles/06125adad2d5898a-01/books/{}/chapters".format(book)
    book_chapter_response = requests.request("GET", book_chapter_url, headers=api, data=book_chapter_payload)
    book_chapter_response_json = json.loads(book_chapter_response.text)

    # for item in book_chapter_response_json["data"]:
    #     chapter_array.append(item["id"])
    # return chapter_array
    return book_chapter_response_json


class InfoForm(FlaskForm):
    # This will become more intuitive, but just to test functionality you type JHN.3.16., In the future you could
    # search john 3:16

    search = StringField('Search')

    book_list_selector = SelectField('Book', choices=book_list(api_header))

    submit = SubmitField('Search')


@app.route('/', methods=['GET', 'POST'])
def index():
    search = False  # initially false so that the if statement doesnt execute
    form = InfoForm()
    response_text = ''  # variable initially empty
    book_list_for_html = book_list(api_header)
    t = ''

    if form.validate_on_submit():
        search = form.search.data
        session['book_list_selector'] = form.book_list_selector.data
        form.search.data = ''

        url = "https://api.scripture.api.bible/v1/bibles/06125adad2d5898a-01/verses/{}".format(search)
        # url = "https://api.scripture.api.bible/v1/bibles/06125adad2d5898a-01/verses/{}?content-type=text&include-" \
        #       "notes=false&include-titles=true&include-chapter-numbers=false&include-verse-numbers=true&include-" \
        #       "verse-spans=true&use-org-id=true".format(search)

        payload = {}
        headers = {
            'api-key': 'b60192d669b35ccaf0693cb1a0775856'
        }

        response = requests.request("GET", url, headers=headers, data=payload)
        # response_text1 = json.loads(response.text)
        # response_text = response_text1["data"]

        response_text = response

        t = book_chapter(api_header, session["book_list_selector"])

    return render_template('index.html', form=form, search=search, response_text=response_text,
                           book_list_for_html=book_list_for_html, t=t)


if __name__ == '__main__':
    app.run(debug=True)
