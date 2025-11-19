from flask import Flask, render_template, request, redirect, url_for, abort, jsonify
from BD_models import db, User, Client, Articuls, Order, Questionnaire
from utils import check_user,send_file, create_task, send_message, check_task
from flask_cors import CORS
import threading
import schedule
import time

app = Flask(__name__)
# Разрешаем CORS для всех маршрутов
CORS(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Привязываем db к приложению
db.init_app(app)

with app.app_context():
    db.create_all()



### Orders
@app.route('/')
def index():
    user = check_user(request)
    if user:
        clients = []
        if user.clients != None:
            clients_user = user.clients.split(',')
            clients = Client.query.filter(Client.inn.in_(clients_user)).all()
        articuls = Articuls.query.all()
        managers = User.query.filter(User.username != "admin").all()
        return render_template("index.html", username=user, clients=clients, managers=managers, articuls=articuls)
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



### Kandidat
@app.route('/api/anket', methods=['POST'])
def anket():
    data = request.get_json()

    if not data:
        return jsonify({'error': 'Нет данных'}), 400

    file_id, full_name, vacancy = send_file(data)
    task_id = create_task(file_id, full_name)

    # Сохранение в базу данных
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

    return jsonify({
        'message': 'Анкета успешно получена',
        'data': data  # можно убрать в продакшене
    }), 200

# Фоновая задача — проверка заявок со статусом False
def check_pending_applications():
    with app.app_context():
        try:
            # Получаем все заявки со статусом False
            pending_apps = Questionnaire.query.filter_by(status=False).all()
            for app_record in pending_apps:
                comment = check_task(app_record.task_id)
                if comment != '':
                    # Пытаемся обновить статус ТОЛЬКО если он ещё False
                    updated = Questionnaire.query.filter_by(id=app_record.id, status=False).update({'status': True})
                    db.session.commit()  # коммитим обновление
                    if updated:
                        send_message("chat14886", f"ФИО: {app_record.full_name} \n Должность: {app_record.vacancy} \n Комментарий СБ: {comment} \n\n Анкета: [URL=https://imperial44.bitrix24.ru/bitrix/tools/disk/focus.php?objectId={app_record.file_id}&cmd=show&action=showObjectInGrid&ncc=1]Ссылка[/URL]")
        except Exception as e:
            db.session.rollback()
            print(f"Ошибка при проверке заявок: {e}")

# Фоновый цикл для schedule запуск раз в 1 минуту
def run_scheduler():
    schedule.every(1).minutes.do(check_pending_applications)

    while True:
        schedule.run_pending()
        time.sleep(1)




### TP 1C

@app.route('/api/create_application_tp', methods=['POST'])
def create_application_tp():
    data = request.get_json()

    if not data:
        return jsonify({'error': 'Нет данных'}), 400

    return data

@app.route('/api/delete_application_tp', methods=['POST'])
def delete_application_tp():
    data = request.get_json()

    if not data:
        return jsonify({'error': 'Нет данных'}), 400

    return data

@app.route('/api/update_application_tp', methods=['POST'])
def update_application_tp():
    data = request.get_json()

    if not data:
        return jsonify({'error': 'Нет данных'}), 400

    return data

@app.route('/api/get_application_tp', methods=['POST'])
def get_application_tp():
    data = request.get_json()

    if not data:
        return jsonify({'error': 'Нет данных'}), 400

    return data



# Запуск приложения
if __name__ == '__main__':
    # Запуск Фоновой функции в отдельном потоке при старте приложения
    threading.Thread(target=run_scheduler, daemon=True).start()

    app.run(debug=False, host='0.0.0.0')