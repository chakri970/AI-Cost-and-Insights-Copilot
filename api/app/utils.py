# api/app/utils.py
import logging
import time


# Logger

logger = logging.getLogger("finops")
logging.basicConfig(level=logging.INFO)


# Sanitize user input


def sanitize_user_input(s: str) -> str:
    banned = ["SYSTEM:", "Assistant:", "<!--", "```", "eval(", "os.", "import "]
    out = s
    for b in banned:
        out = out.replace(b, "")
    if len(out) > 2000:
        out = out[:2000]
    return out


# Timer context manager


class Timer:
    def __enter__(self):
        self.start = time.time()
        return self

    def __exit__(self, *args):
        self.end = time.time()
        self.interval = self.end - self.start


# Dummy retriever for fallback


def dummy_retrieve(query: str, k: int = 5):
    """Return dummy answers if vector store is missing"""
    logger.warning(" Using dummy retriever for query: %s", query)
    return [f"dummy answer {i+1}" for i in range(k)]
