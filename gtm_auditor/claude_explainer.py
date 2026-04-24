import json
import re
from typing import Optional

try:
    import anthropic
    _ANTHROPIC_AVAILABLE = True
except ImportError:
    _ANTHROPIC_AVAILABLE = False

_CHUNK_SIZE = 15

_KIND_EN_TO_JA = {
    "Tag": "タグ",
    "Trigger": "トリガー",
    "Variable": "変数",
    "Folder": "フォルダ",
}


def _has_japanese(text: str) -> bool:
    return bool(re.search(r'[぀-ゟ゠-ヿ一-鿿]', text))


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
            if _has_japanese(diff_summary):
                instruction = "以下のGTM設定変更の内容を1〜2文で日本語で解説してください。\n\n"
            else:
                instruction = "Explain the following GTM configuration change in 1-2 sentences in English.\n\n"
            message = self._client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=256,
                messages=[{"role": "user", "content": instruction + diff_summary}],
            )
            return message.content[0].text.strip()
        except Exception as e:
            print(f"  警告: Claude API エラー (diff解説): {e}")
            return ""

    def _build_prompt(self, element_kind: str, elements: list[dict]) -> str:
        elements_json = json.dumps(elements, ensure_ascii=False, indent=2)
        if _has_japanese(elements_json):
            kind_label = _KIND_EN_TO_JA.get(element_kind, element_kind)
            return f"""以下はGoogle Tag Manager（GTM）の{kind_label}一覧です。
各要素について、以下の2項目を日本語で回答してください。

1. 役割・解説: この{kind_label}が何をするものか（1〜2文）
2. 具体例: 実際にどんな場面で動くか（「〜のページを開いたとき」「〜ボタンをクリックしたとき」など）

必ずJSON形式のみで返してください（コードブロック不要）:
{{
  "要素名": {{
    "explanation": "役割・解説",
    "example": "具体例"
  }}
}}

{kind_label}データ:
{elements_json}
"""
        else:
            return f"""The following is a list of {element_kind}s in Google Tag Manager (GTM).
For each element, provide the following 2 items in English.

1. Role / Description: What this {element_kind} does (1-2 sentences)
2. Example: In what situation it actually fires (e.g. "When a page loads", "When a button is clicked", etc.)

Return only JSON format (no code blocks):
{{
  "element_name": {{
    "explanation": "role / description",
    "example": "example"
  }}
}}

{element_kind} data:
{elements_json}
"""

    def _parse_response(self, raw: str) -> dict[str, dict]:
        cleaned = re.sub(r"```(?:json)?\s*", "", raw).strip()
        try:
            start = cleaned.find("{")
            end = cleaned.rfind("}") + 1
            if start == -1 or end == 0:
                return {}
            return json.loads(cleaned[start:end])
        except (json.JSONDecodeError, ValueError):
            return {}
