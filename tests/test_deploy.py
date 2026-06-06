"""Tests for the spawn deploy init functionality."""

import tempfile
from pathlib import Path

import pytest

from spawn.utils.deploy import (
    DeploymentConfig,
    DeploymentGenerator,
    detect_project_type,
)


@pytest.fixture
def temp_project_dir():
    """Create a temporary directory for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def fastapi_config(temp_project_dir):
    """Create a FastAPI deployment configuration."""
    return DeploymentConfig(
        project_type="fastapi",
        project_path=temp_project_dir,
    )


@pytest.fixture
def flask_config(temp_project_dir):
    """Create a Flask deployment configuration."""
    return DeploymentConfig(
        project_type="flask",
        project_path=temp_project_dir,
    )


@pytest.fixture
def generic_config(temp_project_dir):
    """Create a Generic deployment configuration."""
    return DeploymentConfig(
        project_type="generic",
        project_path=temp_project_dir,
    )


class TestDeploymentConfig:
    """Tests for DeploymentConfig dataclass."""

    def test_config_creation(self, temp_project_dir):
        """Test creating a DeploymentConfig instance."""
        config = DeploymentConfig(
            project_type="fastapi",
            project_path=temp_project_dir,
        )

        assert config.project_type == "fastapi"
        assert config.project_path == temp_project_dir

    def test_config_with_different_types(self, temp_project_dir):
        """Test config with different project types."""
        for project_type in ["fastapi", "flask", "generic"]:
            config = DeploymentConfig(
                project_type=project_type,  # type: ignore
                project_path=temp_project_dir,
            )
            assert config.project_type == project_type


class TestDeploymentGenerator:
    """Tests for DeploymentGenerator class."""

    def test_generator_initialization(self, fastapi_config):
        """Test generator initializes correctly."""
        generator = DeploymentGenerator(fastapi_config)

        assert generator.config == fastapi_config
        assert generator.generated_files == []
        assert generator.skipped_files == []

    def test_file_exists_detection(self, fastapi_config, temp_project_dir):
        """Test detection of existing files."""
        generator = DeploymentGenerator(fastapi_config)

        # File doesn't exist yet
        assert not generator._file_exists("Dockerfile")

        # Create the file
        (temp_project_dir / "Dockerfile").write_text("test")

        # Now it should be detected
        assert generator._file_exists("Dockerfile")

    def test_file_exists_handles_directories(self, fastapi_config, temp_project_dir):
        """Test that directories are not detected as files."""
        generator = DeploymentGenerator(fastapi_config)

        # Create a directory with same name
        (temp_project_dir / "Dockerfile").mkdir()

        # Should return False for directories
        assert not generator._file_exists("Dockerfile")

    # Dockerfile Generation Tests

    def test_generate_dockerfile_fastapi(self, fastapi_config, temp_project_dir):
        """Test Dockerfile generation for FastAPI."""
        generator = DeploymentGenerator(fastapi_config)
        generator.generate_dockerfile()

        dockerfile_path = temp_project_dir / "Dockerfile"
        assert dockerfile_path.exists()
        assert dockerfile_path.is_file()

        content = dockerfile_path.read_text()
        assert "FROM python:3.12-slim" in content
        assert "uvicorn" in content
        assert "8000" in content
        assert "Dockerfile" in generator.generated_files

    def test_generate_dockerfile_flask(self, flask_config, temp_project_dir):
        """Test Dockerfile generation for Flask."""
        generator = DeploymentGenerator(flask_config)
        generator.generate_dockerfile()

        dockerfile_path = temp_project_dir / "Dockerfile"
        assert dockerfile_path.exists()

        content = dockerfile_path.read_text()
        assert "FROM python:3.12-slim" in content
        assert "flask" in content
        assert "5000" in content
        assert "Dockerfile" in generator.generated_files

    def test_generate_dockerfile_generic(self, generic_config, temp_project_dir):
        """Test Dockerfile generation for Generic Python."""
        generator = DeploymentGenerator(generic_config)
        generator.generate_dockerfile()

        dockerfile_path = temp_project_dir / "Dockerfile"
        assert dockerfile_path.exists()

        content = dockerfile_path.read_text()
        assert "FROM python:3.12-slim" in content
        assert "python" in content
        assert "main.py" in content
        assert "Dockerfile" in generator.generated_files

    def test_generate_dockerfile_skips_existing(self, fastapi_config, temp_project_dir):
        """Test that existing Dockerfile is not overwritten."""
        # Create existing Dockerfile
        existing_content = "# Existing Dockerfile"
        (temp_project_dir / "Dockerfile").write_text(existing_content)

        generator = DeploymentGenerator(fastapi_config)
        generator.generate_dockerfile()

        # File should not be in generated list
        assert "Dockerfile" not in generator.generated_files
        assert "Dockerfile" in generator.skipped_files

        # Content should be unchanged
        assert (temp_project_dir / "Dockerfile").read_text() == existing_content

    # Docker Compose Tests

    def test_generate_docker_compose(self, fastapi_config, temp_project_dir):
        """Test docker-compose.yml generation."""
        generator = DeploymentGenerator(fastapi_config)
        generator.generate_docker_compose()

        compose_path = temp_project_dir / "docker-compose.yml"
        assert compose_path.exists()
        assert compose_path.is_file()

        content = compose_path.read_text()
        assert "services:" in content
        assert "app:" in content
        assert "build:" in content
        assert "ports:" in content
        assert "docker-compose.yml" in generator.generated_files

    def test_generate_docker_compose_skips_existing(self, fastapi_config, temp_project_dir):
        """Test that existing docker-compose.yml is not overwritten."""
        existing_content = "# Existing docker-compose"
        (temp_project_dir / "docker-compose.yml").write_text(existing_content)

        generator = DeploymentGenerator(fastapi_config)
        generator.generate_docker_compose()

        assert "docker-compose.yml" not in generator.generated_files
        assert "docker-compose.yml" in generator.skipped_files
        assert (temp_project_dir / "docker-compose.yml").read_text() == existing_content

    # Environment Variables Tests

    def test_generate_env_example(self, fastapi_config, temp_project_dir):
        """Test .env.example generation."""
        generator = DeploymentGenerator(fastapi_config)
        generator.generate_env_example()

        env_path = temp_project_dir / ".env.example"
        assert env_path.exists()
        assert env_path.is_file()

        content = env_path.read_text()
        assert "ENV=" in content
        assert "APP_PORT=" in content
        assert "DEBUG=" in content
        assert ".env.example" in generator.generated_files

    def test_generate_env_example_skips_existing(self, fastapi_config, temp_project_dir):
        """Test that existing .env.example is not overwritten."""
        existing_content = "# Existing env"
        (temp_project_dir / ".env.example").write_text(existing_content)

        generator = DeploymentGenerator(fastapi_config)
        generator.generate_env_example()

        assert ".env.example" not in generator.generated_files
        assert ".env.example" in generator.skipped_files

    # GitHub Actions Tests

    def test_generate_github_actions(self, fastapi_config, temp_project_dir):
        """Test GitHub Actions workflow generation."""
        generator = DeploymentGenerator(fastapi_config)
        generator.generate_github_actions()

        workflow_path = temp_project_dir / ".github" / "workflows" / "ci.yml"
        assert workflow_path.exists()
        assert workflow_path.is_file()

        content = workflow_path.read_text()
        assert "name: CI" in content
        assert "on:" in content
        assert "jobs:" in content
        assert "test:" in content
        assert "pytest" in content
        assert ".github/workflows/ci.yml" in generator.generated_files

    def test_generate_github_actions_creates_directories(self, fastapi_config, temp_project_dir):
        """Test that GitHub Actions generation creates nested directories."""
        generator = DeploymentGenerator(fastapi_config)
        generator.generate_github_actions()

        # Check that directories were created
        assert (temp_project_dir / ".github").exists()
        assert (temp_project_dir / ".github").is_dir()
        assert (temp_project_dir / ".github" / "workflows").exists()
        assert (temp_project_dir / ".github" / "workflows").is_dir()

    def test_generate_github_actions_skips_existing(self, fastapi_config, temp_project_dir):
        """Test that existing GitHub Actions workflow is not overwritten."""
        # Create directory structure
        workflow_dir = temp_project_dir / ".github" / "workflows"
        workflow_dir.mkdir(parents=True)
        workflow_path = workflow_dir / "ci.yml"

        existing_content = "# Existing workflow"
        workflow_path.write_text(existing_content)

        generator = DeploymentGenerator(fastapi_config)
        generator.generate_github_actions()

        assert ".github/workflows/ci.yml" not in generator.generated_files
        assert ".github/workflows/ci.yml" in generator.skipped_files
        assert workflow_path.read_text() == existing_content

    # Integration Tests

    def test_generate_all_fastapi(self, fastapi_config, temp_project_dir):
        """Test generating all files for FastAPI project."""
        generator = DeploymentGenerator(fastapi_config)
        generator.generate_all()

        # Check all files were created
        assert (temp_project_dir / "Dockerfile").exists()
        assert (temp_project_dir / "docker-compose.yml").exists()
        assert (temp_project_dir / ".env.example").exists()
        assert (temp_project_dir / ".github" / "workflows" / "ci.yml").exists()

        # Check generated files list
        assert len(generator.generated_files) == 4
        assert "Dockerfile" in generator.generated_files
        assert "docker-compose.yml" in generator.generated_files
        assert ".env.example" in generator.generated_files
        assert ".github/workflows/ci.yml" in generator.generated_files

        # No files should be skipped
        assert len(generator.skipped_files) == 0

    def test_generate_all_flask(self, flask_config, temp_project_dir):
        """Test generating all files for Flask project."""
        generator = DeploymentGenerator(flask_config)
        generator.generate_all()

        # Check Flask-specific Dockerfile
        dockerfile_content = (temp_project_dir / "Dockerfile").read_text()
        assert "flask" in dockerfile_content
        assert "5000" in dockerfile_content

        assert len(generator.generated_files) == 4

    def test_generate_all_generic(self, generic_config, temp_project_dir):
        """Test generating all files for Generic Python project."""
        generator = DeploymentGenerator(generic_config)
        generator.generate_all()

        # Check Generic Dockerfile
        dockerfile_content = (temp_project_dir / "Dockerfile").read_text()
        assert "main.py" in dockerfile_content

        assert len(generator.generated_files) == 4

    def test_generate_all_with_some_existing(self, fastapi_config, temp_project_dir):
        """Test generation when some files already exist."""
        # Create some existing files
        (temp_project_dir / "Dockerfile").write_text("# Existing")
        (temp_project_dir / ".env.example").write_text("# Existing")

        generator = DeploymentGenerator(fastapi_config)
        generator.generate_all()

        # Check that new files were created
        assert (temp_project_dir / "docker-compose.yml").exists()
        assert (temp_project_dir / ".github" / "workflows" / "ci.yml").exists()

        # Check lists
        assert len(generator.generated_files) == 2
        assert "docker-compose.yml" in generator.generated_files
        assert ".github/workflows/ci.yml" in generator.generated_files

        assert len(generator.skipped_files) == 2
        assert "Dockerfile" in generator.skipped_files
        assert ".env.example" in generator.skipped_files

    def test_generate_all_with_all_existing(self, fastapi_config, temp_project_dir):
        """Test generation when all files already exist."""
        # Create all files
        (temp_project_dir / "Dockerfile").write_text("# Existing")
        (temp_project_dir / "docker-compose.yml").write_text("# Existing")
        (temp_project_dir / ".env.example").write_text("# Existing")

        workflow_dir = temp_project_dir / ".github" / "workflows"
        workflow_dir.mkdir(parents=True)
        (workflow_dir / "ci.yml").write_text("# Existing")

        generator = DeploymentGenerator(fastapi_config)
        generator.generate_all()

        # No files should be generated
        assert len(generator.generated_files) == 0

        # All files should be skipped
        assert len(generator.skipped_files) == 4

    # Template Content Tests

    def test_dockerfile_templates_contain_uv(self, temp_project_dir):
        """Test that all Dockerfile templates use uv."""
        for project_type in ["fastapi", "flask", "generic"]:
            config = DeploymentConfig(
                project_type=project_type,  # type: ignore
                project_path=temp_project_dir,
            )
            generator = DeploymentGenerator(config)
            generator.generate_dockerfile()

            content = (temp_project_dir / "Dockerfile").read_text()
            assert "uv" in content.lower()
            assert "COPY --from=ghcr.io/astral-sh/uv" in content

            # Clean up for next iteration
            (temp_project_dir / "Dockerfile").unlink()

    def test_docker_compose_has_commented_services(self, fastapi_config, temp_project_dir):
        """Test that docker-compose includes commented optional services."""
        generator = DeploymentGenerator(fastapi_config)
        generator.generate_docker_compose()

        content = (temp_project_dir / "docker-compose.yml").read_text()
        
        # Check for commented database service
        assert "# db:" in content or "#   db:" in content
        assert "postgres" in content.lower()

        # Check for commented redis service
        assert "# redis:" in content or "#   redis:" in content
        assert "redis" in content.lower()

    def test_github_actions_includes_tests_and_linting(self, fastapi_config, temp_project_dir):
        """Test that GitHub Actions workflow includes quality checks."""
        generator = DeploymentGenerator(fastapi_config)
        generator.generate_github_actions()

        content = (temp_project_dir / ".github" / "workflows" / "ci.yml").read_text()

        # Check for linting
        assert "ruff" in content.lower()

        # Check for testing
        assert "pytest" in content

        # Check for coverage
        assert "coverage" in content.lower() or "cov" in content

    def test_env_example_has_common_variables(self, fastapi_config, temp_project_dir):
        """Test that .env.example includes common variables."""
        generator = DeploymentGenerator(fastapi_config)
        generator.generate_env_example()

        content = (temp_project_dir / ".env.example").read_text()

        # Common variables
        assert "ENV=" in content
        assert "DEBUG=" in content
        assert "APP_PORT=" in content

        # Database variables (commented)
        assert "DATABASE" in content or "POSTGRES" in content

    # Edge Cases

    def test_generator_handles_nonexistent_parent_directories(self, fastapi_config, temp_project_dir):
        """Test that generator creates parent directories as needed."""
        generator = DeploymentGenerator(fastapi_config)
        
        # GitHub Actions should create nested directories
        generator.generate_github_actions()

        workflow_path = temp_project_dir / ".github" / "workflows" / "ci.yml"
        assert workflow_path.exists()
        assert workflow_path.parent.exists()
        assert workflow_path.parent.parent.exists()

    def test_create_file_with_nested_path(self, fastapi_config, temp_project_dir):
        """Test creating files with nested paths."""
        generator = DeploymentGenerator(fastapi_config)
        
        # Use internal method to test nested path creation
        generator._create_file("nested/dir/file.txt", "test content")

        file_path = temp_project_dir / "nested" / "dir" / "file.txt"
        assert file_path.exists()
        assert file_path.read_text() == "test content"

    def test_different_project_types_generate_different_dockerfiles(self, temp_project_dir):
        """Test that different project types produce different Dockerfiles."""
        dockerfiles = {}

        for project_type in ["fastapi", "flask", "generic"]:
            config = DeploymentConfig(
                project_type=project_type,  # type: ignore
                project_path=temp_project_dir,
            )
            generator = DeploymentGenerator(config)
            generator.generate_dockerfile()

            dockerfiles[project_type] = (temp_project_dir / "Dockerfile").read_text()
            (temp_project_dir / "Dockerfile").unlink()

        # All three should be different
        assert dockerfiles["fastapi"] != dockerfiles["flask"]
        assert dockerfiles["fastapi"] != dockerfiles["generic"]
        assert dockerfiles["flask"] != dockerfiles["generic"]

        # Check specific differences
        assert "uvicorn" in dockerfiles["fastapi"]
        assert "flask" in dockerfiles["flask"]
        assert "main.py" in dockerfiles["generic"]



class TestProjectTypeDetection:
    """Tests for automatic project type detection."""

    def test_detect_fastapi_from_pyproject(self, temp_project_dir):
        """Test FastAPI detection from pyproject.toml."""
        pyproject = temp_project_dir / "pyproject.toml"
        pyproject.write_text('[project]\ndependencies = ["fastapi>=0.100.0"]')
        
        detected = detect_project_type(temp_project_dir)
        assert detected == "fastapi"

    def test_detect_fastapi_from_uvicorn(self, temp_project_dir):
        """Test FastAPI detection from uvicorn dependency."""
        pyproject = temp_project_dir / "pyproject.toml"
        pyproject.write_text('[project]\ndependencies = ["uvicorn>=0.20.0"]')
        
        detected = detect_project_type(temp_project_dir)
        assert detected == "fastapi"

    def test_detect_flask_from_pyproject(self, temp_project_dir):
        """Test Flask detection from pyproject.toml."""
        pyproject = temp_project_dir / "pyproject.toml"
        pyproject.write_text('[project]\ndependencies = ["flask>=2.0.0"]')
        
        detected = detect_project_type(temp_project_dir)
        assert detected == "flask"

    def test_detect_fastapi_from_requirements(self, temp_project_dir):
        """Test FastAPI detection from requirements.txt."""
        requirements = temp_project_dir / "requirements.txt"
        requirements.write_text("fastapi==0.100.0\nuvicorn==0.20.0")
        
        detected = detect_project_type(temp_project_dir)
        assert detected == "fastapi"

    def test_detect_flask_from_requirements(self, temp_project_dir):
        """Test Flask detection from requirements.txt."""
        requirements = temp_project_dir / "requirements.txt"
        requirements.write_text("flask==2.0.0\ngunicorn==20.1.0")
        
        detected = detect_project_type(temp_project_dir)
        assert detected == "flask"

    def test_detect_fastapi_from_app_structure(self, temp_project_dir):
        """Test FastAPI detection from app/main.py."""
        app_dir = temp_project_dir / "app"
        app_dir.mkdir()
        main_file = app_dir / "main.py"
        main_file.write_text("from fastapi import FastAPI\napp = FastAPI()")
        
        detected = detect_project_type(temp_project_dir)
        assert detected == "fastapi"

    def test_detect_flask_from_app_py(self, temp_project_dir):
        """Test Flask detection from app.py."""
        app_file = temp_project_dir / "app.py"
        app_file.write_text("from flask import Flask\napp = Flask(__name__)")
        
        detected = detect_project_type(temp_project_dir)
        assert detected == "flask"

    def test_detect_flask_from_wsgi_py(self, temp_project_dir):
        """Test Flask detection from wsgi.py."""
        wsgi_file = temp_project_dir / "wsgi.py"
        wsgi_file.write_text("from flask import Flask\napp = Flask(__name__)")
        
        detected = detect_project_type(temp_project_dir)
        assert detected == "flask"

    def test_no_detection_empty_project(self, temp_project_dir):
        """Test no detection on empty project."""
        detected = detect_project_type(temp_project_dir)
        assert detected is None

    def test_no_detection_generic_python(self, temp_project_dir):
        """Test no detection on generic Python project."""
        # Create a generic Python file
        (temp_project_dir / "main.py").write_text("print('Hello')")
        
        detected = detect_project_type(temp_project_dir)
        assert detected is None

    def test_fastapi_takes_precedence_over_flask(self, temp_project_dir):
        """Test FastAPI detection when both are present."""
        requirements = temp_project_dir / "requirements.txt"
        requirements.write_text("fastapi==0.100.0\nflask==2.0.0")
        
        detected = detect_project_type(temp_project_dir)
        # FastAPI is checked first
        assert detected == "fastapi"


class TestDryRunMode:
    """Tests for dry-run mode."""

    def test_dry_run_config_attribute(self, temp_project_dir):
        """Test DeploymentConfig with dry_run flag."""
        config = DeploymentConfig(
            project_type="fastapi",
            project_path=temp_project_dir,
            dry_run=True,
        )
        
        assert config.dry_run is True

    def test_dry_run_no_files_created(self, temp_project_dir):
        """Test that dry-run creates no files."""
        config = DeploymentConfig(
            project_type="fastapi",
            project_path=temp_project_dir,
            dry_run=True,
        )
        generator = DeploymentGenerator(config)
        generator.generate_all()
        
        # No files should exist
        assert not (temp_project_dir / "Dockerfile").exists()
        assert not (temp_project_dir / "docker-compose.yml").exists()
        assert not (temp_project_dir / ".env.example").exists()
        assert not (temp_project_dir / ".github" / "workflows" / "ci.yml").exists()
        
        # But generated_files list should be populated
        assert len(generator.generated_files) == 4
        assert "Dockerfile" in generator.generated_files
        assert "docker-compose.yml" in generator.generated_files
        assert ".env.example" in generator.generated_files
        assert ".github/workflows/ci.yml" in generator.generated_files

    def test_dry_run_reports_would_generate(self, temp_project_dir):
        """Test that dry-run reports files it would generate."""
        config = DeploymentConfig(
            project_type="flask",
            project_path=temp_project_dir,
            dry_run=True,
        )
        generator = DeploymentGenerator(config)
        generator.generate_dockerfile()
        generator.generate_docker_compose()
        
        # Files tracked but not created
        assert len(generator.generated_files) == 2
        assert "Dockerfile" in generator.generated_files
        assert "docker-compose.yml" in generator.generated_files
        
        # Files don't exist
        assert not (temp_project_dir / "Dockerfile").exists()
        assert not (temp_project_dir / "docker-compose.yml").exists()

    def test_dry_run_still_detects_existing_files(self, temp_project_dir):
        """Test that dry-run still detects existing files."""
        # Create existing file
        (temp_project_dir / "Dockerfile").write_text("# Existing")
        
        config = DeploymentConfig(
            project_type="fastapi",
            project_path=temp_project_dir,
            dry_run=True,
        )
        generator = DeploymentGenerator(config)
        generator.generate_all()
        
        # Existing file should be in skipped list
        assert "Dockerfile" in generator.skipped_files
        assert "Dockerfile" not in generator.generated_files
        
        # Other files in generated list (but not created)
        assert len(generator.generated_files) == 3
        assert not (temp_project_dir / "docker-compose.yml").exists()


class TestDoctorIntegration:
    """Tests for integration with spawn doctor."""

    def test_deploy_init_improves_doctor_score(self, temp_project_dir):
        """Test that deploy-init improves doctor health score."""
        from spawn.utils.doctor import ProjectHealthChecker
        
        # Run doctor BEFORE deploy-init
        checker_before = ProjectHealthChecker(temp_project_dir)
        checks_before = checker_before.run_all_checks()
        score_before, max_score = checker_before.calculate_score(checks_before)
        
        # Verify baseline: no deployment files
        dockerfile_check = next(c for c in checks_before if c.name == "Dockerfile")
        assert not dockerfile_check.passed
        
        # Run deploy-init
        config = DeploymentConfig(
            project_type="fastapi",
            project_path=temp_project_dir,
            dry_run=False,
        )
        generator = DeploymentGenerator(config)
        generator.generate_all()
        
        # Run doctor AFTER deploy-init
        checker_after = ProjectHealthChecker(temp_project_dir)
        checks_after = checker_after.run_all_checks()
        score_after, _ = checker_after.calculate_score(checks_after)
        
        # Verify improvements
        dockerfile_check = next(c for c in checks_after if c.name == "Dockerfile")
        assert dockerfile_check.passed
        
        env_check = next(c for c in checks_after if c.name == ".env.example")
        assert env_check.passed
        
        github_check = next(c for c in checks_after if c.name == "GitHub Actions")
        assert github_check.passed
        
        # Score should increase
        assert score_after > score_before
        
        # Specifically, should gain 30 points (Dockerfile=10 + GitHub=10 + .env=10)
        assert score_after - score_before >= 25  # At least 25 points improvement

    def test_deploy_init_creates_files_doctor_checks(self, temp_project_dir):
        """Test that deploy-init creates files that doctor checks for."""
        # Run deploy-init
        config = DeploymentConfig(
            project_type="generic",
            project_path=temp_project_dir,
            dry_run=False,
        )
        generator = DeploymentGenerator(config)
        generator.generate_all()
        
        # Verify files exist
        assert (temp_project_dir / "Dockerfile").exists()
        assert (temp_project_dir / ".env.example").exists()
        assert (temp_project_dir / ".github" / "workflows" / "ci.yml").exists()
        
        # Run doctor and verify checks pass
        from spawn.utils.doctor import ProjectHealthChecker
        
        checker = ProjectHealthChecker(temp_project_dir)
        checks = checker.run_all_checks()
        
        # Find deployment-related checks
        dockerfile_check = next(c for c in checks if c.name == "Dockerfile")
        env_check = next(c for c in checks if c.name == ".env.example")
        github_check = next(c for c in checks if c.name == "GitHub Actions")
        
        # All should pass
        assert dockerfile_check.passed
        assert env_check.passed
        assert github_check.passed
