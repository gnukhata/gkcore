from pydantic import BaseModel, confloat
from typing import Optional, Dict, Any, Literal


class GodownStock(BaseModel):
     qty: Optional[float] = None
     rate: Optional[float] = None


class ProductDetail(BaseModel):
    amountdiscount: Optional[confloat(ge=0)] = 0
    categorycode: Optional[int] = None
    gscode: Optional[str] = None
    gsflag: Literal[7, 19]
    openingstock: Optional[float] = None
    percentdiscount: Optional[confloat(ge=0, le=100)] = 0
    prodmrp: Optional[confloat(ge=0)] = 0
    productdesc: str
    prodsp: Optional[confloat(ge=0)] = 0
    specs: Optional[Dict[str, Any]] = None
    uomid: Optional[int] = None


class ProductGodown(BaseModel):
    productdetails: ProductDetail
    godownflag: Optional[bool] = None
    godetails: Optional[Dict[int, GodownStock]] = None
