from flask import Flask, request, jsonify
from pymongo import MongoClient
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# MongoDB connection
client = MongoClient("mongodb://localhost:27017/")  # Replace with your MongoDB URI
db = client["banking_system"]  # Database name
bank_accounts_collection = db["bank_accounts"]  # Collection for existing bank accounts
app_users_collection = db["app_users"]  # Collection for app user accounts
bankdetails = db["bank"]  # Collection for user records
linked_accounts = db["linked_accounts"]  # Collection for linked accounts

@app.route('/addbankdetails', methods=['POST'])
def create_bankrec():
    data = request.json
    bank_accounts_collection.insert_one(data)
    return jsonify({ "message": "User created successfully"}), 201



@app.route('/adduserdetail', methods=['POST'])
def create_user():
    data = request.json
    user_id = app_users_collection.insert_one(data)
    return jsonify({"id": str(user_id.inserted_id), "message": "User created successfully"}), 201

@app.route('/link_bank_account', methods=['POST'])
def link_bank_account():
    try:
        data = request.json
        username = data.get("username")
        mobile_number = data.get("mobile_number")
        password = data.get("password")

        if not all([username, mobile_number, password]):
            return jsonify({"error": "All fields are required"}), 400

        existing_bank_account = bank_accounts_collection.find_one({"mobile_number": mobile_number})
        if not existing_bank_account:
            return jsonify({"error": "No bank account found with this mobile number"}), 404
        
        app_user_account = {
            "username": username,
            "mobile_number": mobile_number,
            "password": password,
            "linked_bank_account": ""
        }
        linked_accounts.insert_one(app_user_account)

        return jsonify({"message": "Bank account successfully linked to app user account"}), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/login', methods=['POST'])
def login():
    try:
        data = request.json
        username = data.get("username")
        password = data.get("password")
        already_linked = linked_accounts.find_one({"username": username, "password": password})
        if already_linked:
            return jsonify({"linked": "true"}), 222
        if not already_linked:
            if not all([username, password]):
                return jsonify({"error": "Username and password are required"}), 400

            user = app_users_collection.find_one({"username": username, "password": password})
            if not user:
                return jsonify({"error": "Invalid username or password"}), 401

            return jsonify({
            "message": "Login successful",
            "user": {
                "username": user["username"],
                "mobile_number": user["mobile_number"],
                "password": user["password"]
}}              ), 200


        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/forgot_password', methods=['POST'])
def forgot_password():
    try:
        data = request.json
        email = data.get("email")
        new_password = data.get("new_password")

        if not all([email, new_password]):
            return jsonify({"error": "Email and new password are required"}), 400

        # Find the user by email
        user = app_users_collection.find_one({"email": email})
        name=user["username"]
        if not user:
            return jsonify({"error": "No account found with this email"}), 404

        # Update the user's password
        app_users_collection.update_one({"email": email}, {"$set": {"password": new_password}})
        passlinked=linked_accounts.find_one({"username": name})
        if passlinked:
            # Update the linked account password as well    
            linked_accounts.update_one({"username": name}, {"$set": {"password": new_password}})
            bank_accounts_collection.update_one({"username": name}, {"$set": {"password": new_password}})
           
        return jsonify({"message": "Password reset successful"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/get_balance', methods=['POST'])
def get_balance():
    try:
        data = request.json
        mobile_number = data.get("mobile_number")

        if not mobile_number:
            return jsonify({"error": "Mobile number is required"}), 400

        # Find the bank account by mobile number
        bank_account = bank_accounts_collection.find_one({"mobile_number": mobile_number})
        if not bank_account:
            return jsonify({"error": "No bank account found with this mobile number"}), 404

        return jsonify({
            "balance": bank_account["balance"]
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)