from flask import Flask, render_template
import json

app = Flask(__name__)


database_file = open("ski_store_inventory.json", "r")
db = json.loads(database_file.read())
database_file.close()

@app.route('/')
def index():
    return render_template("index.html", db=db)

if __name__ == '__main__':
	app.debug = True
	app.run(host="0.0.0.0", port=8090)