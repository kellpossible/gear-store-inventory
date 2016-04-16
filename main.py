from flask import Flask, render_template
import json

app = Flask(__name__)


class Database:
	def __init__(self, filename):
		database_file = open(filename, "r")
		self.json = json.loads(database_file.read())
		database_file.close()

	def count_items_category(self, category_id):
		count = 0
		for item in self.json["items"]:
			if item["category"] == category_id:
				count += 1

		return count

DB = Database("ski_store_inventory.json")

@app.route('/')
def index():
    return render_template("index.html", db=DB)

if __name__ == '__main__':
	app.debug = True
	app.run(host="0.0.0.0", port=8090)