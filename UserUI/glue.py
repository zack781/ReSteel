from flask import Flask, request, render_template, jsonify
import subprocess
import json
import os

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/send-dxf', methods=['POST'])
def receive_dxf_request():
    data = request.get_json()

    if not data or 'requestType' not in data or 'path' not in data:
        # ✅ Use jsonify here
        return jsonify(message="Invalid request: Missing fields."), 400

    print("✅ Received DXF request:")
    print(data)

    # Save request data to a JSON file
    with open('dxf_request.json', 'w') as f:
        json.dump(data, f)

    # Call the Node.js script, passing the file path to the JSON
    try:
        result = subprocess.run(
            ["node", "send_dxf_request.js", "dxf_request.json"],
            capture_output=True,
            text=True,
            check=True
        )
        print("Node.js output:", result.stdout)
    except subprocess.CalledProcessError as e:
        print("❌ Node.js failed:", e.stderr)
        # ✅ Use jsonify here too
        return jsonify(message="Node.js script failed."), 500

    # ✅ This is the key fix — always return valid JSON
    return jsonify(message="DXF request received and sent via CoreLink."), 200

if __name__ == '__main__':
    app.run(debug=True)
