#!/usr/bin/env python3
"""
Validation script to check if the test setup is working correctly.
Run this to verify that tests can be executed properly.
"""

import sys
import subprocess
import importlib
from pathlib import Path


def check_python_version():
    """Check Python version compatibility."""
    print("🐍 Checking Python version...")
    if sys.version_info < (3, 8):
        print("❌ Python 3.8+ required")
        return False
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
    return True


def check_dependencies():
    """Check if required dependencies are installed."""
    print("\n📦 Checking dependencies...")
    
    required = [
        "pytest",
        "pytest_asyncio", 
        "pytest_playwright",
        "playwright",
        "httpx",
        "psutil"
    ]
    
    missing = []
    
    for dep in required:
        try:
            importlib.import_module(dep)
            print(f"✅ {dep}")
        except ImportError:
            print(f"❌ {dep} (missing)")
            missing.append(dep)
    
    if missing:
        print(f"\n💡 Install missing dependencies:")
        print(f"pip install {' '.join(missing)}")
        return False
    
    return True


def check_project_structure():
    """Check if project structure is correct."""
    print("\n📁 Checking project structure...")
    
    required_files = [
        "main.py",
        "requirements.txt", 
        "modules/module_base.py",
        "config/config.json",
        "tests/conftest.py",
        "tests/test_api_endpoints.py",
        "tests/test_frontend_ui.py",
        "tests/test_module_system.py",
        "tests/test_performance.py",
        "tests/test_integration.py"
    ]
    
    missing = []
    project_root = Path(__file__).parent.parent
    
    for file_path in required_files:
        full_path = project_root / file_path
        if full_path.exists():
            print(f"✅ {file_path}")
        else:
            print(f"❌ {file_path} (missing)")
            missing.append(file_path)
    
    if missing:
        print(f"\n💡 Missing files may cause tests to fail")
        return False
    
    return True


def check_playwright_browsers():
    """Check if Playwright browsers are installed."""
    print("\n🌐 Checking Playwright browsers...")
    
    try:
        result = subprocess.run(
            ["playwright", "list"], 
            capture_output=True, 
            text=True,
            timeout=10
        )
        
        if "chromium" in result.stdout:
            print("✅ Chromium browser available")
            return True
        else:
            print("❌ Chromium browser not found")
            print("💡 Run: playwright install chromium")
            return False
            
    except (subprocess.TimeoutExpired, FileNotFoundError):
        print("❌ Playwright CLI not found")
        print("💡 Run: pip install playwright")
        return False


def run_simple_test():
    """Run a simple test to verify everything works."""
    print("\n🧪 Running simple validation test...")
    
    try:
        result = subprocess.run([
            "python", "-m", "pytest", 
            "--version"
        ], capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            print("✅ pytest working correctly")
            return True
        else:
            print(f"❌ pytest error: {result.stderr}")
            return False
            
    except (subprocess.TimeoutExpired, FileNotFoundError) as e:
        print(f"❌ pytest execution failed: {e}")
        return False


def main():
    """Run all validation checks."""
    print("🔍 Validating test setup for Interaction Framework\n")
    
    checks = [
        ("Python Version", check_python_version),
        ("Dependencies", check_dependencies),
        ("Project Structure", check_project_structure),
        ("Playwright Browsers", check_playwright_browsers),
        ("Test Execution", run_simple_test),
    ]
    
    all_passed = True
    
    for name, check_func in checks:
        try:
            if not check_func():
                all_passed = False
        except Exception as e:
            print(f"❌ {name} check failed with error: {e}")
            all_passed = False
    
    print("\n" + "="*60)
    
    if all_passed:
        print("🎉 All validation checks passed!")
        print("\n💡 You can now run tests:")
        print("   python tests/run_tests.py quick")
        print("   python tests/run_tests.py all")
        return 0
    else:
        print("💥 Some validation checks failed!")
        print("\n💡 Fix the issues above and run this script again:")
        print("   python tests/validate_setup.py")
        return 1


if __name__ == "__main__":
    sys.exit(main())