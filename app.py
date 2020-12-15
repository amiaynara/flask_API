from flask import Flask, render_template, request, url_for, flash, redirect, jsonify, make_response,session
from werkzeug.utils import secure_filename
from flask_pymongo import PyMongo
import os
import jwt
import datetime
from functools import wraps
import uuid
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import urllib
from authlib.integrations.flask_client import OAuth
from bson import json_util 
import json
import PIL
from PIL import Image
from io import StringIO

def parse_json(data):
    return json.loads(data)

GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID", None)
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET", None)
print(GOOGLE_CLIENT_ID)
print(GOOGLE_CLIENT_SECRET)
#UPLOAD_FOLDER = './static/uploads/images'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app = Flask(__name__)
# Sensisive informations have been removed so this will not work, instead I have provided dummy variables
db_pass = urllib.parse.quote("thisisnotrealpass")
db_username = "thisisnotrealpass"       # these are intentionally made vague before uploading on github

app.config["MONGO_URI"] = "mongodb+srv://"+db_username+db_pass+"@cluster0.wxsoe.mongodb.net/notherealdatabase"
app.config["SECRET_KEY"] = "thisisnotrealpass"
mongo = PyMongo(app)
#app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.secret_key=b"thisisnotrealpass"


limiter = Limiter(
    app,
    key_func=get_remote_address,
)

oauth = OAuth(app)
google = oauth.register(
    name='google',
    client_id='thisisnotrealclientid',
    client_secret='thisisnotrealclientid',
    access_token_url='https://accounts.google.com/o/oauth2/token',
    access_token_params=None,
    authorize_url='https://accounts.google.com/o/oauth2/auth',
    authorize_params=None,
    api_base_url='https://www.googleapis.com/oauth2/v1/',
    userinfo_endpoint='https://openidconnect.googleapis.com/v1/userinfo',  # This is only needed if using openId to fetch user info
    client_kwargs={'scope': ' openid email profile'},
)



def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS



def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        current_user= dict(session).get('accepted_info', None)
        if bool(current_user): 
            return f(current_user, *args, **kwargs)
        return "session expired log in again" 
    return decorated_function

from user import routes
@app.route("/")
def login():
    google = oauth.create_client('google')
    redirect_uri = url_for('authorize', _external=True)
    return google.authorize_redirect(redirect_uri)
@app.route("/authorize")
def authorize():
    google = oauth.create_client('google')  # create the google oauth client
    token = google.authorize_access_token()  # Access token from google (needed to get user info)
    print(token['access_token'])
    session['access_token'] = token['access_token']
    resp = google.get('userinfo')  # userinfo contains stuff u specificed in the scrope
    print("response is :",type(resp.text))
    print("normal string type: ", type("amiay"))
    response_json = json.loads(resp.text)
    print(response_json['name'])
    user_info = resp.json()
    user = oauth.google.userinfo()  # uses openid endpoint to fetch user info
    name = user_info['name']
    public_id= user_info['id']
    print("actual data that will be fed type: ", name, public_id, type(name), type(public_id))
    current_user = mongo.db.users1.find_one({'name':name, 'public_id': public_id})
    print("what was found", current_user)
    if current_user:        # if the user exists
        print("user already exists")
        pass
    else:
        print("A new user will be added to the data base")
        mongo.db.users1.insert({'name':name, 'public_id':public_id})
    session['accepted_info'] ={
                'name': name,
                'public_id': public_id
            }
    session.permanent = True  # make the session permanant so it keeps existing after broweser gets closed
    flash("Successfully logged in")
    return   redirect(url_for("home")) 
@app.route("/home")
@login_required
def home(current_user):
    message="Welcome Aboard"
    instruction="Upload images and do much more..."
    return render_template("home.html", message=message, instruction=instruction)

@app.route("/upload", methods = ["POST", "GET"])
@limiter.limit("5/minute")      # 5 per minute 
@login_required
def upload(current_user):
    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            mongo.save_file(filename, file)
            mongo.db.pictures.insert({'public_id':current_user['public_id'], 'name':current_user['name'], 'filename':filename})
            return redirect(url_for("success", filename = filename, current_user_id=current_user['public_id']))
        flash("Only IMG, JPEG, JPG, PNG are allowed, Try Again")
    else:
        print("get requierst made")
        message = "Upload an image"
        instruction = "Choose a file image file from your PC and upload."
        return render_template("upload.html", message = message, instruction = instruction)
@app.route("/succeed")
@limiter.limit("5/minute")
@login_required
def success(current_user):
    filename = request.args['filename']     # passed as message, from successful result
    print("filename : ", filename)
    current_user_id = request.args['current_user_id']
    #filename = os.path.join(app.config['UPLOAD_FOLDER'],filename)
    pictures = mongo.db.pictures.find_one({"public_id":current_user_id, "filename": filename})
    if not pictures:
        return f'<h1>Image {filename} not found in the database</h1>', 404
    print("Pictures found in the data base", pictures)
    return f'''
    <h1>{filename} </h1>
    <div id="img-container" style="width: 350px;">
    <img src="{url_for('file', filename=pictures['filename'])}"  >
    </div>
    <script src="https://ajax.googleapis.com/ajax/libs/jquery/3.5.1/jquery.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/js-image-zoom@0.7.0/js-image-zoom.min.js" type="application/javascript"></script>
    <script>
    console.log("new change")
        var options = {{
            width: 150,
            height: 175,
            zoomWidth: 350,
            offset: {{vertical:0, horizontal: 10 }},
            scale:2.5
            }}
            new ImageZoom(document.getElementById("img-container"), options);
    </script>
    '''
@limiter.limit("5/minute")
@app.route("/uploaded/<filename>")
def file(filename):
    return mongo.send_file(filename)

# create one route for the admin to manage the database, if time left


if __name__ == "__main__":
    app.run(debug=True)

