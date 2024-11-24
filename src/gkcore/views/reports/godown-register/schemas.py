from pydantic import BaseModel
from datetime import date

class GodownRegister(BaseModel):
    goid: int
    productcode: int
    startdate: date = None
    enddate: date = None
