import asyncio
from pathlib import Path

async def _save(text, voice, output):
    import edge_tts
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(output)

def synthesize(text: str, voice: str, output: str):
    Path(output).parent.mkdir(parents=True, exist_ok=True)
    asyncio.run(_save(text, voice, output))
    return output
