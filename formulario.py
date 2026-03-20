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
# Importante: Use uma "Senha de App" se for Gmail
EMAIL_ORIGEM = "seu_email@gmail.com" 
SENHA_APP = "sua_senha_de_app"
EMAIL_DESTINO = "victormoreiraicnv@gmail.com"

# ========== GERAR PDF DIVIDIDO ==========
def gerar_pdf(nome, respostas):
    arquivo_pdf = f"respostas_{nome.replace(' ', '_')}.pdf"
    c = canvas.Canvas(arquivo_pdf, pagesize=A4)
    width, height = A4

    # Estilos
    titulo_style = ParagraphStyle("Titulo", fontSize=18, leading=24, alignment=1, textColor=colors.darkblue)
    pergunta_style = ParagraphStyle("Pergunta", fontSize=12, leading=18, textColor=colors.HexColor("#003366"))
    resposta_style = ParagraphStyle("Resposta", fontSize=11, leading=16, backColor=colors.whitesmoke, spaceAfter=10)

    def draw_paragraph(text, style, x, y, max_width):
        p = Paragraph(text, style)
        w, h = p.wrap(max_width, 1000)
        p.drawOn(c, x, y - h)
        return h

    # Página 1 - Bloco 1
    y = height - 50
    y -= draw_paragraph("📝 Diagnóstico de Gestão e Pessoas - Globus", titulo_style, 50, y, width - 100) + 20
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y, f"👤 Colaborador: {nome}")
    y -= 30
    c.setFillColor(colors.HexColor("#4B8BBE"))
    c.rect(50, y - 20, width - 100, 25, fill=1, stroke=0)
    c.setFillColor(colors.white)
    c.drawString(55, y - 10, "🔹 Bloco 1: Cultura e Relacionamento")
    y -= 40

    for i, (pergunta, resposta) in enumerate(respostas[:6], start=1):
        y -= draw_paragraph(f"{i}. {pergunta}", pergunta_style, 50, y, width - 100) + 5
        y -= draw_paragraph(resposta.strip() or "Não respondido", resposta_style, 50, y, width - 100) + 15

    # Página 2 - Bloco 2
    c.showPage()
    y = height - 50
    c.setFillColor(colors.HexColor("#4B8BBE"))
    c.rect(50, y - 20, width - 100, 25, fill=1, stroke=0)
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 12)
    c.drawString(55, y - 10, "🔹 Bloco 2: Liderança e Processos")
    y -= 40

    for i, (pergunta, resposta) in enumerate(respostas[6:], start=7):
        y -= draw_paragraph(f"{i}. {pergunta}", pergunta_style, 50, y, width - 100) + 5
        y -= draw_paragraph(resposta.strip() or "Não respondido", resposta_style, 50, y, width - 100) + 15

    c.save()
    return arquivo_pdf

# ========== ENVIAR E-MAIL COM ANEXO ==========
def enviar_pdf_por_email(nome, arquivo_pdf):
    msg = MIMEMultipart()
    msg["From"] = EMAIL_ORIGEM
    msg["To"] = EMAIL_DESTINO
    msg["Subject"] = f"📋 Diagnóstico Globus: {nome}"

    corpo = f"Olá,\n\nSegue em anexo o formulário de Gestão de Pessoas preenchido por {nome}.\n\nAtenciosamente,\nSistema de Gestão Globus"
    msg.attach(MIMEText(corpo, "plain"))

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
    except Exception as e:
        print("Erro ao enviar:", e)
        return False
    finally:
        if os.path.exists(arquivo_pdf):
            os.remove(arquivo_pdf)

# ========== STREAMLIT APP ==========
st.set_page_config(page_title="Gestão Globus", layout="centered")
st.title("👥 Diagnóstico de Gestão e Pessoas")

with st.form("formulario"):
    nome = st.text_input("👤 Seu nome completo")

    st.markdown("### 🔹 Cultura e Relacionamento")
    perguntas1 = [
        "Como você descreve sua relação de trabalho com os demais membros da equipe comercial e operacional?",
        "Diante de um conflito entre colegas sobre uma demanda de seguro/previdência, como você costuma intervir?",
        "O que você considera essencial para manter um ambiente de trabalho motivado e disciplinado?",
        "Como você lida com feedbacks construtivos sobre sua performance técnica ou comportamental?",
        "De que forma você contribui para que os novos colaboradores se adaptem rápido à rotina da corretora?",
        "Qual valor da Globus você mais pratica no seu dia a dia e por quê?"
    ]
    respostas1 = [st.text_area(p) for p in perguntas1]

    st.markdown("### 🔹 Liderança e Processos")
    perguntas2 = [
        "Se você fosse responsável por organizar as demandas da semana, como faria a divisão entre a equipe?",
        "Como você identifica que um colega está sobrecarregado e como agiria para ajudar?",
        "Para você, qual a maior dificuldade em gerir processos que dependem da colaboração de várias pessoas?",
        "Como você reage quando um erro operacional acontece? Foca na solução imediata ou na busca pelo responsável?",
        "Se você tivesse que sugerir uma mudança na forma como o time se comunica hoje, qual seria?",
        "Como você enxerga seu papel no crescimento da Globus nos próximos meses?"
    ]
    respostas2 = [st.text_area(p) for p in perguntas2]

    enviado = st.form_submit_button("📨 Enviar Diagnóstico")

if enviado and nome.strip():
    respostas_completas = list(zip(perguntas1 + perguntas2, respostas1 + respostas2))
    pdf_path = gerar_pdf(nome, respostas_completas)
    sucesso = enviar_pdf_por_email(nome, pdf_path)

    if sucesso:
        st.success(f"✅ Diagnóstico enviado com sucesso para {EMAIL_DESTINO}!")
    else:
        st.error("❌ Erro ao enviar. Verifique as credenciais de SMTP no código.")
elif enviado:
    st.warning("⚠️ Por favor, preencha seu nome para identificar o formulário.")
