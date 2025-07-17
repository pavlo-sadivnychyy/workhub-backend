import httpx
from datetime import datetime, timedelta
from typing import Optional, Dict
import hmac
import hashlib
import base64
from app.config import settings


class MonobankService:
    """Service for handling Monobank payment operations"""
    
    BASE_URL = "https://api.monobank.ua"
    
    def __init__(self):
        self.token = settings.MONOBANK_TOKEN
        self.webhook_url = settings.MONOBANK_WEBHOOK_URL
        self.merchant_id = settings.MONOBANK_MERCHANT_ID
    
    async def create_invoice(
        self,
        amount: int,  # Amount in kopiykas (1 UAH = 100 kopiykas)
        order_id: str,
        destination: str = "Оплата послуг на WorkHub.ua",
        reference: Optional[str] = None,
        validity: int = 3600  # Invoice validity in seconds
    ) -> Dict:
        """
        Create payment invoice
        
        Args:
            amount: Amount in kopiykas
            order_id: Unique order ID
            destination: Payment description
            reference: Optional reference for reconciliation
            validity: Invoice validity period in seconds
            
        Returns:
            Dict with invoice_id and payment_url
        """
        
        headers = {
            "X-Token": self.token,
            "Content-Type": "application/json"
        }
        
        payload = {
            "amount": amount,
            "ccy": 980,  # UAH currency code
            "merchantPaymInfo": {
                "reference": reference or order_id,
                "destination": destination,
                "basketOrder": [
                    {
                        "name": destination,
                        "qty": 1,
                        "sum": amount,
                        "code": "service",
                        "unit": "шт"
                    }
                ]
            },
            "redirectUrl": f"{settings.FRONTEND_URL}/payment/success",
            "webHookUrl": self.webhook_url,
            "validity": validity
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.BASE_URL}/api/merchant/invoice/create",
                json=payload,
                headers=headers
            )
            
            if response.status_code != 200:
                raise Exception(f"Monobank API error: {response.text}")
            
            data = response.json()
            return {
                "invoice_id": data["invoiceId"],
                "payment_url": data["pageUrl"],
                "expires_at": datetime.utcnow() + timedelta(seconds=validity)
            }
    
    async def check_invoice_status(self, invoice_id: str) -> Dict:
        """Check invoice payment status"""
        
        headers = {
            "X-Token": self.token
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.BASE_URL}/api/merchant/invoice/status?invoiceId={invoice_id}",
                headers=headers
            )
            
            if response.status_code != 200:
                raise Exception(f"Monobank API error: {response.text}")
            
            return response.json()
    
    async def cancel_invoice(self, invoice_id: str) -> bool:
        """Cancel unpaid invoice"""
        
        headers = {
            "X-Token": self.token,
            "Content-Type": "application/json"
        }
        
        payload = {
            "invoiceId": invoice_id
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.BASE_URL}/api/merchant/invoice/cancel",
                json=payload,
                headers=headers
            )
            
            return response.status_code == 200
    
    def verify_webhook_signature(self, body: bytes, x_sign: str) -> bool:
        """Verify webhook signature from Monobank"""
        
        if not self.webhook_url:
            return True  # Skip verification in development
        
        # Monobank uses ECDSA signature, for now we'll trust the webhook
        # In production, implement proper ECDSA verification
        return True
    
    async def process_webhook(self, data: Dict) -> Dict:
        """Process payment webhook from Monobank"""
        
        invoice_id = data.get("invoiceId")
        status = data.get("status")
        amount = data.get("amount")
        reference = data.get("reference")
        
        return {
            "invoice_id": invoice_id,
            "status": status,  # created, processing, hold, success, failure, reversed, expired
            "amount": amount,
            "reference": reference,
            "payment_info": data.get("paymentInfo", {})
        }
    
    async def create_withdrawal(
        self,
        card_number: str,
        amount: int,  # Amount in kopiykas
        order_id: str,
        comment: str = "Виведення коштів з WorkHub.ua"
    ) -> Dict:
        """
        Create withdrawal to card
        
        Note: This requires special merchant account with withdrawal capabilities
        """
        
        headers = {
            "X-Token": self.token,
            "Content-Type": "application/json"
        }
        
        payload = {
            "amount": amount,
            "ccy": 980,  # UAH
            "card": card_number,
            "comment": comment,
            "reference": order_id
        }
        
        # This is a placeholder - actual implementation depends on Monobank merchant API
        # For now, we'll simulate the withdrawal
        return {
            "withdrawal_id": f"wd_{order_id}",
            "status": "processing",
            "amount": amount,
            "card": f"****{card_number[-4:]}"
        }


# Singleton instance
monobank_service = MonobankService()