from pydantic import BaseModel, EmailStr, ValidationInfo, conint, constr, model_validator
from typing import Optional, Dict, Literal
from typing_extensions import Self
from pydantic_extra_types.phone_numbers import PhoneNumber
from gkcore.views.contact.services import check_duplicate_contact_name

# {
# 	"bankdetails": {
# 		"accountno": "1231231231231234",
# 		"bankname": "Canara Bank",
# 		"branchname": "DHULE",
# 		"ifsc": "CNRB0000222"
# 	},
# 	"csflag": 3,
# 	"custaddr": "Door No.42/147,44/146, Santhome High Road, Rosary Church Road, Mylapore, Chennai, Tamil Nadu, 600004",
# 	"custemail": "contact@contact.com",
# 	"custfax": "9123123123",
# 	"custname": "BHARTI TELEMEDIA LIMITED",
# 	"custpan": "AADCB0147R",
# 	"custphone": "9123123123",
# 	"custtan": null,
# 	"gst_party_type": null,
# 	"gst_reg_type": 2,
# 	"gstin": {
# 		"33": "33AADCB0147R1ZM"
# 	},
# 	"pincode": "600004",
# 	"state": "Tamil Nadu"
# }
#

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
    pincode: Optional[conint(le=999999)] = None
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
