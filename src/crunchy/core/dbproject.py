import sqlite3
from crunchy.core.dbusers import DatabaseUsers
from crunchy.core.dbworkunitprovider import DatabaseWorkunitProvider
from crunchy.core.workunit import Workunit

def import_by_name(name):
	mod = __import__(name)
	components = name.split('.')
	for comp in components[1:]:
		mod = getattr(mod, comp)
	return mod

def LoadProjectMeta(project):
	module = import_by_name("projects.%s.server" % project)
	obj = getattr(module, "ProjectMeta")
	return obj

class DatabaseProject:
	TABLE_META = "meta"

	def __init__(self, id):
		self.id = id
		self.db = None
		self.connect()

	def connect(self):
		self.db = sqlite3.connect(self.id)
		assert self.db, Exception("Couldn't connect to database")
		self.userbase = DatabaseUsers(self.db)
		self.workunit_provider = DatabaseWorkunitProvider(self.db)
		self.type = self.get_meta("type", None)
		if self.type:
			self.build_meta()

	def build_meta(self, project_config = None):
		self.meta = LoadProjectMeta(self.type)(self, project_config)

	def initialize(self, project_type, project_config):
		self.userbase.create()
		self.initialize_meta()
		self.type = project_type
		self.set_meta("type", project_type)
		self.build_meta(project_config)
		self.workunit_provider.create(self.meta.get_number_of_workunits())

	def initialize_meta(self):
		c = self.db.cursor()
		try:
			c.execute("drop table %s" % self.TABLE_META)
		except sqlite3.OperationalError:
			pass
		c.execute("create table %s (key string, value string);" % self.TABLE_META)
		self.db.commit()

	def description(self):
		return self.id

	def set_meta(self, key, value):
		c = self.db.cursor()
		c.execute("delete from %s where key=?" % self.TABLE_META, (key,))
		c.execute("insert into %s values (?, ?)" % self.TABLE_META, (key, value))
		self.db.commit()

	def get_meta(self, key, default = None):
		c = self.db.cursor()
		try:
			c.execute("select value from %s where key=?" % self.TABLE_META, (key,))
		except sqlite3.OperationalError:
			return None
		row = c.fetchone()
		if not row:
			return default
		return str(row[0])
