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