from datetime import datetime
from pydantic import BaseModel, Field

class CustomerBase(BaseModel):
    id: str
    name: str
    email: str
    phone: str
    kyc_status: str
    risk_rating: str
    monthly_income: float
    existing_monthly_debt: float
    employer: str
    city: str
    created_at: datetime

class AccountBase(BaseModel):
    id: str
    customer_id: str
    account_number: str
    masked_account_number: str
    account_type: str
    balance: float
    currency: str
    status: str
    created_at: datetime

class TransactionBase(BaseModel):
    id: str
    account_id: str
    customer_id: str
    amount: float
    txn_type: str
    category: str
    merchant_name: str
    location: str
    status: str
    timestamp: datetime
    is_flagged: bool
    description: str

class SpendingCategoryBreakdown(BaseModel):
    category: str
    total_amount: float
    transaction_count: int
    percentage: float

class SpendingSummary(BaseModel):
    customer_id: str
    total_inflow: float
    total_outflow: float
    net_cashflow: float
    transaction_count: int
    categories: list[SpendingCategoryBreakdown] = Field(default_factory=list)
    period_days: int = 30

class Customer360(BaseModel):
    customer: CustomerBase
    accounts: list[AccountBase] = Field(default_factory=list)
    recent_transactions: list[TransactionBase] = Field(default_factory=list)
    spending_summary: SpendingSummary | None = None
