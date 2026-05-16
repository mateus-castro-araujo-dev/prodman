import unicodedata
from django import template

register = template.Library()

EMOJI_MAP = [
    # Insumos / ingredientes
    ("farinha", "🌾"),
    ("trigo", "🌾"),
    ("aveia", "🌾"),
    ("milho", "🌽"),
    ("fuba", "🌽"),
    ("acucar", "🍬"),
    ("sal", "🧂"),
    ("ovo", "🥚"),
    ("leite condensado", "🥫"),
    ("leite", "🥛"),
    ("manteiga", "🧈"),
    ("margarina", "🧈"),
    ("oleo", "🛢️"),
    ("azeite", "🫒"),
    ("agua", "💧"),
    ("fermento", "🫧"),
    ("chocolate", "🍫"),
    ("cacau", "🍫"),
    ("achocolatado", "🍫"),
    ("nescau", "🍫"),
    ("brigadeiro", "🍫"),
    ("morango", "🍓"),
    ("uva", "🍇"),
    ("banana", "🍌"),
    ("maca", "🍎"),
    ("laranja", "🍊"),
    ("limao", "🍋"),
    ("coco", "🥥"),
    ("amendoim", "🥜"),
    ("castanha", "🌰"),
    ("noz", "🌰"),
    ("mel", "🍯"),
    ("canela", "🍂"),
    ("baunilha", "🌼"),
    ("queijo", "🧀"),
    ("requeijao", "🧀"),
    ("polvilho", "🥨"),
    ("goma", "🥨"),
    ("amido", "🥨"),
    ("cenoura", "🥕"),
    ("abobora", "🎃"),
    ("granola", "🥣"),
    ("passas", "🍇"),
    ("gergelim", "🌱"),
    ("linhaca", "🌱"),
    ("essencia", "🌼"),
    ("corante", "🎨"),
    ("embalagem", "📦"),
    ("sacola", "🛍️"),
    ("saco", "🛍️"),
    ("etiqueta", "🏷️"),

    # Receitas / produtos / biscoitos
    ("rosquinha", "🥯"),
    ("rosca", "🥯"),
    ("sequilho", "🍪"),
    ("amanteigado", "🍪"),
    ("recheado", "🍪"),
    ("cookie", "🍪"),
    ("biscoito", "🍪"),
    ("bolacha", "🍪"),
    ("bolo", "🍰"),
    ("cupcake", "🧁"),
    ("muffin", "🧁"),
    ("pao de queijo", "🧀"),
    ("pao", "🍞"),
    ("torta", "🥧"),
    ("doce", "🍬"),
    ("pirulito", "🍭"),
    ("paçoca", "🥜"),
    ("pacoca", "🥜"),
]


def _normalize(text):
    text = unicodedata.normalize("NFD", text or "")
    text = "".join(c for c in text if unicodedata.category(c) != "Mn")
    return text.lower().strip()


@register.filter
def emoji_for(name):
    n = _normalize(name)
    if not n:
        return "🍪"
    for key, emoji in EMOJI_MAP:
        if key in n:
            return emoji
    return "🍪"
