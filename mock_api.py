from flask import Flask, request, jsonify

app = Flask(__name__)
db = {} # Наша "база данных" в оперативной памяти

def calc_asses(full_name):
    parts = full_name.strip().split()
    if len(parts) < 3: return ""
    return parts[0].upper() + parts[1][0].upper() + parts[2][0].upper()

@app.route("/users", methods=["POST"])
def create_user():
    data = request.json
    emp_id = data["employee_id"]
    user = {"employee_id": emp_id, "full_name": data["full_name"], "asses": calc_asses(data["full_name"])}
    db[emp_id] = user
    return jsonify(user), 201

@app.route("/users/<emp_id>", methods=["GET"])
def get_user(emp_id):
    if emp_id not in db: return jsonify({"error": "Not found"}), 404
    return jsonify(db[emp_id]), 200

@app.route("/users/<emp_id>", methods=["PUT"])
def update_user(emp_id):
    if emp_id not in db: return jsonify({"error": "Not found"}), 404
    data = request.json
    db[emp_id]["full_name"] = data["full_name"]
    db[emp_id]["asses"] = calc_asses(data["full_name"])
    return jsonify(db[emp_id]), 200

@app.route("/users/<emp_id>", methods=["DELETE"])
def delete_user(emp_id):
    if emp_id in db: del db[emp_id]
    return "", 204

if __name__ == "__main__":
    app.run(port=8000)