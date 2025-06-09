from gkcore import eng, enumdict
from gkcore.utils import authCheck
from gkcore.models.gkdb import bank, accounts, groupsubgroups
from gkcore.views.bank.schemas import BankCreate, BankUpdate
from sqlalchemy.sql import select, update, insert, delete
from sqlalchemy import and_
from pyramid.view import view_defaults, view_config


@view_defaults(route_name="bank", renderer="json_extended")
class api_bank(object):
    def __init__(self, request):
        self.request = request

    @view_config(request_method="POST")
    def add_bank(self):
        """ API to add banks.
        """
        try:
            token = self.request.headers["gktoken"]
        except:
            return {"gkstatus": enumdict["UnauthorisedAccess"]}
        authDetails = authCheck(token)
        if authDetails["auth"] == False:
            return {"gkstatus": enumdict["UnauthorisedAccess"]}
        validated_data = BankCreate.model_validate(
            self.request.json_body, context={"orgcode": authDetails["orgcode"]}
        )
        dataset = validated_data.model_dump()
        with eng.begin() as con:
            orgcode = dataset["orgcode"] = authDetails["orgcode"]
            opening_balance = dataset.pop("opening_balance", None)

            groupcode = con.execute(
                select([groupsubgroups.c.groupcode])
                .where(
                    and_(
                        groupsubgroups.c.orgcode == orgcode,
                        groupsubgroups.c.groupname == "Bank",
                    )
                )
            ).scalar()
            dataset["accountcode"] = con.execute(
                insert(accounts)
                .values(
                    {
                        "accountname": dataset["account_name"],
                        "openingbal": opening_balance,
                        "groupcode": groupcode,
                        "orgcode": orgcode,
                    }
                )
                .returning(accounts.c.accountcode)
            ).scalar()

            bank_id = con.execute(
                insert(bank)
                .values(dataset)
                .returning(bank.c.id)
            )
            return {
                "gkstatus": enumdict["Success"],
                "gkresult": bank_id.scalar(),
            }


    @view_config(request_method="PUT")
    def update_bank(self):
        """ API to udpate banks.
        """
        try:
            token = self.request.headers["gktoken"]
        except:
            return {"gkstatus": enumdict["UnauthorisedAccess"]}
        authDetails = authCheck(token)
        if authDetails["auth"] == False:
            return {"gkstatus": enumdict["UnauthorisedAccess"]}
        validated_data = BankUpdate.model_validate(
            self.request.json_body, context={"orgcode": authDetails["orgcode"]}
        )
        dataset = validated_data.model_dump()
        with eng.begin() as con:
            id = dataset.pop("id")
            dataset["orgcode"] = authDetails["orgcode"]
            result = con.execute(
                update(bank)
                .where(bank.c.id == id)
                .values(dataset)
                .returning(bank.c.id)
            )
            return {
                "gkstatus": enumdict["Success"],
                "gkresult": result.scalar(),
            }


    @view_config(request_method="DELETE")
    def delete_bank(self):
        """ API to delete banks.
        Requried Fields: id
        """
        try:
            token = self.request.headers["gktoken"]
        except:
            return {"gkstatus": enumdict["UnauthorisedAccess"]}
        authDetails = authCheck(token)
        if authDetails["auth"] == False:
            return {"gkstatus": enumdict["UnauthorisedAccess"]}
        with eng.begin() as con:
            dataset = self.request.json_body
            con.execute(
                delete(bank).where(
                    bank.c.id == dataset["id"]
                )
            )
            return {"gkstatus": enumdict["Success"]}


    @view_config(request_method="GET")
    def get_banks(self):
        """ API to get banks.
        """
        try:
            token = self.request.headers["gktoken"]
        except:
            return {"gkstatus": enumdict["UnauthorisedAccess"]}
        authDetails = authCheck(token)
        if authDetails["auth"] == False:
            return {"gkstatus": enumdict["UnauthorisedAccess"]}

        bank_id = self.request.params.get("bank_id")

        with eng.connect() as con:
            if bank_id:
                banks = con.execute(
                    select([bank]).where(
                        bank.c.id == bank_id,
                    )
                ).fetchone()
            else:
                banks = con.execute(
                    select([bank]).where(
                        bank.c.orgcode == authDetails["orgcode"],
                    )
                ).fetchall()
                banks = [dict(bank) for bank in banks]

            return {
                "gkstatus": enumdict["Success"],
                "gkresult": banks,
            }
