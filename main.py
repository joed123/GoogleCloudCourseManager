from flask import Flask, request, jsonify, send_file
from google.cloud import datastore, storage
from werkzeug.utils import secure_filename
from jose import jwt
import requests
import os
import io
from functools import wraps
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(dotenv_path=Path('.') / '.env')

AUTH0_DOMAIN = os.getenv("AUTH0_DOMAIN", "")
AUTH0_AUDIENCE = os.getenv("AUTH0_AUDIENCE", "https://tarpaulin/api")
ALGORITHMS = ["RS256"]
JWKS_URL = f""
JWKS = requests.get(JWKS_URL).json()

ds_client = datastore.Client(project="")

storage_client = storage.Client()
bucket_name = os.getenv("GCS_BUCKET_NAME")
bucket = storage_client.get_bucket(bucket_name)

app = Flask(__name__)

@app.route("/users/login", methods=["POST"])
def login_user():
    data = request.get_json()
    if not data or "username" not in data or "password" not in data:
        return jsonify({"Error": "The request body is invalid"}), 400

    payload = {
        "grant_type": "password",
        "username": data["username"],
        "password": data["password"],
        "audience": AUTH0_AUDIENCE,
        "client_id": os.getenv("AUTH0_CLIENT_ID"),
        "client_secret": os.getenv("AUTH0_CLIENT_SECRET")
    }

    headers = {'content-type': 'application/json'}
    url = f"https://{AUTH0_DOMAIN}/oauth/token"

    response = requests.post(url, json=payload, headers=headers)

    if response.status_code != 200:
        return jsonify({"Error": "Unauthorized"}), 401

    token = response.json().get("access_token")
    return jsonify({"token": token}), 200


def get_token_auth_header():
    auth = request.headers.get("Authorization", None)
    if not auth or not auth.startswith("Bearer "):
        return None
    return auth.split(" ")[1]


def verify_jwt(token):
    unverified_header = jwt.get_unverified_header(token)
    rsa_key = next((k for k in JWKS["keys"] if k["kid"] == unverified_header["kid"]), None)
    if not rsa_key:
        raise Exception("No valid signing key found.")
    return jwt.decode(token, rsa_key, algorithms=ALGORITHMS, audience=AUTH0_AUDIENCE, issuer=f"https://{AUTH0_DOMAIN}/")


def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = get_token_auth_header()
        if not token:
            return jsonify({"Error": "Unauthorized"}), 401
        try:
            payload = verify_jwt(token)
            request.user = payload
        except Exception:
            return jsonify({"Error": "Unauthorized"}), 401
        return f(*args, **kwargs)
    return decorated


def get_user_by_sub(sub):
    query = ds_client.query(kind="users", filters=[("sub", "=", sub)])
    result = list(query.fetch(limit=1))
    return result[0] if result else None


@app.route("/")
def index():
    return {"message": "Tarpaulin API is up"}


@app.route("/users", methods=["GET"])
@requires_auth
def get_all_users():

    user = get_user_by_sub(request.user['sub'])
    query = ds_client.query(kind="users")
    
    if not user or user.get("role") != "admin":
        return jsonify({"Error": "You don't have permission on this resource"}), 403  
    
    query = ds_client.query(kind="users")
    users = [{"id": u.key.id, "role": u["role"], "sub": u["sub"]} for u in query.fetch()]
    return jsonify(users), 200

@app.route("/users/<int:user_id>", methods=["GET"])
@requires_auth
def get_user(user_id):
    current_user = get_user_by_sub(request.user['sub'])
    if not current_user:
        return jsonify({"Error": "Unauthorized"}), 401

    if current_user.key.id != user_id and current_user.get("role") != "admin":
        return jsonify({"Error": "You don't have permission on this resource"}), 403

    user = ds_client.get(ds_client.key("users", user_id))
    if not user:
        return jsonify({"Error": "Not found"}), 403

    result = {"id": user.key.id, "role": user["role"], "sub": user["sub"]}

    if "avatar" in user:
        result["avatar_url"] = f"{request.host_url}users/{user_id}/avatar"

    if user["role"] in ["student", "instructor"]:
        query = ds_client.query(kind="courses")
        if user["role"] == "student":
            query.add_filter(filter=("students", "=", user.key.id))
        else:
            query.add_filter(filter=("instructor_id", "=", user.key.id))
        result["courses"] = [f"{request.host_url}courses/{c.key.id}" for c in query.fetch()]

    return jsonify(result), 200


@app.route("/users/<int:user_id>/avatar", methods=["POST"])
@requires_auth
def upload_avatar(user_id):
    user = get_user_by_sub(request.user['sub'])
    if not user or user.key.id != user_id:
        return jsonify({"Error": "You don't have permission on this resource"}), 403

    if 'file' not in request.files:
        return jsonify({"Error": "The request body is invalid"}), 400

    file = request.files['file']
    blob = bucket.blob(f"avatars/{user_id}.png")
    blob.upload_from_file(file, content_type='image/png')

    user_entity = ds_client.get(ds_client.key("users", user_id))
    user_entity["avatar"] = True
    ds_client.put(user_entity)
    return jsonify({"avatar_url": f"{request.host_url}users/{user_id}/avatar"}), 200


@app.route("/users/<int:user_id>/avatar", methods=["GET"])
@requires_auth
def get_avatar(user_id):
    user = get_user_by_sub(request.user['sub'])
    if not user or user.key.id != user_id:
        return jsonify({"Error": "You don't have permission on this resource"}), 403

    blob = bucket.blob(f"avatars/{user_id}.png")
    if not blob.exists():
        return jsonify({"Error": "Not found"}), 404

    stream = io.BytesIO()
    blob.download_to_file(stream)
    stream.seek(0)
    return send_file(stream, mimetype='image/png')


@app.route("/users/<int:user_id>/avatar", methods=["DELETE"])
@requires_auth
def delete_avatar(user_id):
    user = get_user_by_sub(request.user['sub'])
    if not user or user.key.id != user_id:
        return jsonify({"Error": "You don't have permission on this resource"}), 403

    blob = bucket.blob(f"avatars/{user_id}.png")
    if not blob.exists():
        return jsonify({"Error": "Not found"}), 404

    blob.delete()
    user_entity = ds_client.get(ds_client.key("users", user_id))
    user_entity.pop("avatar", None)
    ds_client.put(user_entity)
    return ("", 204)


@app.route("/courses", methods=["POST"])
@requires_auth
def create_course():
    try:
        user = get_user_by_sub(request.user['sub'])
        if not user or user.get("role") != "admin":
            return jsonify({"Error": "You don't have permission on this resource"}), 403

        data = request.get_json()
        required_fields = ["title", "subject", "number", "term", "instructor_id"]

        if not data:
            return jsonify({"Error": "The request body is invalid"}), 400

        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            return jsonify({"Error": "The request body is invalid"}), 400

        instructor_key = ds_client.key("users", data["instructor_id"])
        instructor = ds_client.get(instructor_key)
        if not instructor or instructor.get("role") != "instructor":
            return jsonify({"Error": "The request body is invalid"}), 400

        course_key = ds_client.key("courses")
        course = datastore.Entity(key=course_key)
        course.update({
            "title": data["title"],
            "subject": data["subject"],
            "number": data["number"],
            "term": data["term"],
            "instructor_id": data["instructor_id"],
            "students": []
        })
        ds_client.put(course)

        response = {
            "id": course.key.id,
            "instructor_id": data["instructor_id"],
            "number": data["number"],
            "subject": data["subject"],
            "term": data["term"],
            "title": data["title"],
            "self": f"{request.host_url}courses/{course.key.id}"
        }

        return jsonify(response), 201
    except Exception as e:
        return jsonify({"Error": "Internal server error"}), 500

@app.route("/courses", methods=["GET"])
def get_courses():
    try:
        query = ds_client.query(kind="courses")
        query.order = ["subject"]

        offset = int(request.args.get("offset", 0))
        limit = int(request.args.get("limit", 3))

        iterator = query.fetch(offset=offset, limit=limit + 1)
        courses_list = list(iterator)

        has_more = len(courses_list) > limit
        if has_more:
            courses_list = courses_list[:limit]

        courses = []
        for c in courses_list:
            courses.append({
                "id": c.key.id,
                "title": c.get("title", "Missing Title"),
                "subject": c.get("subject", "???"),
                "number": c.get("number", -1),
                "term": c.get("term", "unknown"),
                "instructor_id": c.get("instructor_id"),
                "self": f"{request.host_url}courses/{c.key.id}"
            })

        response = {"courses": courses}
        if has_more:
            response["next"] = f"{request.host_url}courses?offset={offset + limit}&limit={limit}"

        return jsonify(response), 200

    except Exception as e:
        return jsonify({"Error": "Internal server error"}), 500

@app.route("/courses/<int:course_id>", methods=["GET"])
def get_course(course_id):
    try:
        course = ds_client.get(ds_client.key("courses", course_id))
        if not course:
            return jsonify({"Error": "Not found"}), 404

        return jsonify({
            "id": course.key.id,
            "title": course["title"],
            "subject": course["subject"],
            "number": course["number"],
            "term": course["term"],
            "instructor_id": course["instructor_id"],
            "self": f"{request.host_url}courses/{course.key.id}"
        }), 200

    except Exception as e:
        return jsonify({"Error": "Internal server error"}), 500


if __name__ == "__main__":
    app.run(debug=True)
