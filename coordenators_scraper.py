import pandas as pd
import time, traceback
from playwright.sync_api import sync_playwright
import tools

load_time = 2
coordenators_file = tools.csv_prefix + "2.Coordenators.csv"
tools.create_header("CoordenadorID;Nome;Afiliacao;RefID;RefNome", coordenators_file)

def busca_afiliacao(atuacoes, afiliacoes):
    def r_afiliacao(indexes, index):
        afiliacao = None
        for afl, i in indexes.items():
            if index >= i:
                afiliacao = afl
            else:
                break
        return afiliacao

    indexes = {}
    for afiliacao in afiliacoes:
        indexes[afiliacao] = atuacoes.index(afiliacao)
    
    # for afiliacao, index in indexes.items():
    atual = False
    for index, line in enumerate(atuacoes):
        if line.endswith(" - Atual"):
            atual = True
            continue
        if atual and any(map(line.__contains__, ["Enquadramento Funcional: Professor", "Enquadramento Funcional: Pesquisador", "Dedicação exclusiva"])):
            return r_afiliacao(indexes, index)
        else:
            atual = False
    return None

def pega_dados_curriculo(pagina, row):
    # Pega o ID do curriculo
    curriculo_id = pagina.locator('xpath=/html/body/div[1]/div[3]/div/div/div/div[1]/ul/li[2]/span[2]').inner_text()
    coord_nome = pagina.locator('xpath=/html/body/div[1]/div[3]/div/div/div/div[1]/h2[1]').inner_text()
    # Busca todos os elementos com class 'title-wrapper'
    title_wrappers = pagina.query_selector_all('.title-wrapper')
    for title_wrapper in title_wrappers:
        # Busca elemento 'a' com nome 'ProjetosPesquisa'
        if title_wrapper.query_selector('a[name="AtuacaoProfissional"]'):
            # Se for Projeto de pesquisa pega o conteúdo'
            layout_cell = title_wrapper.query_selector('.layout-cell.layout-cell-12.data-cell')
            if layout_cell:
                # Pega afiliacoes e atuações:
                inst_wrappers = layout_cell.query_selector_all('.inst_back')
                afiliacoes = [inst_wrapper.text_content().strip("\r\n\t") for inst_wrapper in inst_wrappers]
                atuacoes = [s for s in layout_cell.text_content().splitlines() if s.strip("\r\n\t")]
                filiacao = busca_afiliacao(atuacoes, afiliacoes)
                ref_id = str(row['LattesID']).strip("\r\n\t")
                tools.export_to_file(f"{curriculo_id};{coord_nome};{filiacao};{ref_id};{row['CoordenadorCitado']}", coordenators_file)
                return
    
    tools.log(f"[{curriculo_id}] Atuações não encontradas", 'coordenators_scraper.log')
    return

def iterate_resultado_busca(pagina, contexto, row):
    time.sleep(load_time)
    # Locate the ordered list element
    ol_element = pagina.query_selector(f'ol[type="1"][start="1"]')
    # Find all <li> elements within the ordered list
    li_elements = ol_element.query_selector_all('li')
    # Iterate over the <li> elements and print their text content
    if len(li_elements) > 1 or len(li_elements) == 0:
        ref_id = str(row['lattes id']).strip("\r\n\t")
        tools.export_to_file(f"{None};{None};{None};{ref_id};{row['CoordenadorCitado']}", coordenators_file)
        return
    pagina.locator(f'xpath=/html/body/form/div/div[4]/div/div/div/div[3]/div/div[3]/ol/li[{1}]/b/a').click()
    time.sleep(7)
    # Abre curriculo em nova pagina
    with contexto.expect_page() as pagina_curriculo_info:
        pagina.locator('xpath=//*[@id="idbtnabrircurriculo"]').click()
    pagina_curriculo = pagina_curriculo_info.value
    pega_dados_curriculo(pagina_curriculo, row)            
    # Fecha curriculo
    pagina_curriculo.close()
    pagina.bring_to_front()
    # Fecha popup
    pagina.locator(f'//*[@id="idbtnfechar"]').click()

def busca_curriculos(pagina, contexto, row):
    pagina.goto("https://buscatextual.cnpq.br/buscatextual/busca.do?metodo=apresentar")
    time.sleep(load_time)
    # Preenche coordenador
    pagina.fill('xpath=/html/body/form/div/div[4]/div/div/div/div[3]/fieldset/div/input', str(row['CoordenadorCitado']))
    # Busca
    pagina.locator('xpath=/html/body/form/div/div[4]/div/div/div/div[7]/div/div[1]/a').click()
    # Iterate nos resultados das buscas
    iterate_resultado_busca(pagina, contexto, row)

def run(row, index):
    with sync_playwright() as playwright:
        tentativas = 0
        while True:
            try:
                # Cria navegador
                tools.log(f"=== BUSCANDO COORDENADOR: {index} - {row['CoordenadorCitado']} ===", 'coordenators_scraper.log')
                navegador = playwright.chromium.launch(headless=True)
                contexto = navegador.new_context()
                pagina = contexto.new_page()
                busca_curriculos(pagina, contexto, row)
                break
            except Exception as e: 
                tentativas+=1
                tools.log(f"Tentativa: {tentativas} |\t{e}", 'coordenators_scraper.log')
                # print(traceback.format_exc())
                navegador.close()
                if tentativas > 9:
                    ref_id = str(row['LattesID']).strip("\r\n\t")
                    tools.export_to_file(f"{None};{None};{None};{ref_id};{row['CoordenadorCitado']}", coordenators_file)
                    return

# Controle de buscas. Buscar a partir da linha h_index
h_index = 0
df = pd.read_csv(tools.csv_prefix + "1.1.NewProjects.csv", sep=";",lineterminator='\r')
for index, row in df.iterrows():
    if index < h_index:
        continue
    run(row, index)