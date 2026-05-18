import os
import stripe
from decimal import Decimal

stripe.api_key = os.environ.get("STRIPE_SECRET_KEY")


class StripeService:
    @staticmethod
    def create_checkout_session(order_id, amount, customer_email, success_url, cancel_url):
        try:
            amount_grosze = int(Decimal(str(amount)) * 100)

            session = stripe.checkout.Session.create(
                mode="payment",
                payment_method_types=["card"],
                line_items=[
                    {
                        "price_data": {
                            "currency": "pln",
                            "product_data": {"name": f"Order #{order_id}"},
                            "unit_amount": amount_grosze,
                        },
                        "quantity": 1,
                    }
                ],
                customer_email=customer_email if customer_email else None,
                success_url=f"{success_url}?session_id={{CHECKOUT_SESSION_ID}}",
                cancel_url=cancel_url,
                metadata={"order_id": str(order_id)},
            )

            return {
                "status": "success",
                "session_id": session.id,
                "checkout_url": session.url,
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}

    @staticmethod
    def retrieve_session(session_id):
        try:
            session = stripe.checkout.Session.retrieve(session_id)
            return {"status": "success", "session": session}
        except Exception as e:
            return {"status": "error", "message": str(e)}