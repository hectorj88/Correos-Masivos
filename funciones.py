def limpiar_correos(df, col_correo):
    """
    Limpia la columna de correos en el DataFrame.
    
    Parámetros:
        df (pd.DataFrame): El DataFrame que contiene los datos.
        col_correo (str): El nombre de la columna que contiene los correos.
    
    Retorna:
        pd.DataFrame: El DataFrame limpio.
    """
    # Eliminar espacios en blanco al inicio y al final de los correos
    df[col_correo] = df[col_correo].str.strip()
    
    # Eliminar filas donde el correo esté vacío
    df = df.dropna(subset=[col_correo])
    
    # Eliminar filas duplicadas basadas en la columna de correos
    df = df.drop_duplicates(subset=[col_correo])
    
    return df

def obtener_primer_nombre(df, col_nombre):
    """Funcion para obtener el primer nombre de una columna de nombres.

    Args:
        df (Dataframe): Dataframe que contiene los datos.
        columna_nombre (str): Nombre de la columna que contiene los nombres.

    Returns:
        df (dataframe): _description_
    """
    
    # Eliminar espacios en blanco al inicio y al final de los nombres
    df[col_nombre] = df[col_nombre].str.strip()
    
    # Dejando la primera letra de cada nombre en mayuscula y el resto en minuscula
    df[col_nombre] = df[col_nombre].str.title()
    
    # Aplicar una función lambda para dividir el nombre y tomar el primero
    df[col_nombre] = df[col_nombre].apply(lambda x: x.split()[0] if isinstance(x, str) else x)
    
    return df