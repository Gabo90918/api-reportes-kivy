from flask import Flask, request, jsonify, send_file
import sqlite3
import pandas as pd
import os

app = Flask(__name__)
DB_NAME = "gestion_reportes.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    # Tabla de Inventario
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS INV (
            ID INTEGER PRIMARY KEY AUTOINCREMENT,
            REGION TEXT, SUCURSAL TEXT, MODELO TEXT,
            NUM_SERIE TEXT UNIQUE, LF TEXT, STATUS TEXT, CLIENTE TEXT
        )
    ''')
    # Tabla de Seguimiento (Con los 18 campos necesarios)
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
    conn.commit()
    conn.close()

@app.route('/enviar_reporte', methods=['POST'])
def enviar_reporte():
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
        return jsonify({"status": "success"}), 201
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400
    finally:
        conn.close()

@app.route('/inventario', methods=['GET'])
def obtener_inventario():
    try:
        conn = sqlite3.connect(DB_NAME)
        df = pd.read_sql_query("SELECT CLIENTE as cliente, SUCURSAL as sucursal, NUM_SERIE as serie, REGION as region FROM INV", conn)
        conn.close()
        return df.to_json(orient='records')
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/descargar_reportes', methods=['GET'])
def descargar_reportes():
    try:
        conn = sqlite3.connect(DB_NAME)
        df = pd.read_sql_query("SELECT * FROM SEGUIMIENTO", conn)
        conn.close()
        if df.empty:
            return "No hay reportes guardados todavía.", 404
        
        excel_file = "reporte_seguimiento.xlsx"
        df.to_excel(excel_file, index=False, engine='openpyxl')
        return send_file(excel_file, as_attachment=True)
    except Exception as e:
        return str(e), 500

if __name__ == '__main__':
    init_db()
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
