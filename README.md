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

No Streamlit Community Cloud, configure **App settings → Secrets** (nunca no GitHub):

```toml
PEXELS_API_KEY = "sua_chave_gratuita"
# Opcional, apenas para gerar roteiro automaticamente:
GEMINI_API_KEY = "sua_chave_gemini"
```

Também é possível colar as chaves na barra lateral durante uma sessão. Para gerar um
MP4 completo basta usar o roteiro manual, a chave gratuita do Pexels e o Edge TTS;
o Gemini permanece opcional.

## Radar Viral, ganchos e publicação

O Radar Viral cria ideias por nicho e ângulo de retenção sem custo adicional. O Modo
Viral cria cinco ganchos para testar no início do roteiro. Após montar o MP4, o painel
de publicação prepara título, descrição e atalhos para as páginas oficiais de upload.
Publicação automática será adicionada apenas por integrações oficiais e contas que o
usuário autorizar; o app não envia vídeos sem confirmação.
# Publicação direta no YouTube (opcional)

O app pode enviar o MP4 diretamente para o canal que o usuário conectar. No
Google Cloud, ative a **YouTube Data API v3** e crie um cliente OAuth do tipo
**Aplicativo da Web**, com esta URI de redirecionamento:

```
https://videoturbo-zero-evplcslk8zxqbdbqxvqshy.streamlit.app/
```

Em **Streamlit → App settings → Secrets**, inclua somente os valores do JSON
baixado do Google (nunca envie esse JSON ou a chave secreta para o GitHub):

```toml
YOUTUBE_CLIENT_ID = "cole o client_id do JSON"
YOUTUBE_CLIENT_SECRET = "cole o client_secret do JSON"
YOUTUBE_REDIRECT_URI = "https://videoturbo-zero-evplcslk8zxqbdbqxvqshy.streamlit.app/"
# Chave de API restrita à YouTube Data API v3, para o Radar de Canais:
YOUTUBE_DATA_API_KEY = "sua_chave_de_api_do_youtube"
```

Para um app OAuth externo em teste, adicione a conta Google que publicará os
vídeos em **Google Cloud → Google Auth Platform → Público-alvo → Usuários de
teste**. A autorização e a publicação só ocorrem após os cliques do usuário.

## Radar de Canais em Ascensão

Com `YOUTUBE_DATA_API_KEY` configurada, o Radar pesquisa vídeos públicos recentes
por nicho e apresenta sinais transparentes: idade do vídeo, visualizações, média de
visualizações por dia e alcance relativo aos inscritos públicos do canal. Os dados
servem para estudar temas e embalagens; não constituem uma previsão de viralização
nem autorização para copiar conteúdo de outros criadores.
