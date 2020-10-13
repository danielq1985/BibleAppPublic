from flask import Flask, render_template, request, session, redirect, url_for
from flask_wtf import FlaskForm
from wtforms import SubmitField, SelectField, StringField
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


def book_chapter_content(api, b_id):
    payload = {}
    url = "https://api.scripture.api.bible/v1/bibles/06125adad2d5898a-01/chapters/{}?content-type=text&include-" \
          "notes=false&include-titles=true&include-chapter-numbers=false&include-verse-numbers=true&include-verse-" \
          "spans=false".format(b_id)
    response = requests.request("GET", url, headers=api, data=payload)
    response_json = json.loads(response.text)
    response_json1 = response_json["data"]
    response_json2 = response_json1["content"]
    return response_json2


def chapter_verses(api, c_id):
    payload = {}
    array = []
    url = "https://api.scripture.api.bible/v1/bibles/06125adad2d5898a-01/chapters/{}/verses".format(c_id)
    response = requests.request("GET", url, headers=api, data=payload)
    response_json = json.loads(response.text)

    for item in response_json["data"]:
        array.append(item["id"])
    return array


def search_bible(api, search_string):
    payload = {}
    url = "https://api.scripture.api.bible/v1/bibles/06125adad2d5898a-01/search?query={}&sort=relevance"\
        .format(search_string.replace(" ", "%20"))
    response = requests.request("GET", url, headers=api, data=payload)
    response_json = json.loads(response.text)
    return response_json

# # # # # Classes # # # # #


class InfoForm(FlaskForm):
    book_list_selector = SelectField(choices=book_list(api_header))
    submit = SubmitField('Search')


class SearchForm(FlaskForm):
    search_string = StringField('Search')
    submit_search = SubmitField('Search')


# # # # # Routes # # # # #


@app.route('/', methods=['GET', 'POST'])
def index():
    form = InfoForm()
    book_data = form.book_list_selector.data

    form_search = SearchForm()
    search_string = False

    if form.validate_on_submit():
        return redirect(url_for('book', book_data=book_data))

    if form_search.validate_on_submit():
        search_string = form_search.search_string.data
        form_search.search_string.data = ''
        return redirect(url_for('search', search_string=search_string))
    return render_template('index.html', form=form, form_search=form_search)


@app.route('/book', methods=['GET', 'POST'])
def book():
    book_id = request.args.get('book_data', None)
    data = book_chapters(api_header, book_id)

    class BookChapter(FlaskForm):
        book_chapter_selector = SelectField(choices=data, default='GEN')
        submit_book_chapter = SubmitField('Search')

    form2 = BookChapter()
    verse_data = form2.book_chapter_selector.data

    if form2.validate_on_submit():
        return redirect(url_for('verse', verse_data=verse_data))
    return render_template('book.html', book_id=book_id, data=data, form2=form2)


@app.route('/verse', methods=['GET', 'POST'])
def verse():
    verse_id = request.args.get('verse_data', None)
    chapter_text = book_chapter_content(api_header, verse_id)

    return render_template('verses.html', verse_id=verse_id, chapter_text=chapter_text)


@app.route('/search', methods=['GET', 'POST'])
def search():
    search_string = request.args.get('search_string', None)
    search_string_response = search_bible(api_header, search_string)

    return render_template('search.html', search_string_response=search_string_response)

if __name__ == '__main__':
    app.run(debug=True)
