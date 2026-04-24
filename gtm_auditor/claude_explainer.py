import json
from typing import Optional

try:
    import anthropic
    _ANTHROPIC_AVAILABLE = True
except ImportError:
    _ANTHROPIC_AVAILABLE = False


class ClaudeExplainer:
    def __init__(self, api_key: Optional[str]):
        self._enabled = bool(api_key) and _ANTHROPIC_AVAILABLE
        if self._enabled:
            self._client = anthropic.Anthropic(api_key=api_key)

    @property
    def enabled(self) -> bool:
        return self._enabled

    def explain_elements(
        self,
        element_kind: str,
        elements: list[dict],
    ) -> dict[str, dict]:
        """
        Returns {name: {"explanation": str, "example": str}} for each element.
        Elements with notes already set are skipped (notes take priority).
        """
        if not self._enabled:
            return {}

        targets = [e for e in elements if not e.get("notes", "").strip()]
        if not targets:
            return {}

        prompt = self._build_prompt(element_kind, targets)
        message = self._client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=4096,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = message.content[0].text
        return self._parse_response(raw)

    def explain_diff(self, diff_summary: str) -> str:
        """Generate a short explanation for a diff entry."""
        if not self._enabled:
            return ""
        message = self._client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=256,
            messages=[
                {
                    "role": "user",
                    "content": (
                        "以下のGTM設定変更の内容を1〜2文で日本語で解説してください。\n\n"
                        + diff_summary
                    ),
                }
            ],
        )
        return message.content[0].text.strip()

    def _build_prompt(self, element_kind: str, elements: list[dict]) -> str:
        elements_json = json.dumps(elements, ensure_ascii=False, indent=2)
        return f"""以下はGoogle Tag Manager（GTM）の{element_kind}一覧です。
各要素について、以下の2項目を日本語で回答してください。

1. 役割・解説: この{element_kind}が何をするものか（1〜2文）
2. 具体例: 実際にどんな場面で動くか（「〜のページを開いたとき」「〜ボタンをクリックしたとき」など）

回答はJSON形式で返してください:
{{
  "要素名": {{
    "explanation": "役割・解説",
    "example": "具体例"
  }},
  ...
}}

{element_kind}データ:
{elements_json}
"""

    def _parse_response(self, raw: str) -> dict[str, dict]:
        try:
            start = raw.find("{")
            end = raw.rfind("}") + 1
            if start == -1 or end == 0:
                return {}
            return json.loads(raw[start:end])
        except (json.JSONDecodeError, ValueError):
            return {}
