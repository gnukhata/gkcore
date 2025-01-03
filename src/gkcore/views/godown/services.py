from gkcore import eng, enumdict
from sqlalchemy import select, and_, func
from gkcore.models.gkdb import godown, usergodown, stock

def getusergodowns(userid):
    with eng.connect() as con:
        uid = userid
        godowns = con.execute(
            select([godown]).where(
                and_(
                    godown.c.goid.in_(
                        select([usergodown.c.goid]).where(usergodown.c.userid == uid)
                    )
                )
            )
        )
        usergo = []
        srno = 1
        for row in godowns:
            godownstock = con.execute(
                select([func.count(stock.c.goid).label("godownstockstatus")]).where(
                    stock.c.goid == row["goid"]
                )
            )

            godownstockcount = godownstock.fetchone()
            godownstatus = godownstockcount["godownstockstatus"]

            if godownstatus > 0:
                status = "Active"
            else:
                status = "Inactive"

            usergo.append(
                {
                    "godownstatus": status,
                    "srno": srno,
                    "goid": row["goid"],
                    "goname": row["goname"],
                    "goaddr": row["goaddr"],
                    "gocontact": row["gocontact"],
                    "state": row["state"],
                    "contactname": row["contactname"],
                    "designation": row["designation"],
                }
            )

            srno = srno + 1
        return {"gkstatus": enumdict["Success"], "gkresult": usergo}
