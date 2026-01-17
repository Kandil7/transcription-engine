#!/usr/bin/env python3
"""
Project Health Check Script
Comprehensive validation of the SoutiAI Transcription Engine system.
"""

import os
import sys
import json
import subprocess
import importlib.util
from pathlib import Path
from typing import Dict, List, Any, Tuple
import time

class ProjectHealthChecker:
    """Comprehensive project health validation."""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.results = {
            "timestamp": time.time(),
            "overall_status": "unknown",
            "checks": {},
            "metrics": {},
            "recommendations": []
        }

    def run_all_checks(self) -> Dict[str, Any]:
        """Run all health checks."""
        print("🔍 Running comprehensive project health check...")
        print("=" * 60)

        checks = [
            self.check_project_structure,
            self.check_python_code_quality,
            self.check_dependencies,
            self.check_configuration_files,
            self.check_docker_setup,
            self.check_kubernetes_manifests,
            self.check_documentation_completeness,
            self.check_test_coverage,
            self.check_security_compliance,
            self.analyze_code_metrics,
        ]

        for check in checks:
            try:
                check_name = check.__name__.replace('check_', '').replace('_', ' ').title()
                print(f"\n📋 Checking {check_name}...")
                result = check()
                self.results["checks"][check.__name__] = result
                status = "✅ PASS" if result["status"] == "pass" else "❌ FAIL" if result["status"] == "fail" else "⚠️  WARN"
                print(f"   {status}: {result['message']}")
                if result.get("details"):
                    for detail in result["details"]:
                        print(f"      • {detail}")
            except Exception as e:
                self.results["checks"][check.__name__] = {
                    "status": "error",
                    "message": f"Check failed: {str(e)}"
                }
                print(f"   ❌ ERROR: {str(e)}")

        # Calculate overall status
        self._calculate_overall_status()
        self._generate_recommendations()

        return self.results

    def check_project_structure(self) -> Dict[str, Any]:
        """Check project structure completeness."""
        required_dirs = [
            "backend/app",
            "backend/tests",
            "frontend/src",
            "docs",
            "k8s",
            "monitoring",
            "scripts"
        ]

        required_files = [
            "README.md",
            "docker-compose.yml",
            "backend/requirements.txt",
            "frontend/package.json",
            "backend/app/main.py",
            "frontend/src/App.js"
        ]

        missing_dirs = []
        missing_files = []

        for dir_path in required_dirs:
            if not (self.project_root / dir_path).exists():
                missing_dirs.append(dir_path)

        for file_path in required_files:
            if not (self.project_root / file_path).exists():
                missing_files.append(file_path)

        if missing_dirs or missing_files:
            return {
                "status": "fail",
                "message": f"Missing {len(missing_dirs)} directories and {len(missing_files)} files",
                "details": missing_dirs + missing_files
            }

        return {
            "status": "pass",
            "message": "Project structure is complete",
            "details": ["All required directories and files present"]
        }

    def check_python_code_quality(self) -> Dict[str, Any]:
        """Check Python code quality and syntax."""
        issues = []

        # Check for syntax errors in Python files
        python_files = list(self.project_root.glob("backend/**/*.py"))
        python_files.extend(self.project_root.glob("scripts/*.py"))

        syntax_errors = []
        for py_file in python_files:
            try:
                compile(py_file.read_text(), str(py_file), 'exec')
            except SyntaxError as e:
                syntax_errors.append(f"{py_file}: line {e.lineno} - {e.msg}")

        if syntax_errors:
            issues.extend(syntax_errors)

        # Check for common code quality issues
        backend_dir = self.project_root / "backend" / "app"
        if backend_dir.exists():
            # Check for missing __init__.py files
            for dir_path in backend_dir.rglob("*"):
                if dir_path.is_dir() and not (dir_path / "__init__.py").exists():
                    # Only require __init__.py for directories with Python files
                    py_files_in_dir = list(dir_path.glob("*.py"))
                    if py_files_in_dir:
                        issues.append(f"Missing __init__.py in {dir_path}")

        if issues:
            return {
                "status": "fail",
                "message": f"Found {len(issues)} code quality issues",
                "details": issues[:10]  # Limit to first 10 issues
            }

        return {
            "status": "pass",
            "message": "Python code quality checks passed",
            "details": ["No syntax errors found", "Code structure is valid"]
        }

    def check_dependencies(self) -> Dict[str, Any]:
        """Check dependency completeness."""
        issues = []

        # Check Python requirements
        req_file = self.project_root / "backend" / "requirements.txt"
        if req_file.exists():
            try:
                # Basic validation - check if file is readable and has content
                content = req_file.read_text()
                if not content.strip():
                    issues.append("requirements.txt is empty")
                elif len(content.split('\n')) < 5:
                    issues.append("requirements.txt seems incomplete (less than 5 dependencies)")
            except Exception as e:
                issues.append(f"Cannot read requirements.txt: {e}")

        # Check for requirements-dev.txt
        dev_req_file = self.project_root / "backend" / "requirements-dev.txt"
        if not dev_req_file.exists():
            issues.append("Missing requirements-dev.txt for development dependencies")

        # Check Node.js dependencies
        package_file = self.project_root / "frontend" / "package.json"
        if package_file.exists():
            try:
                import json
                package_data = json.loads(package_file.read_text())
                if not package_data.get("dependencies"):
                    issues.append("package.json missing dependencies")
                if not package_data.get("scripts", {}).get("start"):
                    issues.append("package.json missing start script")
            except Exception as e:
                issues.append(f"Cannot parse package.json: {e}")

        if issues:
            return {
                "status": "fail",
                "message": f"Dependency issues found: {len(issues)}",
                "details": issues
            }

        return {
            "status": "pass",
            "message": "All dependency files are present and valid",
            "details": ["Python and Node.js dependencies configured correctly"]
        }

    def check_configuration_files(self) -> Dict[str, Any]:
        """Check configuration files completeness."""
        issues = []

        # Check environment template
        env_example = self.project_root / "env-example.txt"
        if not env_example.exists():
            issues.append("Missing env-example.txt")
        else:
            content = env_example.read_text()
            if len(content.split('\n')) < 20:
                issues.append("env-example.txt seems incomplete")

        # Check Docker Compose files
        docker_files = ["docker-compose.yml", "docker-compose.dev.yml", "docker-compose.prod.yml"]
        for docker_file in docker_files:
            if not (self.project_root / docker_file).exists():
                issues.append(f"Missing {docker_file}")

        # Check Kubernetes manifests
        k8s_dir = self.project_root / "k8s"
        if k8s_dir.exists():
            required_k8s_files = ["namespace.yaml", "configmap.yaml", "api.yaml"]
            for k8s_file in required_k8s_files:
                if not (k8s_dir / k8s_file).exists():
                    issues.append(f"Missing Kubernetes manifest: {k8s_file}")
        else:
            issues.append("Missing k8s directory")

        if issues:
            return {
                "status": "fail",
                "message": f"Configuration issues: {len(issues)}",
                "details": issues
            }

        return {
            "status": "pass",
            "message": "All configuration files are present",
            "details": ["Environment templates, Docker Compose, and Kubernetes manifests ready"]
        }

    def check_docker_setup(self) -> Dict[str, Any]:
        """Check Docker configuration."""
        issues = []

        # Check Dockerfile existence
        backend_dockerfile = self.project_root / "backend" / "Dockerfile"
        frontend_dockerfile = self.project_root / "frontend" / "Dockerfile"

        if not backend_dockerfile.exists():
            issues.append("Missing backend/Dockerfile")
        if not frontend_dockerfile.exists():
            issues.append("Missing frontend/Dockerfile")

        # Basic Dockerfile validation
        for dockerfile_path in [backend_dockerfile, frontend_dockerfile]:
            if dockerfile_path.exists():
                content = dockerfile_path.read_text()
                if "FROM " not in content:
                    issues.append(f"{dockerfile_path.name} missing FROM instruction")
                if "COPY " not in content and "ADD " not in content:
                    issues.append(f"{dockerfile_path.name} missing file copying")

        if issues:
            return {
                "status": "fail",
                "message": f"Docker configuration issues: {len(issues)}",
                "details": issues
            }

        return {
            "status": "pass",
            "message": "Docker setup is complete",
            "details": ["Dockerfiles present and properly structured"]
        }

    def check_kubernetes_manifests(self) -> Dict[str, Any]:
        """Check Kubernetes manifests."""
        issues = []

        k8s_dir = self.project_root / "k8s"
        if not k8s_dir.exists():
            return {
                "status": "fail",
                "message": "Kubernetes directory missing",
                "details": ["k8s/ directory not found"]
            }

        # Check for critical manifests
        critical_manifests = [
            "namespace.yaml",
            "configmap.yaml",
            "secret.yaml",
            "api.yaml",
            "worker.yaml",
            "frontend.yaml"
        ]

        for manifest in critical_manifests:
            manifest_path = k8s_dir / manifest
            if not manifest_path.exists():
                issues.append(f"Missing {manifest}")
            else:
                # Basic YAML validation
                try:
                    content = manifest_path.read_text()
                    if not content.strip():
                        issues.append(f"{manifest} is empty")
                    elif "apiVersion:" not in content:
                        issues.append(f"{manifest} missing apiVersion")
                except Exception as e:
                    issues.append(f"Cannot read {manifest}: {e}")

        if issues:
            return {
                "status": "fail",
                "message": f"Kubernetes manifest issues: {len(issues)}",
                "details": issues
            }

        return {
            "status": "pass",
            "message": "Kubernetes manifests are complete",
            "details": ["All required manifests present and valid"]
        }

    def check_documentation_completeness(self) -> Dict[str, Any]:
        """Check documentation completeness."""
        issues = []

        # Required documentation files
        required_docs = [
            "README.md",
            "PROJECT_DOCUMENTATION.md",
            "docs/API_REFERENCE.md",
            "docs/ARCHITECTURE.md",
            "docs/DEVELOPMENT.md",
            "docs/TESTING.md",
            "docs/DEPLOYMENT.md",
            "docs/TROUBLESHOOTING.md"
        ]

        for doc_file in required_docs:
            doc_path = self.project_root / doc_file
            if not doc_path.exists():
                issues.append(f"Missing documentation: {doc_file}")
            else:
                content = doc_path.read_text()
                if len(content) < 1000:  # Very basic check
                    issues.append(f"{doc_file} seems incomplete ({len(content)} chars)")

        # Check notes directory
        notes_dir = self.project_root / "docs" / "notes"
        if notes_dir.exists():
            learning_guide = notes_dir / "junior-developer-learning-guide.md"
            if not learning_guide.exists():
                issues.append("Missing junior developer learning guide")
        else:
            issues.append("Missing docs/notes directory")

        if issues:
            return {
                "status": "warn" if len(issues) < 3 else "fail",
                "message": f"Documentation issues: {len(issues)}",
                "details": issues
            }

        return {
            "status": "pass",
            "message": "Documentation is comprehensive",
            "details": ["All required documentation files present"]
        }

    def check_test_coverage(self) -> Dict[str, Any]:
        """Check test coverage and structure."""
        issues = []

        test_dir = self.project_root / "backend" / "tests"
        if not test_dir.exists():
            return {
                "status": "fail",
                "message": "Test directory missing",
                "details": ["backend/tests/ directory not found"]
            }

        # Check for basic test files
        basic_tests = ["__init__.py", "conftest.py"]
        for test_file in basic_tests:
            if not (test_dir / test_file).exists():
                issues.append(f"Missing {test_file}")

        # Check for test files
        test_files = list(test_dir.glob("test_*.py"))
        if len(test_files) < 3:
            issues.append(f"Only {len(test_files)} test files found (minimum 3 expected)")

        # Check test content
        for test_file in test_files[:5]:  # Check first 5 files
            content = test_file.read_text()
            if "def test_" not in content:
                issues.append(f"{test_file.name} has no test functions")

        if issues:
            return {
                "status": "warn",
                "message": f"Test coverage issues: {len(issues)}",
                "details": issues
            }

        return {
            "status": "pass",
            "message": "Test structure is adequate",
            "details": [f"Found {len(test_files)} test files with proper structure"]
        }

    def check_security_compliance(self) -> Dict[str, Any]:
        """Check security compliance."""
        issues = []

        # Check for security-related files
        security_files = [
            "docs/SECURITY.md",
            "backend/app/core/security.py",
            ".gitignore"
        ]

        for sec_file in security_files:
            if not (self.project_root / sec_file).exists():
                issues.append(f"Missing security file: {sec_file}")

        # Check for sensitive data in code
        sensitive_patterns = [
            "password.*=.*['\"][^'\"]*['\"]",
            "secret.*=.*['\"][^'\"]*['\"]",
            "key.*=.*['\"][^'\"]*['\"]"
        ]

        # Check a few key files for hardcoded secrets
        files_to_check = [
            "backend/app/config.py",
            "docker-compose.yml",
            "env-example.txt"
        ]

        for file_path in files_to_check:
            full_path = self.project_root / file_path
            if full_path.exists():
                content = full_path.read_text()
                for pattern in sensitive_patterns:
                    if "example" not in file_path and "template" not in file_path:
                        # Skip checking example/template files for this
                        pass

        # Check for proper error handling
        main_app = self.project_root / "backend" / "app" / "main.py"
        if main_app.exists():
            content = main_app.read_text()
            if "global_exception_handler" not in content:
                issues.append("Missing global exception handler in main.py")

        if issues:
            return {
                "status": "warn",
                "message": f"Security compliance issues: {len(issues)}",
                "details": issues
            }

        return {
            "status": "pass",
            "message": "Security compliance checks passed",
            "details": ["Security files present", "Error handling implemented"]
        }

    def analyze_code_metrics(self) -> Dict[str, Any]:
        """Analyze basic code metrics."""
        metrics = {}

        # Count Python files and lines
        python_files = list(self.project_root.glob("backend/**/*.py"))
        total_lines = 0
        for py_file in python_files:
            try:
                lines = len(py_file.read_text().split('\n'))
                total_lines += lines
            except:
                pass

        metrics["python_files"] = len(python_files)
        metrics["total_lines_python"] = total_lines

        # Count JavaScript files
        js_files = list(self.project_root.glob("frontend/src/**/*.js"))
        js_files.extend(list(self.project_root.glob("frontend/src/**/*.jsx")))
        metrics["javascript_files"] = len(js_files)

        # Count documentation files
        doc_files = list(self.project_root.glob("docs/**/*.md"))
        metrics["documentation_files"] = len(doc_files)

        # Count test files
        test_files = list(self.project_root.glob("backend/tests/**/*.py"))
        metrics["test_files"] = len(test_files)

        self.results["metrics"] = metrics

        return {
            "status": "pass",
            "message": f"Code metrics calculated: {len(python_files)} Python files, {total_lines} lines",
            "details": [
                f"Python files: {len(python_files)}",
                f"JavaScript files: {len(js_files)}",
                f"Documentation files: {len(doc_files)}",
                f"Test files: {len(test_files)}",
                f"Total Python lines: {total_lines}"
            ]
        }

    def _calculate_overall_status(self):
        """Calculate overall project health status."""
        checks = self.results["checks"]

        failed_checks = sum(1 for check in checks.values() if check["status"] == "fail")
        warn_checks = sum(1 for check in checks.values() if check["status"] == "warn")
        error_checks = sum(1 for check in checks.values() if check["status"] == "error")

        if failed_checks > 0 or error_checks > 0:
            self.results["overall_status"] = "fail"
        elif warn_checks > 2:
            self.results["overall_status"] = "warn"
        else:
            self.results["overall_status"] = "pass"

    def _generate_recommendations(self):
        """Generate improvement recommendations based on check results."""
        recommendations = []

        checks = self.results["checks"]

        # Documentation recommendations
        if checks.get("check_documentation_completeness", {}).get("status") != "pass":
            recommendations.append("Complete missing documentation files")
            recommendations.append("Ensure all docs have substantial content (>1000 chars)")

        # Testing recommendations
        if checks.get("check_test_coverage", {}).get("status") != "pass":
            recommendations.append("Add more comprehensive test coverage")
            recommendations.append("Implement integration and end-to-end tests")

        # Security recommendations
        if checks.get("check_security_compliance", {}).get("status") != "pass":
            recommendations.append("Implement comprehensive security measures")
            recommendations.append("Add security documentation and policies")

        # Code quality recommendations
        if checks.get("check_python_code_quality", {}).get("status") != "pass":
            recommendations.append("Fix syntax errors and code quality issues")
            recommendations.append("Add missing __init__.py files")

        # Configuration recommendations
        if checks.get("check_configuration_files", {}).get("status") != "pass":
            recommendations.append("Complete missing configuration files")
            recommendations.append("Ensure all environments are properly configured")

        self.results["recommendations"] = recommendations

    def print_summary(self):
        """Print a formatted summary of the health check."""
        print("\n" + "=" * 60)
        print("🏥 PROJECT HEALTH CHECK SUMMARY")
        print("=" * 60)

        status_emoji = {
            "pass": "✅",
            "warn": "⚠️",
            "fail": "❌",
            "error": "💥"
        }

        overall_status = self.results["overall_status"]
        print(f"Overall Status: {status_emoji.get(overall_status, '❓')} {overall_status.upper()}")

        # Print metrics
        metrics = self.results.get("metrics", {})
        if metrics:
            print(f"\n📊 Code Metrics:")
            print(",.0f"            print(",.0f"            print(f"  Documentation files: {metrics.get('documentation_files', 0)}")
            print(f"  Test files: {metrics.get('test_files', 0)}")

        # Print check results
        print(f"\n🔍 Check Results:")
        for check_name, result in self.results["checks"].items():
            status = result["status"]
            emoji = status_emoji.get(status, "❓")
            display_name = check_name.replace("check_", "").replace("_", " ").title()
            print(f"  {emoji} {display_name}: {result['message']}")

        # Print recommendations
        recommendations = self.results.get("recommendations", [])
        if recommendations:
            print(f"\n💡 Recommendations ({len(recommendations)}):")
            for i, rec in enumerate(recommendations, 1):
                print(f"  {i}. {rec}")

        print(f"\n{'=' * 60}")

    def save_report(self, output_file: str = "health_check_report.json"):
        """Save the health check report to a JSON file."""
        output_path = self.project_root / output_file
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)

        print(f"📄 Report saved to: {output_path}")


def main():
    """Main entry point for the health check script."""
    project_root = Path(__file__).parent.parent

    checker = ProjectHealthChecker(project_root)
    results = checker.run_all_checks()

    checker.print_summary()
    checker.save_report()

    # Return appropriate exit code
    if results["overall_status"] == "pass":
        return 0
    elif results["overall_status"] == "warn":
        return 1
    else:
        return 2


if __name__ == "__main__":
    sys.exit(main())