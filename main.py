from flask import Flask, request, render_template, redirect, url_for
from datetime import datetime

app = Flask(__name__)

# Список для хранения заявок
applications = []
comments = []

class Application:

    STATUS_PENDING = "в ожидании"
    STATUS_IN_PROGRESS = "в процессе"
    STATUS_CLOSED = "закрыта"


    def __init__(self, application_id, date_added, equipment, fault_type, problem_description, client, status, responsible, executor):
        self.application_id = application_id
        self.date_added = date_added
        self.equipment = equipment
        self.fault_type = fault_type
        self.problem_description = problem_description
        self.client = client
        self.status = status  # Статус заявки
        self.responsible = responsible
        self.executor = executor
        self.date_closed = None  # Время закрытия заявки

    def close(self):
        self.status = 'закрыта'
        self.date_closed = datetime.now()

    def get_duration(self):
        if hasattr(self, 'total_duration'):
            return self.total_duration  # Возвращаем общее время выполнения в секундах
        return None  # Если заявка еще не закрыта
        
class Comment:
    def __init__(self, application_id, text, date_added):
        self.application_id = application_id
        self.text = text
        self.date_added = date_added

    def to_dict(self):
        return {
            'application_id': self.application_id,
            'text': self.text,
            'date_added': self.date_added,
        }

@app.route('/')
def index():
    filter_id = request.args.get('filter')
    filtered_applications = applications

    if filter_id:
        filtered_applications = [app for app in applications if app.application_id == filter_id]

    return render_template('index.html', applications=filtered_applications)

@app.route('/applications/new', methods=['GET', 'POST'])
def new_application():
    if request.method == 'POST':
        data = request.form
        new_application = Application(
            application_id=data['application_id'],
            date_added=datetime.now(),  # Устанавливаем текущее время
            equipment=data['equipment'],
            fault_type=data['fault_type'],
            problem_description=data['problem_description'],
            client=data['client'],
            status='в ожидании',  # Начальный статус
            responsible=data['responsible'],
            executor=data['executor']
        )
        applications.append(new_application)
        return redirect(url_for('index'))
    return render_template('new_application.html')

@app.route('/applications/edit/<application_id>', methods=['GET', 'POST'])
def edit_application(application_id):
    application = next((app for app in applications if app.application_id == application_id), None)
    if request.method == 'POST':
        if application:
            data = request.form
            # Обновляем статус заявки
            application.status = data.get('status', application.status)
            application.problem_description = data.get('problem_description', application.problem_description)
            application.responsible = data.get('responsible', application.responsible)
            application.executor = data.get('executor', application.executor)
            return redirect(url_for('index'))  # Возвращаемся к главной странице
        return 'Заявка не найдена', 404
    return render_template('edit_application.html', application=application, Application=Application)

@app.route('/applications/delete/<application_id>', methods=['POST'])
def delete_application(application_id):
    global applications
    application = next((app for app in applications if app.application_id == application_id), None)
    if application:
        applications = [app for app in applications if app.application_id != application_id]
        return redirect(url_for('index'))  # Возвращаемся к главной странице
    return 'Заявка не найдена', 404

@app.route('/applications/comments/<application_id>', methods=['GET', 'POST'])
def application_comments(application_id):
    # Находим заявку по ID
    application = next((app for app in applications if app.application_id == application_id), None)
    
    if request.method == 'POST':
        # Добавление нового комментария
        comment_text = request.form.get('comment')
        if comment_text:
            new_comment = Comment(
                application_id=application.application_id,
                text=comment_text,
                date_added=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            )
            comments.append(new_comment)

        return redirect(url_for('application_comments', application_id=application_id))

    if application:
        # Получаем комментарии, связанные с текущей заявкой
        related_comments = [c for c in comments if c.application_id == application_id]
        return render_template('comments.html', comments=related_comments, application_id=application_id)
    
    return 'Заявка не найдена', 404

@app.route('/applications/close/<application_id>', methods=['GET', 'POST'])
def close_application(application_id):
    application = next((app for app in applications if app.application_id == application_id), None)
    if application:
        if request.method == 'POST':
            minutes = int(request.form.get('minutes', 0))
            seconds = int(request.form.get('seconds', 0))
            total_duration = minutes * 60 + seconds  # Конвертируем все в секунды
            
            application.close()  # Закрываем заявку
            application.total_duration = total_duration  # Сохраняем общее время выполнения
            
            return redirect(url_for('index'))  # Возвращаемся к главной странице
        return render_template('close_application.html', application=application)  # Отображаем форму для закрытия
    return 'Заявка не найдена', 404

@app.route('/statistics')
def statistics():
    completed_applications = [app for app in applications if app.status == 'закрыта']
    total_completed = len(completed_applications)
    total_duration_seconds = 0
    for app in completed_applications:
        duration_seconds = app.get_duration()
        if duration_seconds is not None:
            total_duration_seconds += duration_seconds
    average_duration_seconds = total_duration_seconds / total_completed if total_completed > 0 else 0

    # Преобразуем среднее время в минуты и секунды
    average_minutes = average_duration_seconds // 60
    average_seconds = average_duration_seconds % 60

    # Печатаем результаты в консоль
    print(f"Total completed applications: {total_completed}")
    print(f"Total duration seconds: {total_duration_seconds}")
    print(f"Average duration: {average_minutes} минут(ы) {average_seconds} секунд(ы)")

    fault_types = {}
    for app in applications:
        if app.fault_type in fault_types:
            fault_types[app.fault_type] += 1
        else:
            fault_types[app.fault_type] = 1

    return render_template('statistics.html',
                           total_completed=total_completed,
                           average_minutes=average_minutes,
                           average_seconds=average_seconds,
                           fault_types=fault_types)

if __name__ == '__main__':
    app.run(debug=True)