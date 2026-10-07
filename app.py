import streamlit as st
import requests
import re
from urllib.parse import quote
from bs4 import BeautifulSoup

st.set_page_config(page_title="Fanatics Ofertas - Bot", page_icon="🔥", layout="centered")

def extrair_dados_nuvem(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept-Language": "pt-BR,pt;q=0.9"
    }
    
    try:
        resposta = requests.get(url, headers=headers, timeout=15, allow_redirects=True)
        url_final = resposta.url
        html = resposta.text

        nome = ""
        preco_at = ""
        preco_ant = ""

        # Tenta extrair via código MLB/MLBU se houver no link ou texto
        match = re.search(r'(MLB[A-Z]*\d+)', url_final + " " + html, re.IGNORECASE)
        if match:
            item_id = match.group(1).upper()
            try:
                api_prod = requests.get(f"https://api.mercadolibre.com/products/{item_id}", timeout=5).json()
                if "name" in api_prod:
                    nome = api_prod.get("name", "")
                    winner = api_prod.get("buy_box_winner", {})
                    if winner:
                        preco_at = str(winner.get("price", ""))
                        preco_ant = str(winner.get("original_price", ""))
            except:
                pass
            
            if not nome:
                try:
                    api_item = requests.get(f"https://api.mercadolibre.com/items/{item_id}", timeout=5).json()
                    if "title" in api_item:
                        nome = api_item.get("title", "")
                        preco_at = str(api_item.get("price", ""))
                        preco_ant = str(api_item.get("original_price", ""))
                except:
                    pass

        # Fallback de Leitura HTML caso a API não traga tudo
        if not nome or not preco_at:
            soup = BeautifulSoup(html, 'html.parser')
            
            if not nome:
                h1 = soup.find("h1")
                if h1:
                    nome = h1.text.strip()
                else:
                    meta = soup.find("meta", property="og:title")
                    if meta:
                        nome = meta.get("content", "").split(" - ")[0].split(" | ")[0].strip()

            if not preco_ant:
                tag_riscada = soup.find("s")
                if tag_riscada:
                    fracao_antiga = tag_riscada.find(class_=lambda c: c and "fraction" in c)
                    if fracao_antiga:
                        preco_ant = fracao_antiga.text.strip()

            if not preco_at:
                fracoes = soup.find_all(class_=lambda c: c and "fraction" in c)
                for f in fracoes:
                    if not f.find_parent("s"):
                        preco_at = f.text.strip()
                        break

        # Formatação de preços para o padrão brasileiro (R$)
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

    except Exception:
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
st.title("🔥 Fanatics Ofertas")
st.write("Cole o seu link de afiliado. O bot puxa os dados e cria o texto para partilhar!")

if "nome_prod" not in st.session_state: st.session_state.nome_prod = ""
if "preco_at" not in st.session_state: st.session_state.preco_at = ""
if "preco_ant" not in st.session_state: st.session_state.preco_ant = ""
if "link_prod" not in st.session_state: st.session_state.link_prod = ""

link_input = st.text_input("🔗 Cole o Link de Afiliado (ex: https://meli.la/...):", placeholder="https://meli.la/...")

col_b1, col_b2 = st.columns(2)
with col_b1:
    btn_buscar = st.button("🤖 Puxar Dados", type="primary", use_container_width=True)
with col_b2:
    btn_limpar = st.button("🧹 Limpar", use_container_width=True)

if btn_limpar:
    st.session_state.nome_prod = ""
    st.session_state.preco_at = ""
    st.session_state.preco_ant = ""
    st.session_state.link_prod = ""
    st.rerun()

if btn_buscar:
    if link_input:
        with st.spinner("A consultar servidores..."):
            nome, atual, antigo = extrair_dados_nuvem(link_input)
            
            if nome or atual:
                st.session_state.link_prod = link_input
                st.session_state.nome_prod = nome
                st.session_state.preco_at = atual
                st.session_state.preco_ant = antigo
                st.success("✅ Dados extraídos com sucesso!")
            else:
                st.error("Não foi possível puxar automaticamente. Preencha os campos abaixo.")
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

    if st.button("✨ GERAR TEXTO DA OFERTA", type="primary", use_container_width=True):
        st.session_state.oferta_gerada = gerar_texto_whatsapp(
            st.session_state.nome_prod,
            st.session_state.preco_at,
            st.session_state.preco_ant,
            st.session_state.link_prod
        )

# Se já gerou a oferta, mostra a caixa de texto e o botão direto para o WhatsApp
if "oferta_gerada" in st.session_state and st.session_state.oferta_gerada:
    st.divider()
    st.subheader("📱 Oferta Pronta para Partilhar")
    st.code(st.session_state.oferta_gerada, language="text")
    
    # Prepara o link codificado para o botão oficial do WhatsApp
    texto_encoded = quote(st.session_state.oferta_gerada)
    whatsapp_url = f"https://api.whatsapp.com/send?text={texto_encoded}"
    
    # Botão visual com link direto (Abre o WhatsApp automaticamente)
    st.markdown(
        f"""
        <a href="{whatsapp_url}" target="_blank" style="text-decoration: none;">
            <div style="background-color: #25D366; color: white; padding: 12px 20px; border-radius: 8px; text-align: center; font-weight: bold; font-size: 16px;">
                🚀 PARTILHAR DIRETAMENTE NO WHATSAPP
            </div>
        </a>
        """,
        unsafe_allow_html=True
    )