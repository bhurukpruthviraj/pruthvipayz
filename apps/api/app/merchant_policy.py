import json
from pathlib import Path


POLICY_PATH = (
    Path(__file__).resolve().parents[3]
    / "data"
    / "merchant_policy.json"
)


class MerchantPolicyService:
    def get(self) -> dict:
        with POLICY_PATH.open("r", encoding="utf-8") as file:
            return json.load(file)

    def update(
        self,
        ai_negotiation_enabled: bool,
        max_ai_discount: int,
    ) -> dict:
        if max_ai_discount < 0:
            raise ValueError("Maximum AI discount cannot be negative.")

        policy = {
            "ai_negotiation_enabled": ai_negotiation_enabled,
            "max_ai_discount": max_ai_discount,
            "require_human_approval_above": max_ai_discount,
        }

        with POLICY_PATH.open("w", encoding="utf-8") as file:
            json.dump(policy, file, indent=2)

        return policy
