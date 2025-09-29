#!/usr/bin/env python3
"""
Test that dakora init command works correctly
"""
import tempfile
import os
from pathlib import Path
import yaml
import sys

# Add parent directory to path to import dakora
sys.path.insert(0, str(Path(__file__).parent.parent))

from dakora.cli import app
import typer.testing

def test_init_creates_proper_structure():
    """Test that init command creates the expected files and directories"""
    runner = typer.testing.CliRunner()

    with tempfile.TemporaryDirectory() as tmpdir:
        original_cwd = os.getcwd()
        os.chdir(tmpdir)

        try:
            # Run init command
            result = runner.invoke(app, ["init"])
            assert result.exit_code == 0, f"Init command failed: {result.stdout}"

            # Check that config file was created
            config_path = Path("dakora.yaml")
            assert config_path.exists(), "dakora.yaml was not created"

            # Check config file contents
            config_data = yaml.safe_load(config_path.read_text())
            assert config_data["registry"] == "local", "Wrong registry type in config"
            assert config_data["prompt_dir"] == "./prompts", "Wrong prompt_dir in config"
            assert "logging" in config_data, "Logging config missing"
            assert config_data["logging"]["enabled"] is True, "Logging not enabled by default"
            assert config_data["logging"]["backend"] == "sqlite", "Wrong logging backend"
            assert config_data["logging"]["db_path"] == "./dakora.db", "Wrong db path"

            # Check that prompts directory was created
            prompts_dir = Path("prompts")
            assert prompts_dir.exists(), "prompts directory was not created"
            assert prompts_dir.is_dir(), "prompts is not a directory"

            # Check that example template was created
            example_template = prompts_dir / "summarizer.yaml"
            assert example_template.exists(), "Example summarizer.yaml was not created"

            # Check example template contents
            template_data = yaml.safe_load(example_template.read_text())
            assert template_data["id"] == "summarizer", "Wrong template id"
            assert template_data["version"] == "1.0.0", "Wrong template version"
            assert "description" in template_data, "Template missing description"
            assert "template" in template_data, "Template missing template field"
            assert "{{ input_text }}" in template_data["template"], "Template doesn't use input_text variable"
            assert "inputs" in template_data, "Template missing inputs"
            assert "input_text" in template_data["inputs"], "Template missing input_text input"
            assert template_data["inputs"]["input_text"]["type"] == "string", "Wrong input type"
            assert template_data["inputs"]["input_text"]["required"] is True, "Input should be required"

            print("✅ Init command creates proper structure")

        finally:
            os.chdir(original_cwd)

def test_init_output_message():
    """Test that init command outputs the expected message"""
    runner = typer.testing.CliRunner()

    with tempfile.TemporaryDirectory() as tmpdir:
        original_cwd = os.getcwd()
        os.chdir(tmpdir)

        try:
            result = runner.invoke(app, ["init"])
            assert result.exit_code == 0, f"Init command failed: {result.stdout}"
            assert "Initialized Dakora project." in result.stdout, f"Wrong output message: {result.stdout}"

            print("✅ Init command outputs correct message")

        finally:
            os.chdir(original_cwd)

def test_init_works_in_existing_directory():
    """Test that init works when run in a directory that already has some files"""
    runner = typer.testing.CliRunner()

    with tempfile.TemporaryDirectory() as tmpdir:
        original_cwd = os.getcwd()
        os.chdir(tmpdir)

        try:
            # Create some existing files
            Path("existing_file.txt").write_text("This file already exists")
            Path("some_dir").mkdir()

            # Run init command
            result = runner.invoke(app, ["init"])
            assert result.exit_code == 0, f"Init command failed: {result.stdout}"

            # Check that existing files are still there
            assert Path("existing_file.txt").exists(), "Existing file was removed"
            assert Path("some_dir").exists(), "Existing directory was removed"

            # Check that new files were created
            assert Path("dakora.yaml").exists(), "Config file was not created"
            assert Path("prompts").exists(), "Prompts directory was not created"
            assert Path("prompts/summarizer.yaml").exists(), "Example template was not created"

            print("✅ Init works in existing directory")

        finally:
            os.chdir(original_cwd)

def main():
    """Run all init tests"""
    print("🧪 Testing dakora init command...\n")

    try:
        test_init_creates_proper_structure()
        test_init_output_message()
        test_init_works_in_existing_directory()

        print("\n🎉 All init tests passed!")
        return 0

    except Exception as e:
        print(f"\n❌ Init test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())