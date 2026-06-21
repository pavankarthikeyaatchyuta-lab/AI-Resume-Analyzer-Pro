import os
import time

import streamlit as st
from groq import APIConnectionError, APIStatusError, APITimeoutError, AuthenticationError, BadRequestError, Groq, RateLimitError
from streamlit.errors import StreamlitSecretNotFoundError

GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
GROQ_FALLBACK_MODEL = os.getenv("GROQ_FALLBACK_MODEL", "llama-3.1-8b-instant")
GROQ_REQUEST_TIMEOUT_SECONDS = float(os.getenv("GROQ_REQUEST_TIMEOUT_SECONDS", "40"))
GROQ_MAX_ATTEMPTS = 3
GROQ_CALL_COOLDOWN_SECONDS = int(os.getenv("GROQ_CALL_COOLDOWN_SECONDS", "8"))


def get_groq_client():
    try:
        api_key = st.secrets.get("GROQ_API_KEY")
    except StreamlitSecretNotFoundError:
        api_key = None

    if not api_key:
        api_key = os.getenv("GROQ_API_KEY")

    if not api_key:
        st.error("Missing Groq API key. Add `GROQ_API_KEY` to Streamlit secrets or environment variables.")
        st.stop()
    return Groq(api_key=api_key, timeout=GROQ_REQUEST_TIMEOUT_SECONDS, max_retries=0)


def get_groq_model_candidates():
    candidates = [GROQ_MODEL]
    if GROQ_FALLBACK_MODEL and GROQ_FALLBACK_MODEL != GROQ_MODEL:
        candidates.append(GROQ_FALLBACK_MODEL)
    return candidates


def is_model_unavailable_error(exception):
    if isinstance(exception, APIStatusError) and getattr(exception, "status_code", None) in {400, 404}:
        message = str(exception).lower()
        return "model" in message and any(token in message for token in ["not found", "deprecated", "unavailable", "does not exist"])
    return False


def is_transient_groq_error(exception):
    if isinstance(exception, (RateLimitError, APITimeoutError, APIConnectionError)):
        return True
    if isinstance(exception, APIStatusError):
        return getattr(exception, "status_code", 0) >= 500
    return False


def classify_groq_error(exception):
    if isinstance(exception, AuthenticationError):
        return "auth"
    if isinstance(exception, BadRequestError):
        return "bad_request"
    if isinstance(exception, RateLimitError):
        return "rate_limit"
    if is_model_unavailable_error(exception):
        return "model_unavailable"
    if isinstance(exception, APIStatusError) and getattr(exception, "status_code", 0) < 500:
        return "bad_request"
    if is_transient_groq_error(exception):
        return "transient"
    return "generic"


def format_groq_error_message(exception):
    category = classify_groq_error(exception)
    if category == "rate_limit":
        return "Too many requests right now, please wait a moment and try again."
    if category == "auth":
        return "API key issue — contact the app owner."
    return "Something went wrong, please try again."


def call_groq_with_retry(client, *, messages, temperature=0, response_format=None):
    last_exception = None
    for model_index, model_name in enumerate(get_groq_model_candidates()):
        for attempt in range(1, GROQ_MAX_ATTEMPTS + 1):
            request_kwargs = {
                "model": model_name,
                "temperature": temperature,
                "messages": messages,
            }
            if response_format is not None:
                request_kwargs["response_format"] = response_format

            try:
                return client.chat.completions.create(**request_kwargs)
            except Exception as exception:
                last_exception = exception
                category = classify_groq_error(exception)

                if category in {"auth", "bad_request"}:
                    raise

                if category == "model_unavailable":
                    break

                if attempt < GROQ_MAX_ATTEMPTS and category in {"transient", "rate_limit", "generic"}:
                    time.sleep(2 ** (attempt - 1))
                    continue

                break

        if last_exception is not None and classify_groq_error(last_exception) in {"auth", "bad_request"}:
            raise last_exception

        if model_index < len(get_groq_model_candidates()) - 1 and classify_groq_error(last_exception) in {"transient", "rate_limit", "model_unavailable", "generic"}:
            continue

    raise last_exception


def groq_call_allowed(action_key, cooldown_seconds=GROQ_CALL_COOLDOWN_SECONDS):
    now = time.time()
    last_call_time = st.session_state.get(f"last_groq_call_at_{action_key}")
    if last_call_time is not None and now - last_call_time < cooldown_seconds:
        remaining_seconds = max(1, int(round(cooldown_seconds - (now - last_call_time))))
        st.warning(f"Please wait a few seconds before trying again. ({remaining_seconds}s remaining)")
        return False

    st.session_state[f"last_groq_call_at_{action_key}"] = now
    return True
