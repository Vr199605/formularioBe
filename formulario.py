import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
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

# ========== CONFIGURAÇÕES DE E-MAIL ==========
EMAIL_ORIGEM = "seu_email@gmail.com" 
SENHA_APP = "sua_senha_de_app"
EMAIL_DESTINO = "victormoreiraicnv@gmail.com"
URL_PLANILHA = "SUA_URL_DA_PLANILHA_AQUI"

# ========== FUNÇÃO GERAR PDF ==========
def gerar_pdf_360(dados, n_colab, n_gestor, media_final):
    nome = dados['Nome']
    arquivo_pdf = f"AVALIACAO_360_{nome.replace(' ', '_')}.pdf"
    c = canvas.Canvas(arquivo_pdf, pagesize=A4)
    width, height = A4
    
    c.setFont("Helvetica-Bold", 14)
    c.drawCentredString(width/2, height-50, "RELATÓRIO DE AVALIAÇÃO 360° - GLOBUS")
    
    c.setFont("Helvetica", 10)
    c.drawString(50, height-80, f"Colaborador: {nome} | Área: {dados['Area']}")
    c.drawString(50, height-95, f"Gestor: {dados['Gestor']} | Período: {dados['Periodo']}")
    c.line(50, height-105, width-50, height-105)
    
    y = height - 130
    c.setFont("Helvetica-Bold", 11)
    c.drawString(50, y, "Notas Comparativas:")
    y -= 20
    
    for i, p in enumerate(dados['Perguntas']):
        c.setFont("Helvetica", 9)
        c.drawString(50, y, f"{i+1}. {p[:55]}...")
        c.drawString(380, y, f"Auto (40%): {n_colab[i]}")
        c.drawString(480, y, f"Gestor (60%): {n_gestor[i]}")
        y -= 20
        
    y -= 30
    c.setFont("Helvetica-Bold", 14)
    c.setFillColor(colors.darkblue)
    c.drawString(50, y, f"MÉDIA FINAL PONDERADA: {media_final:.2f}")
    c.save()
    return arquivo_pdf

# ========== INTERFACE STREAMLIT ==========
st.set_page_config(page_title="Maldivas 360", layout="centered")
conn = st.connection("gsheets", type=GSheetsConnection)

st.title("🏝️ PROGRAMA MALDIVAS - AVALIAÇÃO 360°")

perfil = st.radio("Selecione seu perfil:", ["Colaborador", "Gestor"], horizontal=True)

with st.container(border=True):
    nome_input = st.text_input("Nome Completo do Colaborador*").strip()
    col1, col2 = st.columns(2)
    with col1:
        area = st.text_input("Área*")
    with col2:
        gestor = st.text_input("Gestor Direto*")
    periodo = st.selectbox("Período", ["1º Semestre 2026", "2º Semestre 2026"])

perguntas = [
    "Qualidade técnica e precisão nas tarefas operacionais?",
    "Cumprimento de prazos e organização de demandas?",
    "Proatividade em sugerir melhorias nos processos?",
    "Colaboração e trabalho em equipe?",
    "Resiliência e postura profissional sob pressão?",
    "Alinhamento com a cultura e valores da empresa?"
]

notas_atuais = []
justificativas = []

st.subheader(f"Formulário de {perfil}")
for i, p in enumerate(perguntas):
    st.write(f"**{i+1}. {p}**")
    n = st.selectbox(f"Nota para: {p[:20]}...", [1,2,3,4,5], index=2, key=f"n_{i}")
    notas_atuais.append(n)
    
    obs = ""
    if n in [1, 5]:
        obs = st.text_area(f"Justificativa obrigatória (Nota {n})*", key=f"obs_{i}", placeholder="Explique o motivo...")
    justificativas.append(obs)
    st.divider()

dissertativa = st.text_area("Como você enxerga seu papel no crescimento da Globus nos próximos meses? Como a Globus pode ajudar você nesse processo ?*")

if st.button("🚀 Finalizar e Enviar"):
    df = conn.read(spreadsheet=URL_PLANILHA)
    
    # VALIDAÇÃO DE CAMPOS
    if not nome_input or not area or not dissertativa:
        st.error("Preencha todos os campos obrigatórios!")
    else:
        if perfil == "Colaborador":
            # SALVAR AUTOAVALIAÇÃO
            novo_registro = pd.DataFrame([{
                "Nome": nome_input, "Area": area, "Gestor": gestor, "Periodo": periodo,
                "Notas_Colab": str(notas_atuais), "Dissert_Colab": dissertativa, "Status": "Pendente Gestor"
            }])
            df_atualizado = pd.concat([df, novo_registro], ignore_index=True)
            conn.update(spreadsheet=URL_PLANILHA, data=df_atualizado)
            st.success("✅ Autoavaliação enviada! Agora seu gestor deve preencher a parte dele.")
            
        else: # PERFIL GESTOR
            # BUSCAR DADOS DO COLABORADOR
            match = df[df["Nome"] == nome_input]
            if match.empty:
                st.error("❌ Erro: O colaborador ainda não realizou a autoavaliação.")
            else:
                notas_c = eval(match.iloc[-1]["Notas_Colab"])
                m_c = sum(notas_c) / len(notas_c)
                m_g = sum(notas_atuais) / len(notas_atuais)
                
                # CÁLCULO 40% COLAB / 60% GESTOR
                media_ponderada = (m_c * 0.4) + (m_g * 0.6)
                
                # ATUALIZAR PLANILHA COM DADOS DO GESTOR
                df.loc[df[df["Nome"] == nome_input].index[-1], "Notas_Gestor"] = str(notas_atuais)
                df.loc[df[df["Nome"] == nome_input].index[-1], "Dissert_Gestor"] = dissertativa
                df.loc[df[df["Nome"] == nome_input].index[-1], "Media_Final"] = media_ponderada
                conn.update(spreadsheet=URL_PLANILHA, data=df)
                
                # GERAR RESULTADO
                dados_pdf = {'Nome': nome_input, 'Area': area, 'Gestor': gestor, 'Periodo': periodo, 'Perguntas': perguntas}
                pdf_path = gerar_pdf_360(dados_pdf, notas_c, notas_atuais, media_ponderada)
                
                st.success(f"🎉 Avaliação Consolidada! Média Final: {media_ponderada:.2f}")
                st.balloons()
