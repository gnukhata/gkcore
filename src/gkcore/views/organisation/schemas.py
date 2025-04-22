from pydantic import BaseModel, EmailStr, Field, HttpUrl, constr, model_validator
from typing import Any, Optional
from datetime import date


# This will match numbers with 9-15 numbers with optional '+' sign.
PhoneStr = Field(pattern=r'^\+?\d{9,15}$', min_length=10, max_length=15, default=None)

# PAN pattern: 5 uppercase letters, 4 digits, 1 uppercase letter
PANStr = Field(pattern=r'^[A-Z]{5}[0-9]{4}[A-Z]$', min_length=10, max_length=10, default=None)

def convert_blank_to_none(value: Any) -> Any:
    if isinstance(value, dict):
        return {k: convert_blank_to_none(v) for k, v in value.items()}
    elif isinstance(value, list):
        return [convert_blank_to_none(item) for item in value]
    elif value == "":
        return None
    return value


class CleanBaseModel(BaseModel):
    @model_validator(mode="before")
    @classmethod
    def clean_blank_strings(cls, data: Any) -> Any:
        return convert_blank_to_none(data)


class OrgDetails(CleanBaseModel):
    orgname: constr(max_length=200)
    orgcountry: constr(min_length=2, max_length=200)
    orgtype: constr(max_length=200)
    yearend: date
    yearstart: date
    ainvnoflag: Optional[int] = None
    avflag: Optional[int] = None
    avnoflag: Optional[int] = None
    billflag: Optional[int] = None
    invflag: Optional[int] = None
    invsflag: Optional[int] = None
    maflag: Optional[int] = None
    modeflag: Optional[int] = None
    orgaddr: Optional[constr(min_length=5, max_length=500)] = None
    orgcity: Optional[constr(min_length=2, max_length=100)] = None
    orgemail: Optional[EmailStr] = None
    orgfax: Optional[str] = PhoneStr
    orgfcradate: Optional[date] = None
    orgfcrano: Optional[constr(min_length=5, max_length=50)] = None
    orgmvat: Optional[constr(min_length=5, max_length=50)] = None
    orgpan: Optional[str] = PANStr
    orgpincode: Optional[constr(max_length=10)] = None
    orgregdate: Optional[date] = None
    orgregno: Optional[constr(min_length=1, max_length=50)] = None
    orgstate: Optional[constr(min_length=2, max_length=100)] = None
    orgstax: Optional[constr(min_length=5, max_length=50)] = None
    orgtelno: Optional[str] = PhoneStr
    orgwebsite: Optional[HttpUrl] = None


class OrgCreate(BaseModel):
    orgdetails: OrgDetails




