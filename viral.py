"""Free, local helpers for stronger short-video packaging."""
from urllib.parse import quote_plus


def fallback_radar(niche: str, audience: str):
    niche = niche or "seu nicho"
    audience = audience or "pessoas interessadas no tema"
    angles = [
        ("Erro comum", f"O erro que faz {audience} perderem tempo em {niche}"),
        ("Passo a passo", f"3 passos simples para começar em {niche} hoje"),
        ("Comparação", f"O jeito antigo versus o jeito inteligente de fazer {niche}"),
        ("Mito ou verdade", f"O que quase ninguém explica sobre {niche}"),
        ("Transformação", f"O que muda quando você aplica isto em {niche}"),
    ]
    return [{"angle": angle, "topic": topic, "retention": "Alto"} for angle, topic in angles]


def fallback_hooks(topic: str):
    return [
        f"Se você ainda ignora isto em {topic}, está ficando para trás.",
        f"Ninguém explica esta parte de {topic}.",
        f"Antes de fazer qualquer coisa em {topic}, veja isto.",
        f"O erro mais comum em {topic} — e como evitar.",
        f"Em menos de um minuto, entenda o essencial sobre {topic}.",
    ]


def publish_copy(title: str, topic: str, hooks: list[str]):
    hook = hooks[0] if hooks else title
    description = f"{hook}\n\n{topic}\n\n#shorts #reels #video"
    return {"title": title[:100], "description": description, "hashtags": "#shorts #reels #video"}


def share_links(title: str, description: str):
    text = quote_plus(f"{title}\n{description}")
    return {
        "YouTube Studio": "https://studio.youtube.com/",
        "Facebook": f"https://www.facebook.com/sharer/sharer.php?u=&quote={text}",
        "X": f"https://x.com/intent/post?text={text}",
        "Instagram": "https://www.instagram.com/",
        "TikTok": "https://www.tiktok.com/upload",
    }
