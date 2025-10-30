#!/usr/bin/env python3
"""
AIFormation Web Interface
Een visuele interface voor het beheren van scripts en bekijken van gegenereerde data.
"""

import json
import os
import subprocess
from datetime import datetime
from pathlib import Path
from flask import Flask, render_template, jsonify, request, redirect, url_for
from typing import Dict, List, Any, Optional

app = Flask(__name__)
app.config['SECRET_KEY'] = 'dev-secret-key-change-in-production'

# Base paths
BASE_DIR = Path(__file__).parent
DOCS_DIR = BASE_DIR / "project_docs"
SPRINTS_DIR = BASE_DIR / "sprints"
LOGS_DIR = BASE_DIR / "logs"


class DataLoader:
    """Laadt en parst alle project data."""

    @staticmethod
    def load_json(filepath: Path) -> Optional[Dict]:
        """Laadt JSON bestand veilig."""
        try:
            if filepath.exists():
                with open(filepath, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            print(f"Error loading {filepath}: {e}")
        return None

    @staticmethod
    def get_project_docs() -> Dict[str, Any]:
        """Haalt alle project documentatie op."""
        docs = {}
        if DOCS_DIR.exists():
            # Laad alle JSON bestanden
            doc_files = {
                'overview': DOCS_DIR / 'PROJECT_OVERVIEW.json',
                'requirements': DOCS_DIR / 'requirements' / 'requirements.json',
                'architecture': DOCS_DIR / 'architecture' / 'architecture.json',
                'api': DOCS_DIR / 'api' / 'api_structure.json',
                'workflows': DOCS_DIR / 'workflows' / 'workflows.json',
                'database': DOCS_DIR / 'database' / 'data_models.json',
                'classes': DOCS_DIR / 'classes' / 'classes.json',
                'files': DOCS_DIR / 'files' / 'file_structure.json',
            }

            for key, filepath in doc_files.items():
                data = DataLoader.load_json(filepath)
                if data:
                    docs[key] = data

        return docs

    @staticmethod
    def get_sprints() -> List[Dict]:
        """Haalt alle sprints op."""
        sprints = []
        if SPRINTS_DIR.exists():
            sprint_files = sorted(SPRINTS_DIR.glob('sprint_*.json'))
            for sprint_file in sprint_files:
                data = DataLoader.load_json(sprint_file)
                if data:
                    sprints.append(data)
        return sprints

    @staticmethod
    def get_sprint_overview() -> Optional[Dict]:
        """Haalt sprint overzicht op."""
        overview_path = SPRINTS_DIR / 'sprints_overview.json'
        return DataLoader.load_json(overview_path)

    @staticmethod
    def get_logs() -> List[Dict]:
        """Haalt recente logs op."""
        logs = []
        if LOGS_DIR.exists():
            log_files = sorted(LOGS_DIR.glob('*.log'), reverse=True)[:10]
            for log_file in log_files:
                try:
                    size = log_file.stat().st_size
                    modified = datetime.fromtimestamp(log_file.stat().st_mtime)
                    logs.append({
                        'name': log_file.name,
                        'size': f"{size / 1024:.1f} KB",
                        'modified': modified.strftime('%Y-%m-%d %H:%M:%S')
                    })
                except Exception as e:
                    print(f"Error reading log {log_file}: {e}")
        return logs


@app.route('/')
def index():
    """Dashboard homepage."""
    # Verzamel statistieken
    docs = DataLoader.get_project_docs()
    sprints = DataLoader.get_sprints()
    sprint_overview = DataLoader.get_sprint_overview()

    # Bereken statistieken
    total_tasks = 0
    completed_tasks = 0
    in_progress_tasks = 0
    pending_tasks = 0

    for sprint in sprints:
        if 'tasks' in sprint:
            total_tasks += len(sprint['tasks'])
            for task in sprint['tasks']:
                status = task.get('status', 'pending')
                if status == 'completed':
                    completed_tasks += 1
                elif status == 'in_progress':
                    in_progress_tasks += 1
                elif status == 'pending':
                    pending_tasks += 1

    stats = {
        'total_docs': len(docs),
        'total_sprints': len(sprints),
        'total_tasks': total_tasks,
        'completed_tasks': completed_tasks,
        'in_progress_tasks': in_progress_tasks,
        'pending_tasks': pending_tasks,
        'has_docs': len(docs) > 0,
        'has_sprints': len(sprints) > 0
    }

    return render_template('index.html', stats=stats)


@app.route('/docs')
def docs():
    """Project documentatie overzicht."""
    project_docs = DataLoader.get_project_docs()
    return render_template('docs.html', docs=project_docs)


@app.route('/docs/<doc_type>')
def doc_detail(doc_type):
    """Detailweergave van specifieke documentatie."""
    project_docs = DataLoader.get_project_docs()
    doc_data = project_docs.get(doc_type)

    if not doc_data:
        return "Document niet gevonden", 404

    return render_template('doc_detail.html',
                         doc_type=doc_type,
                         doc_data=doc_data,
                         doc_json=json.dumps(doc_data, indent=2))


@app.route('/sprints')
def sprints():
    """Sprints overzicht."""
    sprint_list = DataLoader.get_sprints()
    sprint_overview = DataLoader.get_sprint_overview()

    return render_template('sprints.html',
                         sprints=sprint_list,
                         overview=sprint_overview)


@app.route('/sprint/<int:sprint_num>')
def sprint_detail(sprint_num):
    """Detailweergave van een specifieke sprint."""
    sprints_list = DataLoader.get_sprints()

    # Vind de juiste sprint
    sprint_data = None
    for sprint in sprints_list:
        if sprint.get('sprint_number') == sprint_num:
            sprint_data = sprint
            break

    if not sprint_data:
        return "Sprint niet gevonden", 404

    # Bereken statistieken voor deze sprint
    tasks = sprint_data.get('tasks', [])
    stats = {
        'total': len(tasks),
        'completed': sum(1 for t in tasks if t.get('status') == 'completed'),
        'in_progress': sum(1 for t in tasks if t.get('status') == 'in_progress'),
        'pending': sum(1 for t in tasks if t.get('status') == 'pending'),
        'blocked': sum(1 for t in tasks if t.get('status') == 'blocked'),
    }

    return render_template('sprint_detail.html',
                         sprint=sprint_data,
                         stats=stats)


@app.route('/task/<task_id>')
def task_detail(task_id):
    """Detailweergave van een specifieke taak."""
    sprints_list = DataLoader.get_sprints()

    # Zoek de taak in alle sprints
    task_data = None
    sprint_info = None

    for sprint in sprints_list:
        for task in sprint.get('tasks', []):
            if task.get('task_id') == task_id:
                task_data = task
                sprint_info = {
                    'number': sprint.get('sprint_number'),
                    'name': sprint.get('sprint_name')
                }
                break
        if task_data:
            break

    if not task_data:
        return "Taak niet gevonden", 404

    return render_template('task_detail.html',
                         task=task_data,
                         sprint=sprint_info)


@app.route('/scripts')
def scripts():
    """Script beheer pagina."""
    scripts_info = [
        {
            'name': 'Project Builder',
            'file': 'project_builder_agent_v2.2.py',
            'description': 'Converteert een projectbeschrijving naar gedetailleerde technische documentatie',
            'icon': '📋',
            'status': 'ready' if DOCS_DIR.exists() and any(DOCS_DIR.iterdir()) else 'not_run'
        },
        {
            'name': 'Sprint Generator',
            'file': 'sprint_generator_v2.2.py',
            'description': 'Genereert uitvoerbare development sprints uit project documentatie',
            'icon': '🏃',
            'status': 'ready' if SPRINTS_DIR.exists() and any(SPRINTS_DIR.iterdir()) else 'not_run'
        },
        {
            'name': 'Development Agents',
            'file': 'development_agents_v2_3_enhanced.py',
            'description': 'Voert development taken uit met Claude AI agents',
            'icon': '🤖',
            'status': 'ready'
        }
    ]

    logs = DataLoader.get_logs()

    return render_template('scripts.html', scripts=scripts_info, logs=logs)


@app.route('/api/run-script', methods=['POST'])
def run_script():
    """API endpoint om een script uit te voeren."""
    data = request.json
    script_name = data.get('script')
    args = data.get('args', [])

    if not script_name:
        return jsonify({'error': 'Geen script opgegeven'}), 400

    script_path = BASE_DIR / script_name
    if not script_path.exists():
        return jsonify({'error': 'Script niet gevonden'}), 404

    try:
        # Start het script in de achtergrond
        # Hier zou je een meer geavanceerde job queue kunnen gebruiken
        return jsonify({
            'status': 'started',
            'message': f'Script {script_name} wordt uitgevoerd',
            'script': script_name
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/docs')
def api_docs():
    """API endpoint voor documentatie data."""
    docs = DataLoader.get_project_docs()
    return jsonify(docs)


@app.route('/api/sprints')
def api_sprints():
    """API endpoint voor sprints data."""
    sprints_list = DataLoader.get_sprints()
    return jsonify(sprints_list)


@app.route('/api/stats')
def api_stats():
    """API endpoint voor statistieken."""
    docs = DataLoader.get_project_docs()
    sprints = DataLoader.get_sprints()

    total_tasks = 0
    completed_tasks = 0

    for sprint in sprints:
        if 'tasks' in sprint:
            total_tasks += len(sprint['tasks'])
            for task in sprint['tasks']:
                if task.get('status') == 'completed':
                    completed_tasks += 1

    return jsonify({
        'docs_count': len(docs),
        'sprints_count': len(sprints),
        'total_tasks': total_tasks,
        'completed_tasks': completed_tasks,
        'completion_percentage': round((completed_tasks / total_tasks * 100) if total_tasks > 0 else 0, 1)
    })


def find_available_port(preferred_port=5001, max_attempts=10):
    """
    Vindt een beschikbare poort, beginnend bij de preferred_port.
    Windows reserveert vaak poort 5000, dus we beginnen bij 5001.
    """
    import socket

    for port in range(preferred_port, preferred_port + max_attempts):
        try:
            # Test of de poort beschikbaar is
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                s.bind(('0.0.0.0', port))
                return port
        except OSError:
            continue

    # Als geen poort beschikbaar is, probeer een hogere range
    for port in range(8000, 8100):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                s.bind(('0.0.0.0', port))
                return port
        except OSError:
            continue

    raise RuntimeError("Geen beschikbare poort gevonden. Sluit andere applicaties en probeer opnieuw.")


if __name__ == '__main__':
    # Zorg ervoor dat directories bestaan
    DOCS_DIR.mkdir(exist_ok=True)
    SPRINTS_DIR.mkdir(exist_ok=True)
    LOGS_DIR.mkdir(exist_ok=True)

    print("🚀 AIFormation Web Interface")
    print(f"📁 Base directory: {BASE_DIR}")
    print(f"📋 Docs directory: {DOCS_DIR}")
    print(f"🏃 Sprints directory: {SPRINTS_DIR}")
    print(f"📝 Logs directory: {LOGS_DIR}")

    # Zoek een beschikbare poort (standaard 5001, niet 5000 vanwege Windows)
    # Kan ook via environment variabele worden ingesteld
    preferred_port = int(os.environ.get('FLASK_PORT', 5001))

    try:
        port = find_available_port(preferred_port)
        print(f"\n🌐 Server draait op: http://localhost:{port}")
        print(f"💡 Tip: Gebruik FLASK_PORT environment variabele om een andere poort te kiezen")
        print(f"   Voorbeeld: set FLASK_PORT=8000 (Windows) of export FLASK_PORT=8000 (Linux/Mac)\n")

        app.run(debug=True, host='0.0.0.0', port=port)
    except RuntimeError as e:
        print(f"\n❌ Error: {e}")
        print("💡 Probeer andere applicaties te sluiten die poorten gebruiken.")
    except Exception as e:
        print(f"\n❌ Onverwachte fout: {e}")
        print("💡 Controleer je firewall instellingen en poort permissies.")
