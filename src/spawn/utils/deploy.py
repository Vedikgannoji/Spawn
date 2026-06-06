"""Deployment file generator for spawn deploy init."""

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

import typer
from rich.panel import Panel
from rich.table import Table

from spawn.templates.deployment_files import (
    DOCKERFILE_FASTAPI,
    DOCKERFILE_FLASK,
    DOCKERFILE_GENERIC,
    DOCKER_COMPOSE_CONTENT,
    ENV_EXAMPLE_CONTENT,
    GITHUB_ACTIONS_CI,
)
from spawn.utils.console import console

ProjectType = Literal["fastapi", "flask", "generic"]


def detect_project_type(project_path: Path) -> ProjectType | None:
    """Automatically detect project type from project files.

    Detection order: FastAPI -> Flask -> Generic (fallback)

    Args:
        project_path: Path to the project directory

    Returns:
        Detected ProjectType or None if detection fails
    """
    # Check pyproject.toml
    pyproject_path = project_path / "pyproject.toml"
    if pyproject_path.exists():
        try:
            content = pyproject_path.read_text(encoding="utf-8").lower()
            
            # Check for FastAPI
            if "fastapi" in content or "uvicorn" in content:
                return "fastapi"
            
            # Check for Flask
            if "flask" in content:
                return "flask"
        except Exception:
            pass
    
    # Check requirements.txt
    requirements_path = project_path / "requirements.txt"
    if requirements_path.exists():
        try:
            content = requirements_path.read_text(encoding="utf-8").lower()
            
            # Check for FastAPI
            if "fastapi" in content or "uvicorn" in content:
                return "fastapi"
            
            # Check for Flask
            if "flask" in content:
                return "flask"
        except Exception:
            pass
    
    # Check for common file patterns
    # FastAPI patterns: app/main.py, api/, routers/
    if (project_path / "app" / "main.py").exists():
        # Could be FastAPI
        try:
            content = (project_path / "app" / "main.py").read_text(encoding="utf-8")
            if "fastapi" in content.lower() or "FastAPI" in content:
                return "fastapi"
        except Exception:
            pass
    
    # Flask patterns: app.py, application.py, wsgi.py
    for flask_file in ["app.py", "application.py", "wsgi.py"]:
        file_path = project_path / flask_file
        if file_path.exists():
            try:
                content = file_path.read_text(encoding="utf-8")
                if "flask" in content.lower() or "Flask" in content:
                    return "flask"
            except Exception:
                pass
    
    # If no specific framework detected, return None (will fallback to manual selection)
    return None


@dataclass
class DeploymentConfig:
    """Configuration for deployment file generation.

    Attributes:
        project_type: Type of Python project (fastapi, flask, generic)
        project_path: Path to the project directory
        dry_run: If True, preview only without creating files
    """

    project_type: ProjectType
    project_path: Path
    dry_run: bool = False


class DeploymentGenerator:
    """Generates deployment files for existing projects.

    This class handles the creation of deployment-ready assets including
    Dockerfile, docker-compose.yml, .env.example, and CI/CD workflows.
    """

    def __init__(self, config: DeploymentConfig):
        """Initialize the deployment generator.

        Args:
            config: Deployment configuration
        """
        self.config = config
        self.generated_files: list[str] = []
        self.skipped_files: list[str] = []

    def _file_exists(self, filename: str) -> bool:
        """Check if a file already exists in the project.

        Args:
            filename: Name of the file to check

        Returns:
            True if file exists, False otherwise
        """
        file_path = self.config.project_path / filename
        return file_path.exists() and file_path.is_file()

    def _create_file(self, filename: str, content: str) -> None:
        """Create a file with the given content.

        Args:
            filename: Name of the file to create
            content: Content to write to the file
        """
        if self._file_exists(filename):
            self.skipped_files.append(filename)
            return

        # Dry run mode: don't actually create files
        if self.config.dry_run:
            self.generated_files.append(filename)
            return

        file_path = self.config.project_path / filename
        
        # Create parent directories if needed (e.g., .github/workflows)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_path.write_text(content, encoding="utf-8")
        self.generated_files.append(filename)

    def generate_dockerfile(self) -> None:
        """Generate Dockerfile based on project type."""
        dockerfile_templates = {
            "fastapi": DOCKERFILE_FASTAPI,
            "flask": DOCKERFILE_FLASK,
            "generic": DOCKERFILE_GENERIC,
        }

        content = dockerfile_templates[self.config.project_type]
        self._create_file("Dockerfile", content)

    def generate_docker_compose(self) -> None:
        """Generate docker-compose.yml file."""
        self._create_file("docker-compose.yml", DOCKER_COMPOSE_CONTENT)

    def generate_env_example(self) -> None:
        """Generate .env.example file."""
        self._create_file(".env.example", ENV_EXAMPLE_CONTENT)

    def generate_github_actions(self) -> None:
        """Generate GitHub Actions CI workflow."""
        workflow_path = ".github/workflows/ci.yml"
        
        if self._file_exists(workflow_path):
            self.skipped_files.append(workflow_path)
            return

        # Dry run mode: don't actually create files
        if self.config.dry_run:
            self.generated_files.append(workflow_path)
            return

        # Create the full path
        full_path = self.config.project_path / workflow_path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_text(GITHUB_ACTIONS_CI, encoding="utf-8")
        self.generated_files.append(workflow_path)

    def generate_all(self) -> None:
        """Generate all deployment files."""
        console.print()
        
        # Different title for dry run
        if self.config.dry_run:
            console.print(
                Panel.fit(
                    f"Previewing deployment assets for [bold cyan]{self.config.project_type}[/bold cyan] project",
                    title="🔍 Spawn Deploy (Dry Run)",
                    border_style="yellow",
                )
            )
        else:
            console.print(
                Panel.fit(
                    f"Generating deployment assets for [bold cyan]{self.config.project_type}[/bold cyan] project",
                    title="🚀 Spawn Deploy",
                    border_style="cyan",
                )
            )
        console.print()

        if self.config.dry_run:
            console.print("[yellow]Preview mode: No files will be created[/yellow]")
        else:
            console.print("[yellow]Generating deployment files...[/yellow]")
        
        self.generate_dockerfile()
        self.generate_docker_compose()
        self.generate_env_example()
        self.generate_github_actions()

        self._show_summary()

    def _show_summary(self) -> None:
        """Display summary of generated and skipped files."""
        console.print()

        if self.config.dry_run:
            if self.generated_files:
                console.print("[bold yellow]📋 Would Generate[/bold yellow]")
                for filename in self.generated_files:
                    console.print(f"  [yellow]✓[/yellow] {filename}")
                console.print()
        else:
            if self.generated_files:
                console.print("[bold green]✅ Generated Files[/bold green]")
                for filename in self.generated_files:
                    console.print(f"  [green]✓[/green] {filename}")
                console.print()

        if self.skipped_files:
            console.print("[bold yellow]⚠ Skipped Files (already exist)[/bold yellow]")
            for filename in self.skipped_files:
                console.print(f"  [yellow]○[/yellow] {filename}")
            console.print()

        # Show next steps only if files were actually generated (not dry run)
        if self.generated_files and not self.config.dry_run:
            console.print(
                Panel(
                    self._get_next_steps_message(),
                    title="[bold cyan]📋 Next Steps[/bold cyan]",
                    border_style="cyan",
                    padding=(1, 2),
                )
            )
            console.print()
        elif self.config.dry_run and self.generated_files:
            console.print(
                "[dim]Run without --dry-run to create these files[/dim]"
            )
            console.print()

    def _get_next_steps_message(self) -> str:
        """Get next steps message based on what was generated.

        Returns:
            Formatted message with next steps
        """
        steps = []

        if "Dockerfile" in self.generated_files:
            steps.append("1. Review and customize Dockerfile for your needs")
            steps.append("2. Build the image: [bold]docker build -t myapp .[/bold]")

        if "docker-compose.yml" in self.generated_files:
            steps.append("3. Configure services in docker-compose.yml")
            steps.append("4. Start services: [bold]docker-compose up -d[/bold]")

        if ".env.example" in self.generated_files:
            steps.append("5. Copy .env.example to .env and configure")

        if ".github/workflows/ci.yml" in self.generated_files:
            steps.append("6. Push to GitHub to trigger CI workflow")

        steps.append("7. Run [bold]spawn doctor[/bold] to check project health")

        return "\n".join(steps)


def get_project_type_choice() -> ProjectType:
    """Prompt user to select project type.

    Returns:
        Selected project type
    """
    project_types = {
        "1": ("fastapi", "FastAPI - Modern async web framework"),
        "2": ("flask", "Flask - Lightweight web framework"),
        "3": ("generic", "Generic Python - CLI tools, scripts, libraries"),
    }

    table = Table(title="Select Project Type")
    table.add_column("#", justify="center", style="cyan")
    table.add_column("Project Type", style="bold")
    table.add_column("Description")

    for key, (name, description) in project_types.items():
        table.add_row(key, name.upper(), description)

    console.print()
    console.print(table)
    console.print()

    choice = typer.prompt("Choose project type [1-3]", default="1")

    while choice not in project_types:
        console.print(
            "[red]Invalid choice. Please select 1, 2, or 3.[/red]"
        )
        choice = typer.prompt("Choose project type [1-3]", default="1")

    selected_type, _ = project_types[choice]
    return selected_type  # type: ignore


def run_deploy_init(project_path: Path | None = None, dry_run: bool = False) -> None:
    """Run deployment initialization.

    This is the main entry point for the deploy-init command.

    Args:
        project_path: Path to the project directory. Defaults to current directory.
        dry_run: If True, preview only without creating files
    """
    target_path = project_path or Path.cwd()

    # Check if we're in a valid directory
    if not target_path.exists():
        console.print(
            f"[red]Error: Directory '{target_path}' does not exist.[/red]"
        )
        raise typer.Exit(1)

    # Show welcome message
    console.print()
    title = "🔍 Spawn Deploy Init (Dry Run)" if dry_run else "🚀 Spawn Deploy Init"
    console.print(
        Panel.fit(
            "Initialize deployment configuration for your project",
            title=title,
            border_style="yellow" if dry_run else "cyan",
        )
    )

    # Try to auto-detect project type
    detected_type = detect_project_type(target_path)
    project_type: ProjectType

    if detected_type:
        # Show detection result
        console.print()
        console.print(
            f"[bold green]✓[/bold green] Detected project type: [bold cyan]{detected_type.upper()}[/bold cyan]"
        )
        console.print()
        
        # Ask for confirmation
        use_detected = typer.confirm(
            "Use detected type?",
            default=True,
        )
        
        if use_detected:
            project_type = detected_type
        else:
            # User wants to override, show selection menu
            project_type = get_project_type_choice()
    else:
        # No detection, show selection menu
        project_type = get_project_type_choice()

    # Create configuration
    config = DeploymentConfig(
        project_type=project_type,
        project_path=target_path,
        dry_run=dry_run,
    )

    # Generate deployment files
    generator = DeploymentGenerator(config)
    generator.generate_all()
