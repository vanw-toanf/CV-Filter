import firebase_admin
from firebase_admin import credentials, firestore, storage

cred = credentials.Certificate("cv-filter-1e64b-firebase-adminsdk-fbsvc-c2e55541d5.json")

# Khởi tạo ứng dụng Firebase
firebase_admin.initialize_app(cred, {
    'storageBucket': 'cv-filter-1e64b.appspot.com'
})

db = firestore.client()
bucket = storage.bucket()

print("✅ Firebase Connected!")