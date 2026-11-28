"""Nối model — chỗ DUY NHẤT trong bản chạy thử gọi model AI. NHÓM VIẾT phần gọi model thật.

Hợp đồng (giữ nguyên để khung đo được token):
    call_model(system: str, user: str) -> dict với 4 khoá
        "text":       str   chữ model trả về
        "model":      str   tên model đã gọi (để tra giá ở bảng giá model)
        "tokens_in":  int   số token vào, lấy từ trường usage trong phản hồi API — KHÔNG ước lượng
        "tokens_out": int   số token ra, gồm cả token suy luận / suy nghĩ nếu API tính riêng
    @model_call (từ tracing.py) tự ghi mỗi lần gọi vào trace; agent.py gọi call_model bao nhiêu lần
    cũng được, khung tự cộng token.
    Lỗi gọi model (hết lượt, sai key, mất mạng): cứ để exception bay ra — khung ghi lỗi vào cột error.

Chế độ giả (mặc định khi .env chưa có MODEL_PROVIDER, hoặc MODEL_PROVIDER=fake):
    trả một câu giả cố định, model "fake", token 0 — để luồng chạy hết từ trước CP2 (guide bước 3.2).
    Lượt `run.py eval` / `run.py simulate` chạy bằng model giả KHÔNG được tính.

Nối model thật: điền .env (chép từ .env.example), rồi viết nhánh gọi API ở dưới theo docs/connect-model.md
(có ví dụ OpenAI, Claude, model chạy trên máy, và cách nối nhà cung cấp khác). Không dán API key vào file này.
"""
import json
import os
import urllib.error
import urllib.parse
import urllib.request

from tracing import model_call

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SHOW_RAW = False
URL_OPENAI = "https://api.openai.com/v1/chat/completions"
URL_CLAUDE = "https://api.anthropic.com/v1/messages"
URL_GEMINI = "https://generativelanguage.googleapis.com/v1beta/models/%s:generateContent"
URL_OLLAMA = "http://localhost:11434/api/chat"


def load_env(path=os.path.join(ROOT, ".env")):
    """Đọc file .env (KEY=VALUE mỗi dòng) vào biến môi trường, không ghi đè biến đã có. Khung — không cần sửa."""
    if not os.path.exists(path):
        return
    with open(path, encoding="utf-8-sig") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


load_env()
MODEL_PROVIDER = (os.environ.get("MODEL_PROVIDER") or "fake").strip().lower()
MODEL_NAME = (os.environ.get("MODEL_NAME") or "").strip()
API_KEY = (os.environ.get("API_KEY") or "").strip()


def post_json(url: str, headers: dict, body: dict, timeout: int = 60) -> dict:
    """Gửi POST JSON bằng thư viện chuẩn và trả về JSON phản hồi."""
    req = urllib.request.Request(
        url,
        data=json.dumps(body).encode("utf-8"),
        method="POST",
        headers=dict({"Content-Type": "application/json"}, **headers),
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            data = json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        try:
            detail = e.read().decode("utf-8", "replace")[:300]
        finally:
            e.close()
        raise RuntimeError("HTTP %d: %s" % (e.code, detail)) from e
    if SHOW_RAW:
        print(json.dumps(data, ensure_ascii=False, indent=2)[:3000])
    return data


def call_openai(system: str, user: str, model: str = "") -> dict:
    """Gọi OpenAI Chat Completions API và trích usage token từ phản hồi."""
    target_model = (model or MODEL_NAME).strip()
    base = (os.environ.get("API_BASE") or "").strip().rstrip("/")
    url = (os.environ.get("OPENAI_BASE_URL") or "").strip()
    if not url:
        url = base + "/chat/completions" if base else URL_OPENAI
    messages = ([{"role": "system", "content": system}] if system else []) + [
        {"role": "user", "content": user}
    ]
    data = post_json(
        url,
        {"Authorization": "Bearer " + API_KEY},
        {"model": target_model, "messages": messages},
    )
    usage = data["usage"]
    text = data["choices"][0]["message"].get("content") or ""
    return {
        "text": text,
        "tokens_in": usage["prompt_tokens"],
        "tokens_out": usage["completion_tokens"],
    }


def call_claude(system: str, user: str, model: str = "") -> dict:
    """Gọi Anthropic Messages API (Claude) và trích usage token từ phản hồi."""
    target_model = (model or MODEL_NAME).strip()
    max_tokens = int((os.environ.get("MAX_TOKENS") or "2048").strip())
    body = {
        "model": target_model,
        "max_tokens": max_tokens,
        "messages": [{"role": "user", "content": user}],
    }
    if system:
        body["system"] = system
    data = post_json(
        URL_CLAUDE,
        {"x-api-key": API_KEY, "anthropic-version": "2023-06-01"},
        body,
    )
    text = "".join(
        block.get("text", "")
        for block in data.get("content", [])
        if block.get("type") == "text"
    )
    usage = data["usage"]
    return {
        "text": text,
        "tokens_in": usage["input_tokens"],
        "tokens_out": usage["output_tokens"],
    }


def call_gemini(system: str, user: str, model: str = "") -> dict:
    """Gọi Google Gemini generateContent API và trích usageMetadata (gồm cả thoughtsTokenCount)."""
    target_model = (model or MODEL_NAME).strip()
    url = URL_GEMINI % urllib.parse.quote(target_model, safe="")
    body = {"contents": [{"role": "user", "parts": [{"text": user}]}]}
    if system:
        body["systemInstruction"] = {"parts": [{"text": system}]}
    data = post_json(url, {"x-goog-api-key": API_KEY}, body)
    parts = data["candidates"][0]["content"].get("parts", [])
    text = "".join(
        part.get("text", "")
        for part in parts
        if "text" in part and not part.get("thought")
    )
    usage = data.get("usageMetadata", {})
    tokens_out = int(usage.get("candidatesTokenCount", 0)) + int(usage.get("thoughtsTokenCount", 0))
    return {
        "text": text,
        "tokens_in": int(usage.get("promptTokenCount", 0)),
        "tokens_out": tokens_out,
    }


def call_ollama(system: str, user: str, model: str = "") -> dict:
    """Gọi Ollama chat API chạy local (không cần API_KEY)."""
    target_model = (model or MODEL_NAME).strip()
    base = (os.environ.get("API_BASE") or "").strip().rstrip("/")
    url = (os.environ.get("OLLAMA_BASE_URL") or "").strip()
    if not url:
        url = base + "/api/chat" if base else URL_OLLAMA
    messages = ([{"role": "system", "content": system}] if system else []) + [
        {"role": "user", "content": user}
    ]
    data = post_json(
        url,
        {},
        {"model": target_model, "messages": messages, "stream": False},
        timeout=300,
    )
    return {
        "text": data["message"].get("content") or "",
        "tokens_in": data.get("prompt_eval_count", 0),
        "tokens_out": data.get("eval_count", 0),
    }


# provider -> (caller_fn, requires_api_key)
_PROVIDERS = {
    "openai": (call_openai, True),
    "anthropic": (call_claude, True),
    "claude": (call_claude, True),
    "gemini": (call_gemini, True),
    "ollama": (call_ollama, False),
}


@model_call
def call_model(system: str, user: str, model: str = "") -> dict:
    """Gọi model AI theo MODEL_PROVIDER trong .env; giữ nguyên hợp đồng 4 khoá cho @model_call."""
    if MODEL_PROVIDER == "fake":
        last = (user.strip().splitlines() or [""])[-1]
        return {
            "text": "[câu trả lời giả — chưa nối model] " + last[:60],
            "model": "fake",
            "tokens_in": 0,
            "tokens_out": 0,
        }

    entry = _PROVIDERS.get(MODEL_PROVIDER)
    if entry is None:
        raise NotImplementedError(
            "chưa hỗ trợ MODEL_PROVIDER=%s trong codebase/ai.py "
            "(hỗ trợ: fake, anthropic/claude, openai, gemini, ollama)" % MODEL_PROVIDER
        )
    caller, requires_key = entry
    chosen_model = (model or MODEL_NAME).strip()
    if requires_key and not API_KEY:
        raise RuntimeError("Thiếu API_KEY trong .env cho MODEL_PROVIDER=%s" % MODEL_PROVIDER)
    if not chosen_model:
        raise RuntimeError("Thiếu MODEL_NAME trong .env cho MODEL_PROVIDER=%s" % MODEL_PROVIDER)

    res = caller(system, user, chosen_model)
    return {
        "text": res["text"],
        "model": chosen_model,
        "tokens_in": int(res["tokens_in"]),
        "tokens_out": int(res["tokens_out"]),
    }
