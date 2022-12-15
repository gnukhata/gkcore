import logging
import gkcore
import jwt
import traceback
from gkcore.models import gkdb
from sqlalchemy.sql import select
from Crypto.PublicKey import RSA


def gk_log(name: str = __name__):
    """
    A wrapper around python's logging library, created for easy use across gkcore to log events
    Supports all `logging` module's methods. First argument must be `__name__`
    """
    return logging.getLogger(name)


def generateAuthToken(con, tokenItems, tokenType="userorg"):
    try:
        result = con.execute(select([gkdb.signature]))
        sign = result.fetchone()
        if sign == None:
            key = RSA.generate(2560)
            privatekey = key.exportKey("PEM")
            sig = {"secretcode": privatekey}
            gkcore.secret = privatekey
            result = con.execute(gkdb.signature.insert(), [sig])
        elif len(sign["secretcode"]) <= 20:
            result = con.execute(gkdb.signature.delete())
            if result.rowcount == 1:
                key = RSA.generate(2560)
                privatekey = key.exportKey("PEM")
                sig = {"secretcode": privatekey}
                gkcore.secret = privatekey
                result = con.execute(gkdb.signature.insert(), [sig])
        if tokenType == "user":
            token = jwt.encode(
                {"username": tokenItems["username"], "userid": tokenItems["userid"]},
                gkcore.secret,
                algorithm="HS256",
            )
        else:  # if userorg
            token = jwt.encode(
                {"orgcode": tokenItems["orgcode"], "userid": tokenItems["userid"]},
                gkcore.secret,
                algorithm="HS256",
            )
        token = token.decode("ascii")
        return token
    except:
        print(traceback.format_exc())
        return -1


def userAuthCheck(token):
    """
    Purpose: on every request check if userid and username are valid combinations
    """
    try:
        tokendict = jwt.decode(token, gkcore.secret, algorithms=["HS256"])
        tokendict["auth"] = True
        tokendict["username"] = tokendict["username"]
        tokendict["userid"] = int(tokendict["userid"])
        return tokendict
    except:
        print(traceback.format_exc())
        tokendict = {"auth": False}
        return tokendict


def authCheck(token):
    """
    Purpose: on every request check if userid and orgcode are valid combinations
    """
    try:
        tokendict = jwt.decode(token, gkcore.secret, algorithms=["HS256"])
        tokendict["auth"] = True
        tokendict["orgcode"] = int(tokendict["orgcode"])
        tokendict["userid"] = int(tokendict["userid"])
        return tokendict
    except:
        tokendict = {"auth": False}
        return tokendict
