import mysql.connector
from datetime import datetime

db_connection = mysql.connector.connect(
    host="localhost",
    user="root",
    password="",  
    database="chatbot_db"
)
cursor = db_connection.cursor()

# Реєстрація користувача
def register_user(chat_id, username):
    cursor.execute("INSERT INTO users (chat_id, username) VALUES (%s, %s)", (chat_id, username))
    db_connection.commit()

# Додавання проекту
def add_project(user_id, project_type, project_name, deadline):
    cursor.execute("INSERT INTO projects (user_id, name, deadline) VALUES (%s, %s, %s)", (user_id, project_name, deadline))
    db_connection.commit()

# Отримання проектів користувача
def get_user_projects(user_id):
    cursor.execute("SELECT name, deadline FROM projects WHERE user_id = %s", (user_id,))
    return cursor.fetchall()

cursor.close()
db_connection.close()
