from flask import Flask, request, jsonify, send_file
from flask_cors import CORS # Importante para conexión móvil
import sqlite3
import pandas as pd
import os

app = Flask(__name__)
CORS(app) # Permite que tu App de Android se conecte sin bloqueos

DB_NAME = "database_final.db"

def crear_tablas_si_no_existen():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    # Tabla SEGUIMIENTO: 18 campos estandarizados
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS SEGUIMIENTO (
            ID INTEGER PRIMARY KEY AUTOINCREMENT,
            FECHA TEXT, REGION TEXT, ANALISTA TEXT, CLIENTE TEXT,
            SUCURSAL TEXT, SERIE TEXT, FOLIO TEXT, LLEGADA TEXT,
            CONTACTO TEXT, CANALIZA TEXT, AREA TEXT, RESP TEXT,
            REC1 TEXT, REC2 TEXT, SOLUCION_H TEXT, CIERRE TEXT,
            FALLA TEXT, SOLUCION TEXT
        )
    ''')
    # Tabla INV: Estructura corregida para el Inventario
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS INV (
            ID INTEGER PRIMARY KEY AUTOINCREMENT,
            REGION TEXT, SUCURSAL TEXT, MODELO TEXT,
            NUM_SERIE TEXT UNIQUE, LF TEXT, STATUS TEXT, CLIENTE TEXT
        )
    ''')
    conn.commit()
    conn.close()

# RUTA DE BIENVENIDA (Para evitar el error 404 en Render)
@app.route('/')
def home():
    crear_tablas_si_no_existen()
    return "Servidor SeproGuardias Activo - API v1.0", 200

# RUTA PARA RECIBIR REPORTES DESDE LA APP
@app.route('/enviar_reporte', methods=['POST'])
def enviar_reporte():
    crear_tablas_si_no_existen()
    data = request.json
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        query = '''
            INSERT INTO SEGUIMIENTO (
                FECHA, REGION, ANALISTA, CLIENTE, SUCURSAL, SERIE, FOLIO, 
                LLEGADA, CONTACTO, CANALIZA, AREA, RESP, REC1, REC2, 
                SOLUCION_H, CIERRE, FALLA, SOLUCION
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        '''
        valores = (
            data.get('fecha'), data.get('region'), data.get('analista'), data.get('cliente'),
            data.get('sucursal'), data.get('serie'), data.get('folio'), data.get('llegada'),
            data.get('contacto'), data.get('canaliza'), data.get('area'), data.get('resp'),
            data.get('rec1'), data.get('rec2'), data.get('solucion_h'), data.get('cierre'),
            data.get('falla'), data.get('solucion')
        )
        cursor.execute(query, valores)
        conn.commit()
        return jsonify({"status": "success", "message": "Reporte guardado"}), 201
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400
    finally:
        conn.close()

# RUTA PARA QUE LA APP DESCARGUE EL INVENTARIO COMPLETO (Optimizada)
@app.route('/inventario_total', methods=['GET'])
def inventario_total():
    crear_tablas_si_no_existen()
    try:
        conn = sqlite3.connect(DB_NAME)
        # Mapeamos los nombres de las columnas para que coincidan con el modelo 'Equipo' de Kotlin
        df = pd.read_sql_query("SELECT CLIENTE, SUCURSAL, NUM_SERIE, REGION FROM INV", conn)
        conn.close()
        return df.to_json(orient='records')
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# RUTA PARA CARGA MASIVA (Desde Excel o JSON externo)
@app.route('/enviar_inventario_masivo', methods=['POST'])
def enviar_inventario_masivo():
    crear_tablas_si_no_existen()
    data = request.json 
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        for item in data:
            cursor.execute('''
                INSERT OR REPLACE INTO INV (REGION, SUCURSAL, MODELO, NUM_SERIE, LF, STATUS, CLIENTE)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (item['region'], item['sucursal'], item['modelo'], item['serie'], item['lf'], item['status'], item['cliente']))
        conn.commit()
        return jsonify({"status": "success", "message": f"{len(data)} equipos actualizados"}), 201
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400
    finally:
        conn.close()

# RUTA PARA DESCARGAR EXCEL DE SEGUIMIENTO
@app.route('/descargar_reportes', methods=['GET'])
def descargar_reportes():
    try:
        crear_tablas_si_no_existen()
        conn = sqlite3.connect(DB_NAME)
        df = pd.read_sql_query("SELECT * FROM SEGUIMIENTO", conn)
        conn.close()

        if df.empty:
            return "No hay reportes para exportar.", 200

        excel_file = "reporte_seguimiento.xlsx"
        df.to_excel(excel_file, index=False, engine='openpyxl')
        return send_file(excel_file, as_attachment=True)
    except Exception as e:
        return f"Error técnico: {str(e)}", 500

if __name__ == '__main__':
    crear_tablas_si_no_existen()
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
