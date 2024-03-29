from flask import Flask, render_template, url_for, redirect, request, send_from_directory, session
import json
import os
import hashlib
from passManager import makePass
import datetime
##################################################################

app = Flask(__name__)
app.config.update(SECRET_KEY=os.urandom(24))

###################################################################

ROOT = "/home/seneshtimes/seneshtimes/mysite"
ARTICLEPATH = f"{ROOT}/articles"
PATH = "/home/seneshtimes/seneshtimes/mysite"

SECTIONS = ['sports','worldevents','schoolevents','artsandentertainment']

def loggedIn(session):
    if "username" in session:
        return session["logged_in"]
    return False

def dev(session):
    return loggedIn(session) and session["username"]=='dev'

def logout(session):
    session.pop('username',None)
    session.pop('logged_in',None)
def getAuth():
    with open(f'{ROOT}/static/auth.json', 'r') as f:
        auth = json.loads(f.read())
    return auth
def login(username,password):
    auth = getAuth()
    if username in auth.keys():
        # Initializing the sha256() method
        sha256 = hashlib.sha256()
        sha256.update(password.encode(encoding="UTF-8"))
        passw = sha256.hexdigest()

        return passw == auth[username]
    return False

def switch_dir_to_section_header(dir):
    if dir == 'schoolevents':
        return 'News'
    if dir == 'sports':
        return 'Sports'
    if dir == 'home':
        return 'The Senesh Times'
    if dir == 'artsandentertainment':
        return 'Arts and Entertainment'
    if dir == 'aboutus':
        return 'About Us'
    if dir == 'worldevents':
        return 'World Events'
    return dir

def getExtension(filename):
  return filename.rsplit('.', 1)[1].lower()

def makeArticle(request):
    try:
        result = request.form
        img = request.files['img']
        extension = getExtension(img.filename)
        filename = f"{result['title']}.{extension}"
        imgPath = f"{result['section']}/imgs/{filename}"
        img.save(f"{ARTICLEPATH}/{imgPath}")

        file = {}
        file["title"] = result["title"]#fix
        file["article"] = result["content"].replace('\n','<br><br>')
        file["author"] = result["author"]
        file["src"] = imgPath
        file["date"] = getDate()

        file = json.dumps(file)

        with open(f"{ARTICLEPATH}/{result['section']}/{result['title']}.json","w")as f:
            f.write(file)

        return True
    except:
        return False

def getArticles(section):
    articles = os.listdir(f"{ARTICLEPATH}/{section}")
    articles = [f.split(".json")[0] for f in articles if ".json" in f]
    return articles

def processDate(dateIn):
    dateIn = dateIn.split(" ")[0]
    dateIn = dateIn.split("-")
    dateIn = [int(x) for x in dateIn]
    date = datetime.datetime(dateIn[0], dateIn[1], dateIn[2])
    return date

def getDate():
    return str(datetime.datetime.now())

@app.route('/')
def hello_world():
    return redirect(url_for('section_page',section='home'))


def loadAllArticles():
    articleBodys = []
    for section in SECTIONS:
        [articleBodys.append(x) for x in loadArticlesFromRaw(section)]
    def keyFxn(e):
        return processDate(e["date"])
    articleBodys.sort(reverse=True,key=keyFxn)
    return articleBodys

def loadAllArticlesCondensed():
    articleBodys = loadAllArticles()
    condense(articleBodys)
    return articleBodys

@app.route("/home")
def home():

    articleBodys = []
    section_name = switch_dir_to_section_header('home')
    articleBodys = loadAllArticlesCondensed()
    html = render_template('home_page_block.html', articles=articleBodys)
    return render_template('base.html',header=section_name,content=html)

@app.route('/<section>')
def section_page(section):
    section_name = switch_dir_to_section_header(section)
    try:
        articleBodys = loadArticlesFromRaw(section)
        condense(articleBodys)

        html = render_template('home_page_block.html', articles=articleBodys)
        return render_template('base.html',header=section_name,content=html)
    except Exception as e:
        return f"ERROR: {e}"

def loadArticlesFromRaw(section):
    articles = getArticles(section);
    articleBodys = []
    for article in articles:
        if(section != 'drafts'):
            if article != "":
                try:
                    with open(f"{ARTICLEPATH}/{section}/{article}.json")as f:
                        articleContent = f.read()
                    articleContent = json.loads(articleContent) #get dictionary from json file
                    articleContent['article_link'] = f"/{section}/{article}" #add article link
                    articleContent['article'] = articleContent['article']
                    articleBodys.append(articleContent)
                except:pass
        else:
            if article != "":
                try:
                    with open(f"{ARTICLEPATH}/{section}/{article}.json")as f:
                        articleContent = f.read()
                    articleContent = json.loads(articleContent) #get dictionary from json file
                    articleContent = articleContent['article']
                    articleContent['article_link'] = f"/{section}/{article}" #add article link
                    articleContent['article'] = articleContent['article']
                    articleBodys.append(articleContent)
                except:pass

    def keyFxn(e):
            return processDate(e["date"])
    articleBodys.sort(reverse=True,key=keyFxn)
    return articleBodys
def condense(articles):
    for a in articles:
        a['article'] = a['article'][:200]+"..." #make summary here
    return articles

@app.route('/<section>/<article>')
def article(section,article):
    try:
        with open(f"{ARTICLEPATH}/{section}/{article}.json") as f:
            articleContent = f.read()

        articleContent = json.loads(articleContent)
        articleContent['article'] += "<br><br><br>"
        article_html = render_template('article.html',\
                                        title=articleContent["title"],\
                                        article=articleContent["article"],\
                                        author=articleContent["author"],\
                                        date=processDate(articleContent["date"]).strftime("%m-%d-%Y")
                                        )

        return render_template('base.html',content=article_html)

    except Exception as e:
        return f"ERROR: {e}"

@app.route("/admin", methods=['GET','POST'])
def admin():
    message = ""
    if request.method=="POST":
        if "login" in request.form: ##login
            if login(request.form["username"],request.form["password"]):
                session["username"]=request.form["username"]
                session["logged_in"]=True
                session.permanent = True

                if dev(session):
                    return redirect("/dev")

        if "logout" in request.form: ##Logout
            session.pop('username',None)
            session.pop('logged_in',None)

        if loggedIn(session) and "makeArticle" in request.form:
            if makeArticle(request):
                message = "<br>Success, Article Made"
            else:
                message = "<br>Failed to Make Article :("



    if loggedIn(session):
        return render_template("admin_with_login.html",\
                                logged_in=True,\
                                message=f'{session["username"]} is logged in' + message
                                )

    return render_template("admin_with_login.html",\
                            logged_in=False,\
                            message="Log In"
                            )



def getTree():
    tree = {}
    for section in SECTIONS:
        tree[section] = getArticles(section)
    return tree

@app.route('/dev', methods=['GET','POST'])
def development():
    if not dev(session):
        return redirect("/home")
    else:
        if request.method == "POST":
            if "logout" in request.form:
                session.pop('username',None)
                session.pop('logged_in',None)
                return redirect("/home")

            if "tree" in request.form:
                # return f"{getTree()}"
                return render_template('dev.html', tree=getTree())

            if "delete" in request.form:
                return render_template('dev.html',delete_tree=getTree())

            if "what_to_delete" in request.form:
                toDelete = []
                for key in request.form.keys():
                    if "/" in key:
                        toDelete.append(request.form[key])
                for file in toDelete:
                    section = file.split("/")[0]
                    fileName = file.split("/")[1]

                    with open(f"{ARTICLEPATH}/{file}.json")as f:
                        articleContent = f.read()
                        # return articleContent
                        articleContent = json.loads(articleContent)

                    imgPath = f"{ARTICLEPATH}/{articleContent['src']}"



                    os.remove(f"{ARTICLEPATH}/{file}.json")
                    os.remove(imgPath)

            if "addUser" in request.form:
                return render_template('dev.html',add_user=True)

            if "addingUser" in request.form:
                username = request.form["username"]
                password = makePass(request.form["password"])

                auth=getAuth()

                auth[username] = password

                with open(f'{ROOT}/static/auth.json', 'w') as f:
                    f.write(json.dumps(auth))

            if "manageUsers" in request.form:
                users = getAuth()
                del users['dev']
                users = users.keys()
                return render_template('dev.html',manage_user=True, users=users)

            if "managingUser" in request.form:
                toDelete = []
                for key in request.form.keys():
                    if "n-" in key:
                        toDelete.append(request.form[key].replace("n-",""))

                newAuth = {}
                auth=getAuth()

                for user in auth.keys():
                    if user not in toDelete:
                        newAuth[user] = auth[user]

                with open(f'{ROOT}/static/auth.json', 'w') as f:
                    f.write(json.dumps(newAuth))

            if "search" in request.form:
                return render_template('dev.html',search=True)
            if "searching" in request.form:
                articles = loadAllArticles()
                target = request.form['text'].upper()

                hits = []
                for a in articles:
                    if target in a['title'].upper() or target in a['author'].upper():
                        hits.append(a)
                for a in articles:
                    if a not in hits and target in a['article'].upper():
                        hits.append(a)
                # return f"{hits} # {target}"
                return render_template('dev.html',search=True, articles=hits)

            if "edited" in request.form:
                for key in request.form.keys():
                    if not key == 'edited':
                        with open(f"{ARTICLEPATH}/{key}.json","r") as f:
                            file = json.loads(f.read())
                        file['article'] = request.form[key]
                        with open(f"{ARTICLEPATH}/{key}.json","w") as f:
                            f.write(json.dumps(file))

            if "process_drafts" in request.form:
                pass
        return render_template('dev.html')

@app.route('/mailinglist', methods=('GET','POST'))
def mailingList():
    if request.method == 'POST':
        email = request.form['email']
        with open(f"{ROOT}/static/emails.txt", 'a') as f:
            f.write(f",{email}")
        return render_template('mailing_list.html', welcome=True)
    return render_template('mailing_list.html')

@app.route('/<section>/imgs/<filename>')
def get_file(section,filename):
    return send_from_directory(f"{ARTICLEPATH}/{section}/imgs", filename, as_attachment=True)

@app.route('/ip')
def ip():
    # return request.environ['REMOTE_ADDR']
    return request.environ.get('HTTP_X_REAL_IP', request.remote_addr)
