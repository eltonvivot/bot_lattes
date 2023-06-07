from pathlib import Path
import pandas as pd
import tools

files = {
    "Non-fungible Token.xls": "NFT",
    "Realidade Aumentada.xls": "Realidade Aumentada",
    "Realidade Mista.xls": "Realidade Mista",
    "Realidade Virtual.xls": "Realidade Virtual",
    "Virtual Reality.xls": "Realidade Virtual",
    "blockchain.xls": "Blockchain",
    "digital twins.xls": "Gêmeo Digital",
    "gemeos digitais.xls": "Gêmeo Digital",
    "metaverse.xls": "Metaverso",
    "5G.xls": "5G",
    "6G.xls": "6G",
    "Artificial Intelligence.xls": "Inteligência Artificial",
    "Inteligencia Artificial.xls": "Inteligência Artificial",
    "Contratos Inteligentes.xls": "Contratos Inteligentes",
    "Smart Contracts.xls": "Contratos Inteligentes",
}

folders = ["results/dgp/2014/", "results/dgp/2016/", "results/dgp/atual/"]
groups_file = tools.csv_prefix + "1.Groups.csv"
institutions_file = tools.csv_prefix + '2.Institutions.csv'
group_states_file = tools.csv_prefix + '3.GroupsStates.csv'

# First step
def merge_groups(outfile=groups_file):
    merged_df = pd.DataFrame()
    for folder in folders:
        for file, assunto in files.items():
            if not Path(folder + file).is_file():
                continue
            df = pd.read_excel(folder + file)
            df['Assunto'] = assunto

            # Append the DataFrame to the merged DataFrame
            merged_df = pd.concat([merged_df, df], ignore_index=True)
    merged_df.drop_duplicates(inplace=True)
    # merged_df.rename(columns={'INSTITUIÇÃO': 'Instituicao', 'GRUPO': 'Grupo', 'DATA DE CRIAÇÃO DO GRUPO': 'DataCriacao', 'LÍDER': 'Lider', '2º LÍDER': 'Lider2', 'ÁREA PREDOMINANTE': 'Area'}, inplace=True)
    merged_df.to_csv(outfile, sep=";", index=False)
    return

# Second step
def extract_institutions(groups_filename=groups_file, institutions_filename=institutions_file):
    tools.drop_duplicates(groups_filename, 'Instituicao', outfile=institutions_filename)
    tools.find_institution_state(institutions_filename, 'Estado', 'Instituicao')
    return

# Third step
def set_group_state(groups_file=groups_file, institutions_file=institutions_file, outfile=group_states_file):
    df_groups = pd.read_csv(groups_file, delimiter=';')
    df_inst = pd.read_csv(institutions_file, delimiter=';')

    for index, row in df_groups.iterrows():
        institution = row['Instituicao']
        state = tools.search_value_in_dataframe(df_inst, institution, 'Instituicao', 'Estado')
        df_groups.at[index, 'Estado'] = state
    df_groups.to_csv(outfile, sep=";", index=False)
    return

# Fourth step
def group_groups(filename=group_states_file, outfile=tools.csv_prefix + "4.GroupsFinal.csv"):
    df = pd.read_csv(filename, delimiter=";")
    grouped = df.groupby(["Instituicao", "Grupo", "DataCriacao", "Lider", "Lider2", "Area", "Estado"]).agg({'Assunto': lambda x: ','.join(x)})
    grouped.reset_index().to_csv(outfile, sep=";", index=False)
    return

# merge_groups()
# After merge, manually remove wrong and extra headers; remove empty column (;;); set the header as ";Instituicao;Grupo;DataCriacao;Lider;Lider2;Area;Assunto"
# extract_institutions()
# set_group_state()
group_groups()