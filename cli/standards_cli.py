#!/usr/bin/env python3
"""
Interactive Standards Research CLI

This tool provides an interactive command-line interface for researching
and creating new coding standards using natural language requests.

Author: Code Standards Auditor
Date: December 31, 2024
Version: 1.0.0
"""

import os
import sys
import json
import asyncio
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.markdown import Markdown
from rich.syntax import Syntax
from rich.tree import Tree

from services.standards_research_service import StandardsResearchService
from services.gemini_service import GeminiService
from services.neo4j_service import Neo4jService
from services.cache_service import CacheService
from config.settings import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Rich console
console = Console()


class StandardCategory(Enum):
    """Categories for standards research."""
    GENERAL = "general"
    LANGUAGE = "language_specific"
    PATTERN = "pattern"
    SECURITY = "security"
    PERFORMANCE = "performance"
    TESTING = "testing"
    DOCUMENTATION = "documentation"
    ARCHITECTURE = "architecture"


class StandardsCLI:
    """Interactive CLI for standards research and management."""
    
    def __init__(self):
        """Initialize the CLI with necessary services."""
        self.console = console
        self.research_service = StandardsResearchService()
        self.gemini_service = GeminiService()
        
        # Initialize Neo4j if enabled
        self.neo4j_service = None
        if settings.USE_NEO4J:
            try:
                self.neo4j_service = Neo4jService()
            except Exception as e:
                logger.warning(f"Neo4j not available: {e}")
        
        # Initialize cache if enabled
        self.cache_service = None
        if settings.USE_CACHE:
            try:
                self.cache_service = CacheService()
            except Exception as e:
                logger.warning(f"Cache not available: {e}")
    
    def display_welcome(self):
        """Display welcome message and instructions."""
        welcome_text = """
        # 🚀 Code Standards Research Assistant
        
        Welcome to the interactive standards research tool!
        
        This assistant helps you:
        - **Research** new coding standards using AI
        - **Discover** patterns in existing code
        - **Generate** comprehensive documentation
        - **Validate** and improve standards
        
        ## Available Commands:
        - `research` - Research a new standard
        - `discover` - Discover patterns from code
        - `validate` - Validate existing standard
        - `list` - List existing standards
        - `help` - Show this help message
        - `exit` - Exit the tool
        """
        
        panel = Panel(
            Markdown(welcome_text),
            title="Code Standards Research CLI",
            border_style="blue"
        )
        self.console.print(panel)
    
    def get_natural_language_input(self) -> Dict[str, Any]:
        """Get standard requirements through natural language."""
        self.console.print("\n[bold cyan]Let's create a new standard![/bold cyan]\n")
        
        # Get the main request
        request = Prompt.ask(
            "[yellow]What standard would you like to research?[/yellow]\n"
            "(Example: 'API error handling best practices for Python')"
        )
        
        # Parse the request using Gemini
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console
        ) as progress:
            task = progress.add_task("Analyzing your request...", total=None)
            
            analysis_prompt = f"""
            Analyze this coding standard request and extract key information:
            Request: "{request}"
            
            Return a JSON object with:
            {{
                "title": "Clear title for the standard",
                "category": "One of: general, language_specific, pattern, security, performance, testing, documentation, architecture",
                "language": "Programming language if specific, or 'general'",
                "description": "Brief description of what the standard should cover",
                "key_topics": ["List", "of", "key", "topics"],
                "examples_needed": true/false
            }}
            
            Return ONLY the JSON object, no additional text.
            """
            
            try:
                response = self.gemini_service.generate_content(analysis_prompt)
                analysis = json.loads(response)
                progress.update(task, completed=True)
            except Exception as e:
                logger.error(f"Failed to analyze request: {e}")
                analysis = {
                    "title": request,
                    "category": "general",
                    "language": "general",
                    "description": request,
                    "key_topics": [],
                    "examples_needed": True
                }
        
        # Show analysis and allow refinement
        self.console.print("\n[bold]Understood! Here's what I gathered:[/bold]")
        
        table = Table(show_header=False, box=None)
        table.add_column("Field", style="cyan")
        table.add_column("Value", style="white")
        
        table.add_row("Title", analysis.get("title", request))
        table.add_row("Category", analysis.get("category", "general"))
        table.add_row("Language", analysis.get("language", "general"))
        table.add_row("Description", analysis.get("description", ""))
        table.add_row("Key Topics", ", ".join(analysis.get("key_topics", [])))
        
        self.console.print(table)
        
        # Ask for confirmation or refinement
        if not Confirm.ask("\n[yellow]Is this correct?[/yellow]"):
            analysis = self.refine_analysis(analysis)
        
        # Get additional context
        analysis["context"] = {}
        
        if Confirm.ask("\n[yellow]Would you like to provide code examples?[/yellow]"):
            analysis["examples"] = self.get_code_examples()
        else:
            analysis["examples"] = []
        
        if Confirm.ask("\n[yellow]Any specific requirements or constraints?[/yellow]"):
            requirements = Prompt.ask("Please describe them")
            analysis["context"]["requirements"] = requirements
        
        return analysis
    
    def refine_analysis(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Allow user to refine the analysis."""
        self.console.print("\n[cyan]Let's refine the details:[/cyan]")
        
        # Allow editing each field
        analysis["title"] = Prompt.ask(
            "Title", 
            default=analysis.get("title", "")
        )
        
        # Category selection
        self.console.print("\n[yellow]Available categories:[/yellow]")
        for i, cat in enumerate(StandardCategory, 1):
            self.console.print(f"  {i}. {cat.value}")
        
        cat_choice = Prompt.ask(
            "Choose category (1-8)", 
            default="1"
        )
        try:
            category_index = int(cat_choice) - 1
            analysis["category"] = list(StandardCategory)[category_index].value
        except (ValueError, IndexError):
            analysis["category"] = "general"
        
        analysis["language"] = Prompt.ask(
            "Programming language",
            default=analysis.get("language", "general")
        )
        
        analysis["description"] = Prompt.ask(
            "Description",
            default=analysis.get("description", "")
        )
        
        # Key topics
        topics_str = Prompt.ask(
            "Key topics (comma-separated)",
            default=", ".join(analysis.get("key_topics", []))
        )
        analysis["key_topics"] = [t.strip() for t in topics_str.split(",")]
        
        return analysis
    
    def get_code_examples(self) -> List[str]:
        """Get code examples from the user."""
        examples = []
        self.console.print("\n[cyan]Please provide code examples:[/cyan]")
        self.console.print("[dim]Enter code, then type 'END' on a new line to finish each example.[/dim]")
        self.console.print("[dim]Type 'DONE' when you've added all examples.[/dim]\n")
        
        while True:
            if examples:
                if not Confirm.ask(f"\n[yellow]Add another example? ({len(examples)} added)[/yellow]"):
                    break
            
            self.console.print(f"\n[cyan]Example {len(examples) + 1}:[/cyan]")
            lines = []
            while True:
                line = input()
                if line == "END":
                    break
                if line == "DONE":
                    if lines:
                        examples.append("\n".join(lines))
                    return examples
                lines.append(line)
            
            if lines:
                examples.append("\n".join(lines))
                self.console.print(f"[green]✓ Example {len(examples)} added[/green]")
        
        return examples
    
    async def research_standard(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Research and create a new standard."""
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console
        ) as progress:
            task = progress.add_task("Researching standard...", total=100)
            
            try:
                # Call research service
                result = await self.research_service.research_standard(
                    topic=request_data["title"],
                    category=request_data.get("category", "general"),
                    context=request_data.get("context", {}),
                    examples=request_data.get("examples", [])
                )
                
                progress.update(task, advance=50)
                
                # Validate the standard
                if result.get("content"):
                    validation = await self.research_service.validate_standard(
                        result["content"]
                    )
                    result["validation"] = validation
                
                progress.update(task, completed=100)
                
                return result
                
            except Exception as e:
                logger.error(f"Research failed: {e}")
                raise
    
    def display_standard(self, standard: Dict[str, Any]):
        """Display the researched standard."""
        self.console.print("\n" + "="*80)
        self.console.print(f"\n[bold green]✨ Standard Created Successfully![/bold green]\n")
        
        # Display metadata
        metadata_table = Table(title="Standard Metadata", show_header=False)
        metadata_table.add_column("Field", style="cyan")
        metadata_table.add_column("Value", style="white")
        
        metadata_table.add_row("ID", standard.get("id", "N/A"))
        metadata_table.add_row("Title", standard.get("title", "N/A"))
        metadata_table.add_row("Category", standard.get("category", "N/A"))
        metadata_table.add_row("Version", standard.get("version", "1.0.0"))
        metadata_table.add_row("Status", standard.get("status", "draft"))
        metadata_table.add_row("Created", standard.get("created_at", "N/A"))
        
        self.console.print(metadata_table)
        
        # Display validation score if available
        if "validation" in standard:
            validation = standard["validation"]
            score = validation.get("score", 0)
            
            score_color = "green" if score >= 80 else "yellow" if score >= 60 else "red"
            self.console.print(f"\n[bold]Quality Score:[/bold] [{score_color}]{score}/100[/{score_color}]")
            
            if validation.get("improvements"):
                self.console.print("\n[yellow]Suggested Improvements:[/yellow]")
                for imp in validation["improvements"]:
                    self.console.print(f"  • {imp}")
        
        # Display content preview
        self.console.print("\n[bold]Content Preview:[/bold]")
        content = standard.get("content", "")
        if content:
            # Show first 500 characters
            preview = content[:500] + "..." if len(content) > 500 else content
            self.console.print(Panel(
                Markdown(preview),
                title="Standard Content",
                border_style="blue"
            ))
    
    def save_standard(self, standard: Dict[str, Any]):
        """Save the standard to file and optionally to Neo4j."""
        # Determine save path
        standards_dir = Path("/Volumes/FS001/pythonscripts/standards")
        category = standard.get("category", "general")
        language = standard.get("language", "general")
        
        if language != "general":
            save_dir = standards_dir / language
        else:
            save_dir = standards_dir / category
        
        save_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        title_slug = standard.get("title", "standard").lower().replace(" ", "_")[:50]
        filename = f"{title_slug}_{timestamp}.md"
        filepath = save_dir / filename
        
        # Save to file
        try:
            with open(filepath, "w") as f:
                f.write(standard.get("content", ""))
            
            self.console.print(f"\n[green]✓ Standard saved to:[/green] {filepath}")
            
            # Save to Neo4j if available
            if self.neo4j_service and Confirm.ask("\n[yellow]Save to Neo4j database?[/yellow]"):
                neo4j_result = self.neo4j_service.create_standard(
                    standard_id=standard.get("id"),
                    name=standard.get("title"),
                    category=standard.get("category"),
                    content=standard.get("content"),
                    version=standard.get("version", "1.0.0"),
                    metadata=standard.get("metadata", {})
                )
                if neo4j_result:
                    self.console.print("[green]✓ Standard saved to Neo4j[/green]")
            
            return filepath
            
        except Exception as e:
            logger.error(f"Failed to save standard: {e}")
            self.console.print(f"[red]✗ Failed to save standard: {e}[/red]")
            return None
    
    def run_interactive(self):
        """Run the interactive CLI."""
        self.display_welcome()
        
        while True:
            try:
                # Get command
                command = Prompt.ask(
                    "\n[bold cyan]standards>[/bold cyan]",
                    choices=["research", "discover", "validate", "list", "help", "exit"],
                    default="help"
                ).lower()
                
                if command == "exit":
                    self.console.print("\n[yellow]Goodbye! 👋[/yellow]\n")
                    break
                
                elif command == "help":
                    self.display_welcome()
                
                elif command == "research":
                    # Get requirements through natural language
                    request_data = self.get_natural_language_input()
                    
                    # Research the standard
                    self.console.print("\n[bold]Starting research...[/bold]")
                    standard = asyncio.run(self.research_standard(request_data))
                    
                    # Display results
                    self.display_standard(standard)
                    
                    # Ask to save
                    if Confirm.ask("\n[yellow]Would you like to save this standard?[/yellow]"):
                        self.save_standard(standard)
                    
                    # Ask for iterations
                    if Confirm.ask("\n[yellow]Would you like to refine this standard?[/yellow]"):
                        self.console.print("[cyan]Refinement feature coming soon![/cyan]")
                
                elif command == "discover":
                    self.console.print("[cyan]Pattern discovery feature coming soon![/cyan]")
                
                elif command == "validate":
                    self.console.print("[cyan]Validation feature coming soon![/cyan]")
                
                elif command == "list":
                    self.list_standards()
                
            except KeyboardInterrupt:
                self.console.print("\n[yellow]Use 'exit' to quit[/yellow]")
            except Exception as e:
                logger.error(f"Error: {e}")
                self.console.print(f"[red]Error: {e}[/red]")
    
    def list_standards(self):
        """List existing standards."""
        standards_dir = Path("/Volumes/FS001/pythonscripts/standards")
        
        if not standards_dir.exists():
            self.console.print("[yellow]No standards directory found[/yellow]")
            return
        
        # Build tree of standards
        tree = Tree("📚 Standards Library")
        
        for category_dir in standards_dir.iterdir():
            if category_dir.is_dir() and not category_dir.name.startswith("."):
                branch = tree.add(f"📁 {category_dir.name}")
                
                for file in category_dir.glob("*.md"):
                    branch.add(f"📄 {file.name}")
        
        self.console.print(tree)


@click.command()
@click.option(
    "--mode",
    type=click.Choice(["interactive", "single"], case_sensitive=False),
    default="interactive",
    help="Mode of operation"
)
@click.option(
    "--topic",
    help="Topic for single research mode"
)
@click.option(
    "--category",
    type=click.Choice([c.value for c in StandardCategory]),
    default="general",
    help="Category for the standard"
)
def main(mode: str, topic: Optional[str], category: str):
    """
    Interactive Standards Research CLI
    
    Research and create new coding standards using AI.
    """
    cli = StandardsCLI()
    
    if mode == "interactive":
        cli.run_interactive()
    elif mode == "single" and topic:
        # Single research mode
        console.print(f"[cyan]Researching: {topic}[/cyan]")
        request_data = {
            "title": topic,
            "category": category,
            "context": {},
            "examples": []
        }
        standard = asyncio.run(cli.research_standard(request_data))
        cli.display_standard(standard)
        
        if Confirm.ask("\n[yellow]Save this standard?[/yellow]"):
            cli.save_standard(standard)
    else:
        console.print("[red]Error: --topic required for single mode[/red]")
        raise click.Abort()


if __name__ == "__main__":
    main()
