from pydantic import BaseModel, EmailStr, ValidationInfo, conint, constr, field_validator, model_validator
from typing import Optional, Dict, Literal
from typing_extensions import Self
from pydantic_extra_types.phone_numbers import PhoneNumber
from gkcore.views.contact.services import check_custid_exists, check_duplicate_contact_name


class BankDetails(BaseModel):
    accountno: Optional[conint(lt=1000000000000000)] = None
    bankname: Optional[constr(max_length=100)] = None
    branchname: Optional[constr(max_length=100)] = None
    ifsc: Optional[constr(max_length=20)] = None


class ContactDetails(BaseModel):
    csflag: Literal[3, 19]
    custaddr: Optional[constr(max_length=200)] = None
    custemail: Optional[EmailStr] = None
    custfax: Optional[conint(lt=1000000000000000)] = None
    custname: constr(max_length=100)
    custpan: Optional[constr(max_length=10)] = None
    custphone: Optional[PhoneNumber] = None
    custtan: Optional[constr(max_length=10)] = None
    gst_party_type: Optional[Literal[0,1,2,3]] = None
    gst_reg_type: Optional[Literal[0,1,2,3]] = None
    gstin: Optional[Dict[conint(le=100), constr(max_length=15)]] = None
    pincode: Optional[constr(max_length=10)] = None
    state: Optional[constr(max_length=20)] = None
    bankdetails: Optional[BankDetails] = None

    @model_validator(mode="after")
    def validate(self, info: ValidationInfo) -> Self:
        check_duplicate_contact_name(
             self.custname,
             info.context["orgcode"],
             getattr(self, "custid", None),
        )
        return self


class ContactDetailsUpdate(ContactDetails):
    custid: int

    @field_validator("custid")
    @classmethod
    def custid_validate(cls, value: int, info: ValidationInfo) -> int:
        check_custid_exists(
             value,
             info.context["orgcode"],
        )
        return value