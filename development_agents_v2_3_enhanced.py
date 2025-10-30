#!/usr/bin/env python3
"""
Development Agents Orchestrator - Enhanced Version met Visibility
Bevat zowel Frontend als Backend Developer agents
Gebruikt Claude CLI om taken uit te voeren volgens sprint specificaties
Language-agnostic: werkt met elke tech stack uit architecture.json

NIEUWE FEATURES:
- Real-time Claude CLI output streaming
- Uitgebreide logging naar file
- Progress tracking
- File creation monitoring
"""

import subprocess
import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
import logging
import re


class DevelopmentAgent:
    """Base class voor development agents met enhanced visibility"""
    
    def __init__(self, agent_type: str, project_root: Path, project_docs_dir: Path, 
                 sprints_dir: Path, verbose: bool = True):
        self.agent_type = agent_type  # 'frontend' of 'backend'
        self.project_root = project_root
        self.project_docs_dir = project_docs_dir
        self.sprints_dir = sprints_dir
        self.agent_name = f"{agent_type.title()} Developer"
        self.verbose = verbose
        
        # Setup logging
        self._setup_logging()
        
        # Setup progress tracking
        self.progress_file = Path(f"./agent_progress_{agent_type}.json")
        self._init_progress_tracking()
        
        # Load project architecture om tech stack te kennen
        self.architecture = self._load_architecture()
        self.tech_stack = self.architecture.get('technology_stack', {})
        
        # Load agent profile
        self.profile = self._create_agent_profile()
        
        self.log(f"\n{'='*70}", 'info')
        self.log(f"🤖 {self.agent_name} Agent geïnitialiseerd", 'info')
        self.log(f"{'='*70}", 'info')
        self.log(f"📂 Project: {project_root}", 'info')
        self.log(f"📚 Docs: {project_docs_dir}", 'info')
        self.log(f"📋 Sprints: {sprints_dir}", 'info')
        self.log(f"📊 Progress: {self.progress_file}", 'info')
        self.log(f"📝 Log: {self.log_file}", 'info')
        self.log(f"🔧 Tech: {self._get_tech_summary()}", 'info')
        self.log(f"{'='*70}\n", 'info')
    
    def _setup_logging(self):
        """Setup comprehensive logging"""
        logs_dir = Path('./logs')
        logs_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.log_file = logs_dir / f"{self.agent_type}_agent_{timestamp}.log"
        
        self.logger = logging.getLogger(f'{self.agent_type}_agent_{timestamp}')
        self.logger.setLevel(logging.DEBUG)
        self.logger.handlers = []  # Clear any existing handlers
        
        # File handler - everything
        fh = logging.FileHandler(self.log_file, encoding='utf-8')
        fh.setLevel(logging.DEBUG)
        fh.setFormatter(logging.Formatter(
            '%(asctime)s [%(levelname)s] %(message)s',
            datefmt='%H:%M:%S'
        ))
        self.logger.addHandler(fh)
        
        # Console handler - only if verbose
        if self.verbose:
            ch = logging.StreamHandler()
            ch.setLevel(logging.INFO)
            ch.setFormatter(logging.Formatter('%(message)s'))
            self.logger.addHandler(ch)
        
        print(f"📋 Logging naar: {self.log_file}")
    
    def log(self, message: str, level: str = 'info'):
        """Unified logging method"""
        log_method = getattr(self.logger, level, self.logger.info)
        log_method(message)
    
    def _init_progress_tracking(self):
        """Initialize progress tracking file"""
        self.progress_state = {
            "agent_type": self.agent_type,
            "last_update": None,
            "current_task": None,
            "current_action": "Initialized",
            "files_created": [],
            "history": []
        }
        self._save_progress()
    
    def _update_progress(self, action: str, details: Dict = None):
        """Update progress tracking"""
        self.progress_state["current_action"] = action
        self.progress_state["last_update"] = datetime.now().isoformat()
        if details:
            self.progress_state.update(details)
        self._save_progress()
    
    def _save_progress(self):
        """Save progress to file"""
        with open(self.progress_file, 'w') as f:
            json.dump(self.progress_state, f, indent=2)
    
    def _load_architecture(self) -> Dict[str, Any]:
        """Laad architecture.json om tech stack te kennen"""
        arch_path = self.project_docs_dir / "architecture" / "architecture.json"
        if arch_path.exists():
            with open(arch_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    
    def _get_tech_summary(self) -> str:
        """Korte samenvatting van relevante tech stack"""
        if self.agent_type == 'backend':
            backend = self.tech_stack.get('backend', {})
            lang = backend.get('language', 'Unknown')
            framework = backend.get('framework', 'Unknown')
            return f"{lang} + {framework}"
        else:  # frontend
            frontend = self.tech_stack.get('frontend', {})
            framework = frontend.get('framework', 'Unknown')
            styling = frontend.get('styling', 'Unknown')
            return f"{framework} + {styling}"
    
    def _create_agent_profile(self) -> Dict[str, Any]:
        """Creëer agent profiel met strikte instructies"""
        
        if self.agent_type == 'backend':
            backend_tech = self.tech_stack.get('backend', {})
            database_tech = self.tech_stack.get('database', {})
            
            return {
                "name": "Backend Developer Agent",
                "role": "backend",
                "technology_stack": {
                    "language": backend_tech.get('language', 'Python'),
                    "framework": backend_tech.get('framework', 'FastAPI'),
                    "server": backend_tech.get('server', 'uvicorn'),
                    "database": database_tech.get('specific', 'PostgreSQL')
                },
                "expertise": [
                    "API implementation (REST/GraphQL)",
                    "Database integration and ORM",
                    "Authentication and authorization",
                    "Backend architecture",
                    "Server-side logic",
                    "Data validation",
                    "Error handling"
                ],
                "strict_rules": [
                    "NEVER add features not in specs",
                    "NEVER use libraries not in architecture.json",
                    "NEVER create files not in file_structure.json",
                    "NEVER hallucinate endpoints not in api_structure.json",
                    "NEVER use different tech stack than specified",
                    "ALWAYS follow execution_guide exactly",
                    "ALWAYS validate against validation_checklist",
                    "ALWAYS update task status",
                    "ONLY implement what's in allowed_docs"
                ],
                "workflow": [
                    "1. Read task from sprint JSON",
                    "2. Read ONLY allowed_docs (no external research)",
                    "3. Understand strict_constraints (absolute boundaries)",
                    "4. Plan implementation based ONLY on specs",
                    "5. Implement exactly according to constraints",
                    "6. Test against validation checklist",
                    "7. Update task status",
                    "8. Document completion with status_notes"
                ]
            }
        else:  # frontend
            frontend_tech = self.tech_stack.get('frontend', {})
            
            return {
                "name": "Frontend Developer Agent",
                "role": "frontend",
                "technology_stack": {
                    "framework": frontend_tech.get('framework', 'React'),
                    "styling": frontend_tech.get('styling', 'TailwindCSS'),
                    "state_management": frontend_tech.get('state_management', 'Context API')
                },
                "expertise": [
                    "UI component development",
                    "Frontend state management",
                    "API integration (client-side)",
                    "Form handling and validation",
                    "Routing and navigation",
                    "Responsive design",
                    "User workflow implementation"
                ],
                "strict_rules": [
                    "NEVER add features not in specs",
                    "NEVER use libraries not in architecture.json",
                    "NEVER create files not in file_structure.json",
                    "NEVER implement workflows not in workflows.json",
                    "NEVER use different tech stack than specified",
                    "ALWAYS follow execution_guide exactly",
                    "ALWAYS validate against validation_checklist",
                    "ALWAYS update task status",
                    "ONLY implement what's in allowed_docs"
                ],
                "workflow": [
                    "1. Read task from sprint JSON",
                    "2. Read ONLY allowed_docs (no external research)",
                    "3. Understand strict_constraints (absolute boundaries)",
                    "4. Plan UI based ONLY on workflows.json",
                    "5. Implement exactly according to constraints",
                    "6. Test against validation checklist",
                    "7. Update task status",
                    "8. Document completion with status_notes"
                ]
            }
    
    def find_next_task(self) -> Optional[Tuple[Path, Dict, Dict]]:
        """Vind de volgende taak voor dit agent type"""
        self.log(f"\n🔍 Zoeken naar volgende {self.agent_type} taak...", 'info')
        self._update_progress("Searching for next task")
        
        # Loop door alle sprints
        for sprint_file in sorted(self.sprints_dir.glob("sprint_*.json")):
            with open(sprint_file, 'r', encoding='utf-8') as f:
                sprint = json.load(f)
            
            # Vind eerste pending taak voor dit agent type
            for task in sprint['tasks']:
                if (task.get('assigned_to') == self.agent_type and 
                    task.get('status') == 'pending' and
                    self._dependencies_met(task, sprint)):
                    
                    self.log(f"✅ Gevonden: {task['task_id']} - {task['title']}", 'info')
                    return sprint_file, sprint, task
        
        self.log(f"ℹ️  Geen pending {self.agent_type} taken gevonden", 'info')
        return None
    
    def _dependencies_met(self, task: Dict, sprint: Dict) -> bool:
        """Check of alle dependencies voltooid zijn"""
        for dep_id in task.get('dependencies', []):
            # Check in huidige sprint
            dep_met = False
            for other_task in sprint['tasks']:
                if other_task['task_id'] == dep_id:
                    if other_task.get('status') == 'completed':
                        dep_met = True
                    break
            
            # Als dependency niet in huidige sprint, check andere sprints
            if not dep_met:
                dep_met = self._check_dependency_in_other_sprints(dep_id)
            
            if not dep_met:
                return False
        
        return True
    
    def _check_dependency_in_other_sprints(self, dep_id: str) -> bool:
        """Check of dependency in andere sprint voltooid is"""
        for sprint_file in self.sprints_dir.glob("sprint_*.json"):
            with open(sprint_file, 'r', encoding='utf-8') as f:
                sprint = json.load(f)
            
            for task in sprint['tasks']:
                if task['task_id'] == dep_id:
                    return task.get('status') == 'completed'
        
        return False
    
    def execute_task(self, sprint_file: Path, sprint: Dict, task: Dict) -> bool:
        """Voer een taak uit met Claude - ENHANCED VERSION"""
        task_id = task['task_id']
        
        self.log(f"\n{'='*70}", 'info')
        self.log(f"🎯 STARTING TASK: {task_id}", 'info')
        self.log(f"   Title: {task['title']}", 'info')
        self.log(f"   Type: {task['type']} | Priority: {task['priority']} | Hours: {task['estimated_hours']}", 'info')
        self.log(f"{'='*70}", 'info')
        
        # Update progress
        self.progress_state["current_task"] = {
            "task_id": task_id,
            "title": task['title'],
            "started_at": datetime.now().isoformat()
        }
        self._update_progress("Task started")
        
        # Update status naar in_progress
        task['status'] = 'in_progress'
        task['started_at'] = datetime.now().isoformat()
        self._save_sprint(sprint_file, sprint)
        
        # Log task details
        self.log(f"\n📝 Task Details:", 'debug')
        self.log(json.dumps(task, indent=2), 'debug')
        
        # Laad allowed docs
        self._update_progress("Loading documentation")
        docs_content = self._load_allowed_docs(task)
        
        if not docs_content:
            self.log("❌ Geen allowed docs beschikbaar - taak kan niet uitgevoerd worden", 'error')
            task['status'] = 'blocked'
            task['status_notes'] = 'No allowed documentation found'
            self._save_sprint(sprint_file, sprint)
            self._update_progress("Task blocked - no docs")
            return False
        
        # Bouw prompt voor Claude
        self._update_progress("Building prompt")
        prompt = self._build_task_prompt(task, docs_content)
        
        # Log prompt (only to file)
        self.log("\n" + "="*70, 'debug')
        self.log("📝 FULL PROMPT SENT TO CLAUDE:", 'debug')
        self.log("="*70, 'debug')
        self.log(prompt, 'debug')
        self.log("="*70 + "\n", 'debug')
        
        # Vraag Claude om implementatie
        self.log("\n🤖 Claude CLI wordt aangeroepen...", 'info')
        self.log("   (Dit kan enkele minuten duren...)", 'info')
        self._update_progress("Calling Claude CLI", {"thinking": "Implementing task"})
        
        try:
            response = self._call_claude(prompt, task_id)
            
            # Log response (only to file)
            self.log("\n" + "="*70, 'debug')
            self.log("📥 FULL RESPONSE FROM CLAUDE:", 'debug')
            self.log("="*70, 'debug')
            self.log(response, 'debug')
            self.log("="*70 + "\n", 'debug')
            
            # Verwerk response
            self._update_progress("Processing response")
            success = self._process_claude_response(task, response)
            
            if success:
                # Update status naar completed
                task['status'] = 'completed'
                task['completed_at'] = datetime.now().isoformat()
                task['status_notes'] = 'Successfully completed and validated'
                self.log(f"\n✅ Taak {task_id} voltooid!", 'info')
                
                # Update progress history
                self.progress_state["history"].append({
                    "task_id": task_id,
                    "title": task['title'],
                    "success": True,
                    "completed_at": datetime.now().isoformat()
                })
                self._update_progress("Task completed successfully")
            else:
                # Update status naar blocked
                task['status'] = 'blocked'
                task['status_notes'] = 'Implementation validation failed - check validation results'
                self.log(f"\n❌ Taak {task_id} geblokkeerd - validatie gefaald", 'warning')
                
                self.progress_state["history"].append({
                    "task_id": task_id,
                    "title": task['title'],
                    "success": False,
                    "completed_at": datetime.now().isoformat()
                })
                self._update_progress("Task blocked - validation failed")
            
            self._save_sprint(sprint_file, sprint)
            self.progress_state["current_task"] = None
            self._save_progress()
            
            return success
            
        except Exception as e:
            self.log(f"\n❌ Error tijdens uitvoering: {e}", 'error')
            self.log(f"Stack trace:", 'debug')
            import traceback
            self.log(traceback.format_exc(), 'debug')
            
            task['status'] = 'blocked'
            task['status_notes'] = f'Error: {str(e)}'
            self._save_sprint(sprint_file, sprint)
            
            self.progress_state["history"].append({
                "task_id": task_id,
                "title": task['title'],
                "success": False,
                "error": str(e),
                "completed_at": datetime.now().isoformat()
            })
            self.progress_state["current_task"] = None
            self._update_progress("Task failed with error")
            
            return False
    
    def _load_allowed_docs(self, task: Dict) -> Dict[str, Any]:
        """Laad alle allowed docs voor een taak"""
        self.log(f"\n📚 Laden van allowed docs...", 'info')
        docs = {}
        
        for doc_path in task.get('allowed_docs', []):
            full_path = self.project_docs_dir / doc_path
            if full_path.exists():
                with open(full_path, 'r', encoding='utf-8') as f:
                    docs[doc_path] = json.load(f)
                self.log(f"  ✅ {doc_path}", 'info')
            else:
                self.log(f"  ❌ {doc_path} niet gevonden!", 'warning')
        
        return docs
    
    def _build_task_prompt(self, task: Dict, docs_content: Dict) -> str:
        """Bouw een strikte prompt voor Claude"""
        
        prompt = f"""You are a {self.agent_name} working on a software project.

# YOUR IDENTITY AND CAPABILITIES
{json.dumps(self.profile, indent=2)}

# CRITICAL RULES - ABSOLUTE - NO EXCEPTIONS
These rules are MANDATORY. Violation will result in task failure.

1. ⚠️  DOCUMENTATION BOUNDARY: You can ONLY use information from "ALLOWED DOCUMENTATION" below
   - NO external knowledge
   - NO assumptions
   - NO "best practices" not in docs
   - NO additional features

2. ⚠️  TECHNOLOGY BOUNDARY: You can ONLY use technologies listed in your technology_stack above
   - NO substitutions
   - NO "better" alternatives
   - NO additional libraries

3. ⚠️  FILE BOUNDARY: You can ONLY create files that align with file_structure.json
   - NO additional directories
   - NO additional files
   - File paths must match specs

4. ⚠️  FEATURE BOUNDARY: You can ONLY implement features explicitly in the documentation
   - NO "nice to have" features
   - NO optimizations not requested
   - NO refactoring not specified

5. ⚠️  EXECUTION BOUNDARY: You MUST follow the execution_guide step by step
   - NO skipping steps
   - NO reordering steps
   - Each step must be completed

# CURRENT TASK
Task ID: {task['task_id']}
Title: {task['title']}
Description: {task['description']}
Type: {task['type']}
Priority: {task['priority']}
Estimated Hours: {task['estimated_hours']}

# EXECUTION GUIDE (FOLLOW STEP BY STEP - DO NOT SKIP)
{chr(10).join(f"{i}. {step}" for i, step in enumerate(task.get('execution_guide', []), 1))}

# STRICT CONSTRAINTS (ABSOLUTE BOUNDARIES - NO DEVIATIONS ALLOWED)
These constraints are MANDATORY. You MUST adhere to ALL of them.
{json.dumps(task.get('strict_constraints', {}), indent=2)}

# DELIVERABLES (MUST PRODUCE ALL - NOTHING MORE, NOTHING LESS)
You must produce EXACTLY these items:
{chr(10).join(f"• {d}" for d in task.get('deliverables', []))}

# VALIDATION CHECKLIST (ALL MUST BE TRUE BEFORE COMPLETION)
After implementation, verify each item:
{chr(10).join(f"[ ] {v}" for v in task.get('validation_checklist', []))}

# ALLOWED DOCUMENTATION (YOUR ONLY SOURCE OF TRUTH)
This is the COMPLETE information available to you. Do NOT use any other information.
{json.dumps(docs_content, indent=2)}

# PROJECT ROOT
All file paths are relative to: {self.project_root}
IMPORTANT: File paths should NOT include the project root directory name itself.
Example: Use "src/app.py" NOT "my_project/src/app.py"

# YOUR TASK
Implement this task following these steps:

1. READ the execution guide completely
2. READ all allowed documentation completely
3. PLAN your implementation (what files, what code)
4. IMPLEMENT according to strict_constraints
5. PRODUCE all deliverables
6. VALIDATE against validation_checklist

# OUTPUT FORMAT
Provide your response in JSON format with this EXACT structure:

{{
  "analysis": {{
    "understood_requirements": "Brief summary of what you understood from docs",
    "identified_constraints": ["constraint 1", "constraint 2"],
    "implementation_plan": "High-level plan of what you will create"
  }},
  "implementation": {{
    "files": [
      {{
        "path": "relative/path/to/file",
        "content": "COMPLETE file content - do not use placeholders",
        "purpose": "What this file does"
      }}
    ],
    "commands": [
      {{
        "command": "command to run (e.g., npm install, pip install)",
        "purpose": "Why this command is needed",
        "working_directory": "directory to run from (relative to project root)"
      }}
    ]
  }},
  "validation": {{
    "checklist_results": [
      {{
        "item": "validation checklist item text",
        "passed": true/false,
        "evidence": "How you verified this (what file, what line, what test)",
        "notes": "Any relevant notes"
      }}
    ],
    "all_passed": true/false,
    "summary": "Overall validation summary"
  }},
  "completion_notes": "Any important notes about the implementation"
}}

# CRITICAL REMINDERS
- ❌ DO NOT add features not in specs
- ❌ DO NOT use technologies not in your tech stack
- ❌ DO NOT create files not aligned with file_structure.json
- ❌ DO NOT make assumptions
- ❌ DO NOT use placeholders like "// TODO" or "# implement later"
- ✅ DO provide COMPLETE, working implementations
- ✅ DO follow execution guide EXACTLY
- ✅ DO validate ALL checklist items
- ✅ DO use ONLY information from allowed docs

BEGIN YOUR IMPLEMENTATION NOW.
"""
        
        return prompt
    
    def _call_claude(self, prompt: str, task_id: str = None) -> str:
        """Roep Claude CLI aan met prompt - ENHANCED with real-time output"""
        
        self.log("\n" + "="*70, 'info')
        if task_id:
            self.log(f"🤖 CLAUDE CLI - Task {task_id}", 'info')
        else:
            self.log("🤖 CLAUDE CLI wordt aangeroepen", 'info')
        self.log("="*70 + "\n", 'info')
        
        try:
            # Start process
            process = subprocess.Popen(
                ['claude', '--dangerously-skip-permissions', '-'],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1  # Line buffered for real-time output
            )
            
            # Send prompt
            process.stdin.write(prompt)
            process.stdin.close()
            
            # Read output real-time
            output_lines = []
            
            if self.verbose:
                self.log("💬 Claude's Response (streaming):", 'info')
                self.log("-"*70, 'info')
            
            # Read stdout line by line
            for line in iter(process.stdout.readline, ''):
                if not line:
                    break
                
                # Always log to file
                self.log(line.rstrip(), 'debug')
                
                # Show in console if verbose
                if self.verbose:
                    print(line, end='', flush=True)
                
                output_lines.append(line)
            
            # Wait for completion
            stderr = process.stderr.read()
            return_code = process.wait()
            
            if self.verbose:
                self.log("-"*70, 'info')
                self.log("✅ Response ontvangen\n", 'info')
            
            if return_code != 0:
                self.log(f"\n❌ Claude CLI Error (exit code {return_code})", 'error')
                if stderr:
                    self.log(f"STDERR: {stderr}", 'error')
                raise Exception(f"Claude CLI error: {stderr}")
            
            if stderr:
                self.log(f"⚠️  STDERR: {stderr}", 'warning')
            
            full_output = ''.join(output_lines)
            
            # Log statistics
            self.log(f"\n📊 Statistics:", 'debug')
            self.log(f"   Output lines: {len(output_lines)}", 'debug')
            self.log(f"   Output length: {len(full_output)} chars", 'debug')
            
            return full_output
            
        except subprocess.TimeoutExpired:
            self.log("❌ Claude call timeout (10 minuten)", 'error')
            raise Exception("Claude call timeout (10 minuten)")
        except FileNotFoundError:
            self.log("❌ Claude CLI niet gevonden", 'error')
            raise Exception("Claude CLI niet gevonden. Installeer: npm install -g @anthropic-ai/claude")
    
    def _process_claude_response(self, task: Dict, response: str) -> bool:
        """Verwerk Claude's response en implementeer de code"""
        self.log("\n📝 Verwerken van Claude's response...", 'info')
        
        # Extraheer JSON uit response
        implementation = self._extract_json_from_response(response)
        
        if not implementation:
            self.log("❌ Geen valide JSON in response", 'error')
            self.log("\nResponse preview:", 'error')
            self.log(response[:500], 'error')
            return False
        
        # Toon analyse
        if 'analysis' in implementation:
            analysis = implementation['analysis']
            self.log(f"\n🔍 Claude's Analyse:", 'info')
            self.log(f"   Requirements: {analysis.get('understood_requirements', 'N/A')[:100]}...", 'info')
            self.log(f"   Constraints: {len(analysis.get('identified_constraints', []))} geïdentificeerd", 'info')
            self.log(f"   Plan: {analysis.get('implementation_plan', 'N/A')[:100]}...", 'info')
        
        # Implementeer files
        if 'implementation' in implementation:
            impl = implementation['implementation']
            
            # Maak files aan
            files_created = 0
            files_list = []
            for file_info in impl.get('files', []):
                file_path = self.project_root / file_info['path']
                
                # Ensure parent directory exists
                file_path.parent.mkdir(parents=True, exist_ok=True)
                
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(file_info['content'])
                
                files_created += 1
                files_list.append(file_info['path'])
                self.log(f"  ✅ Created: {file_info['path']}", 'info')
                if file_info.get('purpose'):
                    self.log(f"     → {file_info['purpose']}", 'info')
            
            self.log(f"\n📁 Totaal {files_created} bestanden aangemaakt", 'info')
            
            # Update progress with files
            self.progress_state["files_created"].extend(files_list)
            self._save_progress()
            
            # Run commands
            commands_run = 0
            for cmd_info in impl.get('commands', []):
                command = cmd_info.get('command') if isinstance(cmd_info, dict) else cmd_info
                working_dir = self.project_root
                
                if isinstance(cmd_info, dict) and cmd_info.get('working_directory'):
                    working_dir = self.project_root / cmd_info['working_directory']
                
                self.log(f"\n  🔧 Running: {command}", 'info')
                if isinstance(cmd_info, dict) and cmd_info.get('purpose'):
                    self.log(f"     Purpose: {cmd_info['purpose']}", 'info')
                
                try:
                    result = subprocess.run(
                        command,
                        shell=True,
                        cwd=working_dir,
                        capture_output=True,
                        text=True,
                        timeout=120
                    )
                    if result.returncode == 0:
                        self.log(f"     ✅ Success", 'info')
                        commands_run += 1
                    else:
                        self.log(f"     ⚠️  Exit code: {result.returncode}", 'warning')
                        if result.stderr:
                            self.log(f"     Error: {result.stderr[:200]}", 'warning')
                except Exception as e:
                    self.log(f"     ❌ Command failed: {e}", 'error')
            
            if impl.get('commands'):
                self.log(f"\n⚙️  {commands_run}/{len(impl['commands'])} commando's succesvol", 'info')
        
        # Check validatie
        validation = implementation.get('validation', {})
        checklist_results = validation.get('checklist_results', [])
        all_passed = validation.get('all_passed', False)
        
        self.log("\n📋 Validation Results:", 'info')
        self.log(f"{'='*70}", 'info')
        
        passed_count = 0
        for item_result in checklist_results:
            item = item_result.get('item', 'Unknown item')
            passed = item_result.get('passed', False)
            evidence = item_result.get('evidence', 'No evidence')
            notes = item_result.get('notes', '')
            
            status = "✅" if passed else "❌"
            self.log(f"{status} {item}", 'info')
            self.log(f"   Evidence: {evidence}", 'info')
            if notes:
                self.log(f"   Notes: {notes}", 'info')
            
            if passed:
                passed_count += 1
        
        self.log(f"\n📊 Validation Score: {passed_count}/{len(checklist_results)} items passed", 'info')
        
        if validation.get('summary'):
            self.log(f"📝 Summary: {validation['summary']}", 'info')
        
        self.log(f"{'='*70}", 'info')
        
        return all_passed
    
    def _extract_json_from_response(self, response: str) -> Optional[Dict]:
        """Extraheer JSON uit Claude's response"""
        
        # Probeer JSON code block
        json_match = re.search(r'```json\s*(\{.*?\})\s*```', response, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except json.JSONDecodeError as e:
                self.log(f"JSON decode error in code block: {e}", 'debug')
        
        # Probeer direct JSON
        try:
            start = response.find('{')
            end = response.rfind('}') + 1
            if start != -1 and end > start:
                json_str = response[start:end]
                return json.loads(json_str)
        except json.JSONDecodeError as e:
            self.log(f"JSON decode error in direct parse: {e}", 'debug')
        
        return None
    
    def _save_sprint(self, sprint_file: Path, sprint: Dict):
        """Sla sprint terug naar file"""
        with open(sprint_file, 'w', encoding='utf-8') as f:
            json.dump(sprint, f, indent=2, ensure_ascii=False)
    
    def run(self, max_tasks: int = 10):
        """Run de agent voor maximaal N taken"""
        self.log(f"\n{'='*70}", 'info')
        self.log(f"🚀 {self.agent_name} Agent gestart", 'info')
        self.log(f"   Max tasks: {max_tasks}", 'info')
        self.log(f"{'='*70}", 'info')
        
        completed_count = 0
        blocked_count = 0
        
        for i in range(max_tasks):
            # Vind volgende taak
            result = self.find_next_task()
            
            if not result:
                self.log(f"\n✨ Geen {self.agent_type} taken meer te doen!", 'info')
                break
            
            sprint_file, sprint, task = result
            
            # Voer taak uit
            success = self.execute_task(sprint_file, sprint, task)
            
            if success:
                completed_count += 1
            else:
                blocked_count += 1
            
            self.log(f"\n📊 Voortgang: {completed_count} completed, {blocked_count} blocked ({i+1} total)", 'info')
        
        self.log(f"\n{'='*70}", 'info')
        self.log(f"🏁 {self.agent_name} Agent klaar", 'info')
        self.log(f"   ✅ Voltooid: {completed_count} taken", 'info')
        self.log(f"   ❌ Geblokkeerd: {blocked_count} taken", 'info')
        self.log(f"{'='*70}", 'info')
        
        return completed_count, blocked_count


class DevelopmentOrchestrator:
    """Orchestrator die beide agents aanstuurt"""
    
    def __init__(self, project_root: str, project_docs_dir: str, sprints_dir: str, verbose: bool = True):
        self.project_root = Path(project_root)
        self.project_docs_dir = Path(project_docs_dir)
        self.sprints_dir = Path(sprints_dir)
        self.verbose = verbose
        
        # Maak beide agents
        self.backend_agent = DevelopmentAgent('backend', self.project_root, 
                                             self.project_docs_dir, self.sprints_dir, verbose)
        self.frontend_agent = DevelopmentAgent('frontend', self.project_root, 
                                              self.project_docs_dir, self.sprints_dir, verbose)
    
    def run_parallel(self, max_tasks_per_agent: int = 10):
        """Run beide agents parallel (turn-based)"""
        print("""
╔════════════════════════════════════════════════════════════════════╗
║           DEVELOPMENT AGENTS ORCHESTRATOR                          ║
║           Frontend + Backend Development                           ║
╚════════════════════════════════════════════════════════════════════╝
        """)
        
        print(f"\n📂 Project: {self.project_root}")
        print(f"📚 Docs: {self.project_docs_dir}")
        print(f"📋 Sprints: {self.sprints_dir}")
        print(f"👁️  Verbose: {self.verbose}")
        
        backend_completed = 0
        backend_blocked = 0
        frontend_completed = 0
        frontend_blocked = 0
        
        # Alterneer tussen agents
        for round_num in range(max_tasks_per_agent):
            print(f"\n{'='*70}")
            print(f"🔄 Round {round_num + 1}")
            print(f"{'='*70}")
            
            agents_worked = False
            
            # Backend agent doet 1 taak
            backend_result = self.backend_agent.find_next_task()
            if backend_result:
                sprint_file, sprint, task = backend_result
                success = self.backend_agent.execute_task(sprint_file, sprint, task)
                if success:
                    backend_completed += 1
                else:
                    backend_blocked += 1
                agents_worked = True
            
            # Frontend agent doet 1 taak
            frontend_result = self.frontend_agent.find_next_task()
            if frontend_result:
                sprint_file, sprint, task = frontend_result
                success = self.frontend_agent.execute_task(sprint_file, sprint, task)
                if success:
                    frontend_completed += 1
                else:
                    frontend_blocked += 1
                agents_worked = True
            
            # Als beide agents geen werk meer hebben, stop
            if not agents_worked:
                print("\n✨ Geen taken meer voor beide agents!")
                break
        
        # Final report
        print(f"\n{'='*70}")
        print(f"🎉 DEVELOPMENT COMPLETED")
        print(f"{'='*70}")
        print(f"\n🔧 Backend Agent:")
        print(f"   ✅ Completed: {backend_completed} taken")
        print(f"   ❌ Blocked: {backend_blocked} taken")
        print(f"   📋 Log: {self.backend_agent.log_file}")
        print(f"   📊 Progress: {self.backend_agent.progress_file}")
        print(f"\n🎨 Frontend Agent:")
        print(f"   ✅ Completed: {frontend_completed} taken")
        print(f"   ❌ Blocked: {frontend_blocked} taken")
        print(f"   📋 Log: {self.frontend_agent.log_file}")
        print(f"   📊 Progress: {self.frontend_agent.progress_file}")
        print(f"\n📊 Totaal:")
        print(f"   ✅ Completed: {backend_completed + frontend_completed} taken")
        print(f"   ❌ Blocked: {backend_blocked + frontend_blocked} taken")
        print(f"{'='*70}")
    
    def run_sequential(self, max_tasks_per_agent: int = 10):
        """Run agents sequentieel (eerst backend, dan frontend)"""
        print("""
╔════════════════════════════════════════════════════════════════════╗
║           DEVELOPMENT AGENTS ORCHESTRATOR                          ║
║           Sequential: Backend → Frontend                           ║
╚════════════════════════════════════════════════════════════════════╝
        """)
        
        # Eerst backend
        print("\n🔧 Starting Backend Development...")
        backend_completed, backend_blocked = self.backend_agent.run(max_tasks_per_agent)
        
        # Dan frontend
        print("\n🎨 Starting Frontend Development...")
        frontend_completed, frontend_blocked = self.frontend_agent.run(max_tasks_per_agent)
        
        # Final report
        print(f"\n{'='*70}")
        print(f"🎉 DEVELOPMENT COMPLETED")
        print(f"{'='*70}")
        print(f"\n🔧 Backend Agent:")
        print(f"   ✅ Completed: {backend_completed} taken")
        print(f"   ❌ Blocked: {backend_blocked} taken")
        print(f"   📋 Log: {self.backend_agent.log_file}")
        print(f"   📊 Progress: {self.backend_agent.progress_file}")
        print(f"\n🎨 Frontend Agent:")
        print(f"   ✅ Completed: {frontend_completed} taken")
        print(f"   ❌ Blocked: {frontend_blocked} taken")
        print(f"   📋 Log: {self.frontend_agent.log_file}")
        print(f"   📊 Progress: {self.frontend_agent.progress_file}")
        print(f"\n📊 Totaal:")
        print(f"   ✅ Completed: {backend_completed + frontend_completed} taken")
        print(f"   ❌ Blocked: {backend_blocked + frontend_blocked} taken")
        print(f"{'='*70}")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Development Agents Orchestrator - Enhanced')
    parser.add_argument('project_root', help='Root directory van het project (waar code komt)')
    parser.add_argument('--docs', default='./project_docs', help='Project documentatie directory')
    parser.add_argument('--sprints', default='./sprints', help='Sprints directory')
    parser.add_argument('--max-tasks', type=int, default=10, help='Max taken per agent')
    parser.add_argument('--mode', choices=['parallel', 'sequential', 'backend', 'frontend'], 
                       default='parallel', help='Execution mode')
    parser.add_argument('--quiet', action='store_true', 
                       help='Disable verbose output (only log to file)')
    
    args = parser.parse_args()
    
    verbose = not args.quiet
    
    # Valideer directories
    if not Path(args.docs).exists():
        print(f"❌ Project docs niet gevonden: {args.docs}")
        sys.exit(1)
    
    if not Path(args.sprints).exists():
        print(f"❌ Sprints directory niet gevonden: {args.sprints}")
        sys.exit(1)
    
    # Maak project root als die niet bestaat
    Path(args.project_root).mkdir(parents=True, exist_ok=True)
    
    print(f"""
╔════════════════════════════════════════════════════════════════════╗
║           ENHANCED DEVELOPMENT AGENTS v2.3                         ║
║           Met Real-time Output & Logging                           ║
╚════════════════════════════════════════════════════════════════════╝

📋 Features:
   • Real-time Claude CLI output streaming
   • Uitgebreide logging naar ./logs/
   • Progress tracking naar ./agent_progress_*.json
   • File creation monitoring

💡 Tip: Open een tweede terminal en run:
   tail -f logs/backend_agent_*.log
   tail -f logs/frontend_agent_*.log

📊 Monitor progress:
   watch -n 1 cat agent_progress_backend.json
    """)
    
    # Run agents
    if args.mode == 'backend':
        # Alleen backend
        agent = DevelopmentAgent('backend', Path(args.project_root), 
                                Path(args.docs), Path(args.sprints), verbose)
        agent.run(args.max_tasks)
    
    elif args.mode == 'frontend':
        # Alleen frontend
        agent = DevelopmentAgent('frontend', Path(args.project_root), 
                                Path(args.docs), Path(args.sprints), verbose)
        agent.run(args.max_tasks)
    
    else:
        # Orchestrator met beide agents
        orchestrator = DevelopmentOrchestrator(args.project_root, args.docs, 
                                              args.sprints, verbose)
        
        if args.mode == 'parallel':
            orchestrator.run_parallel(args.max_tasks)
        else:  # sequential
            orchestrator.run_sequential(args.max_tasks)


if __name__ == "__main__":
    main()
