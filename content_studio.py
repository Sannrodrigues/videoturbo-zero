def retention_outline(topic):
    t=topic or 'este tema'
    return [('0–3s · Gancho',f'Pare: há uma parte de {t} que quase ninguém explica.'),('3–12s · Problema',f'Mostre o erro ou dor mais comum em {t}.'),('12–30s · Virada',f'Apresente o ponto que muda a forma de entender {t}.'),('30–50s · Prova',f'Dê um exemplo simples e verificável.'),('Final · CTA','Diga claramente qual é o próximo passo: comentário, inscrição ou link na descrição.')]
def series(topic):
    t=topic or 'este tema'
    return [f'{t}: o erro #{i} que iniciantes precisam evitar' for i in range(1,6)] + [f'{t}: passo #{i} para começar com mais clareza' for i in range(1,6)]
def multiformat(topic, cta):
    t=topic or 'este tema'; c=cta or 'Veja o link na descrição.'
    return {'Telegram':f'Novo vídeo: {t}.\n\n{c}','Facebook':f'Você já percebeu este ponto sobre {t}? Gravei um vídeo curto explicando.\n\n{c}','Instagram':f'{t}: o ponto que pode mudar sua visão.\n\n{c}\n\n#reels #conteudo','Comunidade YouTube':f'Qual é sua maior dúvida sobre {t}? Responda aqui e veja o novo vídeo. {c}'}
