import bcrypt
import sqlite3

class DatabaseUsers:
	TABLE_USERS = "users"

	def __init__(self, db):
		self.db = db
		
	def create(self):
		c = self.db.cursor()
		
		try:
			c.execute("drop table %s" % self.TABLE_USERS)
		except sqlite3.OperationalError:
			pass
		
		c.execute("create table %s (client integer primary key autoincrement, username string unique, password string);" % self.TABLE_USERS)
		self.db.commit()

	def adduser(self, username, password):
		hashed = bcrypt.hashpw(password, bcrypt.gensalt(6))
		c = self.db.cursor()
		
		try:
			c.execute("insert into %s values (NULL, ?, ?)" % self.TABLE_USERS, (username, hashed))
		except sqlite3.IntegrityError:
			return None
		self.db.commit()

		return c.lastrowid

	def authuser(self, username, password):
		c = self.db.cursor()
		c.execute("select password from %s where username = ?;" % self.TABLE_USERS, (username,))
		row = c.fetchone()
		if not row:
			return False
		
		return bcrypt.hashpw(password, row[0]) == row[0]

	def listusers(self):
		c = self.db.cursor()
		c.execute("select client, username from %s" % self.TABLE_USERS)
		return c.fetchall()
		
