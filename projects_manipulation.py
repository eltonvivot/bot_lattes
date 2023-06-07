import os, chardet, json
import pandas as pd
import tools

projects_file = tools.csv_prefix + '1.Projects.csv'
coordenators_file=tools.csv_prefix + "2.Coordenators.csv"
affiliations_file = tools.csv_prefix + "3.Affiliations.csv"
projects_final = tools.csv_prefix + "4.ProjectsFinal.csv"
projects_group = tools.csv_prefix + "5.ProjectsGroup.csv"

# First step:
def find_matching_projects(search_control="controle_buscas.json", startswith="__", outfile=projects_file):
    # Init function
    tools.create_header("LattesID;CoordenadorCitado;AnoInicio;AnoFim;Titulo;Assunto", outfile)
    # Define function to search each file
    def search_files_from_folders(folder_path):
        # Define coordenator extractor
        def extract_coordenator_name(descricao):
            iend = descricao.find(" - Coordenador")
            if iend == -1:
                return None
            else:
                bar = descricao[:iend].rfind("/")
                dp = descricao[:iend].rfind(":")
                istart = max(bar,dp)
                if istart == -1:
                    return None
                return descricao[istart+2:iend]
        # Search files logic
        tools.log(f"Searching ...", "find_matching_projects.log")   
        for filename in os.listdir(folder_path):  
            tools.log(filename, "find_matching_projects.log", end=' ')    
            with open(os.path.join(folder_path, filename), 'rb') as file:
                data = file.read()
            encoding = chardet.detect(data)['encoding']
            with open(os.path.join(folder_path, filename), 'r', encoding=encoding) as file:
                project_line_start = 0
                year_start = None
                year_end = None
                coordinator = None
                project_name = None
                line_count = 0

                for line in file:
                    line_count+=1
                    years = line.split(" - ")
                    if len(years) == 2 and years[0].isnumeric():
                        year_start = years[0].strip()
                        year_end = years[1].strip()
                        project_line_start = line_count
                    if line_count == project_line_start+2:
                        project_name = line.strip().replace(";", ",")
                    if "Descrição:" in line:
                        if folder_path.split('/')[-1].lower() in line.lower():
                            coordinator = extract_coordenator_name(line)
                            tools.export_to_file(f"{filename[:-4]};{coordinator};{year_start};{year_end};{project_name};{folder_path.split('/')[-1]}", outfile)
        return
    # Extract projects logic
    data = None
    with open(search_control, 'r') as f:
        data = json.load(f)
    for input, _ in data.items():
        if input.startswith(startswith):
            tools.log(f"Searching '{input[len(startswith):]}'", "find_matching_projects.log")
            search_files_from_folders(tools.projects_prefix + input[len(startswith):])
    tools.drop_duplicates(outfile)
    return

# Third step:
def extract_affiliations_from_coordenators(coordenators_file=coordenators_file, affiliations_file=affiliations_file):
    # Init affiliations extractor
    tools.drop_duplicates(coordenators_file, 'Afiliacao', outfile=affiliations_file)
    tools.find_institution_state(affiliations_file, 'Estado', 'Afiliacao')
    return

# Forth step:
def set_coordenator_state(coordenators_file=coordenators_file, affiliations_file=affiliations_file):
    df_coord = pd.read_csv(coordenators_file, delimiter=';')
    df_afl = pd.read_csv(affiliations_file, delimiter=';')

    for index, row in df_coord.iterrows():
        affiliation = row['Afiliacao']
        state = tools.search_value_in_dataframe(df_afl, affiliation, 'Afiliacao', 'Estado')
        df_coord.at[index, 'Estado'] = state
    df_coord.to_csv(coordenators_file, sep=";", index=False)
    return

# Fifth step
def set_project_state(projects_file=projects_file, coordenators_file=coordenators_file):
    df_proj = pd.read_csv(projects_file, delimiter=';')
    df_coord = pd.read_csv(coordenators_file, delimiter=';')
    for index, row in df_proj.iterrows():
        coord_found = row['CoordenadorCitado']
        coord_name = tools.search_value_in_dataframe(df_coord, coord_found, 'RefNome', 'Nome')
        coord_state = tools.search_value_in_dataframe(df_coord, coord_found, 'RefNome', 'Estado')
        df_proj.at[index, 'NomeCoordenador'] = coord_name
        df_proj.at[index, 'Estado'] = coord_state
    df_proj.to_csv(projects_final, sep=";", index=False)

# Fifth step
def group_projects(filename=projects_final):
    df = pd.read_csv(filename, delimiter=";")
    grouped = df.groupby(["LattesID","AnoInicio","AnoFim","Titulo","NomeCoordenador","Estado"]).agg({'Assunto': lambda x: ','.join(x)})
    grouped.reset_index().to_csv(projects_group, sep=";", index=False)

def append_results(prefix_files, startswitch):
    def merge_new_files(old, new):
        df_old = pd.read_csv(old, delimiter=";")
        df_new = pd.read_csv(new, delimiter=";")
        df_old = pd.concat([df_old, df_new], ignore_index=True)
        df_old.drop_duplicates(inplace=True)
        df_old.to_csv(old, sep=";", index=False)
    def create_backup(filename):
        df = pd.read_csv(filename, delimiter=";")
        df.to_csv(f"{filename[:-4]}.bkp", sep=";", index=False)
    prefix_files = tools.csv_prefix + prefix_files
    projects = prefix_files + 'NewProjects.csv'
    coordenators = prefix_files + 'NewCoordenators.csv'
    affiliations = prefix_files + 'NewAffiliations.csv'
    find_matching_projects(outfile=projects, startswith=startswitch)
    extract_affiliations_from_coordenators(coordenators_file=coordenators, affiliations_file=affiliations)
    merge_new_files(projects_file, projects)
    merge_new_files(coordenators_file, coordenators)
    merge_new_files(affiliations_file, affiliations)
    create_backup(projects_final)
    create_backup(projects_group)
    set_coordenator_state()
    set_project_state()
    group_projects()
    return


# Tests
# find_matching_projects()
# extract_affiliations_from_coordenators()
# set_coordenator_state()
# set_project_state()
group_projects()
# append_results('1.1.', '___')



