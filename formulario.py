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

# ========== CONFIGURAÇÕES (SUBSTITUA AQUI) ==========
EMAIL_ORIGEM = "seu_email@gmail.com" 
SENHA_APP = "groh qyqk yvzb agpu"  # Use a senha de 16 dígitos gerada pelo Google
EMAIL_DESTINO = "victormoreiraicnv@gmail.com"

# ========== FUNÇÃO: GERAR PDF ==========
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
        if y < 150: 
            c.showPage()
            y = height - 50
        y -= draw_paragraph(f"<b>{i}. {pergunta}</b> - Nota: {nota}", pergunta_style, 50, y, width - 100) + 5
        if justificativa:
            y -= draw_paragraph(f"Justificativa: {justificativa}", resposta_style, 50, y, width - 100) + 10
        y -= 10

    if y < 150:
        c.showPage()
        y = height - 50

    y -= 10
    y -= draw_paragraph("<b>Visão de Futuro e Suporte:</b>", pergunta_style, 50, y, width - 100) + 5
    y -= draw_paragraph(dissertativa, resposta_style, 50, y, width - 100) + 20

    y -= 30
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y, f"MÉDIA FINAL (40%): {media_final:.2f}")
    
    c.save()
    return arquivo_pdf

# ========== FUNÇÃO: ENVIAR E-MAIL ==========
def enviar_email(nome, arquivo_pdf, media):
    msg = MIMEMultipart()
    msg["From"] = EMAIL_ORIGEM
    msg["To"] = EMAIL_DESTINO
    msg["Subject"] = f"Avaliação Maldivas - {nome}"
    
    corpo = f"Avaliação de {nome} concluída.\nMédia Final: {media:.2f}"
    msg.attach(MIMEText(corpo, "plain"))

    try:
        with open(arquivo_pdf, "rb") as f:
            parte = MIMEBase("application", "pdf")
            parte.set_payload(f.read())
            encoders.encode_base64(parte)
            parte.add_header("Content-Disposition", f"attachment; filename={os.path.basename(arquivo_pdf)}")
            msg.attach(parte)

        # Configuração SMTP recomendada para Gmail
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()  # Camada de segurança
        server.login(EMAIL_ORIGEM, SENHA_APP)
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        st.error(f"Erro técnico no envio: {e}")
        return False
    finally:
        # Garante que o arquivo temporário seja deletado
        if os.path.exists(arquivo_pdf):
            os.remove(arquivo_pdf)

# ========== INTERFACE STREAMLIT ==========
st.set_page_config(page_title="Avaliação Maldivas", layout="centered")
st.title("🏝️ PROGRAMA DE AVALIAÇÃO DE DESEMPENHO")

# CAMPOS DE CABEÇALHO
col1, col2 = st.columns(2)
with col1:
    nome = st.text_input("Nome do Avaliado*")
    area = st.text_input("Qual sua área*")
with col2:
    ano = st.selectbox("Qual ano", ["2026", "2027", "2028"])
    periodo = st.radio("Qual período", ["1º semestre", "2º semestre"], horizontal=True)
gestor = st.text_input("Gestor Direto*")

st.divider()

perguntas_texto = [
    "Qualidade técnica e precisão nas tarefas operacionais?",
    "Cumprimento de prazos e organização de demandas?",
    "Proatividade em sugerir melhorias nos processos?",
    "Colaboração e trabalho em equipe?",
    "Resiliência e postura profissional sob pressão?",
    "Alinhamento com a cultura e valores da empresa?"
]

respostas_coletadas = []
notas_para_media = []

# Loop das perguntas
for i, p in enumerate(perguntas_texto):
    st.write(f"**{i+1}. {p}**")
    nota = st.selectbox(f"Nota para pergunta {i+1}", options=[1, 2, 3, 4, 5], index=2, key=f"n_{i}")
    
    obs = ""
    if nota == 1 or nota == 5:
        obs = st.text_area(f"Justificativa obrigatória (Nota {nota})*", key=f"obs_{i}")
    
    respostas_coletadas.append((p, nota, obs))
    notas_para_media.append(nota)
    st.markdown("---")

# PERGUNTA FINAL E ENVIO
with st.form("botao_final"):
    dissertativa = st.text_area("Como você enxerga seu papel no crescimento da empresa e como podemos ajudar?*")
    enviar = st.form_submit_button("Finalizar e Enviar Avaliação")

if enviar:
    erros = []
    if not nome or not area or not gestor or not dissertativa:
        erros.append("Preencha todos os campos obrigatórios.")
    
    for i, (p, nota, obs) in enumerate(respostas_coletadas):
        if (nota == 1 or nota == 5) and len(obs.strip()) < 5:
            erros.append(f"A pergunta {i+1} exige justificativa.")

    if erros:
        for erro in erros: st.error(erro)
    else:
        media_simples = sum(notas_para_media) / len(notas_para_media)
        media_final = media_simples * 0.40
        dados_cabecalho = {"Nome": nome, "Ano": ano, "Periodo": periodo, "Area": area, "Gestor": gestor}
        
        with st.spinner("Gerando PDF e enviando e-mail..."):
            pdf_path = gerar_pdf(dados_cabecalho, respostas_coletadas, dissertativa, media_final)
            if enviar_email(nome, pdf_path, media_final):
                st.success(f"Enviado com sucesso! Média Final (40%): {media_final:.2f}")
                st.balloons()
            else:
                st.error("Falha no envio. Verifique a Senha de App e o E-mail de Origem.")
