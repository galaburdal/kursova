import time
import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton
from datetime import datetime, timedelta
import mysql.connector

BOT_TOKEN = '6538792811:AAHZG4slG-QD7MRXTQAX5jwbdSFMZkUwlk4'

bot = telebot.TeleBot(BOT_TOKEN)

db_connection = mysql.connector.connect(
    host="localhost",
    user="root",
    password="",
    database="chatbot_db"
)
cursor = db_connection.cursor()

projects = {}
language = {}

# Реєстрація користувача
def register_user(chat_id, username):
    cursor.execute("INSERT INTO users (chat_id, username) VALUES (%s, %s) ON DUPLICATE KEY UPDATE username = VALUES(username)",
                   (chat_id, username))
    db_connection.commit()

# Додавання проекту
def add_project(user_id, project_name, project_type, deadline):
    cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
    user_exists = cursor.fetchone()

    if user_exists:
        cursor.execute("INSERT INTO projects (user_id, name, project_type, deadline) VALUES (%s, %s, %s, %s)",
                       (user_id, project_name, project_type, deadline))
        db_connection.commit()
    else:
        print(f"Error: User with id {user_id} does not exist.")

# Отримання проектів користувача
def get_user_projects(user_id):
    cursor.execute("SELECT name, deadline FROM projects WHERE user_id = %s", (user_id,))
    user_projects = cursor.fetchall()
    print("User Projects from get_user_projects:", user_id, user_projects)
    return user_projects

# Функція для перевірки існування користувача
def user_exists(user_id):
    cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
    return cursor.fetchone() is not None

# Функція для перевірки дедлайнів та надсилання повідомлень
def check_deadline(user_id, selected_language):
    now = datetime.now()
    user_projects = get_user_projects_from_database(user_id)

    for project_data in user_projects:
        deadline_date = datetime.strptime(project_data['deadline'], "%Y-%b-%d")
        remaining_days = (deadline_date - now).days

        if remaining_days <= 5:
            bot.send_message(user_id, f"Нагадування: Залишилося {remaining_days} днів до дедлайну для проекту {project_data['name']}.")

    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row(KeyboardButton('/add_project'))

    bot.send_message(user_id, f'Ви вибрали мову: {selected_language}', reply_markup=markup)

# Редагування проекту в базі даних
def edit_project_in_database(user_id, project_name, new_project_name, new_project_type, new_deadline):
    if user_exists(user_id):
        cursor.execute("SELECT * FROM projects WHERE user_id = %s AND name = %s", (user_id, project_name))
        existing_project = cursor.fetchone()

        if existing_project:
            cursor.execute("UPDATE projects SET name = %s, project_type = %s, deadline = %s WHERE user_id = %s AND name = %s",
                           (new_project_name, new_project_type, new_deadline, user_id, project_name))
            db_connection.commit()
            return True
        else:
            print(f"Error: Project with name {project_name} does not exist for user {user_id}.")
            return False
    else:
        print(f"Error: User with id {user_id} does not exist.")
        return False

# Функція для отримання проектів користувача з бази даних
def get_user_projects_from_database(user_id):
    cursor.execute("SELECT name, project_type, deadline FROM projects WHERE user_id = %s", (user_id,))
    return cursor.fetchall()

# Команда для старту
@bot.message_handler(commands=['start', 'hello'])
def start(message):
    user_id = message.from_user.id
    username = message.from_user.username
    register_user(user_id, username)

    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row(KeyboardButton('Українська'))

    bot.send_message(user_id, "Hello!", reply_markup=markup)
    bot.send_message(user_id, "Виберіть мову:")

# Обробник для вибору мови
@bot.message_handler(func=lambda message: message.text == 'Українська' and language.get(message.from_user.id) is None)
def select_language(message):
    user_id = message.from_user.id
    selected_language = message.text
    language[user_id] = selected_language
    check_deadline(user_id, selected_language)

# Функція для додавання нового проекту
@bot.message_handler(commands=['add_project'])
def add_project_command(message):
    user_id = message.from_user.id
    projects[user_id] = {'name': '', 'type': '', 'deadline': ''}
    bot.send_message(user_id, "Введіть ім'я проекту:")

# Обробник для отримання імені проекту
@bot.message_handler(func=lambda message: projects.get(message.from_user.id) and not projects[message.from_user.id]['name'])
def get_project_name(message):
    user_id = message.from_user.id
    projects[user_id]['name'] = message.text
    bot.send_message(user_id, "Введіть тип роботи:")

# Обробник для отримання типу роботи
@bot.message_handler(func=lambda message: projects.get(message.from_user.id) and not projects[message.from_user.id]['type'])
def get_project_type(message):
    user_id = message.from_user.id
    projects[user_id]['type'] = message.text
    bot.send_message(user_id, "Введіть дедлайн (термін виконання, в такому порядку YYYY-MMM):")

# Обробник для отримання дедлайну
@bot.message_handler(func=lambda message: projects.get(message.from_user.id) and not projects[message.from_user.id]['deadline'])
def get_project_deadline(message):
    user_id = message.from_user.id
    projects[user_id]['deadline'] = message.text

    print("User Info before adding project:", user_id, projects[user_id])

    add_project(user_id, projects[user_id]['name'], projects[user_id]['type'], projects[user_id]['deadline'])

    project_info = f"Ім'я: {projects[user_id]['name']}, Тип: {projects[user_id]['type']}, Дедлайн: {projects[user_id]['deadline']}"
    if language.get(user_id) == 'Українська':
        bot.send_message(user_id, f"Проект додано! {project_info}")

# Запуск перевірки дедлайну кожні 24 години
bot.polling(none_stop=True, timeout=10)
