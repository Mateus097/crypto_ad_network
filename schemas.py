from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, EmailStr

# Resumo geral do Dashboard
class DashboardSummaryResponse(BaseModel):
    publisher_id: int
    wallet_address: str
    total_impressions: int
    valid_impressions: int
    unpaid_balance_usdt: float
    total_paid_usdt: float

# Estatísticas diárias de impressões e ganhos
class DailyStat(BaseModel):
    date: str
    total_views: int
    valid_views: int
    estimated_earnings_usdt: float

# Item do Histórico de Saques/Pagamentos
class PayoutHistoryItem(BaseModel):
    id: int
    amount_usdt: float
    tx_hash: Optional[str] = None
    status: str
    created_at: datetime

    class Config:
        from_attributes = True