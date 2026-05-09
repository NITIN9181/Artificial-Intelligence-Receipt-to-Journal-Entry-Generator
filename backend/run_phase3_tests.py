"""
Phase 3 Test Runner
Runs all Phase 3 tests and generates a report.

Usage:
    python run_phase3_tests.py
"""

import subprocess
import sys
from pathlib import Path


def run_tests():
    """Run all Phase 3 tests and report results."""
    
    print("=" * 80)
    print("PHASE 3 TEST SUITE")
    print("=" * 80)
    print()
    
    test_files = [
        ("Role Tests", "tests/test_roles.py"),
        ("Approval Workflow Tests", "tests/test_approval_workflow.py"),
        ("GnuCash Export Tests", "tests/test_gnucash_export.py"),
        ("Basic Phase 3 Tests", "tests/test_phase3_basic.py"),
    ]
    
    results = {}
    
    for name, test_file in test_files:
        print(f"\n{'=' * 80}")
        print(f"Running: {name}")
        print(f"File: {test_file}")
        print(f"{'=' * 80}\n")
        
        try:
            result = subprocess.run(
                ["pytest", test_file, "-v", "--tb=short"],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            results[name] = {
                "returncode": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr
            }
            
            print(result.stdout)
            if result.stderr:
                print("STDERR:", result.stderr)
            
            if result.returncode == 0:
                print(f"\n✅ {name}: PASSED")
            else:
                print(f"\n❌ {name}: FAILED")
                
        except subprocess.TimeoutExpired:
            print(f"\n⏱️  {name}: TIMEOUT")
            results[name] = {"returncode": -1, "error": "timeout"}
        except FileNotFoundError:
            print(f"\n⚠️  {name}: FILE NOT FOUND")
            results[name] = {"returncode": -1, "error": "not found"}
        except Exception as e:
            print(f"\n❌ {name}: ERROR - {str(e)}")
            results[name] = {"returncode": -1, "error": str(e)}
    
    # Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    
    passed = sum(1 for r in results.values() if r.get("returncode") == 0)
    failed = sum(1 for r in results.values() if r.get("returncode") != 0)
    
    for name, result in results.items():
        status = "✅ PASSED" if result.get("returncode") == 0 else "❌ FAILED"
        print(f"{name:40} {status}")
    
    print(f"\nTotal: {len(results)} test suites")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    
    if failed == 0:
        print("\n🎉 All tests passed!")
        return 0
    else:
        print(f"\n⚠️  {failed} test suite(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(run_tests())
