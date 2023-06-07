import pandas as pd
import datetime

csv_prefix = "results/csv_files/"
projects_prefix = "results/projects/"

def export_to_file(line, filename):
    print(line)
    with open(f"{filename}", "a+", encoding='utf-8') as f:
        f.write(f"{line}\n")
    return

def drop_duplicates(filename, column=None, outfile = None):
    outfile = outfile if outfile else filename
    df = pd.read_csv(f"{filename}", sep=";")
    df.drop_duplicates(subset=column, inplace=True)
    df.to_csv(outfile, sep=";", index=False)
    return

def search_value_in_dataframe(df, search_value, search_column, return_column):
    row = df[df[search_column] == search_value]
    if not row.empty:
        return row[return_column].iloc[0]
    return "None"

def create_header(header, filename):
    with open(filename, 'a+') as file:
        if header in file.read():
            return
    export_to_file(header, filename)

def log(message, filename, end='\n'):
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log_message = f"{timestamp} \t{message}"
    print(log_message, end=end)
    with open(f"logs/{filename}", "a") as f:
        f.write(log_message + end)



def find_institution_state(filename, state_column, institution_column):
    def find_city(affiliation, filename="cidades_brasil.csv"):
        df_cities = pd.read_csv(filename)
        for _, row in df_cities.iterrows():
            if row["city"] in affiliation:
                capital = row["capital"]
                return capital
        return "None"
    # Find logic
    brazil_states = ['Acre', 'Alagoas', 'Amapá', 'Amazonas', 'Bahia', 'Ceará', 'Distrito Federal',
                    'Espírito Santo', 'Goiás', 'Maranhão', 'Mato Grosso', 'Mato Grosso do Sul',
                    'Minas Gerais', 'Pará', 'Paraíba', 'Paraná', 'Pernambuco', 'Piauí', 'Rio de Janeiro',
                    'Rio Grande do Norte', 'Rio Grande do Sul', 'Rondônia', 'Roraima', 'Santa Catarina',
                    'São Paulo', 'Sergipe', 'Tocantins' ]
    df_afl = pd.read_csv(filename, sep=";")
    df_afl[state_column] = df_afl[institution_column].apply(lambda x: next((state for state in brazil_states if state.lower() in x.lower()), "None"))

    for index, row in df_afl.iterrows():
        state = row[state_column]
        affiliation = row[institution_column]
        if pd.isnull(state):
            df_afl.at[index, state_column] = find_city(affiliation)
    df_afl.to_csv(filename, sep=";", index=False)