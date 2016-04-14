__author__ = 'Brad'


from sklearn import svm
from sklearn import datasets
import MySQLdb

clf = svm.SVC()
iris = datasets.load_iris()
X, y = iris.data, iris.target
print clf.fit(X, y)

import pickle
s = pickle.dumps(clf)

host = "localhost"
user = "brad"
password = "moxie100"

database_connector = MySQLdb.connect(host=host, user=user, passwd=password)
cur = database_connector.cursor()

print len(s)

# sql = "INSERT INTO test.scikit (scikitobj) VALUES (%s)"
# cur.execute(sql, [s])
# database_connector.commit()

sql = "SELECT scikitobj FROM test.scikit"

cur.execute(sql)
clf2 = cur.fetchall()
clf2 = clf2[0][0]
clf2 = pickle.loads(clf2)
print clf2
print clf2 == clf