import config

from optparse import OptionParser
parser = OptionParser()
parser.add_option("-c", "--config", dest="filename",
    help="config file", default="../config/sputnik.ini")
(options, args) = parser.parse_args()
if options.filename:
    config.reconfigure(options.filename)

import re
import datetime

__author__ = 'satosushi'

"""
The risk manager manages the financial risk taken by the exchange when extending trading margins.
For now this just means pinging the accountant regularly to see if everyone's margin is in check
"""


from sqlalchemy.orm.exc import NoResultFound
import zmq
import models
import database
import smtplib
import margin
from email.mime.text import MIMEText

from twisted.python import log

NAP_TIME_SECONDS = 10

def email_user(user, cash_position, low_margin, high_margin, severe):
    """

    :param user:
    :type user: User
    :param cash_position:
    :type cash_position: int
    :param low_margin:
    :type low_margin: int
    :param high_margin:
    :type high_margin: int
    :param severe:
    :type severe: bool
    """
    content = open("margin_call_email.txt" if severe else "low_margin_email.txt", "r").read()

    content = re.sub("@NICKNAME", user.nickname, content)
    content = re.sub("@CASH", "%.8f" % (cash_position / 1e8), content)
    content = re.sub("@HIGH_MARGIN", "%.8f" % (high_margin / 1e8), content)
    content = re.sub("@LOW_MARGIN", "%.8f" % (low_margin / 1e8), content)

    msg = MIMEText(content)
    msg['Subject'] = 'Margin called' if severe else 'Low margin warning!'
    msg['From'] = 'Sputnik market'
    msg['To'] = user.nickname
    s = smtplib.SMTP('localhost')
    s.sendmail('sputnik@sputnikmkt.com', [user.email], msg.as_string())

if __name__ == "__main__":

    session = database.make_session()

    context = zmq.Context()
    safe_price_subscriber = context.socket(zmq.SUB)
    safe_price_subscriber.connect(config.get("safe_price_forwarder", "zmq_backend_address"))


    btc = session.query(models.Contract).filter_by(ticker='BTC').one()


    low_margin_users = {}
    bad_margin_users = {}

    # main loop
    while True:

        # todo we should loop on the union of of safe price and message from the accountant asking us to take action
        safe_prices = safe_price_subscriber.recv_json()
        for user in session.query(models.User).filter_by(active=True):

            low_margin, high_margin = margin.calculate_margin(user.username, session, safe_prices)
            cash_position = session.query(models.Position).filter_by(contract=btc, user=user).one()

            if cash_position < low_margin:
                if user.username not in bad_margin_users:
                    bad_margin_users[user.username] = datetime.datetime.utcnow()
                    email_user(user, cash_position, high_margin, severe=True)
                    log.msg("user %s's margin is below the low limit, margin call" % user.username)

            elif cash_position < high_margin:
                if user.username not in low_margin_users:
                    low_margin_users[user.username] = datetime.datetime.utcnow()
                    email_user(user, cash_position, high_margin, severe=False)
                    log.msg("user %s's margin is low, sending a warning" % user.username)

            else:
                del low_margin_users[user.username] # resolved
                del bad_margin_users[user.username] # resolved
                log.msg("user %s's margin is fine and dandy" % user.username)



