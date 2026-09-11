# VideoTurbo Zero

Gerador de vídeos simples e independente, inspirado no fluxo do MoneyPrinterTurbo, com foco em custo zero.

## O que faz
1. Gera roteiro e buscas visuais com Gemini (free tier, quando disponível) ou aceita roteiro manual.
2. Gera narração com Edge TTS, sem API key.
3. Busca clipes gratuitos na Pexels API.
4. Gera legendas SRT localmente.
5. Monta e exporta MP4 com FFmpeg.

## Custos
O software não cobra assinatura nem usa créditos internos. Edge TTS e FFmpeg não exigem pagamento. Pexels exige uma chave gratuita. Gemini exige uma chave e está sujeito às cotas/condições do free tier da Google; se não quiser usar Gemini, selecione roteiro manual.

## Requisitos
- Python 3.11+
- FFmpeg e FFprobe no PATH
- Internet
- Chave Pexels
- Opcional: chave Gemini

## Instalação
```bash
python3.11 -m venv .venv
source .venv/bin/activate   # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
streamlit run app.py
```
Abra o endereço indicado pelo Streamlit, normalmente http://localhost:8501.

## Importante para macOS Catalina
O projeto foi desenhado para rodar em Python 3.11+, portanto o caminho mais simples para um Mac antigo é executar em uma máquina/nuvem compatível e usar a interface pelo navegador.

## Privacidade
As chaves digitadas na interface são mantidas apenas na sessão do Streamlit. O código não grava essas chaves em disco.
