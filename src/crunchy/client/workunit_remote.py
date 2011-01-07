from crunchy.core.workunit import Workunit
import urllib2

class RemoteWorkunitProvider:
	def __init__(self, project, url, username, password):
		self.url = url
		self.username = username
		self.password = password
		
		auth_handler = urllib2.HTTPBasicAuthHandler()
		auth_handler.add_password(realm = project, uri = url, user = username, passwd = password)
		opener = urllib2.build_opener(auth_handler)
		urllib2.install_opener(opener)
		
	def get_workunit(self):
		id = int(urllib2.urlopen(self.url + "/get").read())
		if id < 0:
			return None
		return Workunit(id)

	def put_workunit(self, workunit):
		url = self.url + "/put?id=%d&results=%s" % (workunit.id, workunit.results_as_blob())
		assert urllib2.urlopen(url).read() == "OK"

	# haxx haxx haxx
	def get_meta(self):
		print "open", self.url + "/meta"
		return urllib2.urlopen(self.url + "/meta").read()
