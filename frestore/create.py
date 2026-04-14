import firebase_admin
from firebase_admin import credentials, firestore

cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred)

db = firestore.client()

doc = {
  "name": "施富傑",
  "mail": "fuhojesse@gmail.com",
  "lab": 666
}

doc = {
  "name": "施富傑2",
  "mail": "fuhojesse@gmail.com",
  "lab": 777
}

doc = {
  "name": "施富傑3",
  "mail": "fuhojesse@gmail.com",
  "lab": 777
}

docs = [
{
  "name": "陳武林",
  "mail": "wlchen@pu.edu.tw",
  "lab": 665
},

{
  "name": "王耀德",
  "mail": "ytwang@pu.edu.tw",
  "lab": 686
},

{
  "name": "康贊清",
  "mail": "tckang@pu.edu.tw",
  "lab": 783
}
]



# doc_ref = db.collection("靜宜資管2026a").document("tcyang")
# doc_ref.set(doc)

collection_ref = db.collection("靜宜資管2026a")
for doc in docs:
  collection_ref.add(doc)
