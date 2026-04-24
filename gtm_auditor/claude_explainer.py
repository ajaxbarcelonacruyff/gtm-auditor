import json
import re
from typing import Optional

try:
    import anthropic
    _ANTHROPIC_AVAILABLE = True
except ImportError:
    _ANTHROPIC_AVAILABLE = False

_CHUNK_SIZE = 15


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
        """Returns {name: {"explanation": str, "example": str}} for each element."""
        if not self._enabled:
            return {}

        targets = [e for e in elements if not e.get("notes", "").strip()]
        if not targets:
            return {}

        result: dict[str, dict] = {}
        for i in range(0, len(targets), _CHUNK_SIZE):
            chunk = targets[i : i + _CHUNK_SIZE]
            end_idx = min(i + _CHUNK_SIZE, len(targets))
            print(f"  Claude API: {element_kind} の解説生成中 ({i + 1}〜{end_idx} / {len(targets)})...")
            try:
                prompt = self._build_prompt(element_kind, chunk)
                message = self._client.messages.create(
                    model="claude-haiku-4-5-20251001",
                    max_tokens=4096,
                    messages=[{"role": "user", "content": prompt}],
                )
                raw = message.content[0].text
                chunk_result = self._parse_response(raw)
                if not chunk_result:
                    print(f"  警告: {element_kind} チャンク {i + 1}〜{end_idx} のJSON解析に失敗しました")
                result.update(chunk_result)
            except Exception as e:
                print(f"  警告: Claude API エラー ({element_kind} {i + 1}〜{end_idx}): {e}")

        return result

    def explain_diff(self, diff_summary: str) -> str:
        """Generate a short explanation for a diff entry."""
        if not self._enabled:
            return ""
        try:
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
        except Exception as e:
            print(f"  警告: Claude API エラー (diff解説): {e}")
            return ""

    def _build_prompt(self, element_kind: str, elements: list[dict]) -> str:
        elements_json = json.dumps(elements, ensure_ascii=False, indent=2)
        return f"""以下はGoogle Tag Manager（GTM）の{element_kind}一覧です。
各要素について、以下の2項目を日本語で回答してください。

1. 役割・解説: この{element_kind}が何をするものか（1〜2文）
2. 具体例: 実際にどんな場面で動くか（「〜のページを開いたとき」「〜ボタンをクリックしたとき」など）

必ずJSON形式のみで返してください（コードブロック不要）:
{{
  "要素名": {{
    "explanation": "役割・解説",
    "example": "具体例"
  }}
}}

{element_kind}データ:
{elements_json}
"""

    def _parse_response(self, raw: str) -> dict[str, dict]:
        # Strip markdown code blocks if present
        cleaned = re.sub(r"```(?:json)?\s*", "", raw).strip()
        try:
            start = cleaned.find("{")
            end = cleaned.rfind("}") + 1
            if start == -1 or end == 0:
                return {}
            return json.loads(cleaned[start:end])
        except (json.JSONDecodeError, ValueError):
            return {}
