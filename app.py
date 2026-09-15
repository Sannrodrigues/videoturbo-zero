import json
import streamlit as st
import time
from pathlib import Path

from llm import generate_plan
from stock import download_for_queries
from tts import synthesize
from render import media_duration, make_srt, render_video
from viral import fallback_radar, fallback_hooks, publish_copy, share_links
from youtube import authorization_url, configured as youtube_configured, credentials_from_code, upload_video
from youtube_radar import find_rising_videos
from monetize import GOALS, packaging_options


def get_secret(name: str) -> str:
    """Read an optional Streamlit secret without failing when none is configured."""
    try:
        return str(st.secrets.get(name, ""))
    except (FileNotFoundError, KeyError):
        return ""


def youtube_settings() -> dict[str, str]:
    return {
        'YOUTUBE_CLIENT_ID': get_secret('YOUTUBE_CLIENT_ID'),
        'YOUTUBE_CLIENT_SECRET': get_secret('YOUTUBE_CLIENT_SECRET'),
        'YOUTUBE_REDIRECT_URI': get_secret('YOUTUBE_REDIRECT_URI'),
    }

st.set_page_config(page_title='VideoTurbo Zero', page_icon='🎬', layout='wide')
st.title('🎬 VideoTurbo Zero')
st.caption('Tema → roteiro → voz → vídeos gratuitos → legendas → MP4. Sem assinatura e sem créditos.')

youtube_config = youtube_settings()
if youtube_configured(youtube_config):
    oauth_code = st.query_params.get('code')
    oauth_state = st.query_params.get('state')
    if oauth_code and oauth_state and 'youtube_credentials' not in st.session_state:
        try:
            st.session_state.youtube_credentials = credentials_from_code(youtube_config, oauth_code, oauth_state)
            st.query_params.clear()
            st.success('Canal do YouTube conectado nesta sessão.')
        except Exception as exc:
            st.error(f'Não foi possível conectar o YouTube: {exc}')

with st.container(border=True):
    st.subheader('▶️ YouTube')
    if not youtube_configured(youtube_config):
        st.caption('A publicação direta pode ser configurada depois em Streamlit Secrets.')
    elif 'youtube_credentials' in st.session_state:
        st.success('Canal conectado nesta sessão. Crie o vídeo e publique no final.')
    else:
        st.caption('Conecte seu canal antes de criar o vídeo. Isso não publica nada; apenas autoriza o envio quando você clicar em Publicar no final.')
        st.link_button('CONECTAR MEU YOUTUBE', authorization_url(youtube_config), type='primary')

with st.sidebar:
    st.header('Configuração gratuita')
    gemini_secret = get_secret('GEMINI_API_KEY')
    pexels_secret = get_secret('PEXELS_API_KEY')
    gemini_key = st.text_input('Gemini API Key (para roteiro automático)', value=gemini_secret, type='password')
    pexels_key = st.text_input('Pexels API Key (vídeos gratuitos)', value=pexels_secret, type='password')
    st.info('As chaves podem ficar em Streamlit Secrets ou apenas nesta sessão. Nunca são gravadas pelo app.')

col1,col2=st.columns([2,1])
with col1:
    topic=st.text_input('Tema do vídeo', placeholder='Ex.: Como a inteligência artificial está mudando pequenas empresas')
    monetization_goal=st.selectbox('Objetivo do vídeo', list(GOALS))
    destination=st.text_input('Link ou destino do CTA (opcional)', placeholder='Ex.: link do WhatsApp ou afiliado')
    mode=st.radio('Roteiro', ['Gerar automaticamente com Gemini','Usar meu próprio roteiro'], horizontal=True)
    manual=''
    if mode=='Usar meu próprio roteiro':
        manual=st.text_area('Cole o roteiro', height=220)
with col2:
    language=st.selectbox('Idioma', ['Português (Brasil)','Português (Portugal)','English','Español'])
    duration=st.selectbox('Duração aproximada', [30,60,90,180,300], index=1, format_func=lambda x:f'{x//60} min' if x>=60 else f'{x}s')
    style=st.selectbox('Estilo', ['Informativo','Motivacional','Documentário','Educativo','Vendas suave','Notícias'])
    fmt=st.selectbox('Formato', ['9:16 Vertical','16:9 YouTube','1:1 Quadrado'])
    voice_map={
      'Português (Brasil)': ['pt-BR-AntonioNeural','pt-BR-FranciscaNeural'],
      'Português (Portugal)': ['pt-PT-DuarteNeural','pt-PT-RaquelNeural'],
      'English': ['en-US-GuyNeural','en-US-JennyNeural'],
      'Español': ['es-ES-AlvaroNeural','es-ES-ElviraNeural']}
    voice=st.selectbox('Voz', voice_map[language])

if 'plan' not in st.session_state: st.session_state.plan=None
if 'viral_hooks' not in st.session_state: st.session_state.viral_hooks=[]
if 'last_video' not in st.session_state: st.session_state.last_video=None
if 'youtube_radar' not in st.session_state: st.session_state.youtube_radar=[]
if 'monetization_package' not in st.session_state: st.session_state.monetization_package=None

with st.expander('🚀 Radar Viral, Canais em Ascensão e Modo Viral', expanded=False):
    st.caption('Use referências como inspiração; não copie conteúdo de outros canais e não há promessa de viralização.')
    radar_col, reference_col = st.columns(2)
    with radar_col:
        niche = st.text_input('Nicho para o radar', placeholder='Ex.: finanças pessoais, fitness, IA')
        audience = st.text_input('Público', placeholder='Ex.: iniciantes, mães, pequenos empresários')
        radar_days = st.selectbox('Vídeos publicados nos últimos', [7, 14, 30], index=1, format_func=lambda value: f'{value} dias')
        if get_secret('YOUTUBE_DATA_API_KEY'):
            if st.button('BUSCAR CANAIS E VÍDEOS EM ASCENSÃO', use_container_width=True):
                try:
                    with st.spinner('Pesquisando dados públicos do YouTube...'):
                        st.session_state.youtube_radar = find_rising_videos(
                            get_secret('YOUTUBE_DATA_API_KEY'), niche, radar_days
                        )
                except Exception as exc:
                    st.error(f'Não foi possível pesquisar o YouTube: {exc}')
        else:
            st.info('Adicione YOUTUBE_DATA_API_KEY em Streamlit Secrets para ativar a busca real no YouTube.')
        if st.button('GERAR IDEIAS DE ALTO POTENCIAL'):
            st.session_state.radar = fallback_radar(niche, audience)
    with reference_col:
        references = st.text_area('Referências que você viu (opcional)', placeholder='Cole títulos, links ou anotações de vídeos que chamaram atenção.')
        st.caption('As referências ajudam você a estudar padrões sem copiar conteúdo de outras pessoas.')
    for item in st.session_state.get('radar', []):
        st.write(f"**{item['angle']}** · Retenção: {item['retention']}\n\n{item['topic']}")
    results = st.session_state.get('youtube_radar', [])
    if results:
        st.subheader('Canais e vídeos recentes para estudar')
        st.caption('Pontuação baseada em visualizações por dia e alcance relativo ao número público de inscritos. É um sinal de momento, não previsão de resultado.')
        for index, item in enumerate(results):
            st.markdown(f"**{item['signal']} · {item['score']}/100 — {item['title']}**")
            subscribers = f"{item['subscribers']:,}" if item['subscribers'] else 'não público'
            st.caption(
                f"Canal: {item['channel']} · {item['views']:,} visualizações em {item['age_days']} dia(s) "
                f"· ~{item['views_per_day']:,} visualizações/dia · inscritos: {subscribers}"
            )
            link_col, channel_col = st.columns(2)
            link_col.link_button('Abrir vídeo', item['video_url'], key=f"radar_video_{index}")
            channel_col.link_button('Abrir canal', item['channel_url'], key=f"radar_channel_{index}")
    st.divider()
    st.caption('Depois de escrever o tema abaixo, o Modo Viral cria cinco aberturas para você testar.')

if st.button('1. CRIAR / PREPARAR ROTEIRO', type='primary', use_container_width=True):
    if mode.startswith('Gerar'):
        if not (topic and gemini_key): st.error('Informe o tema e a chave gratuita do Gemini.')
        else:
            with st.spinner('Criando roteiro e cenas...'):
                try:
                    st.session_state.plan = generate_plan(gemini_key, topic, language, duration, style)
                except Exception:
                    st.error(
                        'Não foi possível gerar o roteiro com Gemini. Verifique se a chave está ativa, '
                        'se a API Gemini está disponível para a sua conta e tente novamente.'
                    )
    else:
        if not manual.strip(): st.error('Cole seu roteiro.')
        else:
            # Manual mode: user can edit search terms before generation.
            bits=[x.strip() for x in manual.replace('\n',' ').split('.') if x.strip()]
            scenes=[{'text':x,'search_query':topic or x[:60]} for x in bits[:8]] or [{'text':manual,'search_query':topic or 'technology'}]
            st.session_state.plan={'title':topic or 'Meu vídeo','narration':manual,'scenes':scenes}

plan=st.session_state.plan
if plan:
    st.subheader('Roteiro')
    plan['title']=st.text_input('Título', value=plan.get('title',''))
    plan['narration']=st.text_area('Narração — você pode editar antes de gerar', value=plan.get('narration',''), height=240)
    st.subheader('Buscas visuais')
    queries=[]
    for i,s in enumerate(plan.get('scenes',[])):
        q=st.text_input(f'Cena {i+1}', value=s.get('search_query',''), key=f'q{i}')
        if q.strip():
            queries.append(q.strip())

    st.subheader('🚀 Modo Viral — ganchos para os primeiros segundos')
    if st.button('GERAR 5 GANCHOS', use_container_width=True):
        st.session_state.viral_hooks = fallback_hooks(plan['title'] or topic)
    hooks = st.session_state.get('viral_hooks', [])
    if hooks:
        selected_hook = st.radio('Escolha o gancho que será usado no vídeo', hooks, key='selected_hook')
        if st.button('APLICAR GANCHO AO ROTEIRO'):
            if not plan['narration'].startswith(selected_hook):
                plan['narration'] = f'{selected_hook}\n\n{plan["narration"]}'
            st.success('Gancho aplicado ao início da narração.')

    st.subheader('💰 Laboratório de Títulos, Ganchos e CTA')
    if st.button('GERAR 5 OPÇÕES PARA MEU OBJETIVO', use_container_width=True):
        st.session_state.monetization_options = packaging_options(plan['title'] or topic, monetization_goal, destination)
    options = st.session_state.get('monetization_options', [])
    if options:
        choice = st.radio('Escolha a embalagem para a publicação', range(len(options)), format_func=lambda i: options[i]['title'])
        chosen = options[choice]
        st.caption(f"Gancho: {chosen['hook']}\n\nCTA: {chosen['cta']}")
        if st.button('USAR ESTA OPÇÃO NA PUBLICAÇÃO'):
            st.session_state.monetization_package = chosen
            st.success('Opção selecionada para a publicação.')

    if st.button('2. GERAR VÍDEO COMPLETO', type='primary', use_container_width=True):
        if not pexels_key:
            st.error('Informe a chave gratuita do Pexels em Streamlit Secrets ou na barra lateral.')
        elif not plan['narration'].strip():
            st.error('O roteiro está vazio.')
        elif not queries:
            st.error('Informe ao menos uma busca visual para o Pexels.')
        else:
            job=Path('output')/f'video_{int(time.time())}'; job.mkdir(parents=True,exist_ok=True)
            audio=str(job/'narration.mp3'); srt=str(job/'subtitles.srt'); out=str(job/'video_final.mp4')
            orient={'9:16 Vertical':'portrait','16:9 YouTube':'landscape','1:1 Quadrado':'square'}[fmt]
            dims={'9:16 Vertical':(1080,1920),'16:9 YouTube':(1920,1080),'1:1 Quadrado':(1080,1080)}[fmt]
            try:
                with st.status('Produzindo vídeo...', expanded=True) as status:
                    st.write('1/4 Gerando narração com Edge TTS...')
                    synthesize(plan['narration'], voice, audio)
                    dur=media_duration(audio)
                    st.write(f'2/4 Narração pronta ({dur:.1f}s). Buscando vídeos no Pexels...')
                    clips,credits=download_for_queries(pexels_key, queries, orient, str(job/'clips'))
                    if not clips: raise RuntimeError('Pexels não retornou vídeos para estas buscas.')
                    st.write(f'3/4 {len(clips)} clipes obtidos. Criando legendas...')
                    make_srt(plan['narration'], dur, srt)
                    st.write('4/4 Montando o MP4 com FFmpeg...')
                    render_video(clips,audio,srt,out,*dims,burn_subtitles=True)
                    (job/'credits.json').write_text(json.dumps(credits, ensure_ascii=False, indent=2), encoding='utf-8')
                    copy = st.session_state.monetization_package or publish_copy(plan['title'], topic or plan['title'], hooks)
                    st.session_state.last_video = {'path': out, 'copy': copy}
                    st.session_state.publish_title = copy['title']
                    st.session_state.publish_description = copy['description']
                    status.update(label='Vídeo concluído!', state='complete')
            except Exception as e:
                st.error(f'Falha: {e}')
                st.caption('O vídeo parcial, se existir, fica na pasta output do ambiente de execução.')

    last_video = st.session_state.get('last_video')
    if last_video and Path(last_video['path']).exists():
        video_path = last_video['path']
        copy = last_video['copy']
        st.video(video_path)
        with open(video_path,'rb') as f:
            st.download_button('BAIXAR MP4', f, file_name='videoturbo.mp4', mime='video/mp4', use_container_width=True)
        st.subheader('📣 Publicar e compartilhar')
        st.text_input('Título para publicação', value=copy['title'], key='publish_title')
        st.text_area('Descrição sugerida', value=copy['description'], key='publish_description', height=120)
        st.subheader('▶️ Publicar diretamente no YouTube')
        if not youtube_configured(youtube_config):
            st.info('Configure o OAuth do YouTube em Streamlit Secrets para liberar a publicação direta.')
        elif 'youtube_credentials' not in st.session_state:
            st.warning('Conecte seu canal no início da página e gere o vídeo novamente. A conexão não publica nada automaticamente.')
        else:
            st.success('Canal conectado nesta sessão.')
            privacy = st.selectbox('Visibilidade no YouTube', ['private', 'unlisted', 'public'], format_func=lambda x: {'private':'Privado (recomendado para teste)', 'unlisted':'Não listado', 'public':'Público'}[x])
            if st.button('PUBLICAR NO YOUTUBE', type='primary', use_container_width=True):
                try:
                    with st.status('Enviando vídeo para o YouTube...', expanded=True) as upload_status:
                        st.write('Enviando o MP4 para o canal conectado...')
                        video_id = upload_video(
                            st.session_state.youtube_credentials, video_path,
                            st.session_state.publish_title, st.session_state.publish_description, privacy,
                        )
                        upload_status.update(label='Vídeo publicado no YouTube!', state='complete')
                    st.success('Publicação concluída.')
                    st.link_button('ABRIR VÍDEO NO YOUTUBE', f'https://youtu.be/{video_id}', use_container_width=True)
                except Exception as exc:
                    st.error(f'Não foi possível publicar no YouTube: {exc}')
        st.caption('Para as demais redes, o upload continua sendo feito na conta conectada a cada rede.')
        for network, url in share_links(copy['title'], copy['description']).items():
            if network == 'YouTube Studio':
                continue
            st.link_button(f'Abrir {network}', url)
