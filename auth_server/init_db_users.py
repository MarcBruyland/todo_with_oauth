import sqlite3

connection = sqlite3.connect('instance/users.db')  # file path

# create a cursor object from the cursor class
cur = connection.cursor()

cur.execute('''
   CREATE TABLE User(
       id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT, 
       email TEXT NOT NULL, 
       password TEXT NOT NULL
   )''')

print("\nDatabase created successfully!!!")
# committing our connection
connection.commit()

# close our connection
connection.close()
