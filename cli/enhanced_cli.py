#!/usr/bin/env python3
"""
Enhanced Code Standards Auditor CLI

Main command-line interface providing access to all enhanced features
including conversational research, agent-optimized analysis, and integrated workflows.

Author: Code Standards Auditor
Date: September 01, 2025
Version: 2.0.0
"""

import os
import sys
import asyncio
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.markdown import Markdown
from rich.tree import Tree
from rich.prompt import Prompt, Confirm

# Import our enhanced services
from cli.interactive.conversational_research import ConversationalResearchInterface
from services.integrated_workflow_service import IntegratedWorkflowService
from services.enhanced_recommendations_service import EnhancedRecommendationsService
from services.standards_research_service import StandardsResearchService
from config.settings import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Rich console
console = Console()


class EnhancedCLI:
    """Enhanced CLI for the Code Standards Auditor."""
    
    def __init__(self):
        """Initialize the Enhanced CLI."""
        self.console = console
        
        # Initialize services
        self.workflow_service = IntegratedWorkflowService()
        self.recommendations_service = EnhancedRecommendationsService()
        self.research_service = StandardsResearchService()
        self.conversational_interface = ConversationalResearchInterface()
        
        # CLI state
        self.active_workflows = {}
    
    def display_welcome(self):
        """Display enhanced welcome message."""
        welcome_text = """
        # 🚀 Enhanced Code Standards Auditor CLI v2.0
        
        ## New Features in v2.0
        
        ### 🧠 **Conversational Research**
        - Natural language standard requests
        - Multi-turn requirement gathering
        - Context-aware recommendations
        - Iterative refinement process
        
        ### 🤖 **Agent Integration**
        - Optimized for AI agent consumption
        - Real-time standard updates
        - Batch operations support
        - Context-aware search
        
        ### 🔄 **Integrated Workflows**
        - End-to-end automation
        - Research → Documentation → Analysis
        - Quality validation and deployment
        - Comprehensive feedback loops
        
        ### 🛠 **Enhanced Recommendations**
        - Step-by-step implementation guides
        - Automated fix suggestions
        - Risk assessment and effort estimation
        - Code transformation examples
        
        ## Available Commands
        - `research` - Interactive conversational research
        - `workflow` - Start integrated workflow
        - `analyze` - Enhanced code analysis
        - `standards` - Manage standards library
        - `agent` - Agent-optimized operations
        - `help` - Show detailed help
        - `exit` - Exit the CLI
        """
        
        panel = Panel(
            Markdown(welcome_text),
            title="🎯 Enhanced Code Standards Auditor",
            border_style="cyan"
        )
        self.console.print(panel)
    
    def display_main_menu(self):
        """Display the main menu options."""
        table = Table(show_header=False, box=None, padding=(0, 2))
        table.add_column("Command", style="bold cyan", width=15)
        table.add_column("Description", style="white")
        table.add_column("Status", style="green")
        
        commands = [
            ("research", "Interactive conversational standard research", "✅ Enhanced"),
            ("workflow", "Complete research-to-analysis workflows", "🆕 New"),
            ("analyze", "Advanced code analysis with implementation guides", "✅ Enhanced"),
            ("standards", "Browse and manage standards library", "✅ Available"),
            ("agent", "Agent-optimized operations and real-time updates", "🆕 New"),
            ("status", "Check active workflows and service health", "✅ Available"),
            ("help", "Detailed help and feature documentation", "✅ Available"),
            ("exit", "Exit the CLI", "✅ Available")
        ]
        
        for cmd, desc, status in commands:
            table.add_row(cmd, desc, status)
        
        self.console.print("\n")
        self.console.print(Panel(table, title="🎮 Available Commands", border_style="blue"))
    
    async def handle_research_command(self):
        """Handle the research command."""
        self.console.print("\n[bold cyan]🧠 Conversational Research Interface[/bold cyan]")
        self.console.print("[dim]Starting enhanced conversational research session...[/dim]\n")
        
        # Start conversational research
        await self.conversational_interface.run_conversational_research()
    
    async def handle_workflow_command(self):
        """Handle the workflow command."""
        self.console.print("\n[bold cyan]🔄 Integrated Workflow Manager[/bold cyan]")
        
        # Get workflow request
        research_request = Prompt.ask(
            "\n[yellow]What would you like to research and analyze?[/yellow]\n"
            "[dim](I'll create standards, analyze code, and provide comprehensive feedback)[/dim]"
        )
        
        if not research_request:
            self.console.print("[red]No request provided[/red]")
            return
        
        # Get code samples
        code_samples = []
        if Confirm.ask("\n[yellow]Do you have code samples to analyze against the new standard?[/yellow]"):
            code_samples = self._get_code_samples_input()
        
        # Get project context
        project_context = {}
        if Confirm.ask("\n[yellow]Would you like to provide project context?[/yellow]"):
            project_context = self._get_project_context_input()
        
        # Start workflow
        try:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=self.console
            ) as progress:
                task = progress.add_task("Starting integrated workflow...", total=None)
                
                workflow_id = await self.workflow_service.start_research_to_analysis_workflow(
                    research_request=research_request,
                    code_samples=code_samples,
                    project_context=project_context
                )
                
                self.active_workflows[workflow_id] = {
                    "request": research_request,
                    "started_at": "now",
                    "code_samples": len(code_samples)
                }
                
                progress.update(task, description="Workflow started successfully!")
            
            self.console.print(f"\n[green]✅ Workflow started successfully![/green]")
            self.console.print(f"[cyan]Workflow ID:[/cyan] {workflow_id}")
            self.console.print(f"[cyan]Estimated completion:[/cyan] 5-15 minutes")
            
            # Ask if user wants to monitor progress
            if Confirm.ask("\n[yellow]Would you like to monitor the workflow progress?[/yellow]"):
                await self._monitor_workflow_progress(workflow_id)
            else:
                self.console.print(f"\n[dim]Use 'status {workflow_id}' to check progress later[/dim]")
                
        except Exception as e:
            self.console.print(f"[red]Failed to start workflow: {e}[/red]")
    
    async def handle_analyze_command(self):
        """Handle the analyze command."""
        self.console.print("\n[bold cyan]🔍 Enhanced Code Analysis[/bold cyan]")
        
        # Get code input
        code_samples = self._get_code_samples_input()
        if not code_samples:
            self.console.print("[red]No code provided for analysis[/red]")
            return
        
        # Get analysis preferences
        focus_areas = self._get_focus_areas_input()
        language = self._detect_or_ask_language(code_samples[0])
        
        try:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=self.console
            ) as progress:
                
                # Analyze each code sample
                all_results = []
                for i, code in enumerate(code_samples):
                    task = progress.add_task(f"Analyzing code sample {i+1}...", total=None)
                    
                    result = await self.recommendations_service.generate_enhanced_recommendations(
                        code=code,
                        language=language,
                        focus_areas=focus_areas,
                        include_automated_fixes=True
                    )
                    
                    all_results.append(result)
                    progress.update(task, description=f"Sample {i+1} analysis complete")
            
            # Display results
            self._display_analysis_results(all_results, language)
            
        except Exception as e:
            self.console.print(f"[red]Analysis failed: {e}[/red]")
    
    async def handle_standards_command(self):
        """Handle the standards command."""
        self.console.print("\n[bold cyan]📚 Standards Library Manager[/bold cyan]")
        
        while True:
            action = Prompt.ask(
                "\nWhat would you like to do?",
                choices=["browse", "search", "create", "validate", "back"],
                default="browse"
            )
            
            if action == "back":
                break
            elif action == "browse":
                await self._browse_standards()
            elif action == "search":
                await self._search_standards()
            elif action == "create":
                await self._create_standard()
            elif action == "validate":
                await self._validate_standard()
    
    async def handle_agent_command(self):
        """Handle agent-specific commands."""
        self.console.print("\n[bold cyan]🤖 Agent-Optimized Operations[/bold cyan]")
        
        agent_menu = Table(show_header=False, box=None, padding=(0, 2))
        agent_menu.add_column("Command", style="cyan", width=20)
        agent_menu.add_column("Description", style="white")
        
        agent_commands = [
            ("context-search", "Search standards with agent context"),
            ("batch-analysis", "Batch analyze multiple code files"),
            ("real-time-updates", "Monitor real-time standard updates"),
            ("validation", "Validate code against specific standards"),
            ("recommendations", "Get agent-optimized recommendations")
        ]
        
        for cmd, desc in agent_commands:
            agent_menu.add_row(cmd, desc)
        
        self.console.print(agent_menu)
        
        choice = Prompt.ask(
            "\nSelect agent operation",
            choices=[cmd for cmd, _ in agent_commands] + ["back"],
            default="back"
        )
        
        if choice == "back":
            return
        elif choice == "context-search":
            await self._agent_context_search()
        elif choice == "batch-analysis":
            await self._agent_batch_analysis()
        else:
            self.console.print(f"[yellow]Agent operation '{choice}' implementation coming soon![/yellow]")
    
    async def handle_status_command(self, workflow_id: Optional[str] = None):
        """Handle the status command."""
        if workflow_id:
            await self._show_workflow_status(workflow_id)
        else:
            await self._show_system_status()
    
    def _get_code_samples_input(self) -> List[str]:
        """Get code samples from user input."""
        code_samples = []
        self.console.print("\n[cyan]📝 Code Input[/cyan]")
        self.console.print("[dim]Enter code samples (type 'END' on a new line to finish each sample)[/dim]")
        self.console.print("[dim]Type 'DONE' when finished with all samples[/dim]\n")
        
        while True:
            if code_samples:
                if not Confirm.ask(f"\n[yellow]Add another code sample? ({len(code_samples)} added)[/yellow]"):
                    break
            
            self.console.print(f"\n[cyan]Code Sample {len(code_samples) + 1}:[/cyan]")
            lines = []
            while True:
                try:
                    line = input()
                    if line == "END":
                        break
                    if line == "DONE":
                        if lines:
                            code_samples.append("\n".join(lines))
                        return code_samples
                    lines.append(line)
                except EOFError:
                    break
            
            if lines:
                code_samples.append("\n".join(lines))
                self.console.print(f"[green]✓ Sample {len(code_samples)} added ({len(lines)} lines)[/green]")
        
        return code_samples
    
    def _get_project_context_input(self) -> Dict[str, Any]:
        """Get project context from user."""
        context = {}
        
        context_questions = [
            ("project_type", "What type of project is this?", "web application"),
            ("team_size", "What's your team size?", "small (1-5)"),
            ("experience_level", "Team experience level?", "intermediate"),
            ("tech_stack", "Primary technologies used?", ""),
            ("deployment_env", "Deployment environment?", "cloud")
        ]
        
        self.console.print("\n[cyan]Project Context (optional):[/cyan]")
        for key, question, default in context_questions:
            answer = Prompt.ask(f"  {question}", default=default)
            if answer:
                context[key] = answer
        
        return context
    
    def _get_focus_areas_input(self) -> List[str]:
        """Get analysis focus areas from user."""
        focus_options = [
            "security", "performance", "maintainability", 
            "style", "architecture", "testing", "documentation"
        ]
        
        self.console.print("\n[yellow]Analysis Focus Areas (press Enter for all):[/yellow]")
        for i, area in enumerate(focus_options, 1):
            self.console.print(f"  {i}. {area}")
        
        selection = Prompt.ask(
            "\nEnter numbers separated by commas (e.g., 1,3,5) or press Enter for all",
            default=""
        )
        
        if not selection:
            return focus_options
        
        try:
            indices = [int(x.strip()) - 1 for x in selection.split(",")]
            return [focus_options[i] for i in indices if 0 <= i < len(focus_options)]
        except (ValueError, IndexError):
            self.console.print("[yellow]Invalid selection, using all focus areas[/yellow]")
            return focus_options
    
    def _detect_or_ask_language(self, code: str) -> str:
        """Detect or ask for programming language."""
        # Simple detection
        if "def " in code and ":" in code:
            detected = "python"
        elif "function " in code or "=>" in code:
            detected = "javascript"
        elif "public class" in code:
            detected = "java"
        else:
            detected = None
        
        if detected:
            if Confirm.ask(f"\n[yellow]Detected language: {detected}. Is this correct?[/yellow]"):
                return detected
        
        return Prompt.ask(
            "What programming language is this?",
            default="python"
        )
    
    def _display_analysis_results(self, results: List[Dict[str, Any]], language: str):
        """Display enhanced analysis results."""
        self.console.print("\n" + "="*80)
        self.console.print(f"[bold green]🎯 Enhanced Analysis Results ({language})[/bold green]")
        self.console.print("="*80)
        
        for i, result in enumerate(results):
            self.console.print(f"\n[bold cyan]📄 Code Sample {i+1}[/bold cyan]")
            
            summary = result.get("summary", {})
            recommendations = result.get("recommendations", [])
            
            # Summary table
            summary_table = Table(show_header=False, box=None)
            summary_table.add_column("Metric", style="cyan")
            summary_table.add_column("Value", style="white")
            
            summary_table.add_row("Total Recommendations", str(len(recommendations)))
            summary_table.add_row("Critical Issues", str(summary.get("by_priority", {}).get("critical", 0)))
            summary_table.add_row("High Priority", str(summary.get("by_priority", {}).get("high", 0)))
            summary_table.add_row("Automated Fixes", str(summary.get("automation_available", 0)))
            
            self.console.print(summary_table)
            
            # Top recommendations
            if recommendations:
                self.console.print(f"\n[yellow]🔧 Top Recommendations:[/yellow]")
                for j, rec in enumerate(recommendations[:3]):
                    priority = rec.get("priority", "medium")
                    priority_color = {
                        "critical": "red",
                        "high": "orange3",
                        "medium": "yellow",
                        "low": "green"
                    }.get(priority, "white")
                    
                    self.console.print(
                        f"  {j+1}. [{priority_color}][{priority.upper()}][/{priority_color}] "
                        f"{rec.get('title', 'Untitled')}"
                    )
                    
                    # Show implementation steps if available
                    impl_steps = rec.get("implementation_guide", [])
                    if impl_steps:
                        self.console.print(f"     [dim]Implementation: {len(impl_steps)} steps available[/dim]")
                    
                    # Show automated fixes
                    auto_fixes = rec.get("automated_fixes", [])
                    if auto_fixes:
                        self.console.print(f"     [green]✅ Automated fix available[/green]")
        
        # Ask for detailed view
        if Confirm.ask("\n[yellow]Would you like to see detailed recommendations?[/yellow]"):
            self._display_detailed_recommendations(results)
    
    def _display_detailed_recommendations(self, results: List[Dict[str, Any]]):
        """Display detailed view of recommendations."""
        for i, result in enumerate(results):
            recommendations = result.get("recommendations", [])
            
            if not recommendations:
                continue
            
            self.console.print(f"\n[bold]📋 Detailed Recommendations for Sample {i+1}[/bold]")
            
            for j, rec in enumerate(recommendations):
                self.console.print(f"\n[cyan]━━━ Recommendation {j+1}: {rec.get('title', 'Untitled')} ━━━[/cyan]")
                
                # Basic info
                priority = rec.get('priority', 'medium')
                category = rec.get('category', 'general')
                confidence = rec.get('confidence', 0.0)
                
                info_table = Table(show_header=False, box=None)
                info_table.add_column("Field", style="cyan", width=12)
                info_table.add_column("Value", style="white")
                
                info_table.add_row("Priority", priority.upper())
                info_table.add_row("Category", category)
                info_table.add_row("Confidence", f"{confidence:.1%}")
                
                self.console.print(info_table)
                
                # Description
                if rec.get('description'):
                    self.console.print(f"\n[white]{rec['description']}[/white]")
                
                # Implementation guide
                impl_guide = rec.get('implementation_guide', [])
                if impl_guide:
                    self.console.print(f"\n[yellow]🛠 Implementation Guide:[/yellow]")
                    for step in impl_guide[:3]:  # Show first 3 steps
                        self.console.print(f"  {step.get('step_number', '?')}. {step.get('title', 'Untitled')}")
                        if step.get('description'):
                            self.console.print(f"     [dim]{step['description']}[/dim]")
                
                # Automated fixes
                auto_fixes = rec.get('automated_fixes', [])
                if auto_fixes:
                    self.console.print(f"\n[green]⚡ Automated Fix Available[/green]")
                    fix = auto_fixes[0]
                    self.console.print(f"   Confidence: {fix.get('confidence', 0):.1%}")
                    self.console.print(f"   Risk Level: {fix.get('risk_level', 'unknown')}")
                
                # Examples
                examples = rec.get('examples', [])
                if examples:
                    self.console.print(f"\n[blue]💡 Example:[/blue]")
                    example = examples[0]
                    if example.get('before'):
                        self.console.print("   Before:")
                        self.console.print(f"   [red]{example['before']}[/red]")
                    if example.get('after'):
                        self.console.print("   After:")
                        self.console.print(f"   [green]{example['after']}[/green]")
                
                if j < len(recommendations) - 1:
                    input("\nPress Enter to continue to next recommendation...")
    
    async def _monitor_workflow_progress(self, workflow_id: str):
        """Monitor workflow progress in real-time."""
        self.console.print(f"\n[cyan]Monitoring workflow: {workflow_id}[/cyan]")
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console
        ) as progress:
            
            task = progress.add_task("Monitoring workflow...", total=None)
            
            while True:
                try:
                    status = await self.workflow_service.get_workflow_status(workflow_id)
                    
                    if "error" in status:
                        progress.update(task, description=f"Error: {status['error']}")
                        break
                    
                    current_status = status.get("status", "unknown")
                    current_phase = status.get("phase", "unknown")
                    
                    progress.update(task, description=f"Status: {current_status} | Phase: {current_phase}")
                    
                    if current_status in ["completed", "failed", "cancelled"]:
                        break
                    
                    await asyncio.sleep(10)  # Check every 10 seconds
                    
                except KeyboardInterrupt:
                    self.console.print("\n[yellow]Monitoring stopped (workflow continues in background)[/yellow]")
                    break
                except Exception as e:
                    self.console.print(f"\n[red]Monitoring error: {e}[/red]")
                    break
        
        # Show final status
        await self._show_workflow_status(workflow_id)
    
    async def _show_workflow_status(self, workflow_id: str):
        """Show detailed workflow status."""
        try:
            status = await self.workflow_service.get_workflow_status(workflow_id)
            
            if "error" in status:
                self.console.print(f"[red]Workflow not found: {workflow_id}[/red]")
                return
            
            self.console.print(f"\n[bold]📊 Workflow Status: {workflow_id}[/bold]")
            
            status_table = Table(show_header=False, box=None)
            status_table.add_column("Field", style="cyan", width=15)
            status_table.add_column("Value", style="white")
            
            status_table.add_row("Status", status.get("status", "unknown"))
            status_table.add_row("Phase", status.get("phase", "unknown"))
            status_table.add_row("Execution Time", f"{status.get('execution_time', 0):.2f}s")
            
            if status.get("completed_at"):
                status_table.add_row("Completed At", status["completed_at"])
            
            self.console.print(status_table)
            
            # Show results if completed
            if status.get("status") == "completed" and status.get("results"):
                results = status["results"]
                self.console.print(f"\n[green]✅ Workflow completed successfully![/green]")
                
                # Summary of what was accomplished
                accomplishments = []
                if results.get("research"):
                    accomplishments.append("📝 Standard researched and created")
                if results.get("documentation"):
                    accomplishments.append("📚 Comprehensive documentation generated")
                if results.get("validation"):
                    accomplishments.append("✅ Quality validation performed")
                if results.get("deployment"):
                    accomplishments.append("🚀 Standard deployed to systems")
                if results.get("analysis"):
                    accomplishments.append("🔍 Code analysis completed")
                if results.get("feedback"):
                    accomplishments.append("💡 Feedback and recommendations generated")
                
                self.console.print("\n[yellow]Accomplishments:[/yellow]")
                for accomplishment in accomplishments:
                    self.console.print(f"  • {accomplishment}")
                
                # Show key metrics
                if results.get("analysis"):
                    analysis = results["analysis"]
                    self.console.print(f"\n[yellow]Analysis Results:[/yellow]")
                    self.console.print(f"  • Code Samples: {analysis.get('total_samples', 0)}")
                    self.console.print(f"  • Overall Compliance: {analysis.get('overall_compliance', 0):.1f}%")
                    self.console.print(f"  • Recommendations: {analysis.get('aggregate_analysis', {}).get('total_recommendations', 0)}")
                
                if Confirm.ask("\n[yellow]Would you like to see the detailed results?[/yellow]"):
                    self._display_workflow_results(results)
                    
        except Exception as e:
            self.console.print(f"[red]Failed to get workflow status: {e}[/red]")
    
    def _display_workflow_results(self, results: Dict[str, Any]):
        """Display detailed workflow results."""
        self.console.print("\n[bold]📋 Detailed Workflow Results[/bold]")
        
        # Research results
        if results.get("research"):
            research = results["research"]
            self.console.print(f"\n[cyan]🔬 Research Results:[/cyan]")
            if research.get("standard"):
                standard = research["standard"]
                self.console.print(f"  • Title: {standard.get('title', 'N/A')}")
                self.console.print(f"  • Category: {standard.get('category', 'N/A')}")
                self.console.print(f"  • Version: {standard.get('version', 'N/A')}")
                
                validation = standard.get("validation", {})
                if validation:
                    score = validation.get("score", 0)
                    self.console.print(f"  • Quality Score: {score}/100")
        
        # Analysis results
        if results.get("analysis"):
            analysis = results["analysis"]
            self.console.print(f"\n[cyan]🔍 Analysis Results:[/cyan]")
            
            individual_analyses = analysis.get("individual_analyses", [])
            for i, sample_analysis in enumerate(individual_analyses):
                compliance = sample_analysis.get("compliance_score", 0)
                rec_count = len(sample_analysis.get("analysis", {}).get("recommendations", []))
                self.console.print(f"  • Sample {i+1}: {compliance:.1f}% compliance, {rec_count} recommendations")
        
        # Feedback
        if results.get("feedback"):
            feedback_data = results["feedback"].get("feedback", {})
            if feedback_data.get("next_steps"):
                self.console.print(f"\n[cyan]🎯 Next Steps:[/cyan]")
                for step in feedback_data["next_steps"][:5]:
                    self.console.print(f"  • {step}")
    
    async def _show_system_status(self):
        """Show overall system status."""
        self.console.print("\n[bold]🏥 System Health Status[/bold]")
        
        # Service statistics
        try:
            workflow_stats = self.workflow_service.get_service_statistics()
            
            stats_table = Table(show_header=False, box=None)
            stats_table.add_column("Service", style="cyan", width=20)
            stats_table.add_column("Status", style="green")
            stats_table.add_column("Statistics", style="white")
            
            stats_table.add_row(
                "Workflow Service", 
                "🟢 Active",
                f"Workflows: {workflow_stats.get('completed_workflows', 0)} completed"
            )
            
            recommendations_stats = self.recommendations_service.get_service_stats()
            stats_table.add_row(
                "Recommendations Service",
                "🟢 Active", 
                f"Generated: {recommendations_stats.get('statistics', {}).get('recommendations_generated', 0)}"
            )
            
            self.console.print(stats_table)
            
            # Active workflows
            if self.active_workflows:
                self.console.print(f"\n[yellow]Active Workflows ({len(self.active_workflows)}):[/yellow]")
                for workflow_id, info in self.active_workflows.items():
                    self.console.print(f"  • {workflow_id[:8]}... - {info['request'][:50]}...")
        
        except Exception as e:
            self.console.print(f"[red]Failed to get system status: {e}[/red]")
    
    async def _browse_standards(self):
        """Browse the standards library."""
        self.console.print("\n[cyan]📚 Standards Library Browser[/cyan]")
        
        standards_dir = Path("/Volumes/FS001/pythonscripts/standards")
        if not standards_dir.exists():
            self.console.print("[yellow]No standards directory found[/yellow]")
            return
        
        tree = Tree("📚 Standards Library")
        
        for category_dir in standards_dir.iterdir():
            if category_dir.is_dir() and not category_dir.name.startswith("."):
                branch = tree.add(f"📁 {category_dir.name}")
                
                for file in category_dir.glob("*.md"):
                    file_stats = file.stat()
                    size_kb = file_stats.st_size / 1024
                    branch.add(f"📄 {file.stem} ({size_kb:.1f}KB)")
        
        self.console.print(tree)
    
    async def _search_standards(self):
        """Search for standards."""
        query = Prompt.ask("\n[yellow]Enter search query[/yellow]")
        if not query:
            return
        
        self.console.print(f"\n[cyan]🔍 Searching for: '{query}'[/cyan]")
        self.console.print("[dim]Search functionality will be implemented with Neo4j integration[/dim]")
    
    async def _create_standard(self):
        """Create a new standard."""
        self.console.print("\n[cyan]✨ Create New Standard[/cyan]")
        self.console.print("[dim]Launching conversational research interface...[/dim]\n")
        
        await self.conversational_interface.run_conversational_research()
    
    async def _validate_standard(self):
        """Validate an existing standard."""
        self.console.print("\n[cyan]✅ Standard Validation[/cyan]")
        self.console.print("[dim]Standard validation functionality coming soon![/dim]")
    
    async def _agent_context_search(self):
        """Perform agent context search."""
        self.console.print("\n[cyan]🤖 Agent Context Search[/cyan]")
        
        query = Prompt.ask("Search query")
        context_type = Prompt.ask(
            "Context type",
            choices=["code_review", "development", "refactoring", "testing"],
            default="development"
        )
        language = Prompt.ask("Programming language", default="python")
        
        self.console.print(f"\n[dim]Searching for '{query}' in {context_type} context for {language}...[/dim]")
        self.console.print("[yellow]Agent context search implementation coming soon![/yellow]")
    
    async def _agent_batch_analysis(self):
        """Perform batch analysis."""
        self.console.print("\n[cyan]📊 Agent Batch Analysis[/cyan]")
        
        file_path = Prompt.ask("Enter directory or file path")
        if not file_path:
            return
        
        path = Path(file_path)
        if not path.exists():
            self.console.print(f"[red]Path not found: {file_path}[/red]")
            return
        
        self.console.print(f"[dim]Batch analyzing files in: {path}[/dim]")
        self.console.print("[yellow]Batch analysis implementation coming soon![/yellow]")
    
    async def run_interactive_cli(self):
        """Run the main interactive CLI."""
        self.display_welcome()
        
        while True:
            try:
                self.display_main_menu()
                
                command = Prompt.ask(
                    "\n[bold cyan]enhanced-cli>[/bold cyan]",
                    choices=["research", "workflow", "analyze", "standards", "agent", "status", "help", "exit"],
                    default="help"
                ).lower()
                
                if command == "exit":
                    self.console.print("\n[yellow]Thank you for using the Enhanced Code Standards Auditor! 👋[/yellow]\n")
                    break
                
                elif command == "help":
                    self.display_welcome()
                
                elif command == "research":
                    await self.handle_research_command()
                
                elif command == "workflow":
                    await self.handle_workflow_command()
                
                elif command == "analyze":
                    await self.handle_analyze_command()
                
                elif command == "standards":
                    await self.handle_standards_command()
                
                elif command == "agent":
                    await self.handle_agent_command()
                
                elif command == "status":
                    workflow_id = Prompt.ask("Workflow ID (optional)", default="")
                    await self.handle_status_command(workflow_id if workflow_id else None)
                
            except KeyboardInterrupt:
                self.console.print("\n[yellow]Use 'exit' to quit properly[/yellow]")
            except Exception as e:
                logger.error(f"CLI error: {e}")
                self.console.print(f"[red]Error: {e}[/red]")


@click.group()
def cli():
    """Enhanced Code Standards Auditor CLI v2.0"""
    pass


@cli.command()
@click.option("--debug", is_flag=True, help="Enable debug logging")
def interactive(debug: bool):
    """Start the interactive enhanced CLI."""
    if debug:
        logging.basicConfig(level=logging.DEBUG)
    
    enhanced_cli = EnhancedCLI()
    asyncio.run(enhanced_cli.run_interactive_cli())


@cli.command()
@click.argument("request")
@click.option("--code-file", multiple=True, help="Code files to analyze")
@click.option("--language", default="auto", help="Programming language")
def workflow(request: str, code_file: List[str], language: str):
    """Start an integrated workflow from command line."""
    console.print(f"[cyan]Starting workflow: {request}[/cyan]")
    
    # Read code files
    code_samples = []
    for file_path in code_file:
        try:
            with open(file_path, 'r') as f:
                code_samples.append(f.read())
        except Exception as e:
            console.print(f"[red]Error reading {file_path}: {e}[/red]")
    
    async def run_workflow():
        workflow_service = IntegratedWorkflowService()
        workflow_id = await workflow_service.start_research_to_analysis_workflow(
            research_request=request,
            code_samples=code_samples
        )
        console.print(f"[green]Workflow started: {workflow_id}[/green]")
    
    asyncio.run(run_workflow())


@cli.command()
@click.argument("code-file")
@click.option("--language", default="auto", help="Programming language")
@click.option("--focus", multiple=True, help="Analysis focus areas")
def analyze(code_file: str, language: str, focus: List[str]):
    """Analyze code file with enhanced recommendations."""
    console.print(f"[cyan]Analyzing: {code_file}[/cyan]")
    
    try:
        with open(code_file, 'r') as f:
            code = f.read()
    except Exception as e:
        console.print(f"[red]Error reading file: {e}[/red]")
        return
    
    async def run_analysis():
        service = EnhancedRecommendationsService()
        result = await service.generate_enhanced_recommendations(
            code=code,
            language=language if language != "auto" else "python",
            focus_areas=list(focus) if focus else None
        )
        
        console.print(f"[green]Analysis completed![/green]")
        console.print(f"Recommendations: {len(result.get('recommendations', []))}")
        
        # Show summary
        for i, rec in enumerate(result.get('recommendations', [])[:3]):
            console.print(f"{i+1}. {rec.get('title', 'Untitled')}")
    
    asyncio.run(run_analysis())


if __name__ == "__main__":
    cli()
