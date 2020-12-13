from flask import Flask, render_template, request, url_for, flash, redirect, jsonify, make_response
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

GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID", None)
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET", None)
GOOGLE_DISCOVERY_URL = (
    "https://accounts.google.com/.well-known/openid-configuration"
)

#UPLOAD_FOLDER = './static/uploads/images'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app = Flask(__name__)
# Sensisive informations have been removed so this will not work, instead I have provided dummy variables
db_pass = urllib.parse.quote("thisisnotmyactualserveradminname")
db_username = "thisisnotmyactualpassword"       # these are intentionally made vague before uploading on github

app.config["MONGO_URI"] = "mongodb+srv://"+db_username+db_pass+"@cluster0.wxsoe.mongodb.net/notactualnameofdatabase"
app.config["SECRET_KEY"] = "nottheactualsecret"
mongo = PyMongo(app)
#app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.secret_key=b"notactualkeyonceagain"


limiter = Limiter(
    app,
    key_func=get_remote_address,
)



def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        print("this is what firefox sends back :",request.headers )
        try:

            print("from the token_requeried: ",request.headers["X-Access-Token"])
        except:
            pass
        try:
            token = request.form['x-access-token'][2:-1]
            print("token received through form is: ", token)
        except:
            token = None
        if "X-Access-Token" in request.headers:
            token = request.headers['X-Access-Token']
            #print("token was successfully received from the request")
        if not token:
            return jsonify({"message": "Token is missing"}), 401
        data = jwt.decode(token, app.config["SECRET_KEY"], 'utf-8')
        current_user = mongo.db.users1.find_one({"public_id": data["public_id"]})
        if current_user == None:
            return jsonify({"message": "Token is invalid"}), 401
        
        return f(current_user, *args, **kwargs)
    return decorated





def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS



from user import routes
@app.route("/", methods =["GET", "POST"])
def login():
    if request.method == "POST":
        user_requesting = mongo.db.users1.find_one({"name":request.form["user_name"], "password":request.form["passwd"]}) 
        if  user_requesting== None:
            flash("Password or Username did not match")
            return redirect(url_for("login"))
        else:
            public_id = user_requesting["public_id"]
            token = jwt.encode({"public_id":public_id, "name": request.form["user_name"], "exp": datetime.datetime.utcnow() + datetime.timedelta(minutes=30)}, app.config['SECRET_KEY'])

            response = make_response(render_template("upload.html",jwt=token ,message="Login Successful",instruction="click on upload to upload an image"))
            response.headers.set('x-access-token' , token.decode("UTF-8"))
            #return response
            #return jsonify({"token": token.decode("UTF-8")})
            return response
            #return redirect(url_for("upload"))

    message = "Sign In to Upload."
    instruction = "Enter the credentials to be able to upload the file."
    return render_template("home.html", message = message, instruction = instruction) , 200

@app.route("/signup/", methods =["GET", "POST"])
def signupme():
    if request.method == "POST":
        print("a new user tried to signup in")
        user = {
                "public_id": str(uuid.uuid4()),
                "name" : request.form["user_name"],
                "password" : request.form["passwd"]
                }
        print(user["name"] , user["password"])
        if len(user["name"] )>3 and len(user["password"])>3:
            print("credentials are fine.. adding to the data base")
            flash("Created new user")
            mongo.db.users1.insert(user)
            return redirect(url_for("login"))
        else:
            # some thing wrong with creating new user
            
            flash("Credentials cannot be empty, Must be >3 in length")
            return redirect(url_for("signupme"))
    # for showing the signup page
    message="Sign Up to GET IN!"
    instruction = "Enter your credentials so that we can uniquely identify you."
    return render_template("signup.html", message=message, instruction = instruction), 201

@app.route("/upload", methods = ["POST", "GET"])
@limiter.limit("5/minute")      # 5 per minute 
@token_required 
def upload(current_user):
#def upload():
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
            print("the file name is : ", filename)
            mongo.save_file(filename, file)
            mongo.db.pictures.insert({'public_id':current_user['public_id'], 'name':current_user['name'], 'filename':filename})
            #response = redirect(url_for('success', filename=filename))
            #response.headers['x-access-token'] = request.form['x-access-token'][2:-1]   # creates, but does not pass
            return redirect(url_for("success", filename = filename, current_user_id=current_user['public_id']))
        flash("Only IMG, JPEG, JPG, PNG are allowed, Try Again")
    else:
        print("get requierst made")
        message = "Upload an image"
        instruction = "Choose a file image file from your PC and upload."
        return render_template("upload.html", message = message, instruction = instruction)
@app.route("/succeed")
@limiter.limit("5/minute")
def success():
    filename = request.args['filename']     # passed as message, from successful result
    current_user_id = request.args['current_user_id']
    pictures = mongo.db.pictures.find_one({"public_id":current_user_id, "filename": filename})
    if not pictures:
        return f'<h1>Image {filename} not found in the database</h1>', 404
    print("Pictures found in the data base", pictures)
    return f'''
    <h1>{filename} </h1>
    <div>
    <div class="xzoom-container">
    <img src="{url_for('file', filename=pictures['filename'])}" class="xzoom" xriginal="./images>
    </div>
    </div>
    <script src="https://ajax.googleapis.com/ajax/libs/jquery/3.5.1/jquery.min.js"></script>
    <script>
    console.log("hi")
    </script>
    '''
@limiter.limit("5/minute")
@app.route("/uploaded/<filename>")
def file(filename):
    return mongo.send_file(filename)

# create one route for the admin to manage the database, if time left


if __name__ == "__main__":
    app.run(debug=True)

