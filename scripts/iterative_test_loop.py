"""
Iterative Test Loop for ProjectScout Advanced Rules

This script runs all tests in a loop, reports results, and allows for iterative debugging.
It continues until all tests pass or the user stops it.
"""

import asyncio
import sys
import os
import time
from datetime import datetime

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from test_advanced_rules import run_all_tests, print_results


def print_header():
    """Print a nice header"""
    print("\n" + "="*80)
    print("🔄 PROJECTSCOUT ITERATIVE TEST LOOP")
    print("="*80)
    print("This will run all advanced rules tests repeatedly until they all pass.")
    print("Press Ctrl+C to stop at any time.")
    print("="*80 + "\n")


def print_iteration_header(iteration: int):
    """Print iteration header"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"\n{'='*80}")
    print(f"🔄 ITERATION #{iteration} - {timestamp}")
    print(f"{'='*80}\n")


async def run_iteration(iteration: int) -> tuple[int, int]:
    """Run one iteration of tests"""
    print_iteration_header(iteration)
    
    print("Running all tests...\n")
    results = await run_all_tests()
    passed, failed = print_results(results)
    
    return passed, failed


def analyze_failures(failed_count: int):
    """Provide analysis and suggestions for failures"""
    print("\n" + "="*80)
    print("📊 FAILURE ANALYSIS")
    print("="*80)
    
    if failed_count > 10:
        print("⚠️  Many tests are failing. Possible issues:")
        print("   - Check if OpenAI API key is set correctly")
        print("   - Verify that advanced_rules.py is imported correctly")
        print("   - Check for syntax errors in agent.py")
    elif failed_count > 5:
        print("⚠️  Several tests are failing. Possible issues:")
        print("   - Some rule detection functions may need adjustment")
        print("   - Check regex patterns in advanced_rules.py")
    elif failed_count > 0:
        print("⚠️  A few tests are failing. Possible issues:")
        print("   - Fine-tune detection keywords or patterns")
        print("   - Review test expectations vs. actual behavior")
    
    print("="*80 + "\n")


async def main():
    """Main iterative test loop"""
    print_header()
    
    iteration = 1
    total_passed = 0
    total_failed = 0
    
    try:
        while True:
            passed, failed = await run_iteration(iteration)
            
            total_passed = passed
            total_failed = failed
            
            if failed == 0:
                print("\n" + "🎉"*40)
                print("✅ ALL TESTS PASSED! 🎉")
                print("🎉"*40 + "\n")
                print("The ProjectScout agent is ready for demo!")
                break
            else:
                analyze_failures(failed)
                
                print(f"\n⏸️  Iteration #{iteration} complete.")
                print(f"   Passed: {passed}/{passed + failed}")
                print(f"   Failed: {failed}/{passed + failed}")
                
                # Ask user if they want to continue
                try:
                    user_input = input("\n▶️  Continue to next iteration? (y/n/auto): ").strip().lower()
                    
                    if user_input == 'n':
                        print("\n🛑 Stopping test loop.")
                        break
                    elif user_input == 'auto':
                        print("\n🤖 Entering auto mode. Tests will run continuously.")
                        print("   Press Ctrl+C to stop.\n")
                        # Continue automatically
                        time.sleep(2)  # Brief pause between iterations
                    else:
                        # Default to yes
                        pass
                        
                except KeyboardInterrupt:
                    print("\n\n🛑 Test loop interrupted by user.")
                    break
            
            iteration += 1
            
    except KeyboardInterrupt:
        print("\n\n🛑 Test loop interrupted by user.")
    
    # Final summary
    print("\n" + "="*80)
    print("📊 FINAL SUMMARY")
    print("="*80)
    print(f"Total Iterations: {iteration}")
    print(f"Final Results: {total_passed} passed, {total_failed} failed")
    
    if total_failed == 0:
        print("\n✅ Status: READY FOR DEMO")
        return 0
    else:
        print(f"\n❌ Status: {total_failed} test(s) still failing")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
