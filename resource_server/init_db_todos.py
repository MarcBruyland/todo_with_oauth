import sqlite3

connection = sqlite3.connect('instance/todos.db')  # file path

# create a cursor object from the cursor class
cur = connection.cursor()


cur.execute('''
   CREATE TABLE Todo(
       id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT, 
       uid INTEGER NOT NULL, 
       todo TEXT NOT NULL,
       due TEXT NULL    
   )''')

print("\nDatabase created successfully!!!")
# committing our connection
connection.commit()

# close our connection
connection.close()
