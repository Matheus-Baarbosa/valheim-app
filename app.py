# ============================================================
# Valheim dos Amigos - app feito com Streamlit
# Para rodar:  streamlit run app.py
# ============================================================

import base64                    # transforma a imagem em texto para embutir na página
import html                      # protege textos com caracteres especiais (ex: &)
import io                        # trabalha com "arquivos" em memória
import unicodedata               # ajuda a tirar acentos dos nomes
from pathlib import Path         # forma moderna de lidar com pastas e arquivos

import pandas as pd              # biblioteca para ler e mexer em tabelas (CSV)
import streamlit as st           # biblioteca que cria o site
from PIL import Image            # biblioteca para redimensionar imagens (vem com o Streamlit)

# ------------------------------------------------------------
# 1) CONFIGURAÇÃO DA PÁGINA
# Precisa ser o PRIMEIRO comando do Streamlit no arquivo.
# ------------------------------------------------------------
st.set_page_config(
    page_title="Valheim dos Amigos",
    page_icon="⚔️",
    layout="wide",  # usa a tela toda
)

# Ordem dos biomas (segue a progressão do jogo)
ORDEM_BIOMAS = [
    "Prados", "Floresta Negra", "Oceano", "Pântano", "Montanha",
    "Planícies", "Terras da Névoa", "Terras de Cinzas",
]

# Pasta onde ficam as imagens das criaturas e os formatos aceitos
PASTA_IMAGENS = Path("imagens")
FORMATOS = ["png", "jpg", "jpeg", "webp"]

# Imagem de fundo do site
CAMINHO_FUNDO = Path("assets/fundo.jpg")

# Cor de destaque usada nos links/nomes, inspirada na wiki do Valheim
COR_ACENTO = "#e2712d"

# Tipos de dano que aparecem no filtro "Fraco a"
TIPOS_DANO = [
    "Contusão", "Perfuração", "Corte", "Gelo",
    "Raio", "Fogo", "Veneno", "Espírito", "Picareta",
]

# Estilo da tabela, no visual "wiki" (cabeçalho escuro, nomes em laranja)
ESTILO_TABELA = f"""
<style>
.tabela-criaturas {{ width:100%; border-collapse:collapse; font-size:0.92rem; }}
.tabela-criaturas th {{ text-align:left; padding:10px; font-size:0.78rem;
    text-transform:uppercase; letter-spacing:0.04em; color:rgba(242,237,228,0.75);
    background:rgba(0,0,0,0.28); border-bottom:2px solid rgba(226,113,45,0.4); }}
.tabela-criaturas td {{ padding:10px; vertical-align:middle;
    border-bottom:1px solid rgba(255,255,255,0.08); }}
.tabela-criaturas tr:hover td {{ background:rgba(226,113,45,0.08); }}
.tabela-criaturas .foto {{ width:72px; text-align:center; }}
.tabela-criaturas .foto img {{ max-height:64px; max-width:64px; border-radius:6px; }}
.tabela-criaturas .sem-foto {{ display:inline-block; width:56px; height:56px;
    line-height:56px; border:1px dashed rgba(255,255,255,0.3);
    border-radius:6px; opacity:0.45; }}
.tabela-criaturas .nome {{ font-weight:700; font-size:1rem; color:{COR_ACENTO}; }}
.tabela-criaturas .local {{ font-size:0.78rem; opacity:0.7; }}
.tabela-criaturas .notas {{ min-width:200px; opacity:0.9; }}
.selo {{ display:inline-block; padding:2px 10px; margin:2px 4px 2px 0;
    border-radius:12px; font-size:0.8rem; font-weight:600; }}
.selo-fraqueza {{ background:rgba(255,99,71,0.16); color:#ff9d7a;
    border:1px solid rgba(255,99,71,0.4); }}
.selo-resistencia {{ background:rgba(64,196,140,0.16); color:#7ee2b8;
    border:1px solid rgba(64,196,140,0.4); }}
.vazio {{ opacity:0.4; }}
</style>
"""

# ------------------------------------------------------------
# 2) FUNÇÕES AUXILIARES
# ------------------------------------------------------------

# @st.cache_data guarda o resultado na memória, então o arquivo
# não é lido de novo a cada clique. Fica mais rápido.
CAMINHO_CSV = Path("data/criaturas.csv")


def carregar_criaturas():
    """Lê o CSV, atualizando o cache sempre que o arquivo mudar no disco."""
    return _carregar_criaturas(CAMINHO_CSV.stat().st_mtime)


@st.cache_data
def _carregar_criaturas(modificado_em):
    """Lê o CSV e transforma as colunas de dano em listas.
    'modificado_em' serve só para o cache perceber quando o CSV for editado."""
    df = pd.read_csv(CAMINHO_CSV, sep=";", keep_default_na=False)

    def para_lista(texto):
        texto = texto.strip()
        if texto in ("", "Nenhuma"):
            return []
        return [item.strip() for item in texto.split(",")]

    for coluna in ["Fraqueza", "Resistência"]:
        df[coluna] = df[coluna].apply(para_lista)
    return df


def nome_do_arquivo(nome):
    """Transforma o nome da criatura em nome de arquivo.
    Ex: 'Greydwarf brute' -> 'greydwarf_brute'   |   'Blåbär' -> 'blabar'"""
    sem_acento = unicodedata.normalize("NFKD", nome).encode("ascii", "ignore").decode()
    limpo = "".join(c if c.isalnum() else " " for c in sem_acento.lower())
    return "_".join(limpo.split())


def achar_imagem(nome):
    """Procura a imagem da criatura na pasta 'imagens'. Devolve None se não achar."""
    base = nome_do_arquivo(nome)
    for formato in FORMATOS:
        caminho = PASTA_IMAGENS / f"{base}.{formato}"
        if caminho.exists():
            return caminho
    return None


@st.cache_data
def miniatura_base64(caminho, modificado_em):
    """Redimensiona a imagem e devolve como texto (base64) para usar no HTML.
    'modificado_em' serve só para o cache perceber quando a imagem for trocada."""
    with Image.open(caminho) as img:
        img = img.convert("RGBA")
        img.thumbnail((128, 128))      # miniatura de no máximo 128x128
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode()


@st.cache_data
def fundo_base64(caminho, modificado_em):
    """Lê a imagem de fundo do site e devolve como texto (base64).
    'modificado_em' serve só para o cache perceber quando a imagem for trocada."""
    return base64.b64encode(Path(caminho).read_bytes()).decode()


def estilo_geral():
    """CSS do visual geral do site: fundo com foto, painéis escuros e
    destaques em laranja, inspirado na wiki do Valheim."""
    if CAMINHO_FUNDO.exists():
        dados_fundo = fundo_base64(str(CAMINHO_FUNDO), CAMINHO_FUNDO.stat().st_mtime)
        fundo_css = (
            f'linear-gradient(180deg, rgba(12,14,17,0.90) 0%, '
            f'rgba(12,14,17,0.72) 35%, rgba(12,14,17,0.92) 100%), '
            f'url("data:image/jpeg;base64,{dados_fundo}")'
        )
    else:
        fundo_css = "#14161a"

    return f"""
    <style>
    [data-testid="stAppViewContainer"] {{
        background-image: {fundo_css};
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
    }}
    [data-testid="stHeader"] {{ background: rgba(0,0,0,0); }}
    [data-testid="stSidebar"] {{
        background: rgba(15,17,20,0.94);
        border-right: 1px solid rgba(255,255,255,0.08);
    }}
    .block-container {{
        background: rgba(15,17,20,0.82);
        border-radius: 14px;
        padding: 2rem 2.5rem 3rem;
        margin-top: 1rem;
        box-shadow: 0 8px 30px rgba(0,0,0,0.35);
    }}
    div[data-testid="stExpander"] {{
        background: rgba(24,26,30,0.85);
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 10px;
        margin-bottom: 0.6rem;
    }}
    h1, h2, h3 {{ color: #f2ede4; }}
    h1 {{ border-bottom: 2px solid {COR_ACENTO}; padding-bottom: 0.4rem; }}
    </style>
    """


def html_foto(nome):
    """Devolve o HTML da imagem da criatura (ou um quadradinho vazio)."""
    caminho = achar_imagem(nome)
    if caminho is None:
        return '<span class="sem-foto">?</span>'
    dados = miniatura_base64(str(caminho), caminho.stat().st_mtime)
    return f'<img src="data:image/png;base64,{dados}" alt="{html.escape(nome)}">'


def html_selos(itens, classe):
    """Cria os 'selinhos' coloridos (ex: [Fogo]) em HTML."""
    if not itens:
        return '<span class="vazio">—</span>'
    return "".join(
        f'<span class="selo {classe}">{html.escape(item)}</span>' for item in itens
    )


def texto_ou_traco(texto):
    """Mostra o texto, ou um traço se estiver vazio."""
    texto = str(texto).strip()
    return html.escape(texto) if texto else '<span class="vazio">—</span>'


def mostrar_tabela(df):
    """Desenha a tabela de criaturas, uma linha por criatura, com a foto na frente."""
    linhas = ""
    for _, c in df.iterrows():
        local = f'<div class="local">{html.escape(c["Local"])}</div>' if c["Local"] else ""
        linhas += (
            "<tr>"
            f'<td class="foto">{html_foto(c["Nome"])}</td>'
            f'<td><div class="nome">{html.escape(c["Nome"])}</div></td>'
            f'<td>{texto_ou_traco(c["Bioma"])}{local}</td>'
            f'<td>{texto_ou_traco(c["Vida"])}</td>'
            f'<td>{texto_ou_traco(c["Dano"])}</td>'
            f'<td class="notas">{texto_ou_traco(c["Notas"])}</td>'
            f'<td>{html_selos(c["Fraqueza"], "selo-fraqueza")}</td>'
            f'<td>{html_selos(c["Resistência"], "selo-resistencia")}</td>'
            "</tr>"
        )
    cabecalho = (
        "<tr><th></th><th>Criatura</th><th>Bioma</th><th>Vida</th>"
        "<th>Dano</th><th>Notas</th><th>Fraqueza</th><th>Resistência</th></tr>"
    )
    # Tudo em uma linha só, para o Streamlit não confundir HTML com Markdown
    st.markdown(
        f'<table class="tabela-criaturas"><thead>{cabecalho}</thead>'
        f"<tbody>{linhas}</tbody></table>",
        unsafe_allow_html=True,
    )


def mostrar_tabela_passiva(df):
    """Tabela simples para criaturas pacíficas: foto, nome, bioma, vida e notas
    (não atacam, então não têm dano, fraqueza nem resistência)."""
    linhas = ""
    for _, c in df.iterrows():
        linhas += (
            "<tr>"
            f'<td class="foto">{html_foto(c["Nome"])}</td>'
            f'<td><div class="nome">{html.escape(c["Nome"])}</div></td>'
            f'<td>{texto_ou_traco(c["Bioma"])}</td>'
            f'<td>{texto_ou_traco(c["Vida"])}</td>'
            f'<td class="notas">{texto_ou_traco(c["Notas"])}</td>'
            "</tr>"
        )
    cabecalho = (
        "<tr><th></th><th>Nome</th><th>Bioma</th><th>Vida</th><th>Notas</th></tr>"
    )
    st.markdown(
        f'<table class="tabela-criaturas"><thead>{cabecalho}</thead>'
        f"<tbody>{linhas}</tbody></table>",
        unsafe_allow_html=True,
    )


def mostrar_tabela_npc(df):
    """Tabela simples para NPCs: só foto, nome e localização
    (NPCs não têm vida, dano, fraqueza nem resistência)."""
    linhas = ""
    for _, c in df.iterrows():
        linhas += (
            "<tr>"
            f'<td class="foto">{html_foto(c["Nome"])}</td>'
            f'<td><div class="nome">{html.escape(c["Nome"])}</div></td>'
            f'<td>{texto_ou_traco(c["Local"])}</td>'
            "</tr>"
        )
    cabecalho = "<tr><th></th><th>Nome</th><th>Localização</th></tr>"
    st.markdown(
        f'<table class="tabela-criaturas"><thead>{cabecalho}</thead>'
        f"<tbody>{linhas}</tbody></table>",
        unsafe_allow_html=True,
    )


def secao(titulo, df, descricao="", aberta=False, por_bioma=False, tabela_fn=mostrar_tabela):
    """Cria uma seção que expande e recolhe (o expander).
    'descricao' é o texto que explica o que é aquele tipo de criatura."""
    with st.expander(f"{titulo} ({len(df)})", expanded=aberta):
        if descricao:
            st.markdown(descricao)
        if df.empty:
            st.info("Nenhuma criatura com esses filtros.")
        elif por_bioma:
            # Um subtítulo e uma tabela para cada bioma, na ordem do jogo
            for bioma in ORDEM_BIOMAS:
                do_bioma = df[df["Bioma"] == bioma]
                if not do_bioma.empty:
                    st.markdown(f"#### 📍 {bioma}")
                    tabela_fn(do_bioma)
        else:
            tabela_fn(df)


# ------------------------------------------------------------
# 3) TEXTOS EXPLICATIVOS (baseados na wiki, em português)
# ------------------------------------------------------------
TEXTO_INTRO = (
    "Criaturas são personagens não jogáveis encontrados por todo o Valheim. "
    "Elas se dividem em categorias: chefes, minichefes, criaturas agressivas, "
    "pacíficas e NPCs. Clique em uma seção para abrir."
)

TEXTO_CHEFES = """
**Chefes** são criaturas agressivas e poderosas que precisam ser **invocadas**.
Matá-los libera **poderes dos Esquecidos (Forsaken powers)**, aumenta a
dificuldade do mundo e dá o saque necessário para avançar no jogo.

Também chamados de **Esquecidos (Forsaken)**, eles são invocados ao oferecer
itens específicos (indicados pelas Runestones) no local de invocação deles.
Têm mais vida e ataques especiais do que as criaturas comuns.

O local de um chefe é marcado automaticamente no mapa ao ler a runestone do
bioma. Cada chefe tem vários locais de invocação. Todo Esquecido derrotado
deixa um **troféu especial**, que pode ser levado às Sacrificial Stones para
liberar um novo poder.
"""

TEXTO_MINICHEFES = """
**Minichefes** são criaturas agressivas, únicas e com nome, encontradas em
**masmorras específicas**, graças à Hildir.

Derrotar qualquer minichefe (exceto o Lord Reto) dá como recompensa um dos
**baús da Hildir**.
"""

TEXTO_AGRESSIVAS = """
**Criaturas agressivas** atacam os jogadores quando percebem a presença deles e
também deixam saque quando morrem.

**Estrelas:** algumas criaturas agressivas têm estrelas, que representam o
nível. Com **1 estrela** a criatura tem o dobro da vida e causa 150% de dano.
Com **2 estrelas** tem o triplo da vida e causa o dobro de dano.

**Comportamento**

- As criaturas desistem de perseguir depois de 60 segundos sem conseguir atacar,
  ou 30 segundos sem detectar o alvo.
- Algumas têm um alcance máximo de perseguição. Depois dele, desistem se ficarem
  1 segundo sem detectar o alvo.
- Depois de 15 segundos sem conseguir atacar, elas focam nas construções por
  15 segundos se não alcançarem o alvo.
- Só atacam paredes e portas se não conseguirem chegar ao jogador.
- Algumas têm medo de fogo e fogem dele.
- Algumas evitam o fogo e ficam passivas perto dele.
- Algumas circulam o alvo enquanto esperam para atacar.
- Criaturas que nadam tentam fugir para a água se forem forçadas a ficar em terra.
- Elas regeneram 1,67% da vida máxima por minuto (100% em 60 minutos).
- Ganham **+30% de vida efetiva** para cada jogador adicional em um raio de
  100 metros (ex: 3 jogadores = +60%). Isso é atualizado sempre que a criatura
  leva dano.
- Ganham **+4% de dano** para cada jogador adicional em um raio de 100 metros
  (ex: 3 jogadores = +8%). Isso é atualizado sempre que a criatura causa dano.
"""

TEXTO_PACIFICAS = """
**Criaturas pacíficas não atacam** o jogador nem outras criaturas.
"""

TEXTO_NPCS = """
**NPCs** são personagens amigáveis que **não causam nem sofrem dano**.
"""

# ------------------------------------------------------------
# 4) PÁGINAS
# Cada página é uma função. O menu lateral escolhe qual delas aparece.
# ------------------------------------------------------------
def pagina_criaturas():
    criaturas = carregar_criaturas()

    st.header("🐗 Criaturas")
    st.write(TEXTO_INTRO)

    # ---- Filtros (agora dentro da página, em 3 colunas lado a lado) ----
    col_bioma, col_fraco, col_busca = st.columns(3)

    # Monta a lista de biomas que existem no CSV (uma criatura pode ter vários)
    biomas_no_csv = {b.strip() for lista in criaturas["Bioma"] for b in lista.split(",")}
    biomas_existentes = [b for b in ORDEM_BIOMAS if b in biomas_no_csv]

    with col_bioma:
        bioma_escolhido = st.selectbox("📍 Bioma", ["Todos"] + biomas_existentes)
    with col_fraco:
        fraco_a = st.selectbox("🎯 Fraco a", ["Qualquer"] + TIPOS_DANO)
    with col_busca:
        busca = st.text_input("🔎 Buscar por nome")

    # ---- Aplicando os filtros ----
    filtradas = criaturas.copy()

    if bioma_escolhido != "Todos":
        # 'contains' porque algumas criaturas vivem em mais de um bioma
        filtradas = filtradas[filtradas["Bioma"].str.contains(bioma_escolhido, regex=False)]

    if busca:
        filtradas = filtradas[filtradas["Nome"].str.contains(busca, case=False, na=False)]

    if fraco_a != "Qualquer":
        filtradas = filtradas[filtradas["Fraqueza"].apply(lambda lista: fraco_a in lista)]

    # ---- Adicionar imagem a uma criatura ----
    with st.expander("🖼️ Adicionar ou trocar a imagem de uma criatura"):
        st.write(
            "Escolha a criatura e envie a imagem. Ela é salva na pasta "
            "`imagens` e aparece na primeira coluna da tabela."
        )
        escolhida = st.selectbox("Criatura", criaturas["Nome"].tolist())
        arquivo = st.file_uploader("Imagem", type=FORMATOS)

        if arquivo is not None and st.button("Salvar imagem"):
            PASTA_IMAGENS.mkdir(exist_ok=True)
            # Apaga a imagem antiga (se existir) para não ficar duplicada
            antiga = achar_imagem(escolhida)
            if antiga:
                antiga.unlink()
            extensao = arquivo.name.rsplit(".", 1)[-1].lower()
            destino = PASTA_IMAGENS / f"{nome_do_arquivo(escolhida)}.{extensao}"
            destino.write_bytes(arquivo.getvalue())
            st.success(f"Imagem de {escolhida} salva!")
            st.rerun()

        st.caption(
            "Dica: também dá para colocar os arquivos direto na pasta `imagens`, "
            "com o nome da criatura em minúsculas, sem acento e com _ no lugar "
            "dos espaços. Ex: `troll.png`, `greydwarf_brute.jpg`."
        )

    com_foto = sum(achar_imagem(n) is not None for n in criaturas["Nome"])
    st.write(
        f"Mostrando **{len(filtradas)}** de {len(criaturas)} criaturas. "
        f"**{com_foto}** já têm imagem."
    )
    st.caption("Dados da wiki do Valheim. \"—\" significa que a wiki não informa.")

    # ---- Seções que expandem (uma para cada tipo, como na wiki) ----
    secao("👑 Chefes", filtradas[filtradas["Categoria"] == "Chefe"], TEXTO_CHEFES)
    secao("🗡️ Minichefes", filtradas[filtradas["Categoria"] == "Minichefe"], TEXTO_MINICHEFES)
    secao(
        "👹 Criaturas agressivas",
        filtradas[filtradas["Categoria"] == "Agressiva"],
        TEXTO_AGRESSIVAS,
        aberta=True,
        por_bioma=True,
    )
    secao(
        "🦌 Criaturas pacíficas",
        filtradas[filtradas["Categoria"] == "Passiva"],
        TEXTO_PACIFICAS,
        tabela_fn=mostrar_tabela_passiva,
    )
    secao(
        "🧑 NPCs",
        filtradas[filtradas["Categoria"] == "NPC"],
        TEXTO_NPCS,
        tabela_fn=mostrar_tabela_npc,
    )


def pagina_personagens():
    st.header("🧙 Personagens")
    st.info("Em breve: uma homenagem a cada um dos amigos. 🛡️")


def pagina_materiais():
    st.header("🪓 Materiais")
    st.info("Em breve: painel ligado à planilha do Google Docs. 📊")


# ------------------------------------------------------------
# 5) TÍTULO E MENU LATERAL
# O menu na barra lateral escolhe qual página mostrar.
# ------------------------------------------------------------
st.markdown(estilo_geral(), unsafe_allow_html=True)
st.markdown(ESTILO_TABELA, unsafe_allow_html=True)
st.title("⚔️ Valheim dos Amigos")

PAGINAS = {
    "🐗 Criaturas": pagina_criaturas,
    "🧙 Personagens": pagina_personagens,
    "🪓 Materiais": pagina_materiais,
}

st.sidebar.header("🧭 Menu")
escolha = st.sidebar.radio("Ir para", list(PAGINAS), label_visibility="collapsed")

# Chama a função da página escolhida
PAGINAS[escolha]()