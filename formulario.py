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
    y -= draw_paragraph("📝 Formulário de Perfil Profissional", titulo_style, 50, y, width - 100) + 20
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y, f"👤 Nome: {nome}")
    y -= 30
    c.setFillColor(colors.HexColor("#4B8BBE"))
    c.rect(50, y - 20, width - 100, 25, fill=1, stroke=0)
    c.setFillColor(colors.white)
    c.drawString(55, y - 10, "🔹 Primeiro Bloco")
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
    c.drawString(55, y - 10, "🔹 Segundo Bloco")
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
    msg["Subject"] = f"📋 Formulário Respondido por {nome}"

    corpo = f"Olá,\n\nSegue em anexo o formulário preenchido por {nome}.\n\nAtenciosamente,\nSistema Automatizado"
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
st.set_page_config(page_title="Formulário Profissional", layout="centered")
st.title("📝 Formulário de Perfil Profissional")

with st.form("formulario"):
    nome = st.text_input("👤 Seu nome completo")

    st.markdown("### 🔹 Primeiro Bloco")
    perguntas1 = [
        "Como você se sente ao lidar com clientes ou apresentar uma ideia para outras pessoas?",
        "Você já precisou convencer alguém a tomar uma decisão importante? Como fez isso?",
        "Você gosta de metas e desafios? Pode dar um exemplo recente?",
        "O que você faria se tivesse que bater uma meta de vendas em pouco tempo?",
        "Você prefere trabalhar sozinho ou em ambientes onde precisa interagir constantemente com outras pessoas?",
        "Como reage quando recebe um “não”? O que faz depois?"
    ]
    respostas1 = [st.text_area(p) for p in perguntas1]

    st.markdown("### 🔹 Segundo Bloco")
    perguntas2 = [
        "Onde você se imagina profissionalmente em 3 a 5 anos?",
        "O que te motiva a fazer mais do que o esperado no trabalho?",
        "Você se considera uma pessoa competitiva? Em que situações isso aparece?",
        "Já assumiu responsabilidades que não eram obrigatórias? Pode dar um exemplo?",
        "Se você tivesse liberdade para escolher um novo projeto ou cargo, qual seria e por quê?",
        "Qual sua reação ao ver alguém crescendo rápido dentro da empresa?"
    ]
    respostas2 = [st.text_area(p) for p in perguntas2]

    enviado = st.form_submit_button("📨 Enviar por e-mail")

if enviado and nome.strip():
    respostas_completas = list(zip(perguntas1 + perguntas2, respostas1 + respostas2))
    pdf_path = gerar_pdf(nome, respostas_completas)
    sucesso = enviar_pdf_por_email(nome, pdf_path)

    if sucesso:
        st.success("✅ PDF gerado e enviado por e-mail com sucesso!")
    else:
        st.error("❌ Erro ao enviar o e-mail. Verifique credenciais.")
elif enviado:
    st.warning("⚠️ Por favor, preencha seu nome.")
