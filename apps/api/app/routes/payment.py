from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from apps.api.app.audit.audit_service import AuditService
from apps.api.app.audit.transaction_service import TransactionService
from apps.api.app.commerce.authorization_schemas import Authorization
from apps.api.app.commerce.order_schemas import CreateOrderRequest
from apps.api.app.commerce.payment_schemas import PaymentVerificationRequest
from apps.api.app.commerce.razorpay_service import RazorpayService
from apps.api.app.core.config import settings
from apps.api.app.catalog.catalog_service import get_catalog
from apps.api.app.merchant_policy import MerchantPolicyService


router = APIRouter(
    prefix="/api/payment",
    tags=["Payment"],
)
class BundleOrderRequest(BaseModel):
    transaction_id: str = Field(min_length=1)
    add_on_product_id: str = Field(min_length=1)
razorpay_service = RazorpayService()
transaction_service = TransactionService()
audit_service = AuditService()


@router.get("/config")
def payment_config():
    return {
        "key_id": settings.razorpay_key_id,
    }


@router.post("/create-order")
def create_order(request: CreateOrderRequest):
    try:
        transaction = transaction_service.get(
            request.transaction_id
        )

        if transaction.status != "AUTHORIZED":
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Transaction cannot create an order "
                    f"from status {transaction.status}."
                ),
            )

        authorization = Authorization(
            transaction_id=transaction.transaction_id,
            authorized=True,
            buyer_max_amount=transaction.buyer_max_amount,
            approved_amount=transaction.amount,
            currency=transaction.currency,
            product_id=transaction.product_id,
            merchant_id="merchant_demo",
            reason="Existing authorized transaction.",
        )

        razorpay_order = razorpay_service.create_order(
            authorization
        )

        transaction_service.attach_order(
            transaction_id=transaction.transaction_id,
            razorpay_order_id=razorpay_order["id"],
        )

        audit_service.record(
            transaction.transaction_id,
            "ORDER_CREATED",
            {
                "razorpay_order_id": razorpay_order["id"],
                "amount": razorpay_order["amount"],
                "currency": razorpay_order["currency"],
            },
        )

        return {
            "status": "order_created",
            "authorization": authorization.model_dump(),
            "razorpay_order": razorpay_order,
        }

    except HTTPException:
        raise

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        )

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=str(error),
        )


@router.post("/create-negotiated-order")
def create_negotiated_order(request: CreateOrderRequest):
    try:
        transaction = transaction_service.get(
            request.transaction_id
        )

        if transaction.status != "NEGOTIATION_APPROVED":
            raise HTTPException(
                status_code=400,
                detail=(
                    "Transaction must have an approved negotiation "
                    "before creating a negotiated order."
                ),
            )

        authorization = Authorization(
            transaction_id=transaction.transaction_id,
            authorized=True,
            buyer_max_amount=transaction.buyer_max_amount,
            approved_amount=transaction.amount,
            currency=transaction.currency,
            product_id=transaction.product_id,
            merchant_id="merchant_demo",
            reason="Negotiated transaction approved by merchant policy.",
        )

        razorpay_order = razorpay_service.create_order(
            authorization
        )

        transaction_service.attach_order(
            transaction_id=transaction.transaction_id,
            razorpay_order_id=razorpay_order["id"],
        )

        audit_service.record(
            transaction.transaction_id,
            "NEGOTIATED_ORDER_CREATED",
            {
                "razorpay_order_id": razorpay_order["id"],
                "amount": razorpay_order["amount"],
                "currency": razorpay_order["currency"],
            },
        )

        return {
            "status": "negotiated_order_created",
            "transaction_id": transaction.transaction_id,
            "authorization": authorization.model_dump(),
            "razorpay_order": razorpay_order,
        }

    except HTTPException:
        raise

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        )

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=str(error),
        )

@router.post("/create-bundle-order")
def create_bundle_order(request: BundleOrderRequest):
    try:
        transaction = transaction_service.get(
            request.transaction_id
        )

        catalog = get_catalog()
        products = catalog["products"]

        base_product = next(
            (
                product
                for product in products
                if product["id"] == transaction.product_id
            ),
            None,
        )

        add_on_product = next(
            (
                product
                for product in products
                if product["id"] == request.add_on_product_id
            ),
            None,
        )

        if not base_product:
            raise HTTPException(
                status_code=404,
                detail="Base product not found.",
            )

        if not add_on_product:
            raise HTTPException(
                status_code=404,
                detail="Bundle add-on product not found.",
            )

        if add_on_product["id"] == base_product["id"]:
            raise HTTPException(
                status_code=400,
                detail="Bundle must contain a different add-on product.",
            )

        if not add_on_product["available"]:
            raise HTTPException(
                status_code=400,
                detail="Selected add-on is unavailable.",
            )

        combined_price = (
            base_product["price"] +
            add_on_product["price"]
        )

        buyer_authority = transaction.buyer_max_amount
        required_discount = max(
            0,
            combined_price - buyer_authority,
        )

        policy = MerchantPolicyService().get()

        if required_discount > policy["max_ai_discount"]:
            raise HTTPException(
                status_code=400,
                detail={
                    "message": "Bundle exceeds merchant negotiation authority.",
                    "combined_price": combined_price,
                    "buyer_max_amount": buyer_authority,
                    "required_discount": required_discount,
                    "max_ai_discount": policy["max_ai_discount"],
                },
            )

        if not policy["ai_negotiation_enabled"]:
            raise HTTPException(
                status_code=400,
                detail="AI negotiation is disabled by merchant policy.",
            )

        final_amount = min(
            combined_price,
            buyer_authority,
        )

        transaction_service.update_amount(
            transaction_id=transaction.transaction_id,
            amount=final_amount,
        )

        razorpay_order = razorpay_service.create_bundle_order(
            transaction_id=transaction.transaction_id,
            approved_amount=final_amount,
            currency=transaction.currency,
            base_product=base_product,
            add_on=add_on_product,
        )

        transaction_service.attach_order(
            transaction_id=transaction.transaction_id,
            razorpay_order_id=razorpay_order["id"],
        )

        audit_service.record(
            transaction.transaction_id,
            "BUNDLE_AUTHORIZED",
            {
                "base_product_id": base_product["id"],
                "base_product_name": base_product["name"],
                "add_on_product_id": add_on_product["id"],
                "add_on_product_name": add_on_product["name"],
                "original_bundle_price": combined_price,
                "approved_amount": final_amount,
                "discount": combined_price - final_amount,
                "buyer_max_amount": buyer_authority,
            },
        )

        audit_service.record(
            transaction.transaction_id,
            "BUNDLE_ORDER_CREATED",
            {
                "razorpay_order_id": razorpay_order["id"],
                "amount": razorpay_order["amount"],
                "currency": razorpay_order["currency"],
            },
        )

        return {
            "status": "bundle_order_created",
            "transaction_id": transaction.transaction_id,
            "bundle": {
                "base_product": base_product,
                "add_on": add_on_product,
                "original_price": combined_price,
                "final_price": final_amount,
                "discount": combined_price - final_amount,
                "buyer_max_amount": buyer_authority,
            },
            "razorpay_order": razorpay_order,
        }

    except HTTPException:
        raise

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        )

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=str(error),
        )

@router.post("/verify")
def verify_payment(request: PaymentVerificationRequest):
    try:
        is_valid = razorpay_service.verify_payment(
            order_id=request.order_id,
            payment_id=request.payment_id,
            signature=request.signature,
        )

        if not is_valid:
            raise HTTPException(
                status_code=400,
                detail={
                    "status": "verification_failed",
                    "message": "Invalid Razorpay payment signature.",
                },
            )

        order = razorpay_service.client.order.fetch(
            request.order_id
        )

        transaction_id = order.get("notes", {}).get(
            "transaction_id"
        )

        if not transaction_id:
            raise HTTPException(
                status_code=400,
                detail="Transaction ID missing from Razorpay order.",
            )

        transaction = transaction_service.get(
            transaction_id
        )

        if transaction.razorpay_order_id != request.order_id:
            raise HTTPException(
                status_code=400,
                detail="Razorpay order does not match the transaction.",
            )

        transaction_service.attach_payment(
            transaction_id=transaction_id,
            razorpay_payment_id=request.payment_id,
        )

        audit_service.record(
            transaction_id,
            "PAYMENT_SUCCESS",
            {
                "razorpay_order_id": request.order_id,
                "razorpay_payment_id": request.payment_id,
            },
        )

        return {
            "status": "payment_verified",
            "transaction_id": transaction_id,
            "order_id": request.order_id,
            "payment_id": request.payment_id,
        }

    except HTTPException:
        raise

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        )

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=str(error),
        )