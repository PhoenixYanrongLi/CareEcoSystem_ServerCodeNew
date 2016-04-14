__author__ = 'Brad'

import MySQLdb




x = 'hello'
z = '1'

host = "localhost"
user = "brad"
password = "moxie100"

database_connector = MySQLdb.connect(host=host, user=user, passwd=password)
cur = database_connector.cursor()

sql = 'INSERT INTO test.numpy (letters, numbers) VALUES (%s, %s)'
cur.execute(sql, (x,z))
database_connector.commit()

sql = 'SELECT * FROM test.numpy'

cur.execute(sql)
z = cur.fetchall()[0]
print type(z[1])