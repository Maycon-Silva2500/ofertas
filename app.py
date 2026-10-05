import streamlit as st
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
import time

st.set_page_config(page_title="Gerador de Ofertas - Bot", page_icon="🔥", layout="centered")

def extrair_com_chrome_real(url):
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")  # Roda de forma invisível
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36")
    
    driver = None
    try:
        # Usa o Chrome que já está instalado no seu computador automaticamente
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        
        driver.get(url)
        time.sleep(3) # Aguarda o JavaScript renderizar a página e os preços
        
        html_content = driver.page_source
        driver.quit()
        
        soup = BeautifulSoup(html_content, 'html.parser')

        nome = ""
        preco_at = ""
        preco_ant = ""

        # 1. Pega o Nome do Produto
        h1 = soup.find("h1")
        if h1:
            nome = h1.text.strip()
        else:
            meta = soup.find("meta", property="og:title")
            if meta:
                nome = meta.get("content", "").split(" - ")[0].strip()

        # 2. Pega o Preço Antigo (Riscado)
        tag_riscada = soup.find("s")
        if tag_riscada:
            fracao_antiga = tag_riscada.find(class_=lambda c: c and "fraction" in c)
            if fracao_antiga:
                preco_ant = fracao_antiga.text.strip()

        # 3. Pega o Preço Atual (Não riscado)
        fracoes = soup.find_all(class_=lambda c: c and "fraction" in c)
        for f in fracoes:
            if not f.find_parent("s"):
                preco_at = f.text.strip()
                break

        # Formatação para reais
        try:
            if preco_at and preco_at != "None":
                preco_at = f"{float(preco_at.replace('.', '').replace(',', '.')):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        except:
            pass

        try:
            if preco_ant and preco_ant != "None":
                preco_ant = f"{float(preco_ant.replace('.', '').replace(',', '.')):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            else:
                preco_ant = ""
        except:
            preco_ant = ""

        return nome, preco_at, preco_ant

    except Exception as e:
        if driver:
            try:
                driver.quit()
            except:
                pass
        return None, None, None

def gerar_texto_whatsapp(nome, preco_atual, preco_antigo, link):
    texto = f"🚨 *OFERTA DISPONÍVEL!*\n\n"
    texto += f"*{nome}*\n\n"
    
    if preco_antigo:
        texto += f"💰 De: ~R$ {preco_antigo}~\n"
    
    texto += f"🔥 Por apenas: *R$ {preco_atual}*\n\n"
    texto += f"Aproveite e garanta o seu agora mesmo!\n\n"
    texto += f"⚠️ _Preço e disponibilidade podem mudar._\n\n"
    texto += f"📎 *GARANTA O SEU:*\n{link}"
    
    return texto

# --- INTERFACE GRÁFICA ---
st.title("🔥 Bot de Ofertas com Chrome Real")
st.write("Cole o seu link curto de afiliado. O robô utiliza o seu próprio navegador Google Chrome para ler o produto!")

if "nome_prod" not in st.session_state: st.session_state.nome_prod = ""
if "preco_at" not in st.session_state: st.session_state.preco_at = ""
if "preco_ant" not in st.session_state: st.session_state.preco_ant = ""
if "link_prod" not in st.session_state: st.session_state.link_prod = ""

link_input = st.text_input("🔗 Cole o Link de Afiliado:", placeholder="https://meli.la/...")

col_b1, col_b2 = st.columns(2)
with col_b1:
    btn_buscar = st.button("🤖 Puxar Dados com Chrome", type="primary", use_container_width=True)
with col_b2:
    btn_limpar = st.button("🧹 Limpar Dados", use_container_width=True)

if btn_limpar:
    st.session_state.nome_prod = ""
    st.session_state.preco_at = ""
    st.session_state.preco_ant = ""
    st.session_state.link_prod = ""
    st.rerun()

if btn_buscar:
    if link_input:
        with st.spinner("🚗 A abrir o motor do Google Chrome para ler o produto..."):
            nome, atual, antigo = extrair_com_chrome_real(link_input)
            
            if nome or atual:
                st.session_state.link_prod = link_input
                st.session_state.nome_prod = nome
                st.session_state.preco_at = atual
                st.session_state.preco_ant = antigo
                st.success("✅ Dados extraídos com sucesso pelo Chrome!")
            else:
                st.error("Não foi possível carregar a página. Verifique se o link está correto.")
    else:
        st.warning("Cole o link antes de efetuar a busca.")

if st.session_state.nome_prod or st.session_state.preco_at:
    st.divider()
    st.subheader("🛒 Conferir e Gerar")
    
    st.session_state.nome_prod = st.text_area("Nome do Produto:", value=st.session_state.nome_prod)
    
    col1, col2 = st.columns(2)
    with col1:
        st.session_state.preco_at = st.text_input("Preço Atual", value=st.session_state.preco_at)
    with col2:
        st.session_state.preco_ant = st.text_input("Preço Antigo", value=st.session_state.preco_ant)

    if st.button("✨ GERAR TEXTO PARA O WHATSAPP", type="primary", use_container_width=True):
        oferta_final = gerar_texto_whatsapp(
            st.session_state.nome_prod,
            st.session_state.preco_at,
            st.session_state.preco_ant,
            st.session_state.link_prod
        )
        
        st.divider()
        st.subheader("📱 Copie a Oferta Abaixo")
        st.code(oferta_final, language="text")