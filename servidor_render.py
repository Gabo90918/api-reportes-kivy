from flask import Flask, request, jsonify
import sqlite3
import pandas as pd
import os

app = Flask(__name__)
DB_NAME = "gestion_reportes.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    # Creamos la tabla INV (Inventario)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS INV (
            ID INTEGER PRIMARY KEY AUTOINCREMENT,
            REGION TEXT,
            SUCURSAL TEXT,
            MODELO TEXT,
            NUM_SERIE TEXT UNIQUE,
            LF TEXT,
            STATUS TEXT
        )
    ''')
    # Creamos la tabla SEGUIMIENTO (Reportes)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS SEGUIMIENTO (
            ID INTEGER PRIMARY KEY AUTOINCREMENT,
            FECHA TEXT,
            SERIE TEXT,
            REPORTE TEXT,
            TECNICO TEXT,
            ESTADO TEXT
        )
    ''')
    conn.commit()
    conn.close()

# Ruta para recibir los reportes desde tu App de Kivy
@app.route('/enviar_reporte', methods=['POST'])
def enviar_reporte():
    data = request.json
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO SEGUIMIENTO (FECHA, SERIE, REPORTE, TECNICO, ESTADO)
            VALUES (?, ?, ?, ?, ?)
        ''', (data['fecha'], data['serie'], data['reporte'], data['tecnico'], data['estado']))
        conn.commit()
        return jsonify({"status": "success", "message": "Reporte guardado"}), 201
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400
    finally:
        conn.close()

# Ruta para consultar el inventario (para que la app valide series)
@app.route('/consultar_inv/<serie>', methods=['GET'])
def consultar_inv(serie):
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query(f"SELECT * FROM INV WHERE NUM_SERIE = '{serie}'", conn)
    conn.close()
    if not df.empty:
        return df.to_json(orient='records')
    return jsonify({"message": "No encontrado"}), 404
    @app.route('/descargar_reportes', methods=['GET'])
def descargar_reportes():
    try:
        conn = sqlite3.connect(DB_NAME)
        # Leemos toda la tabla de seguimiento
        df = pd.read_sql_query("SELECT * FROM SEGUIMIENTO", conn)
        conn.close()

        if df.empty:
            return "No hay reportes guardados todavía.", 404

        # Nombre del archivo Excel
        excel_file = "reporte_seguimiento.xlsx"
        
        # Convertimos a Excel usando pandas
        df.to_excel(excel_file, index=False, engine='openpyxl')

        # Enviamos el archivo al navegador
        return send_file(excel_file, as_attachment=True)
    except Exception as e:
        return str(e), 500

if __name__ == '__main__':
    init_db()
    # Render usa el puerto 10000 por defecto
    port = int(os.environ.get("PORT", 10000))

    app.run(host='0.0.0.0', port=port)
