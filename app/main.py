import os
import sqlite3
# pyrefly: ignore [missing-import]
from flask import Flask, jsonify, request

app = Flask(__name__)

# Configuración mediante variables de entorno
ENV = os.environ.get('ENV', 'development')
DEBUG = os.environ.get('DEBUG', 'False').lower() in ('true', '1', 't')
DATABASE_URL = os.environ.get('DATABASE_URL')

def get_db_connection():
    """
    Establece y retorna la conexión a la base de datos adecuada.
    Usa PostgreSQL si DATABASE_URL está definida. En caso contrario, recurre a SQLite local.
    """
    if DATABASE_URL:
        import psycopg2
        conn = psycopg2.connect(DATABASE_URL)
        return conn
    else:
        conn = sqlite3.connect('app.db')
        conn.row_factory = sqlite3.Row
        return conn

def get_cursor(conn):
    """
    Retorna un cursor configurado según el tipo de base de datos.
    Para PostgreSQL retorna un RealDictCursor para obtener diccionarios de manera nativa.
    """
    if DATABASE_URL:
        import psycopg2.extras
        return conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    else:
        return conn.cursor()

def init_db():
    """
    Crea la tabla 'professors' si no existe e inserta datos iniciales.
    """
    conn = get_db_connection()
    cur = get_cursor(conn)
    if DATABASE_URL:
        cur.execute('''
            CREATE TABLE IF NOT EXISTS professors (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                subject VARCHAR(100) NOT NULL
            );
        ''')
    else:
        cur.execute('''
            CREATE TABLE IF NOT EXISTS professors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                subject TEXT NOT NULL
            );
        ''')
    conn.commit()
    
    # Insertar registros semilla si la tabla está vacía
    cur.execute('SELECT COUNT(*) as count FROM professors;' if DATABASE_URL else 'SELECT COUNT(*) as count FROM professors;')
    row = cur.fetchone()
    count = row['count'] if isinstance(row, dict) else row[0]
    
    if count == 0:
        initial_professors = [
            ("Ada Lovelace", "Mathematics"),
            ("Alan Turing", "Computer Science")
        ]
        for name, subject in initial_professors:
            if DATABASE_URL:
                cur.execute('INSERT INTO professors (name, subject) VALUES (%s, %s);', (name, subject))
            else:
                cur.execute('INSERT INTO professors (name, subject) VALUES (?, ?);', (name, subject))
        conn.commit()
        
    cur.close()
    conn.close()

# Inicializar base de datos al arrancar
with app.app_context():
    init_db()

@app.route('/healthcheck', methods=['GET'])
def healthcheck():
    try:
        conn = get_db_connection()
        cur = get_cursor(conn)
        cur.execute('SELECT 1;')
        cur.fetchone()
        cur.close()
        conn.close()
        return jsonify({"status": "ok", "message": "API is running"}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": f"DB connection failed: {str(e)}"}), 500

@app.route('/professors', methods=['GET'])
def get_professors():
    conn = get_db_connection()
    cur = get_cursor(conn)
    cur.execute('SELECT * FROM professors ORDER BY id ASC;')
    rows = cur.fetchall()
    professors = [dict(r) for r in rows]
    cur.close()
    conn.close()
    return jsonify(professors), 200

@app.route('/professors/<int:prof_id>', methods=['GET'])
def get_professor(prof_id):
    conn = get_db_connection()
    cur = get_cursor(conn)
    if DATABASE_URL:
        cur.execute('SELECT * FROM professors WHERE id = %s;', (prof_id,))
    else:
        cur.execute('SELECT * FROM professors WHERE id = ?;', (prof_id,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    if row:
        return jsonify(dict(row)), 200
    return jsonify({"error": "Profesor no encontrado"}), 404

@app.route('/professors', methods=['POST'])
def create_professor():
    data = request.get_json()
    if not data or not 'name' in data or not 'subject' in data:
        return jsonify({"error": "Missing 'name' or 'subject' in request"}), 400
        
    conn = get_db_connection()
    cur = get_cursor(conn)
    
    if DATABASE_URL:
        cur.execute('INSERT INTO professors (name, subject) VALUES (%s, %s) RETURNING id;', (data['name'], data['subject']))
        new_id = cur.fetchone()['id']
    else:
        cur.execute('INSERT INTO professors (name, subject) VALUES (?, ?);', (data['name'], data['subject']))
        new_id = cur.lastrowid
        
    conn.commit()
    cur.close()
    conn.close()
    
    return jsonify({"id": new_id, "name": data['name'], "subject": data['subject']}), 201

@app.route('/professors/<int:prof_id>', methods=['PUT'])
def update_professor(prof_id):
    data = request.get_json()
    conn = get_db_connection()
    cur = get_cursor(conn)
    
    # Verificar si existe
    if DATABASE_URL:
        cur.execute('SELECT * FROM professors WHERE id = %s;', (prof_id,))
    else:
        cur.execute('SELECT * FROM professors WHERE id = ?;', (prof_id,))
    row = cur.fetchone()
    
    if not row:
        cur.close()
        conn.close()
        return jsonify({"error": "Professor not found"}), 404
        
    name = data.get('name', row['name'])
    subject = data.get('subject', row['subject'])
    
    if DATABASE_URL:
        cur.execute('UPDATE professors SET name = %s, subject = %s WHERE id = %s;', (name, subject, prof_id))
    else:
        cur.execute('UPDATE professors SET name = ?, subject = ? WHERE id = ?;', (name, subject, prof_id))
        
    conn.commit()
    cur.close()
    conn.close()
    
    return jsonify({"id": prof_id, "name": name, "subject": subject}), 200

@app.route('/professors/<int:prof_id>', methods=['DELETE'])
def delete_professor(prof_id):
    conn = get_db_connection()
    cur = get_cursor(conn)
    
    # Verificar si existe
    if DATABASE_URL:
        cur.execute('SELECT * FROM professors WHERE id = %s;', (prof_id,))
    else:
        cur.execute('SELECT * FROM professors WHERE id = ?;', (prof_id,))
    row = cur.fetchone()
    
    if not row:
        cur.close()
        conn.close()
        return jsonify({"error": "Professor not found"}), 404
        
    if DATABASE_URL:
        cur.execute('DELETE FROM professors WHERE id = %s;', (prof_id,))
    else:
        cur.execute('DELETE FROM professors WHERE id = ?;', (prof_id,))
        
    conn.commit()
    cur.close()
    conn.close()
    
    return jsonify({"message": "Professor deleted successfully"}), 200

if __name__ == '__main__':
    app.run(debug=DEBUG, host='127.0.0.1', port=5000)

