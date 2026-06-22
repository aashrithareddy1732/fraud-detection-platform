from openai import OpenAI

from app.config import settings


def build_mock_explanation(prediction: dict, transaction: dict) -> str:
    reasons = ", ".join(prediction["top_reasons"])
    return (
        "Local explanation: this transaction was scored as "
        f"{prediction['risk_level']} risk with a {prediction['fraud_probability']:.0%} "
        f"fraud probability. The main drivers were: {reasons}. "
        "Review customer history, recent transaction pattern, and merchant context before taking action."
    )


def explain_prediction(prediction: dict, transaction: dict) -> str:
    if not settings.openai_enabled:
        return build_mock_explanation(prediction, transaction)

    client = OpenAI(api_key=settings.openai_api_key)
    prompt = (
        "Explain this already-computed fraud prediction for an analyst. "
        "Do not make a new fraud decision. Be concise and practical.\n\n"
        f"Transaction: {transaction}\n"
        f"Prediction: {prediction}\n"
    )
    try:
        response = client.responses.create(
            model=settings.openai_model,
            input=prompt,
        )
        return response.output_text
    except Exception as exc:
        return f"{build_mock_explanation(prediction, transaction)} OpenAI explanation unavailable: {exc}"
