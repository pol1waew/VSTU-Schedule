import requests

base_url = "http://localhost:8000"


# Например, получим доступ ко всем занятиям. Запросы выборки, фильтрации не требуют авторизацию
r = requests.get(f"{base_url}/api/events")
print(r.json())


# Теперь, чтобы получить доступ к редактированию и удалению, нужно авторизоваться (ваш аккаунт должен быть администратором)
# Текущая реализация авторизации на токенах - простая. Для реальных проектов стоит использовать более защищенное решение
# На production с текущим решением обязательно должен быть HTTPS!

# Проводим авторизацию и получаем токен
r = requests.post(
    f"{base_url}/api/obtain-token/", data={"username": "brookit", "password": "1234"}
)
my_token = r.json()["token"]

# Сформируем заголовок с полученым токеном авторизации
headers = {"Authorization": f"Token {my_token}"}

# Например, удалим следующую запись
r = requests.delete(f"{base_url}/api/events/13/", headers=headers)
assert r.status_code == 200

# Также можно редактировать данные с помощью методов HTTP - PUT и PATCH.
# PUT - для полного обновления записи по айди, PATCH - для частичного обновления записи

data = {
    "id": 1,
    "faculty": "ФЭВТ",
    "scope": "bachelor",
    "course": 3,
    "years": "2024-2025",
    "semester": 2,
    "start_date": "2025-02-10",
    "finish_date": "2025-06-01",
}

r = requests.put(f"{base_url}/api/schedules/1", data=data, headers=headers)
assert r.status_code == 200

data = {"id": 1, "faculty": "ФАТ"}
r = requests.patch(f"{base_url}/api/schedules/1", data=data, headers=headers)
assert r.status_code == 200
