import subprocess
import pytest
import os
import sys

def test_bandit_security_scan():
    """
    Run bandit programmatically to ensure no security issues are found.
    """
    # Buscar el ejecutable de bandit en el mismo directorio que el binario de Python (entorno virtual)
    python_dir = os.path.dirname(sys.executable)
    bandit_executable = 'bandit'
    
    for name in ['bandit', 'bandit.exe', 'Scripts/bandit.exe', 'bin/bandit']:
        # Buscar en el mismo directorio o directorios relativos comunes
        candidates = [
            os.path.join(python_dir, name),
            os.path.join(python_dir, '..', name),
            os.path.join(python_dir, 'Scripts', name)
        ]
        found = False
        for c in candidates:
            if os.path.exists(c):
                bandit_executable = os.path.abspath(c)
                found = True
                break
        if found:
            break

    try:
        app_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../app'))
        result = subprocess.run(
            [bandit_executable, '-r', app_dir, '-f', 'json'],
            capture_output=True,
            text=True
        )
        
        # Bandit exits with 0 if no issues, or >0 if issues are found
        assert result.returncode == 0, f"Bandit found potential security issues:\n{result.stdout}"
    except FileNotFoundError:
        pytest.fail(f"Bandit is not installed or not found in PATH. Path intentado: {bandit_executable}")

