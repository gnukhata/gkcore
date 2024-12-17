from typing import List, Dict, Optional
from pydantic import BaseModel, Field


# Sub-models for nested JSON fields
class Consignee(BaseModel):
    consigneename: str = Field(..., description="Name of the consignee")
    tinconsignee: Optional[str] = Field(None, description="Tax Identification Number of the consignee")
    gstinconsignee: Optional[str] = Field(None, description="GSTIN of the consignee")
    consigneeaddress: Optional[str] = Field(None, description="Consignee address")
    consigneestate: Optional[str] = Field(None, description="Consignee state")
    consigneestatecode: Optional[str] = Field(None, description="State code of the consignee")
    consigneepincode: Optional[str] = Field(None, description="Pincode of the consignee")


class PriceDetails(BaseModel):
    custid: int = Field(..., description="Customer ID")
    productcode: int = Field(..., description="Product code")
    inoutflag: int = Field(..., description="Flag indicating inward or outward")
    lastprice: str = Field(..., description="Last recorded price")


class BankDetails(BaseModel):
    accountno: str = Field(..., description="Bank account number")
    bankname: Optional[str] = Field(None, description="Name of the bank")
    ifsc: str = Field(..., description="IFSC code")
    branch: Optional[str] = Field(None, description="Branch name")


class AVTax(BaseModel):
    GSTName: Optional[str] = Field(None, description="Name of GST tax")
    CESSName: Optional[str] = Field(None, description="Name of CESS tax")


class AV(BaseModel):
    product: Dict[str, str] = Field(..., description="Product details")
    prodData: Dict[str, str] = Field(..., description="Additional product data")
    taxpayment: str = Field(..., description="Tax payment information")
    totaltaxable: str = Field(..., description="Total taxable amount")
    avtax: Optional[AVTax] = Field(None, description="Tax information")


class InvoiceCommon(BaseModel):
    invoiceno: str = Field(..., description="Invoice number")
    ewaybillno: Optional[str] = Field(None, description="E-way bill number")
    invoicedate: str = Field(..., description="Invoice date")
    sourcestate: Optional[str] = Field(None, description="Source state")
    orgstategstin: Optional[str] = Field(None, description="GSTIN of the source state")
    issuername: str = Field(None, description="Issuer name")
    designation: str = Field(None, description="Designation of the issuer")
    address: Optional[str] = Field(None, description="Address of the issuer")
    pincode: Optional[str] = Field(None, description="Pincode")
    custid: int = Field(..., description="Customer ID")
    consignee: Consignee = Field(None, description="Consignee details")
    roundoffflag: int = Field(..., description="Round-off flag")
    taxflag: int = Field(..., description="Tax flag")
    taxstate: Optional[str] = Field(None, description="Tax state")
    pricedetails: List[PriceDetails] = Field(None, description="Price details for the invoice")
    paymentmode: int = Field(..., description="Mode of payment")
    transportationmode: str = Field(None, description="Mode of transportation")
    reversecharge: int = Field(None, description="Reverse charge flag")
    discflag: int = Field(..., description="Discount flag")
    invnarration: str = Field(None, description="Narration for the invoice")
    inoutflag: int = Field(..., description="Inward or outward flag")
    invoicetotal: str = Field(..., description="Total invoice amount")
    invoicetotalword: str = Field(..., description="Total invoice amount in words")
    contents: Dict[int, Dict[float, str]] = Field(..., description="Contents of the invoice")
    tax: Dict[int, str] = Field(..., description="Tax details")
    cess: Dict[int, str] = Field(..., description="Cess details")
    freeqty: Dict[int, str] = Field(..., description="Free quantity details")
    discount: Dict[int, str] = Field(..., description="Discount details")
    bankdetails: Optional[BankDetails] = Field(None, description="Bank details")
    vehicleno: Optional[str] = Field(None, description="Vehicle number")
    dateofsupply: str = Field(None, description="Date of supply")
    attachment: Optional[List[str]] = Field(None, description="Attachments")
    attachmentcount: Optional[int] = Field(None, description="Count of attachments")


class Invoice(InvoiceCommon):
    av: AV = Field(..., description="Additional values")


class Stock(BaseModel):
    items: Dict[int, str] = Field(..., description="Stock items")
    inout: int = Field(..., description="Inward or outward flag")


class DelChalConsignee(BaseModel):
    consigneename: str = Field(None, description="Consignee name")
    tinconsignee: Optional[str] = Field(None, description="Tax Identification Number")
    gstinconsignee: str = Field(None, description="GSTIN of the consignee")
    consigneeaddress: str = Field(None, description="Address of the consignee")
    consigneestate: Optional[str] = Field(None, description="State of the consignee")
    consigneestatecode: Optional[str] = Field(None, description="State code of the consignee")
    consigneepincode: str = Field(None, description="Pincode of the consignee")


class DelChalData(BaseModel):
    custid: int = Field(..., description="Customer ID")
    dcno: str = Field(..., description="Delivery challan number")
    dcdate: str = Field(..., description="Delivery challan date")
    dcflag: int = Field(..., description="Delivery challan flag")
    taxstate: Optional[str] = Field(None, description="Tax state")
    orgstategstin: str = Field(..., description="GSTIN of the organization")
    discflag: int = Field(..., description="Discount flag")
    taxflag: int = Field(..., description="Tax flag")
    dcnarration: str = Field(..., description="Narration for the delivery challan")
    roundoffflag: int = Field(..., description="Round-off flag")
    consignee: DelChalConsignee = Field(..., description="Consignee details")
    issuername: str = Field(..., description="Issuer name")
    designation: str = Field(..., description="Designation of the issuer")
    vehicleno: Optional[str] = Field(None, description="Vehicle number")
    modeoftransport: str = Field(..., description="Mode of transport")
    noofpackages: int = Field(..., description="Number of packages")
    sourcestate: Optional[str] = Field(None, description="Source state")
    inoutflag: int = Field(..., description="Inward or outward flag")
    delchaltotal: str = Field(..., description="Total amount of the delivery challan")
    totalinword: str = Field(..., description="Total amount in words")
    contents: Dict[int, Dict[float, str]] = Field(..., description="Contents of the delivery challan")
    tax: Dict[int, str] = Field(..., description="Tax details")
    cess: Dict[int, str] = Field(..., description="Cess details")
    freeqty: Dict[int, str] = Field(..., description="Free quantity details")
    discount: Dict[int, str] = Field(..., description="Discount details")
    dateofsupply: str = Field(..., description="Date of supply")


class StockData(BaseModel):
    inout: int = Field(..., description="Inward or outward flag")
    goid: int = Field(..., description="Godown ID")


class DelChalPayload(BaseModel):
    delchaldata: DelChalData = Field(..., description="Delivery challan data")
    stockdata: StockData = Field(..., description="Stock data")


class Payload(BaseModel):
    invoice: Invoice = Field(..., description="Invoice details")
    stock: Stock = Field(..., description="Stock details")


class InvoiceDetails(BaseModel):
    payload: Payload = Field(..., description="Payload details")
    delchalPayload: DelChalPayload = Field(..., description="Delivery challan payload")
