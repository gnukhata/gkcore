import re
from pydantic import BaseModel, constr, field_validator
from gkcore.models.gkdb import organisation
from gkcore import eng
from sqlalchemy.sql import select


class UserLogin(BaseModel):
    username: constr(max_length=200)
    userpassword: constr(pattern=re.compile(r'^[a-fA-F0-9]{128}$'))


class OrgLogin(BaseModel):
    orgcode: int

    @field_validator('orgcode')
    @classmethod
    def validate_orgcode(cls, value):
        with eng.connect() as conn:
            org_query = conn.execute(
                select([organisation]).where(
                    organisation.c.orgcode == value
                )
            )
            if not org_query.rowcount:
                raise ValueError(
                    f"Organisation not found for orgcode: {value}"
                )
        return value
