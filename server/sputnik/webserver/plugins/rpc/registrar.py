from sputnik import config
from sputnik import observatory

debug, log, warn, error, critical = observatory.get_loggers("rpc_registrar")

from sputnik.plugin import PluginException
from sputnik.webserver.plugin import ServicePlugin, schema

from twisted.internet.defer import inlineCallbacks, returnValue
from autobahn import wamp

class RegistrarService(ServicePlugin):
    def __init__(self):
        ServicePlugin.__init__(self)

    def init(self):
        self.administrator = self.require("sputnik.webserver.plugins.backend.administrator.AdministratorProxy")
    
    @wamp.register(u"rpc.registrar.make_account")
    @schema("public/registrar.json#make_account")
    @inlineCallbacks
    def make_account(self, username, password, email, nickname, locale=None):
        try:
            result = yield self.administrator.proxy.make_account(username, password)
            if result:
                profile = {"email": email, "nickname": nickname,
                           "locale": locale}
                yield self.administrator.change_profile(username, profile)
                returnValue([True, username])
        except Exception, e:
            returnValue([False, e.args])

    @wamp.register(u"rpc.registrar.get_reset_token")
    @schema("public/registrar.json#get_reset_token")
    @inlineCallbacks
    def get_reset_token(self, username):
        try:
            result = yield self.administrator.proxy.get_reset_token(username)
            log("Generated password reset token for user %s." % username)
            returnValue([True, None])
        except Exception, e:
            error("Failed to generate password reset token for user %s." % \
                    username)
            error(e)
            returnValue([False, e.args])

    @wamp.register(u"rpc.registrar.change_password_token")
    @schema("public/registrar.json#change_password_token")
    @inlineCallbacks
    def get_reset_token(self, username, hash, token):
        try:
            result = yield self.administrator.proxy.reset_password_hash(username,
                    None, hash, token=token)
            log("Reset password using token for user %s." % username)
            returnValue([True, None])
        except Exception, e:
            error("Failed to reset password using token for user %s." % \
                    username)
            error(e)
            returnValue([False, e.args])

