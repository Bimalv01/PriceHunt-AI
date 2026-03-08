from pydantic import BaseModel, Field
from typing import Optional


class CompareRequest(BaseModel):
    product: str = Field(..., min_length=2, max_length=200, examples=["iPhone 16 Pro"])
    groq_api_key: Optional[str] = Field(default=None)  # optional override


class ProductListing(BaseModel):
    name: str
    price: str
    rating: Optional[str] = None
    link: Optional[str] = None


class AlternativeProduct(BaseModel):
    name: str
    price: str
    platform: str
    note: Optional[str] = None


class AgentStep(BaseModel):
    step: int
    type: str
    message: str


class CompareResponse(BaseModel):
    product: str
    amazon: list[ProductListing] = []
    croma: list[ProductListing] = []
    alternatives: list[AlternativeProduct] = []
    amazon_search_url: str = ""
    croma_search_url: str = ""
    recommendation: Optional[str] = None
    savings: Optional[str] = None
    agent_steps: list[AgentStep] = []
    raw_response: Optional[str] = None


class ErrorResponse(BaseModel):
    detail: str