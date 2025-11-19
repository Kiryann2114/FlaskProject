from flask import Flask, render_template, request, redirect, url_for, jsonify
from BD_models import db, User, Client, Articuls, Order, Questionnaire
from utils import check_user, send_file, create_task, send_message, check_task
from flask_cors import CORS
from apscheduler.schedulers.background import BackgroundScheduler
import atexit
import os

app = Flask(__name__)
CORS(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

# Проверка, запускается ли приложение напрямую (для избежания дублирования scheduler в Gunicorn)
if os.environ.get('WERKZEUG_RUN_MAIN') == 'true' or __name__ == '__main__':
    with app.app_context():
        db.create_all()


### Orders
@app.route('/')
def index():
    user = check_user(request)
    if user:
        clients = []
        if user.clients:
            clients_user = user.clients.split(',')
            clients = Client.query.filter(Client.inn.in_(clients_user)).all()
        articuls = Articuls.query.all()
        managers = User.query.filter(User.username != "admin").all()
        return render_template("index.html", username=user, clients=clients, managers=managers, articuls=articuls)
    else:
        return redirect(url_for("login"))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')
    elif request.method == 'POST':
        # Здесь должна быть логика авторизации
        # Пока заглушка
        return redirect("/")


# API
@app.route('/api/add_order', methods=['POST'])
def add_order():
    if not check_user(request):
        return "Unauthorized", 401

    try:
        client_split = request.json["client"].split(" : ")
        client_data = {"name": client_split[0], "inn": client_split[1] if len(client_split) > 1 else ""}

        order = Order(passed=False, json_str=str({'client': client_data, **{k: v for k, v in request.json.items() if k != 'client'}}))
        db.session.add(order)
        db.session.commit()
        return "Добавление ордера прошло успешно", 200
    except Exception as e:
        db.session.rollback()
        return f"Ошибка при добавлении ордера: {str(e)}", 500


@app.route('/api/get_orders')
def get_orders():
    orders = Order.query.filter_by(passed=False).all()
    struct = [{'id': order.id, 'json': eval(order.json_str)} for order in orders]
    return jsonify(struct)


@app.route('/api/passed_order', methods=['POST'])
def passed_order():
    if not check_user(request):
        return "Unauthorized", 401

    try:
        order_ids = request.json.get("items", [])
        orders = Order.query.filter(Order.id.in_(order_ids)).all()
        for order in orders:
            order.passed = True
        db.session.commit()
        return "Обновление прошло успешно", 200
    except Exception as e:
        db.session.rollback()
        return f"Ошибка при обновлении: {str(e)}", 500


### Kandidat
@app.route('/api/anket', methods=['POST'])
def anket():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Нет данных'}), 400

    try:
        file_id, full_name, vacancy = send_file(data)
        task_id = create_task(file_id, full_name)

        new_application = Questionnaire(
            file_id=file_id,
            full_name=full_name,
            task_id=task_id,
            vacancy=vacancy,
            status=False
        )
        db.session.add(new_application)
        db.session.commit()

        message = f'https://imperial44.bitrix24.ru/company/personal/user/0/tasks/task/view/{task_id}/'
        send_message("chat14882", message)

        return jsonify({'message': 'Анкета успешно получена'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Ошибка при сохранении анкеты: {str(e)}'}), 500


### TP 1C — заглушки, можно реализовать позже
@app.route('/api/create_application_tp', methods=['POST'])
def create_application_tp():
    data = request.get_json()
    return jsonify({'status': 'success', 'data': data}), 200

@app.route('/api/delete_application_tp', methods=['POST'])
def delete_application_tp():
    return jsonify({'status': 'success'}), 200

@app.route('/api/update_application_tp', methods=['POST'])
def update_application_tp():
    data = request.get_json()
    return jsonify({'status': 'success', 'data': data}), 200

@app.route('/api/get_application_tp', methods=['POST'])
def get_application_tp():
    return jsonify({'status': 'success', 'data': []}), 200


# Фоновая задача — проверка заявок со статусом False
def check_pending_applications():
    with app.app_context():
        try:
            pending_apps = Questionnaire.query.filter_by(status=False).all()
            for app_record in pending_apps:
                comment = check_task(app_record.task_id)
                if comment and comment.strip():
                    app_record.status = True
                    db.session.commit()
                    send_message(
                        "chat14886",
                        f"ФИО: {app_record.full_name}\n"
                        f"Должность: {app_record.vacancy}\n"
                        f"Комментарий СБ: {comment}\n\n"
                        f"Анкета: [URL=https://imperial44.bitrix24.ru/bitrix/tools/disk/focus.php?objectId={app_record.file_id}&cmd=show&action=showObjectInGrid&ncc=1]Ссылка[/URL]"
                    )
        except Exception as e:
            print(f"Ошибка при проверке заявок: {e}")


### Настройка планировщика
scheduler = None

def start_scheduler():
    global scheduler
    if scheduler is None:
        scheduler = BackgroundScheduler()
        scheduler.add_job(func=check_pending_applications, trigger="interval", minutes=1)
        scheduler.start()
        print("Scheduler started.")

        # Очистка при завершении
        atexit.register(lambda: scheduler.shutdown())

# Запуск планировщика только при прямом запуске (избежание дублирования в Gunicorn/uWSGI)
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        start_scheduler()
    app.run(debug=False, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))