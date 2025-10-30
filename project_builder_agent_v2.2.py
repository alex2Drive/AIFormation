#!/usr/bin/env python3
"""
ICT Project Builder Agent
Gebruikt Claude CLI om van een projectbeschrijving een gedetailleerde projectstructuur te maken

Doorloopt 7 fasen:
1. Requirements Analyse
2. Architectuur Ontwerp  
3. API Structuur
4. Workflows
5. Data Modellen
6. Class Structuur
7. Bestandsstructuur
"""

import subprocess
import json
import os
from pathlib import Path
from typing import Dict, Any
import sys

class ProjectBuilderAgent:
    def __init__(self, output_dir: str = "./project_docs"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
    def call_claude_cli(self, prompt: str) -> str:
        """Roept Claude CLI aan met een prompt"""
        try:
            # Claude CLI aanroepen met de prompt
            # --dangerously-skip-permissions zorgt ervoor dat geen toestemming gevraagd wordt
            result = subprocess.run(
                ['claude', '--dangerously-skip-permissions', '-'],
                input=prompt,
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout
        except subprocess.CalledProcessError as e:
            print(f"❌ Fout bij aanroepen Claude CLI: {e}")
            print(f"Error output: {e.stderr}")
            sys.exit(1)
        except FileNotFoundError:
            print("❌ Claude CLI niet gevonden. Installeer eerst: npm install -g @anthropic-ai/claude")
            sys.exit(1)
    
    def extract_json_from_response(self, response: str) -> Dict[str, Any]:
        """Haalt JSON uit de Claude response"""
        # Zoek naar JSON in de response (tussen ```json en ``` of direct JSON)
        import re
        
        # Probeer eerst JSON code block
        json_match = re.search(r'```json\s*(\{.*?\})\s*```', response, re.DOTALL)
        if json_match:
            return json.loads(json_match.group(1))
        
        # Probeer direct JSON te parsen
        try:
            # Zoek naar eerste { en laatste }
            start = response.find('{')
            end = response.rfind('}') + 1
            if start != -1 and end > start:
                return json.loads(response[start:end])
        except json.JSONDecodeError:
            pass
        
        print("⚠️  Geen JSON gevonden in response, ruwe response:")
        print(response)
        return {}
    
    def save_phase_result(self, phase_name: str, data: Dict[str, Any], subdir: str):
        """Sla een fase resultaat direct op"""
        phase_dir = self.output_dir / subdir
        phase_dir.mkdir(parents=True, exist_ok=True)
        
        filepath = phase_dir / f"{phase_name}.json"
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"  💾 Opgeslagen: {filepath}")
        return filepath
    
    def analyze_project_requirements(self, project_description: str) -> Dict[str, Any]:
        """Fase 1: Analyseer de projectbeschrijving en identificeer requirements"""
        print("\n📋 Fase 1: Analyseren van projectvereisten...")
        
        prompt = f"""Je bent een ervaren software architect. Analyseer de volgende projectbeschrijving en identificeer de key requirements.

Projectbeschrijving:
{project_description}

Geef je analyse in het volgende JSON formaat (alleen de JSON, geen extra tekst):

{{
  "project_name": "naam van het project",
  "project_type": "web_app|mobile_app|api|desktop_app|cli_tool|other",
  "primary_goal": "hoofddoel van het project",
  "target_users": ["type gebruiker 1", "type gebruiker 2"],
  "key_features": ["feature 1", "feature 2", "feature 3"],
  "technical_requirements": {{
    "frontend": "beschrijving of null",
    "backend": "beschrijving of null",
    "database": "beschrijving of null",
    "authentication": true/false,
    "external_apis": ["api 1", "api 2"] of [],
    "needs_api": true/false
  }},
  "complexity_level": "low|medium|high|very_high",
  "architecture_style": "api_driven|server_side_rendering|hybrid|static|other"
}}

BELANGRIJK voor needs_api beslissing:
- true: Als het een SPA is (React/Vue/Angular), mobile app, of expliciet een API moet bouwen
- false: Bij traditionele server-side rendering (PHP zonder API, Django templates, Rails views, etc)
- false: Bij static sites zonder backend API
"""
        
        response = self.call_claude_cli(prompt)
        result = self.extract_json_from_response(response)
        self.save_phase_result("requirements", result, "requirements")
        return result
    
    def design_architecture(self, requirements: Dict[str, Any]) -> Dict[str, Any]:
        """Fase 2: Ontwerp de software architectuur"""
        print("\n🏗️  Fase 2: Ontwerpen van architectuur...")
        
        prompt = f"""Je bent een software architect. Ontwerp de technische architectuur voor dit project.

Project Requirements:
{json.dumps(requirements, indent=2)}

Geef je architectuur in het volgende JSON formaat (alleen JSON):

{{
  "architecture_pattern": "MVC|Microservices|Layered|Clean|Other",
  "technology_stack": {{
    "frontend": {{
      "framework": "naam of null",
      "styling": "css framework of null",
      "state_management": "tool of null"
    }},
    "backend": {{
      "language": "programmeertaal",
      "framework": "framework naam",
      "server": "server type"
    }},
    "database": {{
      "type": "SQL|NoSQL|Graph|Other",
      "specific": "PostgreSQL|MongoDB|etc"
    }},
    "infrastructure": {{
      "hosting": "platform",
      "ci_cd": "tool",
      "monitoring": "tool of null"
    }}
  }},
  "layers": [
    {{
      "name": "laagnaam",
      "responsibility": "wat doet deze laag",
      "components": ["component1", "component2"]
    }}
  ],
  "data_flow": "beschrijving van hoe data door het systeem stroomt"
}}
"""
        
        response = self.call_claude_cli(prompt)
        result = self.extract_json_from_response(response)
        self.save_phase_result("architecture", result, "architecture")
        return result
    
    def define_api_structure(self, requirements: Dict[str, Any], architecture: Dict[str, Any]) -> Dict[str, Any]:
        """Fase 3: Definieer API structuur (alleen als nodig)"""
        print("\n🔌 Fase 3: Definiëren van API structuur...")
        
        # Check of project een API nodig heeft
        needs_api = requirements.get('technical_requirements', {}).get('needs_api', True)
        
        if not needs_api:
            print("  ℹ️  Project heeft geen API nodig (server-side rendering)")
            result = {
                "api_style": "none",
                "needs_api": False,
                "reason": "Project gebruikt server-side rendering zonder API endpoints",
                "endpoints": []
            }
            self.save_phase_result("api_structure", result, "api")
            return result
        
        prompt = f"""Je bent een API designer. Ontwerp de API structuur voor dit project.

Requirements: {json.dumps(requirements, indent=2)}
Architecture: {json.dumps(architecture, indent=2)}

Geef de API structuur in JSON formaat (alleen JSON):

{{
  "api_style": "REST|GraphQL|gRPC|WebSocket",
  "needs_api": true,
  "base_url": "/api/v1",
  "authentication": {{
    "type": "JWT|OAuth|API_Key|Session",
    "endpoints": ["/auth/login", "/auth/register"]
  }},
  "endpoints": [
    {{
      "path": "/resource",
      "method": "GET|POST|PUT|DELETE",
      "description": "wat doet dit endpoint",
      "request_body": {{"field": "type"}} of null,
      "response": {{"field": "type"}},
      "requires_auth": true/false
    }}
  ],
  "rate_limiting": {{
    "enabled": true/false,
    "requests_per_minute": 100
  }},
  "error_handling": {{
    "format": "beschrijving van error response format"
  }}
}}
"""
        
        response = self.call_claude_cli(prompt)
        result = self.extract_json_from_response(response)
        result['needs_api'] = True  # Expliciet markeren
        self.save_phase_result("api_structure", result, "api")
        return result
    
    def define_workflows(self, requirements: Dict[str, Any], api_structure: Dict[str, Any]) -> Dict[str, Any]:
        """Fase 4: Definieer workflows en user flows"""
        print("\n🔄 Fase 4: Definiëren van workflows...")
        
        prompt = f"""Je bent een UX/Process architect. Ontwerp de workflows en user flows voor dit project.

Requirements: {json.dumps(requirements, indent=2)}
API Structure: {json.dumps(api_structure, indent=2)}

Geef de workflows in JSON formaat (alleen JSON):

{{
  "user_workflows": [
    {{
      "workflow_name": "User Registration",
      "description": "Proces van account aanmaken",
      "trigger": "User clicks sign up button",
      "steps": [
        {{
          "step_number": 1,
          "action": "User fills in registration form",
          "actor": "User",
          "system_action": "Validate input fields",
          "api_calls": ["/api/v1/auth/check-email"],
          "success_condition": "All fields valid",
          "error_handling": "Show validation errors"
        }},
        {{
          "step_number": 2,
          "action": "User submits form",
          "actor": "User",
          "system_action": "Create account and send verification email",
          "api_calls": ["/api/v1/auth/register", "/api/v1/email/send-verification"],
          "success_condition": "Account created",
          "error_handling": "Show error message"
        }}
      ],
      "end_state": "User registered, awaiting email verification",
      "alternative_flows": [
        {{
          "name": "Email already exists",
          "trigger": "Email in use",
          "action": "Show error, suggest login or password reset"
        }}
      ]
    }}
  ],
  "system_workflows": [
    {{
      "workflow_name": "Automated Email Notifications",
      "description": "Systeem stuurt automatische emails",
      "trigger": "Event occurs (task assigned, deadline near, etc)",
      "steps": [
        {{
          "step_number": 1,
          "action": "Event detected",
          "system_action": "Check notification preferences",
          "api_calls": ["/api/v1/users/{{userId}}/preferences"]
        }},
        {{
          "step_number": 2,
          "action": "Send notification",
          "system_action": "Queue email and send",
          "api_calls": ["/api/v1/notifications/send"]
        }}
      ],
      "frequency": "real-time|scheduled|batch",
      "retry_logic": "3 attempts with exponential backoff"
    }}
  ],
  "business_processes": [
    {{
      "process_name": "Task Lifecycle",
      "description": "Complete levenscyclus van een taak",
      "stages": [
        {{
          "stage": "Created",
          "possible_transitions": ["Assigned", "Deleted"],
          "required_permissions": ["task.create"]
        }},
        {{
          "stage": "Assigned",
          "possible_transitions": ["In Progress", "Unassigned"],
          "required_permissions": ["task.assign"]
        }},
        {{
          "stage": "In Progress",
          "possible_transitions": ["Completed", "Blocked", "Assigned"],
          "required_permissions": ["task.update"]
        }},
        {{
          "stage": "Completed",
          "possible_transitions": ["Reopened"],
          "required_permissions": ["task.complete"]
        }}
      ]
    }}
  ],
  "integration_flows": [
    {{
      "name": "Third-party API Integration",
      "description": "Integratie met externe services",
      "external_service": "Service naam",
      "direction": "inbound|outbound|bidirectional",
      "authentication": "API Key|OAuth|JWT",
      "data_sync_frequency": "real-time|hourly|daily",
      "error_handling": "Log and retry with exponential backoff"
    }}
  ]
}}
"""
        
        response = self.call_claude_cli(prompt)
        result = self.extract_json_from_response(response)
        self.save_phase_result("workflows", result, "workflows")
        return result
    
    def define_data_models(self, requirements: Dict[str, Any], api_structure: Dict[str, Any], 
                           workflows: Dict[str, Any]) -> Dict[str, Any]:
        """Fase 5: Definieer data modellen en database schema"""
        print("\n💾 Fase 5: Definiëren van data modellen...")
        
        prompt = f"""Je bent een database architect. Ontwerp de data modellen en database schema.

Requirements: {json.dumps(requirements, indent=2)}
API Structure: {json.dumps(api_structure, indent=2)}
Workflows: {json.dumps(workflows, indent=2)}

Geef de data modellen in JSON formaat (alleen JSON):

{{
  "models": [
    {{
      "name": "ModelNaam",
      "description": "wat representeert dit model",
      "fields": [
        {{
          "name": "field_name",
          "type": "string|integer|boolean|date|reference",
          "required": true/false,
          "unique": true/false,
          "reference_to": "ModelNaam" of null
        }}
      ],
      "relationships": [
        {{
          "type": "one_to_many|many_to_many|one_to_one",
          "with_model": "ModelNaam",
          "description": "beschrijving relatie"
        }}
      ],
      "indexes": ["field1", "field2"]
    }}
  ],
  "database_diagram": "tekstuele beschrijving van hoe modellen aan elkaar hangen"
}}
"""
        
        response = self.call_claude_cli(prompt)
        result = self.extract_json_from_response(response)
        self.save_phase_result("data_models", result, "database")
        return result
    
    def define_classes_structure(self, requirements: Dict[str, Any], architecture: Dict[str, Any], 
                                 data_models: Dict[str, Any]) -> Dict[str, Any]:
        """Fase 6: Definieer class structuur en componenten"""
        print("\n📦 Fase 6: Definiëren van class structuur...")
        
        prompt = f"""Je bent een software engineer. Definieer de belangrijkste classes en componenten.

Requirements: {json.dumps(requirements, indent=2)}
Architecture: {json.dumps(architecture, indent=2)}
Data Models: {json.dumps(data_models, indent=2)}

Geef de class structuur in JSON formaat (alleen JSON):

{{
  "classes": [
    {{
      "name": "ClassName",
      "type": "controller|service|repository|model|utility|component",
      "responsibility": "wat doet deze class",
      "methods": [
        {{
          "name": "method_name",
          "parameters": [{{"name": "param", "type": "type"}}],
          "return_type": "type",
          "description": "wat doet deze methode"
        }}
      ],
      "dependencies": ["ClassName1", "ClassName2"],
      "implements": ["Interface1"] of []
    }}
  ],
  "interfaces": [
    {{
      "name": "InterfaceName",
      "methods": ["method_signature"]
    }}
  ]
}}
"""
        
        response = self.call_claude_cli(prompt)
        result = self.extract_json_from_response(response)
        self.save_phase_result("classes", result, "classes")
        return result
    
    def define_file_structure(self, requirements: Dict[str, Any], architecture: Dict[str, Any], 
                             classes: Dict[str, Any]) -> Dict[str, Any]:
        """Fase 7: Definieer bestandsstructuur"""
        print("\n📁 Fase 7: Definiëren van bestandsstructuur...")
        
        prompt = f"""Je bent een software architect. Ontwerp de complete bestandsstructuur van het project.

Requirements: {json.dumps(requirements, indent=2)}
Architecture: {json.dumps(architecture, indent=2)}
Classes: {json.dumps(classes, indent=2)}

Geef de file structuur in JSON formaat (alleen JSON):

{{
  "project_root": "project-naam",
  "structure": [
    {{
      "path": "src/",
      "type": "directory",
      "purpose": "main source code",
      "children": [
        {{
          "path": "controllers/",
          "type": "directory",
          "purpose": "controller classes",
          "files": [
            {{
              "name": "UserController.py",
              "purpose": "handles user requests",
              "contains_classes": ["UserController"]
            }}
          ]
        }}
      ]
    }},
    {{
      "path": "tests/",
      "type": "directory",
      "purpose": "test files"
    }},
    {{
      "path": "docs/",
      "type": "directory",
      "purpose": "documentation"
    }}
  ],
  "config_files": [
    {{
      "name": ".env.example",
      "purpose": "environment variables template"
    }},
    {{
      "name": "requirements.txt",
      "purpose": "Python dependencies"
    }}
  ]
}}
"""
        
        response = self.call_claude_cli(prompt)
        result = self.extract_json_from_response(response)
        self.save_phase_result("file_structure", result, "files")
        return result
    
    def save_to_files(self, project_data: Dict[str, Any]):
        """Sla complete overview en README op"""
        print("\n💾 Finaliseren van documentatie...")
        
        # Maak een complete overview
        overview_path = self.output_dir / "PROJECT_OVERVIEW.json"
        with open(overview_path, 'w', encoding='utf-8') as f:
            json.dump(project_data, f, indent=2, ensure_ascii=False)
        print(f"  ✅ {overview_path}")
        
        # Maak een README
        self.create_readme(project_data)
    
    def create_readme(self, project_data: Dict[str, Any]):
        """Creëer een README.md met overzicht"""
        readme_path = self.output_dir / "README.md"
        
        requirements = project_data.get('requirements', {})
        architecture = project_data.get('architecture', {})
        
        content = f"""# {requirements.get('project_name', 'ICT Project')}

## Project Overzicht

**Type:** {requirements.get('project_type', 'N/A')}  
**Complexiteit:** {requirements.get('complexity_level', 'N/A')}  
**Primair Doel:** {requirements.get('primary_goal', 'N/A')}

## Doelgroep
{chr(10).join(f'- {user}' for user in requirements.get('target_users', []))}

## Key Features
{chr(10).join(f'- {feature}' for feature in requirements.get('key_features', []))}

## Architectuur
**Patroon:** {architecture.get('architecture_pattern', 'N/A')}

### Technology Stack
- **Frontend:** {architecture.get('technology_stack', {}).get('frontend', {}).get('framework', 'N/A')}
- **Backend:** {architecture.get('technology_stack', {}).get('backend', {}).get('framework', 'N/A')}
- **Database:** {architecture.get('technology_stack', {}).get('database', {}).get('specific', 'N/A')}

## Documentatie Structuur

```
project_docs/
├── requirements/     # Project requirements en analyse
├── architecture/     # Architectuur ontwerp
├── api/             # API specificaties
├── workflows/       # User flows en business processes
├── database/        # Database schema en modellen
├── classes/         # Class diagrammen en structuur
├── files/           # Bestandsstructuur
└── PROJECT_OVERVIEW.json  # Complete overzicht
```

## Volgende Stappen

1. Review de gegenereerde documentatie in elke map
2. Pas aan waar nodig voor jouw specifieke use case
3. Gebruik deze documentatie als input voor development agents
4. Start met de implementatie

---
*Gegenereerd door Project Builder Agent met Claude CLI*
"""
        
        with open(readme_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"  ✅ {readme_path}")
    
    def build_project(self, project_description: str):
        """Hoofdfunctie: bouw het complete project plan"""
        print("🚀 Start Project Builder Agent")
        print("=" * 60)
        
        # Verzamel alle data
        project_data = {}
        
        # Fase 1: Requirements
        project_data['requirements'] = self.analyze_project_requirements(project_description)
        
        # Fase 2: Architectuur
        project_data['architecture'] = self.design_architecture(project_data['requirements'])
        
        # Fase 3: API
        project_data['api_structure'] = self.define_api_structure(
            project_data['requirements'], 
            project_data['architecture']
        )
        
        # Fase 4: Workflows
        project_data['workflows'] = self.define_workflows(
            project_data['requirements'],
            project_data['api_structure']
        )
        
        # Fase 5: Data Models
        project_data['data_models'] = self.define_data_models(
            project_data['requirements'],
            project_data['api_structure'],
            project_data['workflows']
        )
        
        # Fase 6: Classes
        project_data['classes'] = self.define_classes_structure(
            project_data['requirements'],
            project_data['architecture'],
            project_data['data_models']
        )
        
        # Fase 7: File Structure
        project_data['file_structure'] = self.define_file_structure(
            project_data['requirements'],
            project_data['architecture'],
            project_data['classes']
        )
        
        # Sla alles op
        self.save_to_files(project_data)
        
        print("\n" + "=" * 60)
        print("✨ Project documentatie succesvol gegenereerd!")
        print(f"📂 Locatie: {self.output_dir.absolute()}")
        print("\nJe kunt nu de JSON bestanden gebruiken als input voor je development agent.")


def main():
    """Main entry point"""
    print("""
╔════════════════════════════════════════════════════════════╗
║        ICT PROJECT BUILDER AGENT                           ║
║        Powered by Claude CLI                               ║
╚════════════════════════════════════════════════════════════╝
    """)
    
    # Check of er een argument is meegegeven
    if len(sys.argv) > 1:
        # Gebruik command line argument
        project_description = " ".join(sys.argv[1:])
    else:
        # Vraag om input
        print("Beschrijf je ICT project (druk op Ctrl+D of Ctrl+Z om te eindigen):")
        print("-" * 60)
        project_description = sys.stdin.read().strip()
    
    if not project_description:
        print("❌ Geen projectbeschrijving opgegeven.")
        sys.exit(1)
    
    # Maak agent en start proces
    agent = ProjectBuilderAgent(output_dir="./project_docs")
    agent.build_project(project_description)


if __name__ == "__main__":
    main()
