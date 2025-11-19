from flask_sqlalchemy import SQLAlchemy


db = SQLAlchemy()


### Orders
class User(db.Model):
    login = db.Column(db.String(255), nullable=False, primary_key=True)
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
    inn = db.Column(db.String(255), primary_key=True)
    name = db.Column(db.String(255), nullable=False)

    def __repr__(self):
        return self.name + " : " + str(self.inn)

class Articuls(db.Model):
    articul = db.Column(db.String(255), primary_key=True)

    def __repr__(self):
        return self.articul


### Kandidat
class Questionnaire(db.Model):
    task_id = db.Column(db.Integer, primary_key=True)
    file_id = db.Column(db.String, nullable=False)
    full_name = db.Column(db.String, nullable=False)
    vacancy = db.Column(db.String, nullable=False)
    status = db.Column(db.Boolean, default=False)

    def __repr__(self):
        return self.status


### TP 1C
class Account_tp(db.Model):
    login = db.Column(db.String, primary_key=True)
    password = db.Column(db.String, nullable=False)

    def __repr__(self):
        return self.login

class Application_tp(db.Model):
    id = db.Column(db.String, primary_key=True)
    title = db.Column(db.String, nullable=False)
    login_acc = db.Column(db.String, nullable=False)
    status = db.Column(db.String, default=False)
    time = db.Column(db.String, default=False)

    def __repr__(self):
        return self.id,self.title,self.login_acc,self.status,self.time
