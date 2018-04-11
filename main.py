from flask import Flask, render_template, redirect, request, url_for, abort
import json
import flask_resize
import os
import flask_login
from flask import Flask
from flask_bootstrap import Bootstrap
from flask_wtf import Form
from wtforms import StringField, BooleanField, FloatField, IntegerField, SelectField, SubmitField
from wtforms.validators import DataRequired
import time
from shutil import copyfile

from werkzeug.utils import secure_filename
from flask_wtf.file import FileField


app = Flask(__name__)
Bootstrap(app)
login_manager = flask_login.LoginManager()
login_manager.init_app(app)

DIRECTORY = os.path.dirname(os.path.realpath(__file__))

app.secret_key = "SECRETKEY123"
app.config["RESIZE_URL"] = "static/photo/"
app.config["RESIZE_ROOT"] = os.path.join(DIRECTORY, "static/photo")
app.config["RESIZE_NOOP"] = False

USERS = {"ski@mumc.org.au": {'pw': "secret_test_password123!"}}

flask_resize.Resize(app)

class EditItemForm(Form):
    name = StringField('Name', validators=[DataRequired()])
    type = StringField('Type')
    note = StringField('Note')
    purchase_price = FloatField('Purchase Price')
    quantity = IntegerField('Quantity')
    currently_loaned = BooleanField('Currently Loaned')
    category = SelectField('Category', coerce=int)
    submit = SubmitField()


class LoginUser(flask_login.UserMixin):
    pass

@login_manager.user_loader
def user_loader(email):
    if email not in USERS:
        return

    user = LoginUser()
    user.id = email
    return user

@login_manager.request_loader
def request_loader(request):
    email = request.form.get('email')
    if email not in USERS:
        return

    user = LoginUser()
    user.id = email

    # DO NOT ever store passwords in plaintext and always compare password
    # hashes using constant-time comparison!

    user.is_authenticated = request.form['pw'] == USERS[email]['pw']

    return user

@login_manager.unauthorized_handler
def unauthorized_handler():
    return redirect(url_for('login'))

class Database:
    def __init__(self, filename):
        self.filename = filename
        self.read()

    def read(self):
        database_file = open(self.filename, "r")
        self.json = json.loads(database_file.read())
        database_file.close()

    def count_items_category(self, category_id):
        count = 0
        for item in self.json["items"]:
            if item["category"] == category_id:
                count += item["quantity"]

        return count

    def max_id(self):
        max_id = 0
        for item in self.json["items"]:
            comp_id = item["id"]
            if comp_id == None:
                comp_id = 0

            if comp_id > max_id:
                max_id = item["id"]

        return max_id

    def new_item(self, name):
        item = {}
        item["id"] = self.max_id() + 1
        item["name"] = name
        item["category"] = ""
        item["purchase_price"] = 0.0
        item["type"] = ""
        item["note"] = ""
        item["currently_loaned"] = False
        item["quantity"] = 1

        self.json["items"].append(item)
        return item

    def commit(self):
        self.backup()
        database_file = open(self.filename, "w")
        database_file.write(json.dumps(self.json, indent=4))
        database_file.close()

    def delete_item(self, id):
        delete_item = None
        for item in DB.json["items"]:
            if item["id"] == id:
                delete_item = item

        self.json["items"].remove(delete_item)

    def get_item(self, id):
        for item in DB.json["items"]:
            if item["id"] == id:
                return item

        return None

    def get_category_choices(self):
        choices = []
        for category in self.json["categories"]:
            choices.append((int(category["id"]),category["name"]))

        return choices

    def get_inventory_name(self):
        return self.json["inventory-name"]

    def get_category(self, category_id):
        for category in self.json["categories"]:
            if category["id"] == category_id:
                return category

        return None

    def get_img_src(self, image_name):
        return "/static/photo/" + image_name

    def backup(self):
        backup_filename = "database_backup_{0}.json".format(int(time.time()))
        backup_file_path = os.path.join(DIRECTORY, backup_filename)

        copyfile(self.filename, backup_file_path)


DB = Database(os.path.join(DIRECTORY, "ski_store_inventory.json"))

@app.route('/')
@flask_login.login_required
def index():
    DB.read()
    return render_template("index.html", db=DB)

@app.route('/new-item', methods=['GET', 'POST'])
@flask_login.login_required
def new_item():
    DB.read()

    form = EditItemForm()
    form.category.choices = DB.get_category_choices()

    if request.method == 'POST':
        print("post")
        if form.validate_on_submit():
            print("validated")
            item = DB.new_item(form.name.data)
            item["category"] = int(form.category.data)
            item["purchase_price"] = form.purchase_price.data
            item["type"] = form.type.data
            item["note"] = form.note.data
            item["currently_loaned"] = form.currently_loaned.data
            item["quantity"] = form.quantity.data
            DB.commit()

            print("committed")

            return redirect(url_for("index") + "#item-{0}".format(item["id"]))

        return render_template("new_item.html", form=form, new_item_id=DB.max_id() + 1)

    form = EditItemForm(quantity=1,
                        purchase_price=0.0,
                        category=1)
    form.category.choices = DB.get_category_choices()
    return render_template("new_item.html", form=form, new_item_id=DB.max_id()+1)

@app.route('/edit-item/<int:id>', methods=['GET', 'POST'])
@flask_login.login_required
def edit_item(id):
    DB.read()
    item = DB.get_item(id)

    form = EditItemForm()
    form.category.choices = DB.get_category_choices()

    if request.method == 'POST':
        if form.validate_on_submit():
            item["name"] = form.name.data
            item["category"] = form.category.data
            item["purchase_price"] = form.purchase_price.data
            item["type"] = form.type.data
            item["note"] = form.note.data
            item["currently_loaned"] = form.currently_loaned.data
            DB.commit()

        return redirect(url_for("index") + "#item-{0}".format(item["id"]))

    form = EditItemForm(
        name=item["name"],
        category = item["category"],
        purchase_price = float(item["purchase_price"]),
        quantity = item["quantity"],
        type = item["type"],
        note = item["note"],
        currently_loaned = item["currently_loaned"]

    )
    form.category.choices = DB.get_category_choices()
    return render_template("edit_item.html", item=item, form=form)


@app.route('/delete-item/<int:id>', methods=['GET', 'POST'])
@flask_login.login_required
def delete_item(id):
    print("ID", id)
    DB.read()

    if request.method == 'GET':
        delete_item = DB.get_item(id)
        if delete_item:
            return render_template("delete_item.html", item=delete_item)
        else:
            return redirect(url_for("index"))

    if request.method == 'POST':
        if request.form['action'] == 'Delete':
            DB.delete_item(id)
            DB.commit()

    return redirect(url_for("index"))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template("login.html")

    email = request.form['email']
    if request.form['pw'] == USERS[email]['pw']:
        user = LoginUser()
        user.id = email
        flask_login.login_user(user)
        next = request.args.get('next')

        return redirect(next or url_for('index'))

    return 'Bad login'

if __name__ == '__main__':
    app.debug = True
    app.run(host="0.0.0.0", port=8090)
