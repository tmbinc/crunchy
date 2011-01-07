from twisted.cred import error, credentials
from twisted.cred.checkers import FilePasswordDB, ICredentialsChecker
from twisted.cred.portal import IRealm, Portal
from twisted.internet import defer
from twisted.internet import reactor
from twisted.web.guard import HTTPAuthSessionWrapper, BasicCredentialFactory
from twisted.web.resource import IResource
from twisted.web.resource import Resource
from twisted.web.server import Site
from twisted.web.static import File
from zope.interface import implements

from crunchy.core.workunit import Workunit

class ProjectClientResource(Resource):
	def __init__(self, project, client):
		Resource.__init__(self)
		self.client = client
		self.project = project

class WorkunitRequest(ProjectClientResource):
	def render_GET(self, request):
		workunit = self.project.workunit_provider.get_workunit(self.client)

		if workunit:
			return "%d" % workunit.id
		else:
			# no work left
			return "-1"

class WorkunitFinished(ProjectClientResource):
	def render_GET(self, request):
		try:
			workunit_id = int(request.args["id"][0])
			workunit_results = ''.join(request.args["results"])
		except KeyError, ValueError:
			request.setResponseCode(400)
			return "ILLEGAL INVOKE"

		workunit = Workunit(workunit_id, workunit_results)
		
		if self.project.workunit_provider.put_workunit(workunit, self.client):
			return "OK"
		else:
			request.setResponseCode(400)
			return "NOT PENDING"

class ProjectMeta(ProjectClientResource):
	def render_GET(self, request):
		return self.project.meta.build_meta_string()

class ProjectPage(ProjectClientResource):
	def __init__(self, project, client):
		ProjectClientResource.__init__(self, project, client)
		self.putChild("get", WorkunitRequest(self.project, self.client))
		self.putChild("put", WorkunitFinished(self.project, self.client))
		self.putChild("meta", ProjectMeta(self.project, self.client))
	
	def render_GET(self, request):
		return "Project stats for %s" % self.project.description()

class ProjectRealm(object):
	implements(IRealm)
	
	def __init__(self, project):
		self.project = project

	def requestAvatar(self, avatarId, mind, *interfaces):
		if IResource in interfaces:
			return (IResource, ProjectPage(self.project, avatarId), lambda: None)
		raise NotImplementedError()

class DatabaseAuth(object):
	implements(ICredentialsChecker)
	
	credentialInterfaces = (credentials.IUsernamePassword, )
	
	def __init__(self, userbase):
		self.userbase = userbase

	def requestAvatarId(self, c):
		up = credentials.IUsernamePassword(c, None)
		
		client = self.userbase.authuser(up.username, up.password)
		
		if client:
			return defer.succeed(client)
		else:
			return defer.fail(error.UnauthorizedLogin())

def run_server(project):
	portal = Portal(ProjectRealm(project), [DatabaseAuth(project.userbase)])

	credentialFactory = BasicCredentialFactory(project.description())
	resource = HTTPAuthSessionWrapper(portal, [credentialFactory])
	
	factory = Site(resource)
	reactor.listenTCP(8880, factory)
	reactor.run()
