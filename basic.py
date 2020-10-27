from flask import Flask, render_template, request, session, redirect, url_for
from flask_wtf import FlaskForm
from wtforms import SubmitField, SelectField, StringField
import requests
import json
from flask_bootstrap import Bootstrap

app = Flask(__name__)
Bootstrap(app)

app.config['SECRET_KEY'] = 'my_secret_key'

api_header = {
    'api-key': 'b60192d669b35ccaf0693cb1a0775856'
}


# # # # # Functions # # # # #


def book_list(api):
    book_list_payload = {}
    book_array = []
    book_list_url = "https://api.scripture.api.bible/v1/bibles/06125adad2d5898a-01/books?include-chapters=" \
                    "false&include-chapters-and-sections=false"
    book_list_response = requests.request("GET", book_list_url, headers=api, data=book_list_payload)
    book_list_response_json = json.loads(book_list_response.text)

    for item in book_list_response_json["data"]:
        # case = {"id": item["id"], "name": item["name"]}
        book_array.append(item["id"])
        # book_array.append(case)
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
    book_version = session.get('bible_version')
    payload = {}
    url = "https://api.scripture.api.bible/v1/bibles/{}/chapters/{}?content-type=text&include-" \
          "notes=false&include-titles=true&include-chapter-numbers=false&include-verse-numbers=true&include-verse-" \
          "spans=false".format(book_version, b_id)
    response = requests.request("GET", url, headers=api, data=payload)
    response_json = json.loads(response.text)
    response_json1 = response_json["data"]

    return response_json1


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
    array = []

    if not search_string:
        search_string = "love"
    elif search_string == " ":
        search_string = "love"

    url = "https://api.scripture.api.bible/v1/bibles/06125adad2d5898a-01/search?query={}&limit=1000&sort=canonical"\
        .format(search_string.replace(" ", "%20"))
    response = requests.request("GET", url, headers=api, data=payload)
    response_json = json.loads(response.text)
    response_json1 = response_json["data"]

    if len(response_json1) > 1:
        search_text = response_json1["query"]
        result_count = response_json1["total"]
        for item in response_json1["verses"]:
            case = {"search_text": search_text, "result_count": result_count, 'reference': item["reference"],
                    'text': item["text"], "chapterId": item["chapterId"]}
            array.append(case)
    elif len(response_json1) == 1:
        for item in response_json1["passages"]:
            case = {"reference": item["reference"], "text": item["content"], "chapterId": item["chapterIds"]}
            array.append(case)
    return array


# # # # # Classes # # # # #


class InfoForm(FlaskForm):
    version = SelectField(choices=[("06125adad2d5898a-01", "ASV"), ("de4e12af7f28f599-01", "KJV"),
                                   ("592420522e16049f-01", "Spanish - Reina Valera 1909 ")],
                          default="06125adad2d5898a-01")
    book_list_selector = SelectField(choices=book_list(api_header))
    submit = SubmitField('>')


class SearchForm(FlaskForm):
    search_string = StringField('', render_kw={"placeholder": "Search Here"})
    submit_search = SubmitField('Search')


# # # # # Routes # # # # #


@app.route('/', methods=['GET', 'POST'])
def index():

    form = InfoForm()
    session['bible_version'] = form.version.data
    book_data = form.book_list_selector.data

    if form.validate_on_submit():
        return redirect(url_for('book', book_data=book_data))

    form_search = SearchForm()
    search_string = False
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
        submit_book_chapter = SubmitField('>')

    form2 = BookChapter()
    verse_data = form2.book_chapter_selector.data

    if form2.validate_on_submit():
        return redirect(url_for('verse', verse_data=verse_data, book_data=book_id))

    form_search = SearchForm()
    search_string = False
    if form_search.validate_on_submit():
        search_string = form_search.search_string.data
        form_search.search_string.data = ''
        return redirect(url_for('search', search_string=search_string))
    return render_template('book.html', book_id=book_id, data=data, form2=form2, form_search=form_search)


@app.route('/verse', methods=['GET', 'POST'])
def verse():
    verse_id = request.args.get('verse_data', None)
    book_id = request.args.get('book_data', None)
    chapter_text = book_chapter_content(api_header, verse_id)

    form_search = SearchForm()
    search_string = False
    if form_search.validate_on_submit():
        search_string = form_search.search_string.data
        form_search.search_string.data = ''
        return redirect(url_for('search', search_string=search_string))

    return render_template('verses.html', verse_id=verse_id, book_id=book_id, chapter_text=chapter_text, form_search=form_search)


@app.route('/search', methods=['GET', 'POST'])
def search():
    search_string = request.args.get('search_string', None)
    search_string_response = search_bible(api_header, search_string)

    form_search = SearchForm()
    search_string = False
    if form_search.validate_on_submit():
        search_string = form_search.search_string.data
        form_search.search_string.data = ''
        return redirect(url_for('search', search_string=search_string))

    return render_template('search.html', search_string_response=search_string_response, form_search=form_search)


if __name__ == '__main__':
    app.run(debug=True)
