#!/usr/bin/env python3
"""
Enhanced Conversational Standards Research Interface

This module provides an advanced conversational interface for researching
and creating coding standards through natural language interaction.

Author: Code Standards Auditor
Date: September 01, 2025
Version: 2.0.0
"""

import os
import sys
import json
import asyncio
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from dataclasses import dataclass, asdict
from enum import Enum
import uuid

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.markdown import Markdown
from rich.syntax import Syntax
from rich.tree import Tree
from rich.live import Live
from rich.layout import Layout
from rich.text import Text
from rich.columns import Columns

from services.standards_research_service import StandardsResearchService
from services.recommendations_service import RecommendationsService
from services.gemini_service import GeminiService
from services.neo4j_service import Neo4jService
from services.cache_service import CacheService
from config.settings import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class ConversationContext:
    """Context for maintaining conversation state."""
    session_id: str
    current_research: Optional[Dict[str, Any]] = None
    conversation_history: List[Dict[str, Any]] = None
    user_preferences: Dict[str, Any] = None
    active_standards: List[str] = None
    
    def __post_init__(self):
        if self.conversation_history is None:
            self.conversation_history = []
        if self.user_preferences is None:
            self.user_preferences = {}
        if self.active_standards is None:
            self.active_standards = []


class ResearchPhase(Enum):
    """Phases of the research process."""
    INITIAL_REQUEST = "initial_request"
    REQUIREMENTS_GATHERING = "requirements_gathering"
    RESEARCH_EXECUTION = "research_execution"
    REVIEW_AND_REFINEMENT = "review_and_refinement"
    VALIDATION = "validation"
    FINALIZATION = "finalization"


class ConversationalResearchInterface:
    """Enhanced conversational interface for standards research."""
    
    def __init__(self):
        """Initialize the conversational interface."""
        self.console = Console()
        self.research_service = StandardsResearchService()
        self.recommendations_service = RecommendationsService()
        self.gemini_service = GeminiService()
        
        # Initialize services
        self.neo4j_service = None
        if settings.USE_NEO4J:
            try:
                self.neo4j_service = Neo4jService()
            except Exception as e:
                logger.warning(f"Neo4j not available: {e}")
        
        self.cache_service = None
        if settings.USE_CACHE:
            try:
                self.cache_service = CacheService()
            except Exception as e:
                logger.warning(f"Cache not available: {e}")
        
        # Conversation state
        self.context = ConversationContext(session_id=str(uuid.uuid4()))
        self.current_phase = ResearchPhase.INITIAL_REQUEST
        
        # Research assistant persona
        self.assistant_persona = """
        You are an expert coding standards research assistant. Your role is to:
        1. Understand user requirements through natural conversation
        2. Ask clarifying questions to gather comprehensive requirements
        3. Research and generate high-quality coding standards
        4. Provide iterative feedback and refinement
        5. Ensure standards are practical and implementable
        
        Maintain a helpful, professional, and collaborative tone.
        Ask one question at a time to avoid overwhelming the user.
        """
    
    def display_welcome(self):
        """Display enhanced welcome message."""
        layout = Layout()
        layout.split_column(
            Layout(name="header", size=8),
            Layout(name="features", size=12),
            Layout(name="instructions", size=6)
        )
        
        # Header
        header_text = Text()
        header_text.append("🚀 Enhanced Standards Research Assistant", style="bold cyan")
        header_text.append("\nVersion 2.0 - Conversational AI Interface", style="dim")
        header_text.append(f"\nSession ID: {self.context.session_id}", style="blue")
        
        layout["header"].update(Panel(header_text, title="Welcome", border_style="cyan"))
        
        # Features
        features = [
            "🧠 **AI-Powered Research** - Natural language standard generation",
            "💬 **Conversational Flow** - Multi-turn requirements gathering",
            "🔄 **Iterative Refinement** - Collaborative standard improvement",
            "📊 **Quality Validation** - Automatic quality scoring and feedback",
            "🎯 **Context Awareness** - Learns from your preferences and history",
            "🔗 **Smart Integration** - Connects with existing codebase patterns"
        ]
        
        features_text = "\n".join(features)
        layout["features"].update(
            Panel(Markdown(features_text), title="Capabilities", border_style="green")
        )
        
        # Instructions
        instructions = """
        **Getting Started:**
        - Simply describe what standard you need in natural language
        - The assistant will guide you through the research process
        - Provide code examples, constraints, or specific requirements as needed
        - Review and refine the generated standards interactively
        """
        
        layout["instructions"].update(
            Panel(Markdown(instructions), title="Instructions", border_style="yellow")
        )
        
        self.console.print(layout)
    
    async def analyze_user_request(self, request: str) -> Dict[str, Any]:
        """Analyze user request using AI to extract requirements."""
        analysis_prompt = f"""
        {self.assistant_persona}
        
        The user has made the following request for a coding standard:
        "{request}"
        
        Previous conversation context: {json.dumps(self.context.conversation_history[-3:] if len(self.context.conversation_history) > 3 else self.context.conversation_history, indent=2)}
        
        Please analyze this request and return a JSON object with:
        {{
            "title": "Clear, descriptive title for the standard",
            "category": "One of: general, language_specific, pattern, security, performance, testing, documentation, architecture",
            "language": "Programming language if specific, or 'general'",
            "description": "Brief description of what the standard should cover",
            "key_topics": ["Array of key topics to address"],
            "complexity_level": "One of: basic, intermediate, advanced, expert",
            "estimated_time": "Estimated research time in minutes",
            "confidence": "Confidence level from 0.0 to 1.0 in understanding the request",
            "clarifying_questions": ["Array of questions to better understand requirements"],
            "related_standards": ["Array of potentially related existing standards"],
            "examples_needed": true/false,
            "priority": "One of: low, medium, high, critical"
        }}
        
        Return ONLY the JSON object.
        """
        
        try:
            response = await self.gemini_service.generate_content_async(analysis_prompt)
            analysis = json.loads(response)
            
            # Store in conversation history
            self.context.conversation_history.append({
                "type": "user_request",
                "content": request,
                "timestamp": datetime.now().isoformat(),
                "analysis": analysis
            })
            
            return analysis
            
        except Exception as e:
            logger.error(f"Failed to analyze request: {e}")
            # Fallback analysis
            return {
                "title": request[:100],
                "category": "general",
                "language": "general",
                "description": request,
                "key_topics": [],
                "complexity_level": "intermediate",
                "estimated_time": "15-30",
                "confidence": 0.5,
                "clarifying_questions": ["Could you provide more specific details about your requirements?"],
                "related_standards": [],
                "examples_needed": True,
                "priority": "medium"
            }
    
    def display_analysis(self, analysis: Dict[str, Any]):
        """Display the request analysis in a structured format."""
        self.console.print("\n[bold]🧠 Request Analysis[/bold]\n")
        
        # Create layout for analysis
        layout = Layout()
        layout.split_row(
            Layout(name="left"),
            Layout(name="right")
        )
        
        # Left panel - Basic info
        left_table = Table(show_header=False, box=None, padding=(0, 1))
        left_table.add_column("Field", style="cyan", width=15)
        left_table.add_column("Value", style="white")
        
        left_table.add_row("Title", analysis.get("title", ""))
        left_table.add_row("Category", analysis.get("category", ""))
        left_table.add_row("Language", analysis.get("language", ""))
        left_table.add_row("Complexity", analysis.get("complexity_level", ""))
        left_table.add_row("Est. Time", f"{analysis.get('estimated_time', 'Unknown')} min")
        left_table.add_row("Priority", analysis.get("priority", "medium"))
        
        # Confidence indicator
        confidence = analysis.get("confidence", 0.5)
        confidence_color = "green" if confidence >= 0.8 else "yellow" if confidence >= 0.6 else "red"
        left_table.add_row("Confidence", f"[{confidence_color}]{confidence:.1%}[/{confidence_color}]")
        
        layout["left"].update(Panel(left_table, title="Basic Information", border_style="blue"))
        
        # Right panel - Additional info
        right_content = []
        
        if analysis.get("key_topics"):
            topics = ", ".join(analysis["key_topics"])
            right_content.append(f"**Key Topics:** {topics}")
        
        if analysis.get("description"):
            right_content.append(f"**Description:** {analysis['description']}")
        
        if analysis.get("related_standards"):
            standards = ", ".join(analysis["related_standards"])
            right_content.append(f"**Related Standards:** {standards}")
        
        right_text = "\n\n".join(right_content) if right_content else "No additional information available."
        
        layout["right"].update(
            Panel(Markdown(right_text), title="Details", border_style="green")
        )
        
        self.console.print(layout)
        
        # Show clarifying questions if any
        questions = analysis.get("clarifying_questions", [])
        if questions:
            self.console.print("\n[yellow]💭 Clarifying Questions:[/yellow]")
            for i, question in enumerate(questions, 1):
                self.console.print(f"   {i}. {question}")
    
    async def gather_requirements(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Gather detailed requirements through conversation."""
        self.console.print(f"\n[bold cyan]Phase 2: Requirements Gathering[/bold cyan]")
        self.current_phase = ResearchPhase.REQUIREMENTS_GATHERING
        
        requirements = {
            "basic_info": analysis,
            "examples": [],
            "constraints": [],
            "specific_requirements": [],
            "target_audience": "",
            "implementation_context": {}
        }
        
        # Ask clarifying questions
        questions = analysis.get("clarifying_questions", [])
        if questions and analysis.get("confidence", 0) < 0.8:
            self.console.print("\nLet me ask a few questions to better understand your needs:\n")
            
            for question in questions[:3]:  # Limit to top 3 questions
                answer = Prompt.ask(f"[yellow]❓ {question}[/yellow]")
                if answer:
                    requirements["specific_requirements"].append({
                        "question": question,
                        "answer": answer,
                        "timestamp": datetime.now().isoformat()
                    })
        
        # Gather code examples if needed
        if analysis.get("examples_needed", False):
            if Confirm.ask("\n[yellow]Would you like to provide code examples to guide the standard?[/yellow]"):
                requirements["examples"] = await self.gather_code_examples()
        
        # Gather constraints and preferences
        if Confirm.ask("\n[yellow]Do you have any specific constraints or preferences?[/yellow]"):
            constraints = Prompt.ask("Please describe them")
            requirements["constraints"].append({
                "description": constraints,
                "timestamp": datetime.now().isoformat()
            })
        
        # Target audience
        audience = Prompt.ask(
            "\n[yellow]Who is the primary audience for this standard?[/yellow]",
            default="development team",
            show_default=True
        )
        requirements["target_audience"] = audience
        
        # Implementation context
        context_questions = [
            ("team_size", "What's your team size?", "small (1-5)"),
            ("experience_level", "What's the team's experience level?", "intermediate"),
            ("existing_standards", "Do you have existing coding standards?", "some"),
            ("tools_used", "What development tools do you use?", "standard IDE")
        ]
        
        self.console.print("\n[cyan]Implementation Context (optional):[/cyan]")
        for key, question, default in context_questions:
            answer = Prompt.ask(f"  {question}", default=default)
            requirements["implementation_context"][key] = answer
        
        # Store requirements in context
        self.context.current_research = requirements
        self.context.conversation_history.append({
            "type": "requirements_gathered",
            "content": requirements,
            "timestamp": datetime.now().isoformat()
        })
        
        return requirements
    
    async def gather_code_examples(self) -> List[Dict[str, Any]]:
        """Gather code examples from the user."""
        examples = []
        self.console.print("\n[cyan]📝 Code Examples Collection[/cyan]")
        self.console.print("[dim]Provide examples of code that should follow (or violate) the standard.[/dim]\n")
        
        while True:
            if examples:
                if not Confirm.ask(f"\n[yellow]Add another example? ({len(examples)} added)[/yellow]"):
                    break
            
            example_type = Prompt.ask(
                f"\nExample {len(examples) + 1} - Type",
                choices=["good", "bad", "neutral"],
                default="good"
            )
            
            description = Prompt.ask("Description (optional)", default="")
            
            self.console.print("[dim]Enter your code (type 'END' on a new line when finished):[/dim]")
            lines = []
            while True:
                try:
                    line = input()
                    if line.strip() == "END":
                        break
                    lines.append(line)
                except EOFError:
                    break
            
            if lines:
                code = "\n".join(lines)
                language = Prompt.ask("Language", default="auto")
                
                examples.append({
                    "type": example_type,
                    "code": code,
                    "language": language,
                    "description": description,
                    "timestamp": datetime.now().isoformat()
                })
                
                # Show preview
                self.console.print(f"\n[green]✓ Example {len(examples)} added ({example_type})[/green]")
                if code:
                    try:
                        self.console.print(Syntax(code[:200] + "..." if len(code) > 200 else code, 
                                                language if language != "auto" else "text", 
                                                theme="monokai"))
                    except:
                        self.console.print(f"[dim]{code[:100]}...[/dim]")
        
        return examples
    
    async def execute_research(self, requirements: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the AI research process."""
        self.console.print(f"\n[bold cyan]Phase 3: AI Research Execution[/bold cyan]")
        self.current_phase = ResearchPhase.RESEARCH_EXECUTION
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console
        ) as progress:
            # Prepare research context
            research_task = progress.add_task("Preparing research context...", total=100)
            
            research_context = {
                "basic_info": requirements["basic_info"],
                "examples": requirements.get("examples", []),
                "constraints": requirements.get("constraints", []),
                "requirements": requirements.get("specific_requirements", []),
                "target_audience": requirements.get("target_audience", ""),
                "implementation_context": requirements.get("implementation_context", {}),
                "conversation_history": self.context.conversation_history
            }
            
            progress.update(research_task, advance=20)
            progress.update(research_task, description="Executing AI research...")
            
            try:
                # Call research service with enhanced context
                standard = await self.research_service.research_standard(
                    topic=requirements["basic_info"]["title"],
                    category=requirements["basic_info"].get("category", "general"),
                    context=research_context,
                    examples=[ex["code"] for ex in requirements.get("examples", [])]
                )
                
                progress.update(research_task, advance=60)
                progress.update(research_task, description="Validating standard quality...")
                
                # Validate the generated standard
                if standard.get("content"):
                    validation = await self.research_service.validate_standard(
                        standard["content"],
                        standard.get("category", "general")
                    )
                    standard["validation"] = validation
                
                progress.update(research_task, advance=20)
                progress.update(research_task, description="Research completed!")
                
                # Store in context
                self.context.current_research["generated_standard"] = standard
                self.context.conversation_history.append({
                    "type": "research_completed",
                    "content": standard,
                    "timestamp": datetime.now().isoformat()
                })
                
                return standard
                
            except Exception as e:
                logger.error(f"Research failed: {e}")
                progress.update(research_task, description=f"Research failed: {e}")
                raise
    
    def display_generated_standard(self, standard: Dict[str, Any]):
        """Display the generated standard with enhanced formatting."""
        self.console.print(f"\n[bold green]✨ Standard Generated Successfully![/bold green]\n")
        
        # Create layout
        layout = Layout()
        layout.split_column(
            Layout(name="metadata", size=8),
            Layout(name="validation", size=6),
            Layout(name="content", min_size=20)
        )
        
        # Metadata table
        metadata_table = Table(show_header=False, box=None)
        metadata_table.add_column("Field", style="cyan", width=12)
        metadata_table.add_column("Value", style="white")
        
        metadata_table.add_row("ID", standard.get("id", "N/A"))
        metadata_table.add_row("Title", standard.get("title", "N/A"))
        metadata_table.add_row("Category", standard.get("category", "N/A"))
        metadata_table.add_row("Version", standard.get("version", "1.0.0"))
        metadata_table.add_row("Status", standard.get("status", "draft"))
        metadata_table.add_row("Created", standard.get("created_at", "N/A"))
        
        layout["metadata"].update(
            Panel(metadata_table, title="📋 Standard Metadata", border_style="blue")
        )
        
        # Validation results
        validation_content = []
        if "validation" in standard:
            validation = standard["validation"]
            score = validation.get("score", 0)
            score_color = "green" if score >= 80 else "yellow" if score >= 60 else "red"
            
            validation_content.append(f"**Quality Score:** [{score_color}]{score}/100[/{score_color}]")
            
            if validation.get("strengths"):
                strengths = "\n".join(f"• {s}" for s in validation["strengths"][:3])
                validation_content.append(f"**Strengths:**\n{strengths}")
            
            if validation.get("improvements"):
                improvements = "\n".join(f"• {imp}" for imp in validation["improvements"][:3])
                validation_content.append(f"**Areas for Improvement:**\n{improvements}")
        else:
            validation_content.append("*Validation pending...*")
        
        validation_text = "\n\n".join(validation_content)
        layout["validation"].update(
            Panel(Markdown(validation_text), title="🎯 Quality Assessment", border_style="yellow")
        )
        
        # Content preview
        content = standard.get("content", "")
        if content:
            # Show structured preview
            content_preview = content[:1000] + "..." if len(content) > 1000 else content
            layout["content"].update(
                Panel(
                    Markdown(content_preview),
                    title="📄 Standard Content",
                    border_style="green"
                )
            )
        else:
            layout["content"].update(
                Panel("No content generated", title="📄 Standard Content", border_style="red")
            )
        
        self.console.print(layout)
    
    async def review_and_refine(self, standard: Dict[str, Any]) -> Dict[str, Any]:
        """Interactive review and refinement process."""
        self.console.print(f"\n[bold cyan]Phase 4: Review and Refinement[/bold cyan]")
        self.current_phase = ResearchPhase.REVIEW_AND_REFINEMENT
        
        refined_standard = standard.copy()
        
        while True:
            self.console.print("\n[yellow]Review Options:[/yellow]")
            self.console.print("1. 👀 View full standard")
            self.console.print("2. ✏️  Request specific changes")
            self.console.print("3. 🔄 Regenerate sections")
            self.console.print("4. ✅ Accept as-is")
            self.console.print("5. ❌ Start over")
            
            choice = Prompt.ask(
                "\nWhat would you like to do?",
                choices=["1", "2", "3", "4", "5"],
                default="1"
            )
            
            if choice == "1":
                self.display_full_standard(refined_standard)
            
            elif choice == "2":
                changes = Prompt.ask("\nDescribe the changes you'd like to make")
                refined_standard = await self.apply_changes(refined_standard, changes)
                self.display_generated_standard(refined_standard)
            
            elif choice == "3":
                section = Prompt.ask(
                    "\nWhich section would you like to regenerate?",
                    choices=["introduction", "guidelines", "examples", "rationale", "all"]
                )
                refined_standard = await self.regenerate_section(refined_standard, section)
                self.display_generated_standard(refined_standard)
            
            elif choice == "4":
                break
                
            elif choice == "5":
                if Confirm.ask("\nAre you sure you want to start over?"):
                    return None
        
        return refined_standard
    
    def display_full_standard(self, standard: Dict[str, Any]):
        """Display the complete standard content."""
        content = standard.get("content", "")
        if content:
            # Create a scrollable view
            self.console.print("\n" + "="*80)
            self.console.print(f"[bold]📄 Complete Standard: {standard.get('title', 'Untitled')}[/bold]")
            self.console.print("="*80)
            
            try:
                self.console.print(Markdown(content))
            except:
                self.console.print(content)
            
            self.console.print("="*80)
        else:
            self.console.print("[red]No content available[/red]")
        
        input("\nPress Enter to continue...")
    
    async def apply_changes(self, standard: Dict[str, Any], changes: str) -> Dict[str, Any]:
        """Apply user-requested changes to the standard."""
        refinement_prompt = f"""
        {self.assistant_persona}
        
        The user has requested changes to the following standard:
        
        **Current Standard:**
        {standard.get('content', '')}
        
        **Requested Changes:**
        {changes}
        
        **Conversation Context:**
        {json.dumps(self.context.conversation_history[-2:], indent=2)}
        
        Please update the standard content incorporating the requested changes.
        Return the updated markdown content only, maintaining the same structure and quality.
        """
        
        with Progress(
            SpinnerColumn(),
            TextColumn("Applying changes..."),
            console=self.console
        ) as progress:
            task = progress.add_task("Processing changes...", total=None)
            
            try:
                updated_content = await self.gemini_service.generate_content_async(refinement_prompt)
                
                # Update the standard
                updated_standard = standard.copy()
                updated_standard["content"] = updated_content
                updated_standard["updated_at"] = datetime.now().isoformat()
                updated_standard["version"] = self.increment_version(standard.get("version", "1.0.0"))
                
                # Re-validate
                validation = await self.research_service.validate_standard(
                    updated_content,
                    standard.get("category", "general")
                )
                updated_standard["validation"] = validation
                
                # Store in context
                self.context.conversation_history.append({
                    "type": "standard_refined",
                    "changes_requested": changes,
                    "content": updated_standard,
                    "timestamp": datetime.now().isoformat()
                })
                
                return updated_standard
                
            except Exception as e:
                logger.error(f"Failed to apply changes: {e}")
                self.console.print(f"[red]Failed to apply changes: {e}[/red]")
                return standard
    
    async def regenerate_section(self, standard: Dict[str, Any], section: str) -> Dict[str, Any]:
        """Regenerate a specific section of the standard."""
        # Implementation for regenerating specific sections
        self.console.print(f"[cyan]Regenerating {section} section...[/cyan]")
        
        # For now, return the same standard
        # In a full implementation, this would regenerate specific sections
        return standard
    
    def increment_version(self, version: str) -> str:
        """Increment the version number."""
        try:
            parts = version.split(".")
            parts[-1] = str(int(parts[-1]) + 1)
            return ".".join(parts)
        except:
            return "1.0.1"
    
    async def finalize_standard(self, standard: Dict[str, Any]) -> Optional[Path]:
        """Finalize and save the standard."""
        self.console.print(f"\n[bold cyan]Phase 5: Finalization[/bold cyan]")
        self.current_phase = ResearchPhase.FINALIZATION
        
        # Final validation
        self.console.print("\n[yellow]Final validation...[/yellow]")
        final_validation = await self.research_service.validate_standard(
            standard["content"],
            standard.get("category", "general")
        )
        standard["validation"] = final_validation
        
        # Display final summary
        self.display_final_summary(standard, final_validation)
        
        # Save options
        save_options = []
        if Confirm.ask("\n[yellow]Save to file system?[/yellow]", default=True):
            filepath = await self.save_to_file(standard)
            if filepath:
                save_options.append(("file", str(filepath)))
        
        if self.neo4j_service and Confirm.ask("\n[yellow]Save to Neo4j database?[/yellow]"):
            neo4j_result = await self.save_to_neo4j(standard)
            if neo4j_result:
                save_options.append(("neo4j", neo4j_result))
        
        # Update context with final result
        self.context.conversation_history.append({
            "type": "standard_finalized",
            "content": standard,
            "save_locations": save_options,
            "timestamp": datetime.now().isoformat()
        })
        
        return save_options[0][1] if save_options else None
    
    def display_final_summary(self, standard: Dict[str, Any], validation: Dict[str, Any]):
        """Display final summary of the research process."""
        self.console.print("\n[bold green]🎉 Standard Research Complete![/bold green]\n")
        
        # Summary statistics
        summary_table = Table(show_header=False, box=None)
        summary_table.add_column("Metric", style="cyan")
        summary_table.add_column("Value", style="white")
        
        content_length = len(standard.get("content", ""))
        session_duration = "N/A"  # Would calculate from session start time
        
        summary_table.add_row("Final Quality Score", f"{validation.get('score', 0)}/100")
        summary_table.add_row("Content Length", f"{content_length:,} characters")
        summary_table.add_row("Version", standard.get("version", "1.0.0"))
        summary_table.add_row("Refinement Iterations", str(len([h for h in self.context.conversation_history if h.get("type") == "standard_refined"])))
        summary_table.add_row("Session Duration", session_duration)
        
        self.console.print(Panel(summary_table, title="📊 Research Summary", border_style="green"))
    
    async def save_to_file(self, standard: Dict[str, Any]) -> Optional[Path]:
        """Save standard to file system."""
        try:
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
            title_slug = standard.get("title", "standard").lower()
            title_slug = "".join(c for c in title_slug if c.isalnum() or c in "_ ").replace(" ", "_")[:50]
            filename = f"{title_slug}_{timestamp}.md"
            filepath = save_dir / filename
            
            # Create comprehensive content
            full_content = self.create_full_standard_content(standard)
            
            # Save to file
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(full_content)
            
            self.console.print(f"[green]✓ Standard saved to: {filepath}[/green]")
            return filepath
            
        except Exception as e:
            logger.error(f"Failed to save standard: {e}")
            self.console.print(f"[red]✗ Failed to save standard: {e}[/red]")
            return None
    
    def create_full_standard_content(self, standard: Dict[str, Any]) -> str:
        """Create comprehensive content for the standard file."""
        metadata = standard.get("metadata", {})
        validation = standard.get("validation", {})
        
        header = f"""# {standard.get('title', 'Coding Standard')}

**Category:** {standard.get('category', 'general')}  
**Language:** {standard.get('language', 'general')}  
**Version:** {standard.get('version', '1.0.0')}  
**Status:** {standard.get('status', 'draft')}  
**Created:** {standard.get('created_at', datetime.now().isoformat())}  
**Session ID:** {self.context.session_id}  

**Quality Score:** {validation.get('score', 'N/A')}/100

---

"""
        
        content = standard.get("content", "")
        
        footer = f"""

---

## Metadata

**Research Context:**
- Target Audience: {self.context.current_research.get('target_audience', 'N/A')}
- Complexity Level: {self.context.current_research.get('basic_info', {}).get('complexity_level', 'N/A')}
- Research Duration: {len(self.context.conversation_history)} interactions

**Quality Assessment:**
"""
        
        if validation.get("strengths"):
            footer += "\n**Strengths:**\n"
            footer += "\n".join(f"- {s}" for s in validation["strengths"])
        
        if validation.get("improvements"):
            footer += "\n\n**Areas for Improvement:**\n"
            footer += "\n".join(f"- {imp}" for imp in validation["improvements"])
        
        footer += f"\n\n*Generated by Code Standards Auditor v2.0*  \n*Last updated: {datetime.now().isoformat()}*"
        
        return header + content + footer
    
    async def save_to_neo4j(self, standard: Dict[str, Any]) -> Optional[str]:
        """Save standard to Neo4j database."""
        try:
            result = await self.neo4j_service.create_standard(
                standard_id=standard.get("id"),
                name=standard.get("title"),
                category=standard.get("category"),
                content=standard.get("content"),
                version=standard.get("version", "1.0.0"),
                metadata={
                    **standard.get("metadata", {}),
                    "session_id": self.context.session_id,
                    "conversation_length": len(self.context.conversation_history),
                    "validation": standard.get("validation", {})
                }
            )
            
            if result:
                self.console.print("[green]✓ Standard saved to Neo4j[/green]")
                return standard.get("id")
            
        except Exception as e:
            logger.error(f"Failed to save to Neo4j: {e}")
            self.console.print(f"[red]✗ Failed to save to Neo4j: {e}[/red]")
        
        return None
    
    async def run_conversational_research(self):
        """Main conversational research workflow."""
        self.display_welcome()
        
        try:
            # Phase 1: Initial request
            self.console.print(f"\n[bold cyan]Phase 1: Initial Request[/bold cyan]")
            request = Prompt.ask(
                "\n[yellow]🚀 What coding standard would you like me to research for you?[/yellow]\n"
                "[dim](Describe it naturally - I'll understand and ask follow-up questions)[/dim]"
            )
            
            if not request:
                self.console.print("[red]No request provided. Exiting.[/red]")
                return
            
            # Analyze request
            analysis = await self.analyze_user_request(request)
            self.display_analysis(analysis)
            
            if not Confirm.ask("\n[yellow]Shall we proceed with this analysis?[/yellow]"):
                self.console.print("[yellow]Let's start over.[/yellow]")
                return await self.run_conversational_research()
            
            # Phase 2: Requirements gathering
            requirements = await self.gather_requirements(analysis)
            
            # Phase 3: Execute research
            standard = await self.execute_research(requirements)
            self.display_generated_standard(standard)
            
            # Phase 4: Review and refine
            refined_standard = await self.review_and_refine(standard)
            if not refined_standard:
                self.console.print("[yellow]Research cancelled. Starting over...[/yellow]")
                return await self.run_conversational_research()
            
            # Phase 5: Finalize
            save_location = await self.finalize_standard(refined_standard)
            
            self.console.print(f"\n[bold green]✅ Research session completed successfully![/bold green]")
            if save_location:
                self.console.print(f"[green]Standard available at: {save_location}[/green]")
            
            # Ask about next actions
            if Confirm.ask("\n[yellow]Would you like to research another standard?[/yellow]"):
                self.context = ConversationContext(session_id=str(uuid.uuid4()))  # New session
                return await self.run_conversational_research()
            
        except KeyboardInterrupt:
            self.console.print("\n[yellow]Research interrupted. Session saved.[/yellow]")
        except Exception as e:
            logger.error(f"Research session failed: {e}")
            self.console.print(f"[red]Research session failed: {e}[/red]")


@click.command()
@click.option(
    "--session-id",
    help="Resume a previous research session"
)
@click.option(
    "--debug",
    is_flag=True,
    help="Enable debug logging"
)
def main(session_id: Optional[str], debug: bool):
    """
    Enhanced Conversational Standards Research Interface
    
    Research and create coding standards through natural language conversation.
    """
    if debug:
        logging.basicConfig(level=logging.DEBUG)
    
    interface = ConversationalResearchInterface()
    
    if session_id:
        interface.context.session_id = session_id
        interface.console.print(f"[cyan]Resuming session: {session_id}[/cyan]")
    
    try:
        asyncio.run(interface.run_conversational_research())
    except KeyboardInterrupt:
        interface.console.print("\n[yellow]Goodbye! 👋[/yellow]")


if __name__ == "__main__":
    main()
