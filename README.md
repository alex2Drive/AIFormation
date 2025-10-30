# AIFormation 🤖

AI-Driven Development Orchestration System met een visuele webinterface voor het beheren van scripts en bekijken van gegenereerde project data.

## Overzicht

AIFormation bestaat uit twee delen:
1. **Python Scripts** - Genereren project documentatie en sprints via Claude AI
2. **Web Interface** - Visuele interface om data te bekijken en scripts te beheren

## Installatie

### Vereisten

- Python 3.8+
- pip (Python package manager)

### Stappen

1. Clone de repository (indien nog niet gedaan)

2. Installeer de vereiste Python packages:
```bash
pip install -r requirements.txt
```

3. Start de webserver:
```bash
python app.py
```

4. Open je browser en ga naar:
```
http://localhost:5000
```

## Web Interface

### Dashboard
Het dashboard toont een overzicht van:
- Aantal documenten en sprints
- Totaal aantal taken en voltooide taken
- Voortgangsbalk met percentage voltooid
- Snelle toegang tot belangrijke secties

### Documentatie Viewer
Bekijk alle gegenereerde project documentatie visueel:
- **Project Overzicht** - Algemene projectinformatie en tech stack
- **Requirements** - Functionele en niet-functionele eisen
- **Architectuur** - Technische architectuur en lagen
- **API Structuur** - Endpoints en authenticatie
- **Workflows** - User flows en processen
- **Data Models** - Database schema en relaties
- **Class Structuur** - Backend en frontend classes
- **File Structuur** - Project folder hiërarchie

Elk document kan zowel visueel als in JSON formaat bekeken worden.

### Sprints Viewer
Bekijk en beheer development sprints:
- **Sprint Overzicht** - Lijst van alle sprints met voortgang
- **Sprint Details** - Gedetailleerde weergave van een sprint
- **Taak Cards** - Visuele weergave van taken met status badges
- **Filter Opties** - Filter taken op status (voltooid, bezig, wachtend, geblokkeerd)
- **Taak Details** - Volledige informatie over elke taak inclusief:
  - Beschrijving en uitvoerings gids
  - Deliverables en validatie checklist
  - Constraints en toegestane documentatie
  - Dependencies

### Script Manager
Beheer en configureer de Python scripts:
- **Project Builder** - Genereert project documentatie uit beschrijving
- **Sprint Generator** - Maakt sprints uit project docs
- **Development Agents** - Voert taken uit met AI agents

Elk script heeft een configuratie dialog met de benodigde parameters.

### Recente Logs
Bekijk recente log bestanden van script uitvoeringen.

## Python Scripts

### 1. Project Builder Agent

Converteert een natuurlijke taal projectbeschrijving naar gedetailleerde technische documentatie.

```bash
python project_builder_agent_v2.2.py "Beschrijf je project hier"
```

**Output:** `project_docs/` directory met 7 JSON bestanden

### 2. Sprint Generator

Genereert uitvoerbare development sprints uit project documentatie.

```bash
python sprint_generator_v2.2.py ./project_docs
```

**Output:** `sprints/` directory met sprint JSON bestanden

### 3. Development Agents

Voert development taken uit met Claude AI agents.

```bash
python development_agents_v2_3_enhanced.py ./my_project \
  --docs ./project_docs \
  --sprints ./sprints \
  --mode parallel \
  --max-tasks 10
```

**Modes:**
- `parallel` - Beide agents (backend + frontend) werken afwisselend
- `sequential` - Eerst backend, dan frontend
- `backend` - Alleen backend agent
- `frontend` - Alleen frontend agent

## Workflow

1. **Definieer je Project**
   - Gebruik Project Builder om documentatie te genereren
   - Bekijk de gegenereerde docs in de web interface

2. **Genereer Sprints**
   - Gebruik Sprint Generator om uitvoerbare taken te maken
   - Bekijk sprints en taken in de web interface

3. **Voer Taken Uit**
   - Gebruik Development Agents om code te genereren
   - Monitor voortgang in real-time via de web interface

4. **Track Voortgang**
   - Dashboard toont overall voortgang
   - Sprint detail pagina's tonen status per taak
   - Filter en zoek door taken

## Directory Structuur

```
AIFormation/
├── app.py                              # Flask web applicatie
├── requirements.txt                    # Python dependencies
├── project_builder_agent_v2.2.py      # Script 1: Project documentatie
├── sprint_generator_v2.2.py           # Script 2: Sprint generator
├── development_agents_v2_3_enhanced.py # Script 3: Development agents
├── templates/                          # HTML templates
│   ├── base.html                      # Base template
│   ├── index.html                     # Dashboard
│   ├── docs.html                      # Docs overzicht
│   ├── doc_detail.html               # Doc detail view
│   ├── sprints.html                   # Sprints overzicht
│   ├── sprint_detail.html            # Sprint detail view
│   ├── task_detail.html              # Taak detail view
│   └── scripts.html                   # Script manager
├── static/                             # Statische bestanden
│   ├── css/
│   │   └── style.css                  # Styling
│   └── js/
│       └── main.js                    # JavaScript
├── project_docs/                       # Gegenereerde documentatie
├── sprints/                           # Gegenereerde sprints
└── logs/                              # Script logs
```

## Features

### ✨ Visuele Interface
- Modern en responsive design
- Geen rauwe JSON - alles mooi geformatteerd
- Kleurgecodeerde status badges
- Voortgangsbalken en statistieken

### 📊 Real-time Data
- Automatisch laden van gegenereerde data
- Live statistieken op dashboard
- Filter en zoek functionaliteit

### 🎯 Taak Management
- Overzichtelijke taakkaarten
- Status tracking (pending, in progress, completed, blocked)
- Dependencies en validatie checklists
- Uitgebreide taak details

### 🔧 Script Management
- Eenvoudige configuratie van scripts
- Commando generator voor terminal uitvoering
- Log viewer (in ontwikkeling)

## API Endpoints

De web interface biedt ook REST API endpoints:

- `GET /api/docs` - Alle project documentatie
- `GET /api/sprints` - Alle sprints
- `GET /api/stats` - Statistieken

## Tips

1. **Start Simpel** - Begin met een kleine projectbeschrijving om het systeem te leren kennen
2. **Gebruik de Web Interface** - Veel makkelijker dan JSON bestanden bekijken
3. **Monitor Logs** - Kijk in `logs/` directory voor gedetailleerde uitvoer
4. **Itereer** - Je kunt scripts meerdere keren uitvoeren en verfijnen

## Troubleshooting

**Web interface start niet:**
- Controleer of Flask geïnstalleerd is: `pip install Flask`
- Controleer of poort 5000 vrij is

**Geen data zichtbaar:**
- Voer eerst de Python scripts uit om data te genereren
- Controleer of `project_docs/` en `sprints/` directories bestaan

**Scripts werken niet:**
- Zorg dat Claude CLI geïnstalleerd is: `npm install -g @anthropic-ai/claude`
- Controleer je Claude API credentials

## Licentie

Dit project is gemaakt voor AI-gedreven software development.