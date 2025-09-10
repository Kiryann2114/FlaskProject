from flask import Flask, render_template, request, redirect, url_for, abort
from flask_sqlalchemy import SQLAlchemy
import json
import hashlib

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
db = SQLAlchemy(app)

class User(db.Model):
    login = db.Column(db.String(255), nullable=False, primary_key=True,)
    username = db.Column(db.String(255), nullable=False)
    password = db.Column(db.String(255), nullable=False)
    clients = db.Column(db.Text, nullable=True)

    def __repr__(self):
        return self.username

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    passed = db.Column(db.Boolean, nullable=False)
    json_str = db.Column(db.Text, nullable=False)

    def __repr__(self):
        return self.json_str

class Client(db.Model):
    inn = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)

    def __repr__(self):
        return self.name + " : " + str(self.inn)

class Articuls(db.Model):
    articul = db.Column(db.String(255), primary_key=True)

    def __repr__(self):
        return self.articul

with app.app_context():
    db.create_all()


def hash_password(password):
    return hashlib.sha256(password.encode('utf-8')).hexdigest()

def check_user(request):
    if request.cookies.get("login") != None and request.cookies.get("password") != None:
        login = request.cookies.get("login").encode('latin-1').decode('utf-8')
        password = request.cookies.get("password")
        print(hash_password(password))
        user = User.query.filter_by(login=login,password=hash_password(password)).first()
        return user
    return None


# Пути, которые доступны всем
PUBLIC_PATHS = ['/', '/login', '/api/add_order']

# IP локальной сети
LOCAL_NETWORKS = ['127.0.0.1', '192.168.', '10.0.']


@app.before_request
def restrict_access():
    path = request.path

    # Пропускаем публичные пути
    if any(path.startswith(public_path) for public_path in PUBLIC_PATHS):
        return None

    client_ip = request.remote_addr

    # Проверяем, находится ли IP в локальной сети
    is_local = any(client_ip.startswith(network) for network in LOCAL_NETWORKS)

    if not is_local:
        abort(403)


@app.route('/')
def index():
    user = check_user(request)
    if user:
        clients = []
        if user.clients != None:
            clients_user = user.clients.split(',')
            clients = Client.query.filter(Client.inn.in_(clients_user)).all()
        articuls = Articuls.query.all()
        return render_template("index.html", username=user, clients=clients, articuls=articuls)
    else:
        return redirect(url_for("login"))

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')
    elif request.method == 'POST':
        return redirect("/")


#API
@app.route('/api/add_order', methods=['POST'])
def add_order():
    if request.method == 'POST' and check_user(request):
        client_split = request.json["client"].split(" : ")
        if len(client_split) < 2:
            client_split.append("")
        request.json["client"] = {"name": client_split[0], "inn": client_split[1]}
        order = Order(passed=False,json_str=str(request.json))
        try:
            db.session.add(order)
            db.session.commit()
            return "Добавление ордера прошло успешно"
        except:
            return "Произошла ошибка при добавлении ордера"

@app.route('/api/get_orders')
def get_orders():
    orders = Order.query.filter_by(passed=False).all()
    struct = []
    for order in orders:
        struct.append({'id': order.id, 'json': eval(order.json_str)})
    return struct

@app.route('/api/passed_order', methods=['POST'])
def passed_order():
    if request.method == 'POST' and check_user(request):
        orders = Order.query.filter(Order.id.in_(request.json["items"])).all()
        for order in orders:
            order.passed = True
        try:
            db.session.commit()
            return "Обновление прошло успешно"
        except:
            return "Ошибка при обновлении"


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')