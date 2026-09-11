import streamlit as st

from llm import generate_plan
from stock import download_for_queries
from tts import synthesize
from render import media_duration, make_srt, render_video

st.set_page_config(page_title='VideoTurbo Zero', page_icon='🎬', layout='wide')
st.title('🎬 VideoTurbo Zero')
st.caption('Tema → roteiro → voz → vídeos gratuitos → legendas → MP4. Sem assinatura e sem créditos.')

with st.sidebar:
    st.header('Configuração gratuita')
    gemini_key=st.text_input('Gemini API Key (para roteiro automático)', type='password')
    pexels_key=st.text_input('Pexels API Key (vídeos gratuitos)', type='password')
    st.info('As chaves ficam apenas nesta sessão do navegador e não são gravadas pelo app.')

col1,col2=st.columns([2,1])
with col1:
    topic=st.text_input('Tema do vídeo', placeholder='Ex.: Como a inteligência artificial está mudando pequenas empresas')
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

if st.button('1. CRIAR / PREPARAR ROTEIRO', type='primary', use_container_width=True):
    if mode.startswith('Gerar'):
        if not (topic and gemini_key): st.error('Informe o tema e a chave gratuita do Gemini.')
        else:
            with st.spinner('Criando roteiro e cenas...'):
                st.session_state.plan=generate_plan(gemini_key, topic, language, duration, style)
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
        queries.append(q)

    if st.button('2. GERAR VÍDEO COMPLETO', type='primary', use_container_width=True):
        if not pexels_key: st.error('Informe a chave gratuita do Pexels.')
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
                    (job/'credits.json').write_text(json.dumps(credits,ensure_ascii=False,indent=2),encoding='utf-8')
                    status.update(label='Vídeo concluído!', state='complete')
                st.video(out)
                with open(out,'rb') as f: st.download_button('BAIXAR MP4', f, file_name='videoturbo.mp4', mime='video/mp4', use_container_width=True)
            except Exception as e:
                st.error(f'Falha: {e}')
