import streamlit as st
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email import encoders
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.platypus import Paragraph
from reportlab.lib.styles import ParagraphStyle

# ========== CONFIGURAÇÕES ==========
EMAIL_ORIGEM = "seu_email@gmail.com" 
SENHA_APP = "yksp blsm viin nowj"
EMAIL_DESTINO = "victormoreiraicnv@gmail.com"

# ========== GERAR PDF ==========
def gerar_pdf(dados_cabecalho, respostas, dissertativa, media_final):
    nome = dados_cabecalho['Nome']
    arquivo_pdf = f"AVALIACAO_MALDIVAS_{nome.replace(' ', '_')}.pdf"
    c = canvas.Canvas(arquivo_pdf, pagesize=A4)
    width, height = A4

    titulo_style = ParagraphStyle("Titulo", fontSize=16, leading=20, alignment=1, textColor=colors.darkblue)
    pergunta_style = ParagraphStyle("Pergunta", fontSize=11, leading=14, textColor=colors.HexColor("#003366"))
    resposta_style = ParagraphStyle("Resposta", fontSize=10, leading=14, backColor=colors.whitesmoke, leftIndent=10)

    def draw_paragraph(text, style, x, y, max_width):
        p = Paragraph(text, style)
        w, h = p.wrap(max_width, 1000)
        p.drawOn(c, x, y - h)
        return h

    y = height - 50
    y -= draw_paragraph("🏝️ PROGRAMA DE AVALIAÇÃO DE DESEMPENHO INDIVIDUAL MALDIVAS", titulo_style, 50, y, width - 100) + 20
    
    c.setFont("Helvetica-Bold", 10)
    c.drawString(50, y, f"Colaborador: {nome} | Ano: {dados_cabecalho['Ano']} | Período: {dados_cabecalho['Periodo']}")
    y -= 15
    c.drawString(50, y, f"Área: {dados_cabecalho['Area']} | Gestor: {dados_cabecalho['Gestor']}")
    y -= 30

    for i, (pergunta, nota, justificativa) in enumerate(respostas, start=1):
        if y < 120: 
            c.showPage()
            y = height - 50
        y -= draw_paragraph(f"<b>{i}. {pergunta}</b> - Nota: {nota}", pergunta_style, 50, y, width - 100) + 5
        if justificativa:
            y -= draw_paragraph(f"Justificativa: {justificativa}", resposta_style, 50, y, width - 100) + 10
        y -= 10

    y -= 10
    y -= draw_paragraph("<b>Visão de Futuro e Suporte:</b>", pergunta_style, 50, y, width - 100) + 5
    y -= draw_paragraph(dissertativa, resposta_style, 50, y, width - 100) + 20

    y -= 20
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y, f"MÉDIA FINAL (40%): {media_final:.2f}")
    
    c.save()
    return arquivo_pdf

# ========== ENVIAR E-MAIL ==========
def enviar_email(nome, arquivo_pdf, media):
    msg = MIMEMultipart()
    msg["From"] = EMAIL_ORIGEM
    msg["To"] = EMAIL_DESTINO
    msg["Subject"] = f"Avaliação Maldivas - {nome}"
    msg.attach(MIMEText(f"Avaliação de {nome} concluída.\nMédia Final: {media:.2f}", "plain"))

    with open(arquivo_pdf, "rb") as f:
        parte = MIMEBase("application", "pdf")
        parte.set_payload(f.read())
        encoders.encode_base64(parte)
        parte.add_header("Content-Disposition", f"attachment; filename={arquivo_pdf}")
        msg.attach(parte)

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(EMAIL_ORIGEM, SENHA_APP)
            server.send_message(msg)
        return True
    except: return False
    finally:
        if os.path.exists(arquivo_pdf): os.remove(arquivo_pdf)

# ========== INTERFACE STREAMLIT ==========
st.set_page_config(page_title="Avaliação Maldivas", layout="centered")
st.title("🏝️ PROGRAMA DE AVALIAÇÃO DE DESEMPENHO INDIVIDUAL MALDIVAS")

# Fora do formulário para garantir que a interface atualize ao mudar a nota
if 'respostas_notas' not in st.session_state:
    st.session_state.respostas_notas = [3] * 6

with st.form("form_maldivas"):
    col1, col2 = st.columns(2)
    with col1:
        nome = st.text_input("Nome do Avaliado*")
        area = st.text_input("Qual sua área*")
    with col2:
        ano = st.selectbox("Qual ano", ["2026", "2027", "2028"])
        periodo = st.radio("Qual período", ["1º semestre", "2º semestre"], horizontal=True)
    gestor = st.text_input("Gestor Direto*")

    st.divider()
    
    preguntas_texto = [
        "Qualidade técnica e precisão nas tarefas operacionais?",
        "Cumprimento de prazos e organização de demandas?",
        "Proatividade em sugerir melhorias nos processos?",
        "Colaboração e trabalho em equipe?",
        "Resiliência e postura profissional sob pressão?",
        "Alinhamento com a cultura e valores da empresa?"
    ]

    respostas_finais_lista = []
    notas_para_media = []

    for i, p in enumerate(preguntas_texto):
        st.write(f"**{i+1}. {p}**")
        # Selectbox conforme imagem
        nota = st.selectbox(f"Selecione a nota para a pergunta {i+1}", options=[1, 2, 3, 4, 5], index=2, key=f"n_{i}")
        
        obs = ""
        # Lógica para aparecer o comentário obrigatório
        if nota == 1 or nota == 5:
            obs = st.text_area(f"Justificativa obrigatória (Nota {nota})*", placeholder="Explique o motivo desta nota...", key=f"obs_{i}")
        
        respostas_finais_lista.append((p, nota, obs))
        notas_para_media.append(nota)
        st.markdown("---")

    st.write("**Pergunta Dissertativa Final**")
    dissertativa = st.text_area("Como você enxerga seu papel no crescimento da Globus nos próximos meses? Como a Globus pode ajudar você nesse processo ?*")

    enviar = st.form_submit_button("Finalizar Avaliação")

if enviar:
    erros = []
    if not nome or not area or not gestor or not dissertativa:
        erros.append("Por favor, preencha todos os campos obrigatórios (*).")
    
    for i, (p, nota, obs) in enumerate(respostas_finais_lista):
        if (nota == 1 or nota == 5) and len(obs.strip()) < 5:
            erros.append(f"A pergunta {i+1} exige uma justificativa para a nota {nota}.")

    if erros:
        for erro in erros: st.error(erro)
    else:
        media_final = (sum(notas_para_media) / len(notas_para_media)) * 0.40
        dados_cabecalho = {"Nome": nome, "Ano": ano, "Periodo": periodo, "Area": area, "Gestor": gestor}
        
        pdf_path = gerar_pdf(dados_cabecalho, respostas_finais_lista, dissertativa, media_final)
        
        if enviar_email(nome, pdf_path, media_final):
            st.success(f"Avaliação enviada com sucesso! Média Final: {media_final:.2f}")
            st.balloons()
        else:
            st.error("Erro ao enviar e-mail. Verifique a Senha de App do Google.")
