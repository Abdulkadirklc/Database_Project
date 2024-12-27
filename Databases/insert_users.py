import requests

# API URL
API_URL = "http://127.0.0.1:5000/users"

# List of users to insert
users = [
    {"username": "Abdulkadir", "email": "abdulkadirkk42@gmail.com", "password": "password123", "bio": "Doğa sever"},
    {"username": "Ahmet", "email": "ahmett52@gmail.com", "password": "password456", "bio": "Sporcu"},
    {"username": "Emre", "email": "emre34@gmail.com", "password": "password789", "bio": "Yazılım geliştiricisi"},
    {"username": "Serpil", "email": "serpil@gmail.com", "password": "password101", "bio": "Kitap okumayı severim"},
    {"username": "Arda", "email": "ardagüler@gmail.com", "password": "password112", "bio": "Sinema tutkunu ve gezgin"},
    {"username": "Ayşe", "email": "ayse@gmail.com", "password": "password131", "bio": "Usmanım"},
    {"username": "Zeynep", "email": "zeyno@gmail.com", "password": "password415", "bio": "Sosyal medya ve dijital pazarlama uzmanı"},
    {"username": "Arda Utku", "email": "ardautku@gmail.com", "password": "pw124235346", "bio": "Profesyonel tenis oyuncusu"},
    {"username": "Efekan", "email": "efkn@gmail.com", "password": "pssw234wetr36", "bio": "Kitap kurdu"},
    {"username": "Mete", "email": "egmt@gmail.com", "password": "12345", "bio": "İlkel teknolojiler meraklısı"},
    {"username": "Utku", "email": "utku@gmail.com", "password": "sst3424146", "bio": "CEO @qFin"},
]

def insert_users():
    for user in users:
        response = requests.post(API_URL, json=user)
        if response.status_code == 201:
            print(f"User {user['username']} created successfully.")
        else:
            print(f"Failed to create user {user['username']}. Error: {response.text}")

if __name__ == "__main__":
    insert_users()
