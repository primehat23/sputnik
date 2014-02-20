import sys
from pprint import pprint

from twisted.python import log
from twisted.internet import reactor, ssl

from autobahn.websocket import connectWS
from autobahn.wamp import WampClientFactory, WampCraClientProtocol

class TradingBot(WampCraClientProtocol):
    """
   Authenticated WAMP client using WAMP-Challenge-Response-Authentication ("WAMP-CRA").

   """

    def __init__(self):
        self.base_uri = "ws://localhost:8000"
        self.username = 'testuser1'
        self.password = 'testuser1'
        self.markets = {}
        self.orders = {}

    def action(self):
        '''
        overwrite me
        '''
        return True

    """
    reactive events - on* 
    """

    def onSessionOpen(self):
        ## "authenticate" as anonymous
        ##
        #d = self.authenticate()
        self.getMarkets()
        self.subChat()
        ## authenticate as "foobar" with password "secret"
        ##
        d = self.authenticate(authKey=self.username,
                              authExtra=None,
                              authSecret=self.password)

        d.addCallbacks(self.onAuthSuccess, self.onAuthError)

    def onClose(self, wasClean, code, reason):
        reactor.stop()

    def onAuthSuccess(self, permissions):
        print "Authentication Success!", permissions
        self.subOrders()
        self.subFills()

        self.startAutomation()


    def onAuthError(self, e):
        uri, desc, details = e.value.args
        print "Authentication Error!", uri, desc, details

    def onMarkets(self, event):
        pprint(event)
        self.markets = event[1]
        for ticker, contract in self.markets.iteritems():
            if contract['contract_type'] != "cash":
                self.subBook(ticker)
                self.subTrades(ticker)
                self.subSafePrices(ticker)
        return event

    def onBook(self, topicUri, event):
        """
        overwrite me
        """
        pprint(["Book: ", topicUri, event])

    def onTrade(self, topicUri, event):
        """
        overwrite me
        """
        pprint(["Trade: ", topicUri, event])

    def onSafePrice(self, topicUri, event):
        """
        overwrite me
        """
        pprint(["SafePrice", topicUri, event])

    def onOpenOrders(self, event):
        pprint(event)
        self.orders = event[1]

    def onOrder(self, topicUri, order):
        """
        overwrite me
        """
        id = order['id']
        if id in self.orders and (order['is_cancelled'] or order['quantity_left'] == 0):
            del self.orders[id]
        else:
            if order['quantity_left'] > 0:
                self.orders[id] = order

        pprint(["Order", topicUri, order])

    def onFill(self, topicUri, event):
        """
        overwrite me
        """
        pprint(["Fill", topicUri, event])

    def onChat(self, topicUri, event):
        pprint(["Chat", topicUri, event])

    def onPlaceOrder(self, event):
        pprint(event)

    """
    Subscriptions
    """
    def subOrders(self):
        uri = "%s/feeds/orders#%s" % (self.base_uri, self.username)
        self.subscribe(uri, self.onOrder)
        print 'subscribed to: ', uri

    def subFills(self):
        uri = "%s/feeds/fills#%s" % (self.base_uri, self.username)
        self.subscribe(uri, self.onFill)
        print 'subscribed to: ', uri

    def subBook(self, ticker):
        uri = "%s/feeds/book#%s" % (self.base_uri, ticker)
        self.subscribe(uri, self.onBook)
        print 'subscribed to: ', uri

    def subTrades(self, ticker):
        uri = "%s/feeds/trades#%s" % (self.base_uri, ticker)
        self.subscribe(uri, self.onTrade)
        print 'subscribed to: ', uri

    def subSafePrices(self, ticker):
        uri = "%s/feeds/safe_prices#%s" % (self.base_uri, ticker)
        self.subscribe(uri, self.onSafePrice)
        print 'subscribed to: ', uri

    def subChat(self):
        uri = "%s/feeds/chat" % self.base_uri
        self.subscribe(uri, self.onChat)
        print 'subscribe to: ', uri

    """
    RPC calls
    """

    def getNewAddress(self):
        d = self.call(self.base_uri + "/rpc/get_new_address")
        d.addBoth(pprint)

    def getPositions(self):
        d = self.call(self.base_uri + "/rpc/get_positions")
        d.addBoth(pprint)

    def getMarkets(self):
        d = self.call(self.base_uri + "/rpc/get_markets")
        d.addBoth(self.onMarkets)

    def getOrderBook(self, ticker):
        d = self.call(self.base_uri + "/rpc/get_order_book", ticker)
        d.addBoth(pprint)

    def getOpenOrders(self):
        # store cache of open orders update asynchronously
        d = self.call(self.base_URI + "/rpc/get_open_orders")
        d.addBoth(self.onOpenOrders)

    def placeOrder(self, ticker, quantity, price, side):
        ord= {}
        ord['contract'] = ticker
        ord['quantity'] = quantity
        ord['price'] = price
        ord['side'] = side
        print "inside place order", ord
        print self.base_uri + "/rpc/place_order"
        d = self.call(self.base_uri + "/rpc/place_order", ord)
        d.addBoth(self.onPlaceOrder)

    def chat(self, message):
        print "chatting: ", message
        self.publish(self.base_uri + "/feeds/chat", message)

    def cancelOrder(self, id):
        """
        cancels an order by its id.
        :param id: order id
        """
        print "inside cancel order"
        d = self.call(self.base_uri + "/rpc/cancel_order", id)
        d.addBoth(pprint)


if __name__ == '__main__':

    if len(sys.argv) > 1 and sys.argv[1] == 'debug':
        log.startLogging(sys.stdout)
        debug = True
    else:
        debug = False

    log.startLogging(sys.stdout)
    factory = WampClientFactory("ws://localhost:8000", debugWamp=debug)
    factory.protocol = TradingBot

    # null -> ....
    if factory.isSecure:
        contextFactory = ssl.ClientContextFactory()
    else:
        contextFactory = None

    connectWS(factory, contextFactory)
    reactor.run()