"""
Loads prompt wording from backend/prompts/*.txt and fills in placeholders.

Prompts live in plain .txt files, not in this file or any other .py file -
see backend/prompts/README.md for the placeholder convention and why this
split exists. This module is just the small loader; it has no opinions
about what any prompt actually says.
"""

from pathlib import Path
from string import Template

PROMPTS_DIR = Path(__file__).resolve().parent / "prompts"


def load_prompt(name: str, **values: str) -> str:
    """Reads backend/prompts/<name>.txt and fills in $placeholders with
    `values`.

    Raises KeyError if the template contains a placeholder that wasn't
    provided - on purpose, so a typo'd or forgotten value fails loudly
    instead of leaving a literal "$placeholder" in text sent to the AI.
    """
    path = PROMPTS_DIR / f"{name}.txt"
    template = Template(path.read_text(encoding="utf-8"))
    return template.substitute(**values)
