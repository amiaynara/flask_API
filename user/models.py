from flask import Flask, jsonify, request

# this is where we define the structure for our database



class User:
    def signup(self):
        if request.method == "POST":
            user = {
                    "name":request.form["name"],
                    "email":"",
                    "password":""
                    }
        else:
            user= {
                    "name": "amiay"
                    }
        return jsonify(user), 200
