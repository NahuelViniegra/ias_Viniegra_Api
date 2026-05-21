import pytest
import sys
import os

# Añadimos el directorio app al path para poder importar
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from app.main import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    
    # Limpiar y resembrar la base de datos de prueba para asegurar aislamiento e idempotencia
    from app.main import get_db_connection, get_cursor
    conn = get_db_connection()
    cur = get_cursor(conn)
    cur.execute('DELETE FROM professors;')
    try:
        # Resetear el autoincremento en SQLite
        cur.execute("DELETE FROM sqlite_sequence WHERE name='professors';")
    except Exception:
        pass
        
    initial_professors = [
        ("Ada Lovelace", "Mathematics"),
        ("Alan Turing", "Computer Science")
    ]
    for name, subject in initial_professors:
        cur.execute('INSERT INTO professors (name, subject) VALUES (?, ?);', (name, subject))
    conn.commit()
    cur.close()
    conn.close()

    with app.test_client() as client:
        yield client


def test_healthcheck(client):
    response = client.get('/healthcheck')
    assert response.status_code == 200
    assert response.get_json() == {"status": "ok", "message": "API is running"}

def test_get_professors(client):
    response = client.get('/professors')
    assert response.status_code == 200
    data = response.get_json()
    assert len(data) >= 2
    assert data[0]['name'] == 'Ada Lovelace'

def test_get_single_professor(client):
    response = client.get('/professors/1')
    assert response.status_code == 200
    data = response.get_json()
    assert data['name'] == 'Ada Lovelace'

def test_get_professor_not_found(client):
    response = client.get('/professors/999')
    assert response.status_code == 404

def test_create_professor(client):
    new_prof = {"name": "Grace Hopper", "subject": "Compilers"}
    response = client.post('/professors', json=new_prof)
    assert response.status_code == 201
    data = response.get_json()
    assert data['name'] == "Grace Hopper"
    assert data['id'] > 0

def test_update_professor(client):
    update_data = {"subject": "Advanced Mathematics"}
    response = client.put('/professors/1', json=update_data)
    assert response.status_code == 200
    data = response.get_json()
    assert data['subject'] == "Advanced Mathematics"
    assert data['name'] == "Ada Lovelace"

def test_delete_professor(client):
    response = client.delete('/professors/2')
    assert response.status_code == 200
    
    # Verify deletion
    verify_response = client.get('/professors/2')
    assert verify_response.status_code == 404
