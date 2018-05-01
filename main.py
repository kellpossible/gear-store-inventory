"""Gear Store Inventory

Usage:
  main.py [-p <port>] [-a <address>] new
  main.py [-p <port>] [-a <address>] <file>
  main.py (-h | --help)

Arguments:
  <file>        a json file containing an existing inventory
  <address>     an ip address of an interface on your computer
  <port>        an available port number on your computer

Options:
  -p <port>     port to host webserver on [default: 8090]
  -a <address>  address to host webserver on [default: 0.0.0.0]

Commands:
  new           command to create a new inventory
"""

from flask import Flask, render_template, redirect, request, url_for, abort
import json
import flask_resize
import os
import flask_login
from flask import Flask, abort, Response
from flask_bootstrap import Bootstrap
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired, FileAllowed
from flask_uploads import UploadSet
import flask_uploads
from wtforms import StringField, BooleanField, FloatField, IntegerField, SelectField, SubmitField
from wtforms.fields.html5 import DateField
from wtforms.validators import DataRequired, Optional
from werkzeug.datastructures import CombinedMultiDict, FileStorage
import time
from shutil import copyfile
import io
import csv
import datetime

from werkzeug.utils import secure_filename
from flask_wtf.file import FileField

from docopt import docopt


app = Flask(__name__)

DATETIME_FORMAT = "%Y-%m-%d %H:%M"
DATE_FORMAT = "%Y-%m-%d"

DB = None

DIRECTORY = os.path.dirname(os.path.realpath(__file__))
PHOTOS_DIR = "static/photo"
app.config["SECRET_KEY"] = "SECRETKEY123"
app.config["UPLOADED_PHOTOS_DEST"] = os.path.join(DIRECTORY, PHOTOS_DIR)
app.config["RESIZE_URL"] = PHOTOS_DIR
app.config["RESIZE_ROOT"] = os.path.join(DIRECTORY, PHOTOS_DIR)
app.config["RESIZE_NOOP"] = False

Bootstrap(app)
login_manager = flask_login.LoginManager()
login_manager.init_app(app)

PHOTOS = UploadSet('photos', flask_uploads.IMAGES)
flask_uploads.configure_uploads(app, PHOTOS)

USERS = {"ski@mumc.org.au": {'pw': "jfd$&Dlkj22f!"}}

# command line arguments
ARGUMENTS = None

flask_resize.Resize(app)

class EditItemForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    type = StringField('Type')
    note = StringField('Note')
    purchase_price = FloatField('Purchase Price')
    quantity = IntegerField('Quantity')
    # currently_loaned = BooleanField('Currently Loaned')
    category = SelectField('Category', coerce=int)
    submit = SubmitField()

class NewItemForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    image_1 = FileField('Image 1', validators=[FileAllowed(PHOTOS, u'Image only!')])
    image_2 = FileField('Image 2', validators=[FileAllowed(PHOTOS, u'Image only!')])
    type = StringField('Type')
    note = StringField('Note')
    purchase_price = FloatField('Purchase Price')
    purchase_date = DateField('Purchase Date', format=DATE_FORMAT, validators=[Optional()])
    quantity = IntegerField('Quantity')
    # currently_loaned = BooleanField('Currently Loaned')
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
        item["images"] = []
        item["category"] = ""
        item["purchase_price"] = 0.0
        item["type"] = ""
        item["note"] = ""
        item["currently_loaned"] = False
        item["quantity"] = 1

        created_date = datetime.datetime.now()
        item["created_date"] = created_date.strftime(DATETIME_FORMAT)

        item["purchase_date"] = None

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

    def get_item_purchase_date(self, id):
        item = self.get_item(id)
        if "purchase_date" in item and item["purchase_date"] is not None:
            return datetime.datetime.strptime(item["purchase_date"], DATETIME_FORMAT)
        else:
            return None

    def get_item_age_years(self, id):
        now = datetime.datetime.now()
        purchase_date = self.get_item_purchase_date(id)

        if purchase_date is None:
            return None

        time_diff_seconds = (now - purchase_date).total_seconds()

        return time_diff_seconds/(60.0 * 60.0 * 24.0 * 365.25)

    def get_item_age_years_string(self, id):
        age = self.get_item_age_years(id)
        if age is None:
            return ""
        else:
            return "{:.2f}".format(age)
    

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

    def get_json_string(self):
        return json.dumps(self.json, indent=4)

    def get_csv_string(self):
        output = io.StringIO()
        writer = csv.writer(output, quoting=csv.QUOTE_NONNUMERIC)

        writer.writerow([
            "id",
            "name", 
            "images", 
            "category",
            "purchase price", 
            "type", 
            "note", 
            "currently loaned", 
            "quantity", 
            "created date",
            "purchase date"
            ])

        for item in DB.json["items"]:
            writer.writerow([
                item["id"],
                item["name"],
                str(item["images"]) if "images" in item else [],
                self.get_category(item["category"])["name"],
                item["purchase_price"],
                item["type"],
                item["note"],
                item["currently_loaned"],
                item["quantity"],
                item["created_date"] if "created_date" in item else None,
                item["purchase_date"] if "purchase_date" in item else None
            ])
        
        return output.getvalue()

    def get_filename(self):
        return self.filename

    def get_img_src(self, image_name):
        return "/static/photo/" + image_name

    def backup(self):
        backup_filename = "database_backup_{0}.json".format(int(time.time()))
        backup_file_path = os.path.join(DIRECTORY, backup_filename)

        copyfile(self.filename, backup_file_path)

@app.route('/')
@flask_login.login_required
def index():
    if (ARGUMENTS['new']):
        return redirect('/new-inventory')
    else:
        DB.read()
        return render_template("index.html", db=DB)

@app.route('/new-inventory')
def new_inventory():
    abort(404)

@app.route('/new-item', methods=['GET', 'POST'])
@flask_login.login_required
def new_item():
    DB.read()

    form = NewItemForm()
    form.category.choices = DB.get_category_choices()

    if request.method == 'POST':
        print("post")
        if form.validate_on_submit():
            print("validated")

            item = DB.new_item(form.name.data)

            if form.image_1.data is not None:
                filename = PHOTOS.save(form.image_1.data)
                item["images"].append(filename)
                print("uploaded image 1:", filename)

            if form.image_2.data is not None:
                filename = PHOTOS.save(form.image_2.data)
                item["images"].append(filename)
                print("uploaded image 2:", filename)

            item["category"] = int(form.category.data)
            item["purchase_price"] = form.purchase_price.data
            item["type"] = form.type.data
            item["note"] = form.note.data
            # item["currently_loaned"] = form.currently_loaned.data
            item["quantity"] = form.quantity.data

            purchase_date = form.purchase_date.data
            if purchase_date is not None:    
                purchase_date = datetime.datetime.combine(purchase_date, datetime.time(0, 0))
                item["purchase_date"] = purchase_date.strftime(DATETIME_FORMAT)
            else:
                item["purchase_date"] = None
             
            DB.commit()

            print("committed")

            return redirect(url_for("index") + "#item-{0}".format(item["id"]))

        return render_template("new_item.html", form=form, new_item_id=DB.max_id() + 1)
    
    if request.method == 'GET':
        category_id = 1
        if "category" in request.args:
            category_id = int(request.args["category"])
        
        form = NewItemForm(quantity=1,
                            purchase_price=0.0,
                            category=category_id)
        form.category.choices = DB.get_category_choices()
        return render_template("new_item.html", form=form, new_item_id=DB.max_id()+1)

@app.route('/edit-item/<int:id>', methods=['GET', 'POST'])
@flask_login.login_required
def edit_item(id):
    DB.read()
    item = DB.get_item(id)

    if item is None:
        abort(404)

    form = EditItemForm()
    form.category.choices = DB.get_category_choices()

    if request.method == 'POST':
        if form.validate_on_submit():
            item["name"] = form.name.data
            item["category"] = form.category.data
            item["purchase_price"] = form.purchase_price.data
            item["type"] = form.type.data
            item["note"] = form.note.data
            # item["currently_loaned"] = form.currently_loaned.data
            DB.commit()

        return redirect(url_for("index") + "#item-{0}".format(item["id"]))

    form = EditItemForm(
        name=item["name"],
        category = item["category"],
        purchase_price = float(item["purchase_price"]),
        quantity = item["quantity"],
        type = item["type"],
        note = item["note"]
        #currently_loaned = item["currently_loaned"]
    )
    form.category.choices = DB.get_category_choices()
    return render_template("edit_item.html", item=item, form=form, db=DB)

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

@app.route('/download', methods=['GET'])
def download():
    download_format = request.args.get("format")

    db_filepath = DB.get_filename()
    db_basename = os.path.basename(db_filepath)
    download_filename = os.path.splitext(db_basename)[0]

    if download_format == "json":
        download_filename += ".json"

        return Response(
            DB.get_json_string(),
            mimetype="text/json",
            headers={
                "Content-disposition": 
                "attachment; filename={}".format(download_filename)}
        )
    elif download_format == "csv":
        download_filename += ".csv"
        return Response(
            DB.get_csv_string(),
            mimetype="text/csv",
            headers={
                "Content-disposition": 
                "attachment; filename={}".format(download_filename)}
        )
    else:
        abort(404)

if __name__ == '__main__':
    arguments = docopt(__doc__, version='Gear Store Inventory 0.1')
    ARGUMENTS = arguments

    if not ARGUMENTS['new']:
        DB = Database(os.path.join(DIRECTORY, ARGUMENTS["<file>"]))
    print(arguments)
    app.debug = True
    app.run(host=arguments['-a'], port=int(arguments['-p']))

    
