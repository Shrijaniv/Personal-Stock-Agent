import anthropic
from config import ANTHROPIC_API_KEY

_client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

_SYSTEM = (
    "You are a concise stock portfolio advisor. "
    "Respond in 2-3 sentences max. Be direct and actionable. "
    "Never give generic disclaimers about consulting a financial advisor."
)


def analyze(prompt: str) -> str:
    response = _client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=256,
        system=[
            {
                "type": "text",
                "text": _SYSTEM,
                "cache_control": {"type": "ephemeral"},
            }
        ],
        messages=[{"role": "user", "content": prompt}],
    )
    return response.content[0].text.strip()
