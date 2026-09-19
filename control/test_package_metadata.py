"""Offline consistency checks for package metadata and dependency pins."""
from __future__ import annotations

import ast
from pathlib import Path
import tomllib
import unittest


ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / ".prime/agent/skills/article-loop"


class PackageMetadataTests(unittest.TestCase):
    def test_version_has_one_source_and_remains_070(self) -> None:
        config = tomllib.loads((PACKAGE / "pyproject.toml").read_text(encoding="utf-8"))
        project = config["project"]
        self.assertNotIn("version", project)
        self.assertEqual(project["dynamic"], ["version"])
        self.assertEqual(
            config["tool"]["setuptools"]["dynamic"]["version"]["attr"],
            "article_loop.__version__",
        )
        module = ast.parse(
            (PACKAGE / "src/article_loop/__init__.py").read_text(encoding="utf-8")
        )
        versions = [
            node.value.value
            for node in module.body
            if isinstance(node, ast.Assign)
            and any(isinstance(target, ast.Name) and target.id == "__version__" for target in node.targets)
            and isinstance(node.value, ast.Constant)
        ]
        self.assertEqual(versions, ["0.7.0"])

    def test_runtime_and_development_dependencies_are_aligned(self) -> None:
        config = tomllib.loads((PACKAGE / "pyproject.toml").read_text(encoding="utf-8"))
        dependencies = config["project"]["dependencies"]
        self.assertEqual(dependencies, ["PyYAML==6.0.3", "jsonschema==4.26.0"])
        requirements = [
            line for line in (ROOT / "requirements-dev.txt").read_text(encoding="utf-8").splitlines()
            if line and not line.startswith("#")
        ]
        self.assertEqual(requirements, dependencies)
        self.assertEqual(
            config["project"]["description"],
            "Project-local Prime Agent skill scaffold for article-loop",
        )
        self.assertEqual(config["project"]["requires-python"], ">=3.11")

    def test_build_artifacts_are_ignored_without_being_required(self) -> None:
        self.assertIn("*.egg-info/", (ROOT / ".gitignore").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
