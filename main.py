from flask import Flask, render_template, redirect, request
import json
import flask_resize
import os

app = Flask(__name__)
app.config["RESIZE_URL"] = "http://localhost:8090/static/photo/"
app.config["RESIZE_ROOT"] = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static/photo")
app.config["RESIZE_NOOP"] = False

flask_resize.Resize(app)



class Database:
    def __init__(self, filename):
        database_file = open(filename, "r")
        self.json = json.loads(database_file.read())
        database_file.close()

    def count_items_category(self, category_id):
        count = 0
        for item in self.json["items"]:
            if item["category"] == category_id:
                count += item["quantity"]

        return count


    def get_img_src(self, image_name):
        return "/static/photo/" + image_name

@app.route('/')
def index():
    DB = Database("ski_store_inventory.json")
    return render_template("index.html", db=DB)

if __name__ == '__main__':
    app.debug = True
    app.run(host="0.0.0.0", port=8090)
