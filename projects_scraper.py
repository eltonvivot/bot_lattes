import time, os, json, threading
from playwright.sync_api import sync_playwright, TimeoutError
import tools

load_time = 2
data = None

def read_write_json(data: dict = None) -> dict:
    if data is None:
        with open("controle_buscas.json", 'r') as f:
            data = json.load(f)
    else:
        with open("controle_buscas.json", 'w') as f:
            json.dump(data, f, indent=4)
    return data

def update_data(key, value):
    data = read_write_json()
    data[key] = value
    read_write_json(data=data)

def escreve_projetos(curriculo_id, projetos, input):
    # Cria pasta "results" se nao existir
    if not os.path.exists(input):
        os.makedirs(input)
    # Escreve em arquivo
    file_path = os.path.join(input, f"{curriculo_id}.txt")
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(projetos)
    tools.log(f"[{curriculo_id}] Projetos armazenados", f"{input}.log")

def pega_dados_curriculo(pagina, input):
    # Pega o ID do curriculo
    curriculo_id = pagina.locator('xpath=/html/body/div[1]/div[3]/div/div/div/div[1]/ul/li[2]/span[2]').inner_text()
    # Busca todos os elementos com class 'title-wrapper'
    title_wrappers = pagina.query_selector_all('.title-wrapper')
    for title_wrapper in title_wrappers:
        # Busca elemento 'a' com nome 'ProjetosPesquisa'
        if title_wrapper.query_selector('a[name="ProjetosPesquisa"]'):
            # Se for Projeto de pesquisa pega o conteúdo'
            layout_cell = title_wrapper.query_selector('.layout-cell.layout-cell-12.data-cell')
            if layout_cell:
                # Pega o conteudo do layout cell
                projetos = layout_cell.text_content()
                # Remove linhas em branco
                projetos = os.linesep.join([s for s in projetos.splitlines() if s])
                # Escreve em arquivo
                escreve_projetos(curriculo_id, projetos, input)
                return
    tools.log(f"[{curriculo_id}] Projetos não encontrados", f"{input}.log")
    return

def encontra_paginacao_atual(pagina, input):
    i = 0
    while True:
        i += 1
        p = pagina.locator(f'xpath=/html/body/form/div/div[4]/div/div/div/div[3]/div/div[2]/a[{i}]')
        inner_html = p.evaluate('(el) => el.innerHTML')
        if 'color="#ff0000"' in inner_html:
            tools.log(f" > Pagina atual: {p.inner_text()}", f"{input}.log")
            return i
        if p.inner_text() == "próximo":
            return i
        
def retoma_paginacao(pagina, input, pagina_index):
    i=encontra_paginacao_atual(pagina, input)
    while True:
        p = pagina.locator(f'xpath=/html/body/form/div/div[4]/div/div/div/div[3]/div/div[2]/a[{i}]')
        if(p.inner_text() == f"{pagina_index}"):
            print(f" > Encontrou {p.inner_text()}. Index: {i}")
            acessa_pagina(pagina, i, input)
            return
        if p.inner_text() == "próximo":
            acessa_pagina(pagina, i, input)
            i=encontra_paginacao_atual(pagina, input)
            i-=1 # não incrementar
        i+=1

def acessa_pagina(pagina, index, input):
    pagina.locator(f'xpath=/html/body/form/div/div[4]/div/div/div/div[3]/div/div[2]/a[{index}]').click()
    time.sleep(load_time)
    encontra_paginacao_atual(pagina, input)

def proxima_pagina(pagina, input):
    index_atual = encontra_paginacao_atual(pagina, input)
    pagina_index= read_write_json()[input] +1
    update_data(input, pagina_index)
    acessa_pagina(pagina, index_atual+1, input)
    return pagina_index

def iterate_resultado_busca(pagina, contexto, input):
    # Retomar
    pagina_index = read_write_json()[input]
    retoma_paginacao(pagina, input, pagina_index)
    while True:
        # Locate the ordered list element
        ol_element = pagina.query_selector(f'ol[type="1"][start="{(pagina_index-1)*10 + 1}"]')
        # Find all <li> elements within the ordered list
        li_elements = ol_element.query_selector_all('li')
        # Iterate over the <li> elements and print their text content
        li_index = 1
        for li_element in li_elements:
            # print(li_element.text_content())
            pagina.locator(f'xpath=/html/body/form/div/div[4]/div/div/div/div[3]/div/div[3]/ol/li[{li_index}]/b/a').click()
            time.sleep(7)
            # Abre curriculo em nova pagina
            with contexto.expect_page() as pagina_curriculo_info:
                pagina.locator('xpath=//*[@id="idbtnabrircurriculo"]').click()
            pagina_curriculo = pagina_curriculo_info.value
            pega_dados_curriculo(pagina_curriculo, input)            
            # Fecha curriculo
            pagina_curriculo.close()
            pagina.bring_to_front()
            # Fecha popup
            pagina.locator(f'//*[@id="idbtnfechar"]').click()
            li_index+=1
        # Se tiver menos de 10 em uma pagina então retorna pois terminou
        if li_index < 11:
            tools.log("=== FINALIZADO ===", f"{input}.log")
            return
        # Acessa proxima pagina
        pagina_index = proxima_pagina(pagina, input)

def busca_curriculos(pagina, contexto, input):
    pagina.goto("https://buscatextual.cnpq.br/buscatextual/busca.do?metodo=apresentar")
    time.sleep(load_time)
    # Preenche assunto
    pagina.fill('xpath=/html/body/form/div/div[4]/div/div/div/div[3]/fieldset/div/input', input)
    # Preenche checkboxes
    pagina.locator('xpath=//*[@id="buscaAssunto"]').check()
    # pagina.locator('xpath=//*[@id="buscarDemais"]').check()
    pagina.locator('xpath=//*[@id="filtro9"]').check()
    pagina.locator('xpath=//*[@id="participaDGP"]').check()
    pagina.locator('xpath=/html/body/form/div/div[4]/div/div/div/div[18]/div[2]/div/div/div/a[1]').click()
    # Busca
    pagina.locator('xpath=/html/body/form/div/div[4]/div/div/div/div[7]/div/div[1]/a').click()
    # Iterate nos resultados das buscas
    iterate_resultado_busca(pagina, contexto, input)

def run(input):
    with sync_playwright() as playwright:
        tentativas = 0
        while True:
            try:
                # Cria navegador
                tools.log(f"=== INICIANDO NOVA EXECUÇÃO: {input} ===", f"{input}.log")
                navegador = playwright.chromium.launch(headless=True)
                contexto = navegador.new_context()
                pagina = contexto.new_page()
                busca_curriculos(pagina, contexto, input)
                break
            except Exception as e: 
                tentativas+=1
                tools.log(f"Tentativa: {tentativas} |\t{e}", f"{input}.log")
                navegador.close()
                # print(f"Erro. Tentativas realizadas: {tentativas}")



data = read_write_json()
# Iterate over the keys and create a thread for each key-value pair
threads = []
for input, _ in data.items():
        if input.startswith("__"):
            continue
        t = threading.Thread(target=run, args=(input,))
        threads.append(t)
        t.start()
        # break
# Wait for all threads to finish before returning
for t in threads:
    t.join()
# run("metaverso", data["metaverso"])