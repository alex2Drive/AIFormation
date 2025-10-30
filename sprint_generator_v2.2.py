#!/usr/bin/env python3
"""
Deterministic Sprint Generator v2.1 met Status Tracking
Genereert development sprints DIRECT uit ICT Project Builder Agent JSON output
Versie: 2.1 (met task status tracking)
"""

import json
import sys
from pathlib import Path
from typing import Dict, Any, List, Set, Tuple
from datetime import datetime, timedelta


class TaskValidator:
    """Valideert dat taken kloppen met project documentatie"""
    
    def __init__(self, project_data: Dict[str, Any], project_docs_dir: Path):
        self.project_data = project_data
        self.project_docs_dir = project_docs_dir
        
        # Bouw indexen van beschikbare specs
        self.available_files = self._index_available_files()
        self.available_classes = self._index_available_classes()
        self.available_endpoints = self._index_available_endpoints()
        self.tech_stack = self._extract_tech_stack()
        
        print(f"📊 Validator geïnitialiseerd:")
        print(f"   - {len(self.available_files)} bestanden/folders geïndexeerd")
        print(f"   - {len(self.available_classes)} classes geïndexeerd")
        print(f"   - {len(self.available_endpoints)} endpoints geïndexeerd")
    
    def _index_available_files(self) -> Set[str]:
        """Index alle bestanden uit file_structure.json"""
        files = set()
        file_structure = self.project_data.get('file_structure', {})
        
        def walk_structure(items, parent_path=""):
            for item in items:
                path = parent_path + item.get('path', '')
                if item.get('type') == 'directory':
                    files.add(path)
                    if 'children' in item:
                        walk_structure(item['children'], path)
                    for file_info in item.get('files', []):
                        files.add(path + file_info['name'])
        
        walk_structure(file_structure.get('structure', []))
        
        for config in file_structure.get('config_files', []):
            files.add(config['name'])
        
        return files
    
    def _index_available_classes(self) -> Dict[str, Dict]:
        """Index alle classes uit classes.json"""
        classes = {}
        for cls in self.project_data.get('classes', {}).get('classes', []):
            classes[cls['name']] = cls
        return classes
    
    def _index_available_endpoints(self) -> List[Dict]:
        """Index alle endpoints uit api_structure.json"""
        return self.project_data.get('api_structure', {}).get('endpoints', [])
    
    def _extract_tech_stack(self) -> Dict[str, Any]:
        """Extraheer tech stack uit architecture.json"""
        return self.project_data.get('architecture', {}).get('technology_stack', {})
    
    def validate_task(self, task: Dict[str, Any]) -> Tuple[bool, List[str], List[str]]:
        """Valideer één taak tegen project specs"""
        errors = []
        warnings = []
        
        doc_errors = self._validate_allowed_docs(task)
        errors.extend(doc_errors)
        
        deliverable_warnings = self._validate_deliverables(task)
        warnings.extend(deliverable_warnings)
        
        constraint_errors = self._validate_constraints(task)
        errors.extend(constraint_errors)
        
        tech_warnings = self._validate_tech_mentions(task)
        warnings.extend(tech_warnings)
        
        dep_errors = self._validate_dependencies(task)
        errors.extend(dep_errors)
        
        return len(errors) == 0, errors, warnings
    
    def _validate_allowed_docs(self, task: Dict) -> List[str]:
        errors = []
        for doc in task.get('allowed_docs', []):
            doc_path = self.project_docs_dir / doc
            if not doc_path.exists():
                errors.append(f"allowed_doc '{doc}' bestaat niet")
            elif doc_path.stat().st_size < 10:
                errors.append(f"allowed_doc '{doc}' is (bijna) leeg")
        return errors
    
    def _validate_deliverables(self, task: Dict) -> List[str]:
        warnings = []
        for deliverable in task.get('deliverables', []):
            if any(keyword in deliverable.lower() for keyword in ['file', 'folder', 'directory', '.py', '.js', '.json', '.md']):
                if not self._deliverable_mentions_known_file(deliverable):
                    warnings.append(f"deliverable '{deliverable}' vermeldt mogelijk bestanden niet in specs")
        return warnings
    
    def _validate_constraints(self, task: Dict) -> List[str]:
        errors = []
        constraints = task.get('strict_constraints', {})
        for key, value in constraints.items():
            if 'use_' in key and isinstance(value, str):
                if not self._tech_or_pattern_exists(value):
                    errors.append(f"constraint '{key}={value}' verwijst naar tech/patroon niet in specs")
        return errors
    
    def _validate_tech_mentions(self, task: Dict) -> List[str]:
        warnings = []
        text = f"{task.get('title', '')} {task.get('description', '')}"
        known_tech = {'react', 'vue', 'angular', 'svelte', 'express', 'fastapi', 'django', 'flask',
                      'postgresql', 'mongodb', 'mysql', 'redis', 'jwt', 'oauth', 'graphql', 'rest'}
        
        mentioned_tech = set()
        for tech in known_tech:
            if tech in text.lower():
                mentioned_tech.add(tech)
        
        for tech in mentioned_tech:
            if not self._tech_exists_in_stack(tech):
                warnings.append(f"taak vermeldt '{tech}' maar dit staat niet expliciet in architecture.json")
        return warnings
    
    def _validate_dependencies(self, task: Dict) -> List[str]:
        errors = []
        for dep in task.get('dependencies', []):
            if not isinstance(dep, str):
                errors.append(f"dependency '{dep}' is geen string")
            elif dep and not dep.startswith('S'):
                errors.append(f"dependency '{dep}' heeft invalide formaat (verwacht S##-T###)")
        return errors
    
    def _deliverable_mentions_known_file(self, deliverable: str) -> bool:
        deliverable_lower = deliverable.lower()
        for known_file in self.available_files:
            if known_file.lower() in deliverable_lower:
                return True
        return False
    
    def _tech_exists_in_stack(self, tech: str) -> bool:
        tech_lower = tech.lower()
        stack_str = json.dumps(self.tech_stack).lower()
        return tech_lower in stack_str
    
    def _tech_or_pattern_exists(self, item: str) -> bool:
        item_lower = item.lower()
        all_specs = json.dumps(self.project_data).lower()
        return item_lower in all_specs


class SpecToTaskMapper:
    """Mapt project specs DIRECT naar taken"""
    
    def __init__(self, project_data: Dict[str, Any]):
        self.project_data = project_data
    
    def generate_setup_tasks(self) -> List[Dict[str, Any]]:
        """Genereer setup taken DIRECT uit specs"""
        tasks = []
        
        if self.project_data.get('file_structure'):
            tasks.append(self._create_file_structure_task())
        
        if self.project_data.get('architecture', {}).get('technology_stack'):
            tasks.append(self._create_dependencies_task())
        
        if self._has_database_requirement():
            tasks.append(self._create_database_setup_task())
        
        tasks.append(self._create_environment_task())
        
        return tasks
    
    def _create_file_structure_task(self) -> Dict[str, Any]:
        file_structure = self.project_data['file_structure']
        num_directories = self._count_directories(file_structure)
        num_config_files = len(file_structure.get('config_files', []))
        
        return {
            "title": "Create Project File Structure",
            "description": f"Create the complete folder and file structure as specified in file_structure.json. This includes {num_directories} directories and {num_config_files} configuration files.",
            "type": "setup",
            "assigned_to": "backend",
            "priority": "critical",
            "estimated_hours": self._estimate_hours_for_structure(num_directories, num_config_files),
            "dependencies": [],
            "can_run_parallel": False,
            "allowed_docs": [
                "files/file_structure.json"
            ],
            "strict_constraints": {
                "must_match_structure_exactly": True,
                "no_additional_folders": True,
                "no_missing_folders": True,
                "verify_against_spec": "files/file_structure.json"
            },
            "deliverables": self._extract_deliverables_from_structure(file_structure),
            "validation_checklist": self._create_validation_for_structure(file_structure),
            "execution_guide": [
                "1. Open and read files/file_structure.json completely",
                "2. Create each directory in the 'structure' array in order",
                "3. For each directory, create any nested 'children' directories",
                "4. Create all files listed in 'config_files' array",
                "5. Create README.md in project root if specified",
                "6. Verify: Walk through file_structure.json and check each item exists",
                "7. Verify: No extra folders or files were created",
                "8. Update task status to 'completed' when done"
            ],
            "status": "pending",
            "status_notes": "",
            "completed_at": None
        }
    
    def _create_dependencies_task(self) -> Dict[str, Any]:
        tech_stack = self.project_data['architecture']['technology_stack']
        backend = tech_stack.get('backend', {})
        frontend = tech_stack.get('frontend', {})
        database = tech_stack.get('database', {})
        
        parts = []
        if backend.get('framework'):
            parts.append(f"backend ({backend['framework']})")
        if frontend.get('framework'):
            parts.append(f"frontend ({frontend['framework']})")
        if database.get('specific'):
            parts.append(f"database ({database['specific']})")
        
        description = f"Install and configure all dependencies for: {', '.join(parts)}. Use EXACT tech stack specified in architecture.json."
        
        backend_lang = backend.get('language', '').lower()
        if 'python' in backend_lang:
            dep_file = "requirements.txt"
            assigned_to = "backend"
        elif frontend.get('framework'):
            dep_file = "package.json"
            assigned_to = "frontend"
        else:
            dep_file = "dependency configuration file"
            assigned_to = "backend"
        
        return {
            "title": "Install Project Dependencies",
            "description": description,
            "type": "setup",
            "assigned_to": assigned_to,
            "priority": "critical",
            "estimated_hours": 2,
            "dependencies": [],
            "can_run_parallel": False,
            "allowed_docs": [
                "architecture/architecture.json",
                "files/file_structure.json"
            ],
            "strict_constraints": {
                "use_exact_tech_stack": True,
                "no_substitutions": True,
                "backend_framework": backend.get('framework'),
                "frontend_framework": frontend.get('framework') if frontend else None,
                "database_type": database.get('specific') if database else None
            },
            "deliverables": [
                f"{dep_file} created with all dependencies",
                "Lock file generated (if applicable)",
                "All dependencies successfully installed",
                "Dependency versions match architecture.json"
            ],
            "validation_checklist": [
                f"{dep_file} exists in project root",
                "All tech from architecture.json is listed",
                "No additional dependencies added",
                "Installation runs without errors"
            ],
            "execution_guide": [
                "1. Read architecture/architecture.json completely",
                "2. Extract technology_stack section",
                "3. Identify all required dependencies",
                f"4. Create {dep_file} with exact versions",
                "5. Run installation command",
                "6. Verify all dependencies installed successfully",
                "7. Update task status to 'completed' when done"
            ],
            "status": "pending",
            "status_notes": "",
            "completed_at": None
        }
    
    def _create_database_setup_task(self) -> Dict[str, Any]:
        architecture = self.project_data['architecture']
        database = architecture['technology_stack']['database']
        
        return {
            "title": f"Setup {database['specific']} Database",
            "description": f"Initialize {database['specific']} database connection and schema as specified in architecture.json and data_models.json.",
            "type": "setup",
            "assigned_to": "backend",
            "priority": "high",
            "estimated_hours": 3,
            "dependencies": [],
            "can_run_parallel": False,
            "allowed_docs": [
                "architecture/architecture.json",
                "database/data_models.json"
            ],
            "strict_constraints": {
                "use_specified_database": database['specific'],
                "database_type": database['type'],
                "follow_data_models": True
            },
            "deliverables": [
                f"{database['specific']} connection configured",
                "Database connection module created",
                "Connection pooling setup",
                "Schema matches data_models.json"
            ],
            "validation_checklist": [
                f"Can connect to {database['specific']}",
                "Connection settings in configuration",
                "Connection pooling works",
                "Database schema matches data_models.json"
            ],
            "execution_guide": [
                "1. Read architecture/architecture.json for database configuration",
                "2. Read database/data_models.json for schema specifications",
                "3. Create database connection module",
                "4. Configure connection pooling",
                "5. Test database connection",
                "6. Create initial schema if needed",
                "7. Update task status to 'completed' when done"
            ],
            "status": "pending",
            "status_notes": "",
            "completed_at": None
        }
    
    def _create_environment_task(self) -> Dict[str, Any]:
        architecture = self.project_data.get('architecture', {})
        env_vars = []
        
        if self._has_database_requirement():
            env_vars.extend(["DATABASE_URL", "DATABASE_NAME"])
        
        # Alleen auth vars toevoegen als project een API heeft
        api_structure = self.project_data.get('api_structure', {})
        needs_api = api_structure.get('needs_api', True)
        
        if needs_api and api_structure.get('authentication'):
            auth_type = api_structure['authentication'].get('type', 'JWT')
            if 'JWT' in auth_type.upper():
                env_vars.extend(["JWT_SECRET_KEY", "JWT_ALGORITHM"])
        
        requirements = self.project_data.get('requirements', {})
        external_apis = requirements.get('technical_requirements', {}).get('external_apis', [])
        for api in external_apis[:3]:
            env_vars.append(f"{api.upper().replace(' ', '_')}_API_KEY")
        
        description = "Setup environment configuration with all required variables based on project architecture."
        if not needs_api:
            description += " Note: This project uses server-side rendering without API endpoints."
        
        return {
            "title": "Configure Environment Variables",
            "description": description,
            "type": "setup",
            "assigned_to": "backend",
            "priority": "high",
            "estimated_hours": 2,
            "dependencies": [],
            "can_run_parallel": True,
            "allowed_docs": [
                "architecture/architecture.json",
                "api/api_structure.json",
                "requirements/requirements.json"
            ],
            "strict_constraints": {
                "include_all_required_vars": True,
                "no_hardcoded_secrets": True
            },
            "deliverables": [
                ".env.example file with all required variables",
                "README section explaining environment setup",
                "Config loader implementation"
            ],
            "validation_checklist": [
                ".env.example exists in project root",
                "Contains all required variables",
                "No actual secrets in .env.example",
                "README explains environment setup"
            ],
            "execution_guide": [
                "1. Read architecture/architecture.json for tech stack",
                "2. Read api/api_structure.json for authentication requirements (if applicable)",
                "3. Read requirements/requirements.json for external APIs",
                "4. List all required environment variables",
                "5. Create .env.example with placeholder values",
                "6. Add environment variables section to README",
                "7. Create config loader module",
                "8. Update task status to 'completed' when done"
            ],
            "status": "pending",
            "status_notes": "",
            "completed_at": None
        }
    
    def generate_backend_tasks(self) -> List[Dict[str, Any]]:
        """Genereer backend taken uit classes.json + api_structure.json (indien van toepassing)"""
        tasks = []
        
        classes = self.project_data.get('classes', {}).get('classes', [])
        backend_classes = [c for c in classes if self._is_backend_class(c)]
        
        for cls in backend_classes:
            tasks.append(self._create_class_implementation_task(cls))
        
        # Check of project daadwerkelijk API endpoints nodig heeft
        api_structure = self.project_data.get('api_structure', {})
        needs_api = api_structure.get('needs_api', True)  # Default true voor backwards compatibility
        
        if needs_api and api_structure.get('endpoints'):
            endpoints = api_structure['endpoints']
            resources = self._group_endpoints_by_resource(endpoints)
            for resource_name, resource_endpoints in resources.items():
                tasks.append(self._create_api_resource_task(resource_name, resource_endpoints))
        elif not needs_api:
            print("  ℹ️  Geen API endpoints gegenereerd (project gebruikt server-side rendering)")
        
        return tasks
    
    def _is_backend_class(self, cls: Dict) -> bool:
        name = cls.get('name', '').lower()
        layer = cls.get('layer', '').lower()
        
        if any(keyword in layer for keyword in ['backend', 'service', 'model', 'repository', 'controller']):
            return True
        
        if any(keyword in name for keyword in ['service', 'model', 'repository', 'controller', 'handler']):
            return True
        
        return False
    
    def _group_endpoints_by_resource(self, endpoints: List[Dict]) -> Dict[str, List[Dict]]:
        resources = {}
        for endpoint in endpoints:
            path = endpoint.get('path', '')
            parts = [p for p in path.split('/') if p and p != 'api' and p != 'v1']
            resource = parts[0] if parts else 'root'
            
            if resource not in resources:
                resources[resource] = []
            resources[resource].append(endpoint)
        
        return resources
    
    def _create_class_implementation_task(self, cls: Dict) -> Dict[str, Any]:
        methods = cls.get('methods', [])
        dependencies = cls.get('dependencies', [])
        
        return {
            "title": f"Implement {cls['name']} Class",
            "description": f"{cls.get('purpose', 'Implementation of ' + cls['name'])}. This class has {len(methods)} methods.",
            "type": "backend",
            "assigned_to": "backend",
            "priority": "high",
            "estimated_hours": 2 + len(methods),
            "dependencies": [],
            "can_run_parallel": len(dependencies) == 0,
            "allowed_docs": [
                "classes/classes.json",
                "database/data_models.json",
                "files/file_structure.json"
            ],
            "strict_constraints": {
                "implement_exact_class": cls['name'],
                "implement_all_methods": [m['name'] for m in methods],
                "respect_dependencies": dependencies,
                "layer": cls.get('layer', 'unknown')
            },
            "deliverables": [
                f"Class {cls['name']} implemented",
                f"All {len(methods)} methods implemented",
                "Unit tests for all methods",
                "Documentation for class and methods"
            ],
            "validation_checklist": [
                f"File containing {cls['name']} exists in correct location",
                f"Class {cls['name']} is defined",
                "All methods from classes.json are implemented",
                "Class follows architecture pattern",
                "Unit tests pass"
            ],
            "execution_guide": [
                "1. Read classes/classes.json and locate specification for " + cls['name'],
                "2. Read files/file_structure.json to find correct file location",
                "3. Create class file in specified location",
                f"4. Implement class {cls['name']} with all methods",
                "5. Add type hints and documentation",
                "6. Create unit tests",
                "7. Verify all methods from spec are implemented",
                "8. Update task status to 'completed' when done"
            ],
            "status": "pending",
            "status_notes": "",
            "completed_at": None
        }
    
    def _create_api_resource_task(self, resource_name: str, endpoints: List[Dict]) -> Dict[str, Any]:
        has_auth = any(endpoint.get('requires_auth', False) for endpoint in endpoints)
        methods = [endpoint['method'] for endpoint in endpoints]
        
        return {
            "title": f"Implement /{resource_name} API Endpoints",
            "description": f"Implement all {len(endpoints)} endpoints for the /{resource_name} resource. Methods: {', '.join(set(methods))}.",
            "type": "backend",
            "assigned_to": "backend",
            "priority": "high",
            "estimated_hours": len(endpoints) * 2,
            "dependencies": [],
            "can_run_parallel": True,
            "allowed_docs": [
                "api/api_structure.json",
                "classes/classes.json",
                "workflows/workflows.json"
            ],
            "strict_constraints": {
                "implement_exact_paths": [e['path'] for e in endpoints],
                "use_exact_methods": methods,
                "implement_auth": has_auth,
                "follow_request_format": True,
                "follow_response_format": True
            },
            "deliverables": [
                f"All {len(endpoints)} endpoints for /{resource_name} implemented",
                "Request validation for all endpoints",
                "Response formatting for all endpoints",
                "Error handling per endpoint"
            ],
            "validation_checklist": [
                f"All {len(endpoints)} endpoints are implemented",
                "Each endpoint responds to correct HTTP method",
                "Authentication enforced where requires_auth is true",
                "Request bodies match api_structure.json",
                "Response bodies match api_structure.json"
            ],
            "execution_guide": [
                "1. Read api/api_structure.json completely",
                f"2. Find all endpoints for /{resource_name} resource",
                "3. For each endpoint: create route handler, implement validation, add auth if needed",
                "4. Test all endpoints",
                "5. Verify each endpoint against api_structure.json",
                "6. Update task status to 'completed' when done"
            ],
            "status": "pending",
            "status_notes": "",
            "completed_at": None
        }
    
    def generate_frontend_tasks(self) -> List[Dict[str, Any]]:
        """Genereer frontend taken uit workflows + api_structure"""
        tasks = []
        
        workflows = self.project_data.get('workflows', {}).get('user_workflows', [])
        
        tasks.append(self._create_component_structure_task())
        
        if self.project_data.get('api_structure', {}).get('endpoints'):
            tasks.append(self._create_api_client_task())
        
        for i, workflow in enumerate(workflows[:3], 1):
            tasks.append(self._create_workflow_implementation_task(workflow, i))
        
        return tasks
    
    def _create_component_structure_task(self) -> Dict[str, Any]:
        architecture = self.project_data.get('architecture', {})
        frontend = architecture.get('technology_stack', {}).get('frontend', {})
        framework = frontend.get('framework', 'the framework')
        
        return {
            "title": "Setup Frontend Component Structure",
            "description": f"Create the base component architecture for {framework}.",
            "type": "frontend",
            "assigned_to": "frontend",
            "priority": "critical",
            "estimated_hours": 4,
            "dependencies": [],
            "can_run_parallel": False,
            "allowed_docs": [
                "architecture/architecture.json",
                "files/file_structure.json"
            ],
            "strict_constraints": {
                "use_specified_framework": framework,
                "follow_file_structure": True
            },
            "deliverables": [
                "Component folder structure created",
                "Base layout components",
                "Routing setup",
                f"{framework} configuration complete"
            ],
            "validation_checklist": [
                "Component directories match file_structure.json",
                f"{framework} is properly configured",
                "Routing works",
                "Base components render"
            ],
            "execution_guide": [
                "1. Read architecture/architecture.json for frontend.framework",
                "2. Read files/file_structure.json for component structure",
                "3. Create component directories as specified",
                "4. Setup routing system",
                "5. Create base layout components",
                "6. Test that components render",
                "7. Update task status to 'completed' when done"
            ],
            "status": "pending",
            "status_notes": "",
            "completed_at": None
        }
    
    def _create_api_client_task(self) -> Dict[str, Any]:
        endpoints = self.project_data.get('api_structure', {}).get('endpoints', [])
        
        return {
            "title": "Implement API Client",
            "description": f"Create API client for backend communication with methods for all {len(endpoints)} endpoints.",
            "type": "frontend",
            "assigned_to": "frontend",
            "priority": "critical",
            "estimated_hours": 5,
            "dependencies": [],
            "can_run_parallel": False,
            "allowed_docs": [
                "api/api_structure.json",
                "architecture/architecture.json"
            ],
            "strict_constraints": {
                "implement_all_endpoints": True,
                "use_exact_paths": True,
                "handle_auth_headers": True,
                "follow_error_format": True
            },
            "deliverables": [
                "API client service created",
                f"Methods for all {len(endpoints)} endpoints",
                "Request/response interceptors",
                "Error handling",
                "Authentication header handling"
            ],
            "validation_checklist": [
                "All API endpoints have corresponding client methods",
                "Authentication headers included where needed",
                "Error responses handled correctly",
                "Base URL matches api_structure.json"
            ],
            "execution_guide": [
                "1. Read api/api_structure.json completely",
                "2. Extract base_url and authentication type",
                "3. Create API client class/service",
                "4. For each endpoint: create method with correct HTTP method",
                "5. Add request/response interceptors",
                "6. Add error handling",
                "7. Test API client methods",
                "8. Update task status to 'completed' when done"
            ],
            "status": "pending",
            "status_notes": "",
            "completed_at": None
        }
    
    def _create_workflow_implementation_task(self, workflow: Dict, index: int) -> Dict[str, Any]:
        workflow_name = workflow.get('workflow_name', f'Workflow {index}')
        steps = workflow.get('steps', [])
        
        return {
            "title": f"Implement User Workflow: {workflow_name}",
            "description": f"Implement the complete user workflow for {workflow_name} with {len(steps)} steps.",
            "type": "frontend",
            "assigned_to": "frontend",
            "priority": "high",
            "estimated_hours": 4 + len(steps),
            "dependencies": [],
            "can_run_parallel": True,
            "allowed_docs": [
                "workflows/workflows.json",
                "api/api_structure.json",
                "architecture/architecture.json"
            ],
            "strict_constraints": {
                "implement_all_steps": True,
                "follow_step_order": True,
                "use_specified_api_calls": True
            },
            "deliverables": [
                f"UI components for {workflow_name}",
                f"All {len(steps)} workflow steps implemented",
                "Form validation",
                "Error handling per step"
            ],
            "validation_checklist": [
                f"All {len(steps)} steps are implemented",
                "User can complete workflow start to finish",
                "API calls match workflow specification",
                "Error scenarios are handled"
            ],
            "execution_guide": [
                f"1. Read workflows/workflows.json and find '{workflow_name}'",
                "2. For each step: create UI component, implement validation, add API calls",
                "3. Connect steps in correct order",
                "4. Test complete workflow",
                "5. Verify against workflow specification",
                "6. Update task status to 'completed' when done"
            ],
            "status": "pending",
            "status_notes": "",
            "completed_at": None
        }
    
    def generate_integration_tasks(self) -> List[Dict[str, Any]]:
        """Genereer integratie en test taken"""
        tasks = []
        
        tasks.append({
            "title": "End-to-End API Integration Testing",
            "description": "Test all API endpoints and workflows in integrated environment.",
            "type": "testing",
            "assigned_to": "backend",
            "priority": "high",
            "estimated_hours": 8,
            "dependencies": [],
            "can_run_parallel": False,
            "allowed_docs": [
                "api/api_structure.json",
                "workflows/workflows.json"
            ],
            "strict_constraints": {
                "test_all_endpoints": True,
                "test_all_workflows": True
            },
            "deliverables": [
                "E2E test suite",
                "All endpoints tested",
                "All workflows tested",
                "Test report"
            ],
            "validation_checklist": [
                "All API endpoints have tests",
                "All workflows have tests",
                "Tests pass",
                "Coverage report generated"
            ],
            "execution_guide": [
                "1. Read api/api_structure.json for all endpoints",
                "2. Read workflows/workflows.json for all workflows",
                "3. Create E2E test for each endpoint",
                "4. Create E2E test for each workflow",
                "5. Run all tests",
                "6. Generate coverage report",
                "7. Update task status to 'completed' when done"
            ],
            "status": "pending",
            "status_notes": "",
            "completed_at": None
        })
        
        return tasks
    
    # Helper methods
    def _has_database_requirement(self) -> bool:
        requirements = self.project_data.get('requirements', {})
        tech_reqs = requirements.get('technical_requirements', {})
        return bool(tech_reqs.get('database'))
    
    def _count_directories(self, file_structure: Dict) -> int:
        count = 0
        def walk(items):
            nonlocal count
            for item in items:
                if item.get('type') == 'directory':
                    count += 1
                    if 'children' in item:
                        walk(item['children'])
        walk(file_structure.get('structure', []))
        return count
    
    def _estimate_hours_for_structure(self, num_dirs: int, num_configs: int) -> int:
        hours = 2 + (num_dirs // 5) * 0.5 + (num_configs // 2) * 0.5
        return max(2, min(int(hours), 8))
    
    def _extract_deliverables_from_structure(self, file_structure: Dict) -> List[str]:
        deliverables = []
        main_dirs = [item['path'] for item in file_structure.get('structure', [])[:5] if item.get('type') == 'directory']
        if main_dirs:
            deliverables.append(f"Top-level directories: {', '.join(main_dirs[:3])}{'...' if len(main_dirs) > 3 else ''}")
        
        configs = [cf['name'] for cf in file_structure.get('config_files', [])]
        if configs:
            deliverables.append(f"Configuration files: {', '.join(configs)}")
        
        deliverables.append("Complete structure matches file_structure.json exactly")
        return deliverables
    
    def _create_validation_for_structure(self, file_structure: Dict) -> List[str]:
        checklist = []
        for item in file_structure.get('structure', [])[:5]:
            if item.get('type') == 'directory':
                checklist.append(f"Directory '{item['path']}' exists")
        
        for config in file_structure.get('config_files', []):
            checklist.append(f"File '{config['name']}' exists")
        
        checklist.append("No extra directories or files created")
        checklist.append("Structure matches file_structure.json exactly")
        return checklist


class SprintGenerator:
    """Deterministic Sprint Generator met Status Tracking"""
    
    def __init__(self, project_docs_dir: str = "./project_docs", output_dir: str = "./sprints"):
        self.project_docs_dir = Path(project_docs_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        self.project_data = self.load_project_data()
        self.validator = TaskValidator(self.project_data, self.project_docs_dir)
        self.spec_mapper = SpecToTaskMapper(self.project_data)
    
    def load_project_data(self) -> Dict[str, Any]:
        print("📂 Laden van project documentatie...")
        
        data = {}
        files_to_load = {
            'requirements': 'requirements/requirements.json',
            'architecture': 'architecture/architecture.json',
            'api_structure': 'api/api_structure.json',
            'workflows': 'workflows/workflows.json',
            'data_models': 'database/data_models.json',
            'classes': 'classes/classes.json',
            'file_structure': 'files/file_structure.json'
        }
        
        for key, filepath in files_to_load.items():
            full_path = self.project_docs_dir / filepath
            if full_path.exists():
                with open(full_path, 'r', encoding='utf-8') as f:
                    data[key] = json.load(f)
                print(f"  ✅ {filepath}")
            else:
                print(f"  ⚠️  {filepath} niet gevonden")
                data[key] = {}
        
        return data
    
    def generate_task_id(self, sprint_number: int, task_index: int) -> str:
        return f"S{sprint_number:02d}-T{task_index:03d}"
    
    def generate_sprints(self, sprint_duration_days: int = 14) -> List[Dict[str, Any]]:
        print("\n🏗️  Genereren van sprints (deterministisch met status tracking)...")
        
        sprints = []
        sprints.append(self.create_setup_sprint(1, sprint_duration_days))
        
        if self._has_backend():
            sprints.append(self.create_backend_sprint(2, sprint_duration_days))
        
        if self._has_frontend():
            sprint_num = len(sprints) + 1
            sprints.append(self.create_frontend_sprint(sprint_num, sprint_duration_days))
        
        if len(sprints) >= 2:
            sprint_num = len(sprints) + 1
            sprints.append(self.create_integration_sprint(sprint_num, sprint_duration_days))
        
        return sprints
    
    def create_setup_sprint(self, sprint_number: int, duration_days: int) -> Dict[str, Any]:
        print(f"\n  📋 Sprint {sprint_number}: Setup & Infrastructure")
        
        tasks = self.spec_mapper.generate_setup_tasks()
        
        for i, task in enumerate(tasks, 1):
            task['task_id'] = self.generate_task_id(sprint_number, i)
        
        self._update_task_dependencies(tasks, sprint_number)
        self._validate_and_report_tasks(tasks, sprint_number)
        
        sprint = {
            "sprint_number": sprint_number,
            "sprint_name": "Setup & Infrastructure",
            "duration_days": duration_days,
            "start_date": datetime.now().isoformat(),
            "end_date": (datetime.now() + timedelta(days=duration_days)).isoformat(),
            "goal": "Complete project setup and development environment",
            "tasks": tasks,
            "parallel_groups": self.identify_parallel_tasks(tasks),
            "total_estimated_hours": sum(t['estimated_hours'] for t in tasks),
            "status": "not_started"
        }
        
        print(f"     ✅ {len(tasks)} taken gegenereerd ({sprint['total_estimated_hours']} uur)")
        return sprint
    
    def create_backend_sprint(self, sprint_number: int, duration_days: int) -> Dict[str, Any]:
        print(f"\n  📋 Sprint {sprint_number}: Backend Core Development")
        
        tasks = self.spec_mapper.generate_backend_tasks()
        
        for i, task in enumerate(tasks, 1):
            task['task_id'] = self.generate_task_id(sprint_number, i)
            if not task.get('dependencies'):
                task['dependencies'] = []
            task['dependencies'].insert(0, f"S{sprint_number-1:02d}-T001")
        
        self._validate_and_report_tasks(tasks, sprint_number)
        
        sprint = {
            "sprint_number": sprint_number,
            "sprint_name": "Backend Core Development",
            "duration_days": duration_days,
            "start_date": (datetime.now() + timedelta(days=(sprint_number-1)*duration_days)).isoformat(),
            "end_date": (datetime.now() + timedelta(days=sprint_number*duration_days)).isoformat(),
            "goal": "Implement core backend functionality from classes.json and api_structure.json",
            "tasks": tasks,
            "parallel_groups": self.identify_parallel_tasks(tasks),
            "total_estimated_hours": sum(t['estimated_hours'] for t in tasks),
            "status": "not_started"
        }
        
        print(f"     ✅ {len(tasks)} taken gegenereerd ({sprint['total_estimated_hours']} uur)")
        return sprint
    
    def create_frontend_sprint(self, sprint_number: int, duration_days: int) -> Dict[str, Any]:
        print(f"\n  📋 Sprint {sprint_number}: Frontend Development")
        
        tasks = self.spec_mapper.generate_frontend_tasks()
        
        for i, task in enumerate(tasks, 1):
            task['task_id'] = self.generate_task_id(sprint_number, i)
            if not task.get('dependencies'):
                task['dependencies'] = []
            task['dependencies'].insert(0, f"S01-T001")
        
        self._validate_and_report_tasks(tasks, sprint_number)
        
        sprint = {
            "sprint_number": sprint_number,
            "sprint_name": "Frontend Development",
            "duration_days": duration_days,
            "start_date": (datetime.now() + timedelta(days=(sprint_number-1)*duration_days)).isoformat(),
            "end_date": (datetime.now() + timedelta(days=sprint_number*duration_days)).isoformat(),
            "goal": "Implement frontend UI and user workflows",
            "tasks": tasks,
            "parallel_groups": self.identify_parallel_tasks(tasks),
            "total_estimated_hours": sum(t['estimated_hours'] for t in tasks),
            "status": "not_started"
        }
        
        print(f"     ✅ {len(tasks)} taken gegenereerd ({sprint['total_estimated_hours']} uur)")
        return sprint
    
    def create_integration_sprint(self, sprint_number: int, duration_days: int) -> Dict[str, Any]:
        print(f"\n  📋 Sprint {sprint_number}: Integration & Testing")
        
        tasks = self.spec_mapper.generate_integration_tasks()
        
        for i, task in enumerate(tasks, 1):
            task['task_id'] = self.generate_task_id(sprint_number, i)
            if not task.get('dependencies'):
                task['dependencies'] = []
            task['dependencies'].extend([f"S{sprint_number-2:02d}-T001", f"S{sprint_number-1:02d}-T001"])
        
        self._validate_and_report_tasks(tasks, sprint_number)
        
        sprint = {
            "sprint_number": sprint_number,
            "sprint_name": "Integration & Testing",
            "duration_days": duration_days,
            "start_date": (datetime.now() + timedelta(days=(sprint_number-1)*duration_days)).isoformat(),
            "end_date": (datetime.now() + timedelta(days=sprint_number*duration_days)).isoformat(),
            "goal": "Integrate all components and test complete system",
            "tasks": tasks,
            "parallel_groups": self.identify_parallel_tasks(tasks),
            "total_estimated_hours": sum(t['estimated_hours'] for t in tasks),
            "status": "not_started"
        }
        
        print(f"     ✅ {len(tasks)} taken gegenereerd ({sprint['total_estimated_hours']} uur)")
        return sprint
    
    def _update_task_dependencies(self, tasks: List[Dict], sprint_number: int):
        for task in tasks:
            if task.get('dependencies'):
                formatted_deps = []
                for dep in task['dependencies']:
                    if isinstance(dep, int):
                        formatted_deps.append(self.generate_task_id(sprint_number, dep))
                    else:
                        formatted_deps.append(dep)
                task['dependencies'] = formatted_deps
    
    def _validate_and_report_tasks(self, tasks: List[Dict], sprint_number: int):
        print(f"     🔍 Valideren van {len(tasks)} taken...")
        
        total_errors = 0
        total_warnings = 0
        
        for task in tasks:
            is_valid, errors, warnings = self.validator.validate_task(task)
            
            if errors:
                total_errors += len(errors)
                print(f"        ❌ {task['title']}: {len(errors)} errors")
            
            if warnings:
                total_warnings += len(warnings)
        
        if total_errors == 0:
            print(f"     ✅ Alle taken valid")
        else:
            print(f"     ⚠️  {total_errors} errors, {total_warnings} warnings")
    
    def identify_parallel_tasks(self, tasks: List[Dict[str, Any]]) -> List[List[str]]:
        parallel_groups = []
        parallel_tasks = [t for t in tasks if t.get('can_run_parallel', False)]
        
        if parallel_tasks:
            group = [t['task_id'] for t in parallel_tasks]
            if len(group) > 1:
                parallel_groups.append(group)
        
        return parallel_groups
    
    def _has_backend(self) -> bool:
        """Check of project backend code heeft (classes of API's)"""
        classes = self.project_data.get('classes', {}).get('classes', [])
        
        # Een project heeft backend als het classes heeft OF API endpoints nodig heeft
        api_structure = self.project_data.get('api_structure', {})
        needs_api = api_structure.get('needs_api', True)
        has_endpoints = len(api_structure.get('endpoints', [])) > 0
        
        return len(classes) > 0 or (needs_api and has_endpoints)
    
    def _has_frontend(self) -> bool:
        workflows = self.project_data.get('workflows', {}).get('user_workflows', [])
        frontend = self.project_data.get('architecture', {}).get('technology_stack', {}).get('frontend')
        return len(workflows) > 0 or frontend is not None
    
    def save_sprints(self, sprints: List[Dict[str, Any]]):
        print("\n💾 Opslaan van sprints...")
        
        for sprint in sprints:
            sprint_file = self.output_dir / f"sprint_{sprint['sprint_number']:02d}.json"
            with open(sprint_file, 'w', encoding='utf-8') as f:
                json.dump(sprint, f, indent=2, ensure_ascii=False)
            print(f"  ✅ {sprint_file.name}")
        
        overview = {
            "project_name": self.project_data.get('requirements', {}).get('project_name', 'Unknown'),
            "generated_at": datetime.now().isoformat(),
            "generator_version": "2.1-deterministic-with-status",
            "total_sprints": len(sprints),
            "total_tasks": sum(len(s['tasks']) for s in sprints),
            "total_estimated_hours": sum(s['total_estimated_hours'] for s in sprints),
            "sprints_summary": [
                {
                    "sprint_number": s['sprint_number'],
                    "sprint_name": s['sprint_name'],
                    "tasks_count": len(s['tasks']),
                    "estimated_hours": s['total_estimated_hours'],
                    "status": s['status']
                }
                for s in sprints
            ]
        }
        
        overview_file = self.output_dir / "sprints_overview.json"
        with open(overview_file, 'w', encoding='utf-8') as f:
            json.dump(overview, f, indent=2, ensure_ascii=False)
        print(f"  ✅ {overview_file.name}")
        
        self.create_agent_instructions(sprints)
    
    def create_agent_instructions(self, sprints: List[Dict[str, Any]]):
        instructions_file = self.output_dir / "AGENT_INSTRUCTIONS.md"
        
        content = f"""# Development Agent Instructies 🤖

## ⚠️ KRITIEKE REGELS

### 1. Documentatie Beperking
- Lees ALLEEN de bestanden vermeld in `allowed_docs` van je taak
- Geen andere documentatie, geen externe bronnen, geen aannames

### 2. Strict Constraints
- De `strict_constraints` zijn ABSOLUUT
- GEEN afwijkingen toegestaan

### 3. Status Tracking
- Elke taak heeft een `status` veld
- Statussen: pending → in_progress → completed → blocked
- Update ALTIJD de status na wijzigingen
- Voeg `status_notes` toe bij problemen

### 4. Deliverables & Validation
- Lever EXACT wat gevraagd wordt
- Check tegen `validation_checklist`
- Update `completed_at` timestamp bij voltooiing

## Workflow

```
1. Open: sprints/sprint_XX.json
2. Find: Je toegewezen task_id
3. Update status: "pending" → "in_progress"
4. Lees: execution_guide
5. Lees: ALLEEN de allowed_docs
6. Implementeer: volgens strict_constraints
7. Lever: alle deliverables
8. Valideer: tegen checklist
9. Update status: "in_progress" → "completed"
10. Set: completed_at timestamp
```

## Status Codes

- **pending**: Nog niet begonnen
- **in_progress**: Bezig met implementatie
- **completed**: Helemaal klaar, gevalideerd
- **blocked**: Geblokkeerd (geef reden in status_notes)

## Per Sprint Overzicht

"""
        
        for sprint in sprints:
            content += f"""
### Sprint {sprint['sprint_number']}: {sprint['sprint_name']}
**Duur:** {sprint['duration_days']} dagen  
**Taken:** {len(sprint['tasks'])}  
**Geschatte uren:** {sprint['total_estimated_hours']}

**Taken:**
"""
            for task in sprint['tasks']:
                parallel = "🔀" if task.get('can_run_parallel') else "⏩"
                assigned = task.get('assigned_to', 'any')
                content += f"- `{task['task_id']}` {parallel} [{assigned}] {task['title']} ({task['estimated_hours']}h) - Status: {task.get('status', 'pending')}\n"
            
            content += "\n"
        
        content += """
---

*Gegenereerd door Deterministic Sprint Generator v2.1 met Status Tracking*
"""
        
        with open(instructions_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"  ✅ {instructions_file.name}")


def main():
    print("""
╔═══════════════════════════════════════════════════════════╗
║      DETERMINISTIC SPRINT GENERATOR v2.1                  ║
║      Met Status Tracking voor Development Agents         ║
╚═══════════════════════════════════════════════════════════╝
    """)
    
    project_docs_dir = sys.argv[1] if len(sys.argv) > 1 else "./project_docs"
    output_dir = sys.argv[2] if len(sys.argv) > 2 else "./sprints"
    
    print(f"📂 Project docs: {project_docs_dir}")
    print(f"📁 Output dir: {output_dir}")
    
    if not Path(project_docs_dir).exists():
        print(f"\n❌ Project docs directory niet gevonden: {project_docs_dir}")
        print("\nRun eerst de Project Builder Agent om documentatie te genereren.")
        sys.exit(1)
    
    generator = SprintGenerator(project_docs_dir, output_dir)
    sprints = generator.generate_sprints(sprint_duration_days=14)
    generator.save_sprints(sprints)
    
    print("\n" + "=" * 60)
    print("✨ Sprint planning succesvol gegenereerd!")
    print(f"📂 Locatie: {Path(output_dir).absolute()}")
    print(f"\n📊 Totaal: {len(sprints)} sprints")
    print(f"⏱️  Geschat: {sum(s['total_estimated_hours'] for s in sprints)} uren")
    print(f"📅 Duur: ~{len(sprints) * 2} weken (bij 2-week sprints)")
    print("\n💡 Lees AGENT_INSTRUCTIONS.md voor development agents")
    print("\n🎯 Status tracking enabled - agents kunnen voortgang bijhouden")


if __name__ == "__main__":
    main()
