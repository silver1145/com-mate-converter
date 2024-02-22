import gettext
from locale import getdefaultlocale
from pathlib import Path

translation = gettext.translation(
    "com-mate-converter",
    localedir=Path(__file__).parent / "locale",
    languages=[lang] if (lang := getdefaultlocale()[0]) else None,
    fallback=True,
)
_ = translation.gettext
