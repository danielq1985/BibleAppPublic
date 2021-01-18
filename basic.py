from flask import Flask, render_template, request, session, redirect, url_for, jsonify
from flask_wtf import FlaskForm
from wtforms import SubmitField, SelectField, StringField
import requests
import json
from flask_bootstrap import Bootstrap
import pandas as pd
import numpy as np

from itertools import chain


app = Flask(__name__)
Bootstrap(app)

app.config['SECRET_KEY'] = 'my_secret_key'

api_header = {
    'api-key': '9aef133b02bc5dea8ab5497ecaa31d18'
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


def book_chapter_content_esv(b_id):
    url = "https://api.esv.org/v3/passage/text/?q={}".format(b_id)

    payload = {}
    headers = {
        'Authorization': 'a05fdda7696b61ae651a321fce2cb2025936c9d4'
    }

    params = {
        'include-headings': False,
        'include-footnotes': False,
        'include-verse-numbers': True,
        'include-short-copyright': False,
        'include-passage-references': False
    }

    response = requests.request("GET", url, headers=headers, data=payload, params=params)
    response_json = json.loads(response.text)

    return response_json


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

    url = "https://api.scripture.api.bible/v1/bibles/de4e12af7f28f599-01/search?query={}&limit=1000&sort=canonical"\
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


def cross(chapter_input):
    df = pd.read_csv("static/cross.csv")
    selected_chapter = df[(df.book_chapter == '{}'.format(chapter_input))][['verse', 'to_verse', 'to_verse_display']]
    arr = selected_chapter.verse.unique()
    master_array = []
    for item in arr:
        a = selected_chapter[(selected_chapter.verse == item)]['to_verse_display']
        a_arr = []
        for item2 in a:
            a_arr.append(item2)

        b = selected_chapter[(selected_chapter.verse == item)]['to_verse']
        b_arr = []
        for item3 in b:
            b_arr.append(item3)

        dictionary = dict(zip(a_arr, b_arr))

        case = {"Verse": item, "Verses": dictionary}
        master_array.append(case)

    if master_array:
        return master_array
    else:
        return ""


def ppt(book_chapter):
    df = pd.read_csv("static/verses.csv")
    df_people = pd.read_csv("static/people.csv")
    df_places = pd.read_csv("static/places.csv")

    main = df[(df.book_chapter == '{}'.format(book_chapter))]
    main = main.fillna('0')

    people_list = []
    for item in main.people:
        p = item.split(",")
        people_list.append(p)

    people_list = list(chain.from_iterable(people_list))
    people_list = set(people_list)

    people_list_v = []
    for item in people_list:
        if item != '0':
            people_list_v.append(item)

    people_list_k = []
    for item in people_list_v:
        name_display = df_people[(df_people.personLookup == "{}".format(item))]["displayTitle"].iat[0]
        people_list_k.append(name_display)

    dictionary_people = dict(zip(people_list_v, people_list_k))

    #####################################################################

    places_list = []
    for item in main.places:
        pl = item.split(",")
        places_list.append(pl)

    places_list = list(chain.from_iterable(places_list))
    places_list = set(places_list)

    places_list_v = []
    for item in places_list:
        if item != '0':
            places_list_v.append(item)

    places_list_k = []
    for item in places_list_v:
        name_display = df_places[(df_places.placeLookup == "{}".format(item))]["displayTitle"].iat[0]
        places_list_k.append(name_display)

    dictionary_places = dict(zip(places_list_v, places_list_k))

    case = {"people": dictionary_people, "places": dictionary_places}

    return case


    # df_chapter = df[(df.book_chapter == "{}".format(book_chapter))][
    #     ["verseNum", "people", "places", "yearNum", "eventsDescribed", "timeline"]]
    # df_chapter = df_chapter.fillna('0')
    #
    # arr = df_chapter[(df_chapter.people != '0') | (df_chapter.places != '0')]
    # arr_l = arr['verseNum']
    #
    # array = []
    #
    # for item in arr_l:
    #     people_data = arr[(arr.verseNum == item)]['people']
    #     places_data = arr[(arr.verseNum == item)]['places']
    #
    #     ## people ##
    #     for item2 in people_data:
    #         people = item2.split(",")
    #
    #     array_name_disp = []
    #     array_name = []
    #     if '0' not in people:
    #         for item2a in people:
    #             name_display = df_people[(df_people.personLookup == "{}".format(item2a))]["displayTitle"].iat[0]
    #             array_name_disp.append(name_display)
    #
    #         for item2a in people:
    #             name = item2a
    #             array_name.append(name)
    #
    #     else:
    #         people = '0'
    #         array_name_disp.append(people)
    #         array_name.append(people)
    #     dictionary_people = dict(zip(array_name_disp, array_name))
    #
    #     ## places ##
    #     for item3 in places_data:
    #         places = item3.split(",")
    #
    #     array_places_disp = []
    #     array_places = []
    #     if '0' not in places:
    #         for item3a in places:
    #             places_display = df_places[(df_places.placeLookup == "{}".format(item3a))]["displayTitle"].iat[0]
    #             array_places_disp.append(places_display)
    #
    #         for item3a in places:
    #             place = item3a
    #             array_places.append(place)
    #
    #     else:
    #         places = '0'
    #         array_places_disp.append(places)
    #         array_places.append(places)
    #
    #     dictionary_places = dict(zip(array_places_disp, array_places))
    #
    #     case = {"verse": item, "people": dictionary_people, "places": dictionary_places}
    #     array.append(case)
    # return array


# # # # # Classes # # # # #

class InfoForm(FlaskForm):
    version = SelectField(choices=[("06125adad2d5898a-01", "ASV"), ("de4e12af7f28f599-01", "KJV"),
                                   ("592420522e16049f-01", "Spanish - Reina Valera 1909 "),
                                   ("705aad6832c6e4d2-02", "Hindi - The Holy Bible in Hindi")],
                          default="06125adad2d5898a-01")
    # book_list_selector = SelectField(choices=book_list(api_header))
    book_list_selector = SelectField(choices=[("GEN", "Genesis"), ("EXO", "Exodus"),
                                              ("LEV", "Leviticus"), ("NUM", "Numbers"), ("DEU", "Deuteronomy"),
                                              ("JOS", "Joshua"), ("JDG", "Judges"), ("RUT", "Ruth"),
                                              ("1SA", "1 Samuel"), ("2SA", "2 Samuel"), ("1KI", "1 Kings"),
                                              ("2KI", "2 Kings"), ("1CH", "1 Chronicles"), ("2CH", "2 Chronicles"),
                                              ("EZR", "Ezra"), ("NEH", "Nehemiah"), ("EST", "Esther"), ("JOB", "Job"),
                                              ("PSA", "Psalms"), ("PRO", "Proverbs"), ("ECC", "Ecclesiastes"),
                                              ("SNG", "Song of Solomon"), ("ISA", "Isaiah"), ("JER", "Jeremiah"),
                                              ("LAM", "Lamentations"), ("EZK", "Ezekiel"),
                                              ("DAN", "Daniel"), ("HOS", "Hosea"), ("JOL", "Joel"), ("AMO", "Amos"),
                                              ("OBA", "Obadiah"), ("JON", "Jonah"), ("MIC", "Micah"), ("NAM", "Nahum"),
                                              ("HAB", "Habakkuk"), ("ZEP", "Zephaniah"), ("HAG", "Haggai"),
                                              ("ZEC", "Zechariah"), ("MAL", "Malachi"), ("MAT", "Matthew"),
                                              ("MRK", "Mark"), ("LUK", "Luke"), ("JHN", "John"), ("ACT", "Acts"),
                                              ("ROM", "Romans"), ("1CO", "1 Corinthians"), ("2CO", "2 Corinthians"),
                                              ("GAL", "Galatians"), ("EPH", "Ephesians"), ("PHP", "Philippians"),
                                              ("COL", "Colossians"), ("1TH", "1 Thessalonians"),
                                              ("2TH", "2 Thessalonians"), ("1TI", "1 Timothy"), ("2TI", "2 Timothy"),
                                              ("TIT", "Titus"),
                                              ("PHM", "Philemon"), ("HEB", "Hebrews"), ("JAS", "James"),
                                              ("1PE", "1 Peter"), ("2PE", "2 Peter"),
                                              ("1JN", "1 John"), ("2JN", "2 John"), ("3JN", "3 John"), ("JUD", "Jude"),
                                              ("REV", "Revelation")
                                              ])
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
    chapter_text_esv = book_chapter_content_esv(verse_id)
    cross_ref = cross(verse_id)
    b_chapters = verse_id[:3]
    chapter_count = book_chapters(api_header, b_chapters)
    content = ""
    switch = 0
    peopleplacetime = ppt(verse_id)

    if len(chapter_count) <= 2 and 'intro' not in chapter_text["id"]:
        a = verse_id[:3]
        b = book_chapter_content_esv(a)
        c = b['passages']
        for item in c:
            content = item
        switch = 1
    elif 'intro' in chapter_text['id']:
        content = chapter_text['content']
        switch = 0
    else:
        for item in chapter_text_esv['passages']:
            content = item
        switch = 1

    form_search = SearchForm()
    search_string = False
    if form_search.validate_on_submit():
        search_string = form_search.search_string.data
        form_search.search_string.data = ''
        return redirect(url_for('search', search_string=search_string))

    return render_template('verses.html', verse_id=verse_id, book_id=book_id, chapter_text_esv=chapter_text_esv,
                           chapter_text=chapter_text, form_search=form_search, cross_ref=cross_ref,
                           content=content, switch=switch, peopleplacetime=peopleplacetime)


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


@app.route('/ref/<ref_input>')
def ref(ref_input):

    a = book_chapter_content_esv(ref_input)
    b = a['query']
    for item in a['passages']:
        c = item

    return jsonify(ref=b, text=c)


@app.route('/person/<person>')
def person(person):
    df_people = pd.read_csv("static/people.csv")
    df = df_people[(df_people.personLookup == '{}'.format(person))]
    # df = df.fillna('0')

    display = df['displayTitle'].iat[0]

    aka = df['alsoCalled'].iat[0]
    akaDis = ''
    if aka is not np.nan:
        akaDis = '<br> Also known as: {} <br>'.format(aka)

    dictText1 = df['dictText'].iat[0]
    if dictText1 is not np.nan:
        dictText = dictText1
    else:
        dictText = ""

    verses1 = df['verses']
    if verses1 is not np.nan:
        for item in verses1:
            verses = item.split(",")
    else:
        verses = ""

    button = []
    for item in verses:
        html = """
            <a class="process_input" href="/ref/{}" role="button">{}</a>
            """.format(item, item)
        button.append(html)

    return jsonify(display=display, dictText=dictText, verses=verses, button=button, akaDis=akaDis)


@app.route('/place/<place>')
def places(place):
    df_places = pd.read_csv("static/places.csv")
    df = df_places[(df_places.placeLookup == '{}'.format(place))]
    df = df.fillna('0')

    display = df['displayTitle'].iat[0]

    dictText1 = df['dictText'].iat[0]
    if dictText1 is not np.nan:
        dictText = dictText1
    else:
        dictText = ""

    verses1 = df['verses']
    if verses1 is not np.nan:
        for item in verses1:
            verses = item.split(",")
    else:
        verses = ""

    return jsonify(display=display, dictText=dictText, verses=verses)



if __name__ == '__main__':
    app.run(debug=True)
