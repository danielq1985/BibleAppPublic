from flask import Flask, render_template, request, session, redirect, url_for, jsonify
from flask_wtf import FlaskForm
from wtforms import SubmitField, SelectField, StringField
import requests
import json
from flask_bootstrap import Bootstrap
import pandas as pd
import numpy as np

from itertools import chain
import folium


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
    # Ruth and Joel are the only two books that the api book id doesnt match the ESV api format. Instead of
    # changing EVERYTHING this is a bandaid
    if 'RUT' in b_id:
        b_id = b_id.replace("RUT", "RUTH")
    elif 'JOL' in b_id:
        b_id = b_id.replace("JOL", "JOEL")

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
    selected_chapter = df[(df.book_chapter == '{}'.format(chapter_input))][['verse', 'to_verse', 'to_verse_display', 'book_chapter']]
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

        c = selected_chapter[(selected_chapter.verse == item)]['book_chapter']
        c_arr = []
        for item4 in c:
            c_arr.append(item4)

        dictionary = dict(zip(a_arr, b_arr))

        case = {"Verse": item, "Verses": dictionary, "book_chapter": c_arr}
        # print(case)
        master_array.append(case)

    if master_array:
        return master_array
    else:
        return ""


def ppt(book_chapter):
    df = pd.read_csv("static/verses.csv")
    df_people = pd.read_csv("static/people.csv")
    df_places = pd.read_csv("static/places.csv")
    df_books = pd.read_csv("static/books.csv")
    df_chapters = pd.read_csv("static/chapters.csv")

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

###########################################################

    book_key = book_chapter.split('.')
    book_key = book_key[0]

    book_author = df_books[(df_books.osisName==book_key)].writers
    for item in book_author:
        book_author_arr = item.split(", ")

    author_list_k = []
    for item in book_author_arr:
        name_display = df_people[(df_people.personLookup == "{}".format(item))]["displayTitle"].iat[0]
        author_list_k.append(name_display)

    book_authors_dict = dict(zip(book_author_arr, author_list_k))

############################################################

    if 'intro' in book_chapter:
        book_chapter1 = book_key + '.' + '1'
    else:
        book_chapter1 = book_chapter

    book_chapter_author = df_chapters[(df_chapters.book_chapter==book_chapter1)].writer.iat[0]

    chapter_author_arr = []
    chapter_author_list_k = []
    if type(book_chapter_author) == float:
        pass
    else:
        book_chapter_author = df_chapters[(df_chapters.book_chapter == book_chapter1)].writer
        for item in book_chapter_author:
            chapter_author_arr = item.split(", ")

        chapter_author_list_k = []
        for item in chapter_author_arr:
            name_display = df_people[(df_people.personLookup == "{}".format(item))]["displayTitle"].iat[0]
            chapter_author_list_k.append(name_display)

    chapter_authors_dict = dict(zip(chapter_author_arr, chapter_author_list_k))
    # print(chapter_authors_dict)

##############################################################################

    book_name = df_books[(df_books.osisName == book_key)].bookName.iat[0]
    book_div = df_books[(df_books.osisName == book_key)].bookDiv.iat[0]
    book_testament = df_books[(df_books.osisName == book_key)].testament.iat[0]

    book_info = "<b>Book:</b> {} <br><br> <b>BookDiv:</b> {} <br><br> <b>Testament:</b> {} <br><br>".format(book_name, book_div, book_testament)

    events_timeline = df[(df.book_chapter == '{}'.format(book_chapter))].eventsDescribed.iat[0]

    print(book_name, book_div, book_testament)

    case = {"people": dictionary_people, "places": dictionary_places, "book_authors": book_authors_dict,
            "chapter_authors": chapter_authors_dict, "book_info": book_info}

    return case


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

    split2 = ref_input.split('.', -1)
    chapter = "{}.{}".format(split2[0], split2[1])
    goto_chapter = """
    <a class="btn btn-outline-secondary btn-sm" id=loadingMain href="/verse?verse_data={}">Chapter →</a>
    """.format(chapter)

    a = book_chapter_content_esv(ref_input)

    b = a['query']
    for item in a['passages']:
        c = item

    return jsonify(ref=b, text=c, goto_chapter=goto_chapter)


@app.route('/ref_modal/<ref_input>')
def ref_modal(ref_input):

    book_list1 = ['Gen', 'Exod', 'Lev', 'Num', 'Deut', 'Josh', 'Judg', 'Ruth',
       '1Sam', '2Sam', '1Kgs', '2Kgs', '1Chr', '2Chr', 'Ezra', 'Neh',
       'Esth', 'Job', 'Ps', 'Prov', 'Eccl', 'Song', 'Isa', 'Jer', 'Lam',
       'Ezek', 'Dan', 'Hos', 'Joel', 'Amos', 'Obad', 'Jonah', 'Mic',
       'Nah', 'Hab', 'Zeph', 'Hag', 'Zech', 'Mal', 'Matt', 'Mark', 'Luke',
       'John', 'Acts', 'Rom', '1Cor', '2Cor', 'Gal', 'Eph', 'Phil', 'Col',
       '1Thess', '2Thess', '1Tim', '2Tim', 'Titus', 'Phlm', 'Heb', 'Jas',
       '1Pet', '2Pet', '1John', '2John', '3John', 'Jude', 'Rev']

    book_list = ['GEN', 'EXO', 'LEV', 'NUM', 'DEU', 'JOS', 'JDG', 'RUT', '1SA',
                 '2SA', '1KI', '2KI', '1CH', '2CH', 'EZR', 'NEH', 'EST', 'JOB',
                 'PSA', 'PRO', 'ECC', 'SNG', 'ISA', 'JER', 'LAM', 'EZK', 'DAN',
                 'HOS', 'JOL', 'AMO', 'OBA', 'JON', 'MIC', 'NAM', 'HAB', 'ZEP',
                 'HAG', 'ZEC', 'MAL', 'MAT', 'MRK', 'LUK', 'JHN', 'ACT', 'ROM',
                 '1CO', '2CO', 'GAL', 'EPH', 'PHP', 'COL', '1TH', '2TH', '1TI',
                 '2TI', 'TIT', 'PHM', 'HEB', 'JAS', '1PE', '2PE', '1JN', '2JN',
                 '3JN', 'JUD', 'REV']
    goto_chapter = ''
    count = -1
    for item in range(66):
        count += 1

        if book_list1[count] in ref_input:
            split = ref_input.split('.', -1)
            chapter = "{}.{}".format(book_list[count], split[1])

            goto_chapter = """
            <a class="btn btn-outline-secondary btn-sm" id=loadingMainModal href="/verse?verse_data={}">Chapter →</a>
            """.format(chapter)

    a = book_chapter_content_esv(ref_input)

    b = a['query']
    for item in a['passages']:
        c = item

    return jsonify(ref=b, text=c, goto_chapter=goto_chapter)


@app.route('/person/<person>')
def person(person):
    df_people = pd.read_csv("static/people.csv")
    df_people = df_people.applymap(str)

    df_places = pd.read_csv("static/places.csv")
    df_places = df_places.applymap(str)

    df = df_people[(df_people.personLookup == '{}'.format(person))]

    display = df['displayTitle'].iat[0]

    dictText = df['dictText'].iat[0]
    if dictText is np.nan:
        dictText = ""

    aka = df['alsoCalled'].iat[0]
    akaDis = ''
    if aka != 'nan':
        aka_1 = aka.replace(',', ', ')
        akaDis = '<br><b> Also known as:</b> {} <br>'.format(aka_1)
    else:
        akaDis = ''

    verses1 = df['verses']
    verses_arr = []
    if verses1 is not np.nan:
        for item in verses1:
            verses = item.split(",")
            # for item2 in verses:
            #     verses2 = item2.split('.', -1)
            #     verses3 = verses2[0] + '.' + verses2[1]
            #     verses_arr.append(verses3)

    else:
        verses = ""

    # print(verses_arr)

    birth_year = df['birthYear'].iat[0]
    birth_year_display = ''
    birth_year_display1 = str(birth_year)
    if birth_year_display1 != 'nan':
        if '-' in birth_year_display1:
            birth_year_display2 = birth_year_display1[1:]
            birth_year_display = '<br><b> Birth year:</b> {} BC <br>'.format(birth_year_display2[:-2])
        else:
            birth_year_display1 = str(birth_year)
            birth_year_display2 = birth_year_display1
            birth_year_display = '<br><b> Birth year:</b> {} AD <br>'.format(birth_year_display2[:-2])

    death_year = df['deathYear'].iat[0]
    death_year_display = ''
    death_year_display1 = str(death_year)
    if death_year_display1 != 'nan':
        if '-' in death_year_display1:
            death_year_display2 = death_year_display1[1:]
            death_year_display = '<br><b> Death year:</b> {} BC <br>'.format(death_year_display2[:-2])
        else:
            death_year_display1 = str(death_year)
            death_year_display2 = death_year_display1
            death_year_display = '<br><b> Death year:</b> {} AD <br>'.format(death_year_display2[:-2])

    birth_place = df['birthPlace'].iat[0]
    birth_place_display = ''
    if birth_place != 'nan':
        birth_place_display1 = df_places[(df_places.placeLookup == "{}".format(birth_place))]["displayTitle"].iat[0]
        birth_place_display = "<br><b> Birth Place:</b> {} <br>".format(birth_place_display1)

    death_place = df['deathPlace'].iat[0]
    death_place_display = ''
    if death_place != 'nan':
        death_place_display1 = df_places[(df_places.placeLookup == "{}".format(death_place))]["displayTitle"]
        death_place_display = "<br><b> Death Place:</b> {} <br>".format(death_place_display1)

    modal_arr = []

    for item in verses:

        modal = """
        
    
              <!-- Trigger the modal with a button -->
              <a type="button" class="process_input_verse_modal" id={} data-toggle="modal" data-target="#myModal">{}</a>
            
              <!-- Modal -->
              <div class="modal fade" id="myModal" role="dialog">
                <div class="modal-dialog">
                
                  <!-- Modal content-->
                  <div class="modal-content">
                    <div class="modal-header" >
                      <button type="button" class="close" data-dismiss="modal">&times;</button>
                    </div>
                    <div id="modal-body" style="margin:40px">
                        <div id='loadingmessageModal' style='display:none'>
                        <div class="spinner-border text-primary" role="status">
                            <span class="visually-hidden"></span>
                        </div>
                        
        </div>
                    </div>
                    <div class="modal-footer">
                      <button type="button" class="btn btn-default" data-dismiss="modal">Close</button>
                    </div>
                  </div>
                  
                </div>
              </div>
              
          
              
            """.format(item, item)
        # <a class="process_input" id="{}" back_key="{}" data-toggle="collapse" href="#" role="button">{}</a>

        modal_arr.append(modal)

    test = df.father.iat[0]
    print(test)

    return jsonify(display=display, dictText=dictText, verses=verses, akaDis=akaDis,
                   birth_year_display=birth_year_display, death_year_display=death_year_display, birth_place_display=birth_place_display,
                   death_place_display=death_place_display, modal=modal_arr)


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

    modal_arr = []
    for item in verses:
        modal = """


                  <!-- Trigger the modal with a button -->
                  <a type="button" class="process_input_verse_modal" id={} data-toggle="modal" data-target="#myModal">{}</a>

                  <!-- Modal -->
                  <div class="modal fade" id="myModal" role="dialog">
                    <div class="modal-dialog">

                      <!-- Modal content-->
                      <div class="modal-content">
                        <div class="modal-header" >
                          <button type="button" class="close" data-dismiss="modal">&times;</button>
                        </div>
                        <div id="modal-body" style="margin:40px">
                        <div id='loadingmessageModal' style='display:none'>
    <div class="spinner-border text-primary" role="status">
        <span class="visually-hidden"></span>
    </div>
</div>
                        </div>
                        <div class="modal-footer">
                          <button type="button" class="btn btn-default" data-dismiss="modal">Close</button>
                        </div>
                      </div>

                    </div>
                  </div>



                """.format(item, item)
        # <a class="process_input" id="{}" back_key="{}" data-toggle="collapse" href="#" role="button">{}</a>

        modal_arr.append(modal)

    lat = df['openBibleLat'].iat[0]
    long = df['openBibleLong'].iat[0]

    # print(lat, long)
    # print(type(lat), type(long))

    if lat == '0':
        map = ""
    else:
        map = """
        
                  <!-- Trigger the modal with a button -->
                  <a class="btn btn-outline-secondary btn-sm" type="button" data-toggle="modal" data-target="#myModalmap">map →</a>

                  <!-- Modal -->
                  <div class="modal fade" id="myModalmap" role="dialog">
                    <div class="modal-dialog modal-lg">

                      <!-- Modal content-->
                      <div class="modal-content">
                        <div class="modal-header" >
                          <button type="button" class="close" data-dismiss="modal">&times;</button>
                        </div>
                        <div id="modal-body-map" class="container">
                                <center>
                                <h4 class="modal-title"> {} </h4>
                                <iframe 
                                src="/map/{}/{}/{}" frameborder="0" src="" style="position: relative; height: 450px; width: 100%;">
                                </iframe>
                                </center>
                        </div>
                        <div class="modal-footer">
                          <button type="button" class="btn btn-default" data-dismiss="modal">Close</button>
                        </div>
                      </div>

                    </div>
                  </div>
        
        """.format(display, lat, long, display)

    # print(lat, long)

    return jsonify(display=display, dictText=dictText, modal=modal_arr, map=map)


@app.route('/map/<lat>/<long>/<name>/')
def map(lat, long, name):
    cords = (lat, long)
    folium_map = folium.Map(location=cords, tiles='Stamen Terrain')
    folium.Marker(
        [lat, long], popup="<i>{}</i>".format(name),
    ).add_to(folium_map)
    return folium_map._repr_html_()


if __name__ == '__main__':
    app.run(debug=True)
