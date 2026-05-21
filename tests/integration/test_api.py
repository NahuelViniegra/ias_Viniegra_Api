import pytest
import sys
import os

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


def test_api_workflow(client):
    # 1. Check health
    assert client.get('/healthcheck').status_code == 200
    
    # 2. Add a new professor
    new_prof = {"name": "Linus Torvalds", "subject": "Operating Systems"}
    create_response = client.post('/professors', json=new_prof)
    assert create_response.status_code == 201
    created_id = create_response.get_json()['id']
    
    # 3. Retrieve the created professor
    get_response = client.get(f'/professors/{created_id}')
    assert get_response.status_code == 200
    assert get_response.get_json()['name'] == "Linus Torvalds"
    
    # 4. Update the professor
    update_response = client.put(f'/professors/{created_id}', json={"subject": "Linux Kernel"})
    assert update_response.status_code == 200
    
    # 5. Delete the professor
    delete_response = client.delete(f'/professors/{created_id}')
    assert delete_response.status_code == 200
    
    # 6. Verify it's gone
    assert client.get(f'/professors/{created_id}').status_code == 404
