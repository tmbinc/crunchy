import sqlite3
import bcrypt

from workunit import Workunit

DatabaseError = sqlite3.OperationalError

class DatabaseWorkunitProvider:
	TABLE_WORKUNITS = "workunits"
	TABLE_RESULTS = "results"

	def __init__(self, db):
		self.db = db
		
	def create(self, nr_workunits):
		c = self.db.cursor()
		for table in [self.TABLE_WORKUNITS, self.TABLE_RESULTS]:
			try:
				c.execute('''drop table %s''' % table)
			except DatabaseError:
				pass
		c.execute('''create table %s (id integer not null, client integer, submitted date, finished date)''' % self.TABLE_WORKUNITS)
		c.execute('''create table %s (id integer not null, result blob not null)''' % self.TABLE_RESULTS)
		
		workunits = [Workunit(i) for i in range(nr_workunits)]
		c.executemany('''insert into %s (id) values (?)''' % self.TABLE_WORKUNITS, [(workunit.id,) for workunit in workunits])
		self.db.commit()
	
	def get_workunit(self, client):
		c = self.db.cursor()
		
		while True:
			# get a workunit id
			c.execute("select id from %s where submitted is null limit 1" % self.TABLE_WORKUNITS)
		
			row = c.fetchone()
			if not row:
				return None
			
			id = row[0]

			try:
				c.execute("update %s set client = ?, submitted = datetime() where id = ? and client is null" % self.TABLE_WORKUNITS, (client, id,))
				if c.rowcount == 0:
					continue
				self.db.commit()
			except DatabaseError:
				self.db.rollback()
				continue
		
			return Workunit(id)

	def put_workunit(self, workunit, client):
		c = self.db.cursor()
		c.execute("update %s set finished = datetime() where id = ? and client = ? and finished is null" % self.TABLE_WORKUNITS, (workunit.id, client))
		if c.rowcount == 0:
			print "not pending: id=%d, client=%d" % (workunit.id, client)
			return False
		
		c.execute("insert into %s values (?, ?)" % self.TABLE_RESULTS, (workunit.id, workunit.results_as_blob()))

		self.db.commit()
		print "finished workunit %d" % workunit.id
		return True

	def results(self):
		c = self.db.cursor()
		c.execute("select * from %s" % self.TABLE_RESULTS)
		return [Workunit(*i) for i in c.fetchall()]

	def pending(self):
		c = self.db.cursor()
		c.execute("select * from %s where submitted is not null and finished is null" % self.TABLE_WORKUNITS)
		return [(Workunit(i[0]), i[1], i[2]) for i in c.fetchall()]

	def expire_pending(self, expiration):
		c = self.db.cursor()
		
		c.execute("update %s set submitted = null, client = null where submitted is not null and submitted < datetime('now','-%d seconds') and finished is null;" % (self.TABLE_WORKUNITS, expiration))
		self.db.commit()

	def progress(self):
		c = self.db.cursor()
		c.execute("select count(*) from %s where submitted is null;" % self.TABLE_WORKUNITS)
		nworkunits = c.fetchone()[0]
		c.execute("select count(*) from %s where submitted is not null and finished is null;" % self.TABLE_WORKUNITS)
		nworkunits_pending = c.fetchone()[0]
		c.execute("select count(*) from %s where finished is not null;" % self.TABLE_WORKUNITS)
		nworkunits_finished = c.fetchone()[0]

		return nworkunits, nworkunits_pending, nworkunits_finished
