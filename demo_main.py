import openai
import os
import time
from flask import Flask, request, jsonify


openai.api_key = os.environ["OPENAI_API_KEY"]

app = Flask(__name__)

DATABASE_PATH = r"C:\Users\Padre\Documents\dev\GPT4-as-DataAnalyst\sql_database\nvBench\databases\database\department_store\department_store.sqlite"
SCHEMA_PATH = os.path.join(os.path.dirname(__file__), "schema.sql")


@app.route("/")
def home():
    return "<h1>Flask Application is Running!</h1>"

def get_gpt_result(system_role, question, max_tokens):
    response = openai.ChatCompletion.create(
        model="gpt-4o",
        max_tokens=max_tokens,
        temperature=0,
        messages=[
            {"role": "system", "content": system_role},
            {"role": "user", "content": question},
        ],
    )
    return response["choices"][0]["message"]["content"]


def save_python(ipt):
    with open("demo.py", "w") as py_file:
        py_file.write(ipt)


def execute_python_code():
    os.system("python demo.py")


def find_all(a_str, sub):
    start = 0
    while True:
        start = a_str.find(sub, start)
        if start == -1:
            return
        yield start
        start += len(sub)


def extract_create_table(s):
    output = ""
    tables = s.split("CREATE TABLE")[1:]
    for table in tables:
        output += "CREATE TABLE"
        output += table.split(");")[0]
        output += ");\n"
    return output


@app.route("/analyze", methods=["POST"])
def analyze():
    question = request.json.get("question")
    if not question:
        return jsonify({"error": "No question provided"}), 400

    # Read schema
    with open(SCHEMA_PATH, "r") as schema_file:
        schema = extract_create_table(schema_file.read())

    # Generate and execute code
    system_role = """Write python code to select relevant data and for drawing a chart. Please save the label and value for potential graph to "data.txt"."""
    question_with_context = f"Question: {question}\n\nconn = sqlite3.connect(r'{DATABASE_PATH}')\n\nSchema: \n{schema}"

    text = get_gpt_result(system_role, question_with_context, 2000)
    try:
        matches = find_all(text, "```")
        matches_list = [x for x in matches]

        python_code = text[matches_list[0] + 10 : matches_list[1]]
    except:
        python_code = text
    save_python(python_code)
    execute_python_code()

    # Read and return data
    try:
        with open("data.txt", "r") as data_file:
            data = data_file.read()

        # Generate analysis
        analysis_system_role = (
            "Generate analysis and insights about the data in 5 bullet points."
        )
        analysis_question = f"Question: {question}\nData: \n{data}"
        analysis = get_gpt_result(analysis_system_role, analysis_question, 2000)

        return jsonify({"data": data, "analysis": analysis})
    except FileNotFoundError:
        return jsonify({"error": "Data file not found"}), 500


if __name__ == "__main__":
    app.run(debug=True)
