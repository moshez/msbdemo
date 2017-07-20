from __future__ import absolute_import

import os

import pkg_resources

from zope import interface

from twisted.python import usage, reflect, threadpool, filepath
from twisted import plugin
from twisted.application import service, strports, internet
from twisted.web import wsgi, server, static, resource
from twisted.internet import reactor

import sayhello.wsgi

class Options(usage.Options):
    optParameters = [["port", None, None,
                      "port on which to listen (strports format)"],
                    ]

@interface.implementer(service.IServiceMaker, plugin.IPlugin)
class ServiceMaker(object):
    tapname = "sayhello"
    description = "Greet people nicely"
    options = Options

    def makeService(self, options):
        application = sayhello.wsgi.app
        pool = threadpool.ThreadPool()
        reactor.callWhenRunning(pool.start)
        reactor.addSystemEventTrigger('after', 'shutdown', pool.stop)
        root = wsgi.WSGIResource(reactor, pool, application)
        site = server.Site(root)
        return strports.service(options['port'], site)

serviceMaker = ServiceMaker()
