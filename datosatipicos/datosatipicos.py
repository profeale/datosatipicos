import numpy as np
import csv
from tkinter import Tk
from tkinter.filedialog import askopenfilename, askopenfilenames, asksaveasfilename
import tkinter.simpledialog as simpledialog
import tkinter.messagebox as messagebox
import openpyxl
import scipy.stats as stats

def detect_delimiter(file_path):
    with open(file_path, 'r') as file:
        first_line = file.readline()
        # Prueba diferentes delimitadores
        for delimiter in [',', ';', '\t']:
            if first_line.count(delimiter) > 0:
                return delimiter
    return None  # Retorna None si no se encontró un delimitador

def iqr_outliers(data):
    Q1 = np.percentile(data, 25)
    Q3 = np.percentile(data, 75)
    IQR = Q3 - Q1
    lower_bound = Q1 - 1.5 * IQR
    upper_bound = Q3 + 1.5 * IQR
    return [x for x in data if x < lower_bound or x > upper_bound]

def select_file(multiple=False):
    Tk().withdraw()
    if multiple:
        filenames = askopenfilenames(filetypes=[("CSV files", "*.csv")])
        if not filenames:
            messagebox.showwarning("Advertencia", "No se seleccionó ningún archivo.")
        return list(filenames)
    else:
        filename = askopenfilename(filetypes=[("CSV files", "*.csv")])
        if not filename:
            messagebox.showwarning("Advertencia", "No se seleccionó ningún archivo.")
        return filename

def dixon_test(data):
    data_sorted = np.sort(data)
    n = len(data_sorted)
    if n < 3:
        return []

    lower = (data_sorted[1] - data_sorted[0]) / (data_sorted[-1] - data_sorted[0])
    upper = (data_sorted[-1] - data_sorted[-2]) / (data_sorted[-1] - data_sorted[0])
    critical_value_lower = 0.2
    critical_value_upper = 0.2

    outliers = []
    if lower > critical_value_lower:
        outliers.append(data_sorted[0])
    if upper > critical_value_upper:
        outliers.append(data_sorted[-1])

    return outliers

def z_score_method(data):
    mean = np.mean(data)
    std_dev = np.std(data)
    z_scores = [(x - mean) / std_dev for x in data]
    return [data[i] for i, z in enumerate(z_scores) if abs(z) > 2]

def identify_outliers(data):
    n = len(data)
    if n < 3:
        print("La muestra es demasiado pequeña para aplicar el test de Dixon o IQR.")
        return None

    if n <= 30:
        print("Se utilizará el test de Dixon.")
        return dixon_test(data)

    # Realiza la prueba de normalidad solo si n > 30
    shapiro_test = stats.shapiro(data)
    p_value = shapiro_test.pvalue
    alpha = 0.05  # Nivel de significancia

    if p_value > alpha:
        print("Los datos parecen tener distribución normal. Se utilizará el método Z-scores.")
        return z_score_method(data)
    else:
        print("Los datos no parecen tener distribución normal. Se utilizará el método IQR.")
        return iqr_outliers(data)

def get_data_from_csv(file_path, columns):
    delimiter = detect_delimiter(file_path)
    if delimiter is None:
        raise ValueError("No se pudo determinar el delimitador del archivo.")

    data_dict = {col: [] for col in columns}

    with open(file_path, newline='') as csvfile:
        reader = csv.DictReader(csvfile, delimiter=delimiter)
        original_headers = reader.fieldnames
        normalized_headers = [header.strip().lower() for header in original_headers]

        for column in data_dict.keys():
            if column not in normalized_headers:
                raise ValueError(f"La columna '{column}' no se encuentra en el archivo.")

        for row in reader:
            for column in data_dict.keys():
                try:
                    original_column = original_headers[normalized_headers.index(column)]
                    raw_value = row[original_column].replace(',', '.')
                    print(f"Valor leído de '{original_column}': {raw_value}")  # Línea de depuración
                    data_dict[column].append(float(raw_value))
                except ValueError:
                    print(f"Valor no numérico encontrado en la columna '{column}': {row[original_column]}")

    return data_dict

def clean_data(data, outliers):
    return {column: [x for x in values if x not in outliers] for column, values in data.items()}


def select_save_file():
    Tk().withdraw()
    filename = asksaveasfilename(defaultextension=".xlsx",
                                  filetypes=[("Excel files", "*.xlsx"),
                                             ("All files", "*.*")],
                                  title="Guardar archivo como")
    if not filename:
        messagebox.showwarning("Advertencia", "No se seleccionó ningún archivo para guardar.")
    return filename
def main():
    file_paths = select_file(multiple=True)

    for file_path in file_paths:
        try:
            print(f"\nAnalizando archivo: {file_path}")
            column_names_input = simpledialog.askstring(
                "Columnas",
                "Introduce los nombres de las columnas a analizar (separados por comas):"
            )
            column_names = [name.strip().lower() for name in column_names_input.split(',')] if column_names_input else []
            print("Nombres de columnas ingresados:", column_names)

            data = get_data_from_csv(file_path, column_names)
            if data is None:
                continue

            headers = list(data.keys())
            print("Encabezados encontrados:", headers)

            results = {}
            original_data = {}

            for column in column_names:
                if column not in headers:
                    print(f"La columna '{column}' no se encuentra en el archivo. Encabezados disponibles: {headers}")
                    continue

                outliers = identify_outliers(data[column])
                if outliers is None:
                    continue

                print(f"Valores atípicos identificados en '{column}':", outliers)

                cleaned_data = clean_data(data, outliers)
                results[column] = cleaned_data[column]
                original_data[column] = data[column]
                print(f"Datos después de eliminar outliers en '{column}':", cleaned_data[column])

            # Permitir que el usuario elija dónde guardar el archivo
            output_file = select_save_file()
            if output_file:
                workbook = openpyxl.Workbook()
                sheet = workbook.active
                sheet.title = 'Resultados'
                sheet.append(['Columna', 'Datos Originales', 'Datos Limpiados'])

                for column in results.keys():
                    max_length = max(len(original_data[column]), len(results[column]))
                    for i in range(max_length):
                        original_value = original_data[column][i] if i < len(original_data[column]) else ''
                        cleaned_value = results[column][i] if i < len(results[column]) else ''
                        sheet.append([column, original_value, cleaned_value])

                workbook.save(output_file)
                print(f"Resultados guardados en '{output_file}'.")

        except Exception as e:
            print(f"Error procesando el archivo {file_path}: {e}")


if __name__ == "__main__":
    main()

