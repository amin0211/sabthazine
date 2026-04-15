

# taskkill /F /IM python.exe
# python server.py
# curl http://127.0.0.1:10000
# https://github.com/amin0211/sabthazine.git
# pip install -r requirements.txt


# git config --global user.name "amin0211"
# git config --global user.email "aminyavari53@gmail.com"

# git init
# git add .
# git commit -m "first commit"

# git branch -M main

# git remote remove origin
# git remote add origin https://github.com/amin0211/sabthazine.git

# git add .
# git commit -m "update deps"
# git pull origin main --rebase
# git push --set-upstream origin main
# git push

from flask import Flask, request, jsonify
from openai import OpenAI
import os
import json, re

app = Flask(__name__)

# ---------------- OPENAI ----------------
client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")  # روی Render باید ست کنی
)

# ---------------- PARSER ----------------
def parse_expense(text):
    try:
        response = client.chat.completions.create(
            model="gpt-5-mini",
            messages=[
                {
                    "role": "system",
                    "content": """
Return ONLY valid JSON.

Keys:
- hazine (string)
- price (number)
- currency (string)
- date (YYYY-MM-DD or null)

Rules:
- NEVER guess date
- If no date → null
"""
                },
                {"role": "user", "content": text}
            ]
        )

        raw = response.choices[0].message.content

        if not raw:
            return {}

        match = re.search(r"\{.*\}", raw, re.DOTALL)
        if not match:
            return {}

        return json.loads(match.group(0))

    except Exception as e:
        return {"error": str(e)}

# ---------------- ROUTE ----------------
@app.route("/parse", methods=["POST"])
def parse_route():
    try:
        data = request.get_json()
        text = data.get("text", "")

        result = parse_expense(text)

        return jsonify(result)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ---------------- HOME TEST ----------------
@app.route("/")
def home():
    return "🚀 Server is running"

# ---------------- RUN ----------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

#print("🔥 SERVER IS STARTING...")

