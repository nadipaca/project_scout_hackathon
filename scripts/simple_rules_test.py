"""
Simplified test runner that writes output to file for debugging
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from agi_agents.project_scout import advanced_rules

def test_all_rules():
    """Test all rules and write results to file"""
    results = []
    
    # Test 1: Motivation Detection
    try:
        state = advanced_rules.detect_motivation_state("I'm overwhelmed")
        results.append(f"✅ Test 1 (Motivation): {state}")
    except Exception as e:
        results.append(f"❌ Test 1 (Motivation): {str(e)}")
    
    # Test 2: Constraint Conflict
    try:
        conflict = advanced_rules.detect_constraint_conflicts("advanced", "weekend", "distributed")
        results.append(f"✅ Test 2 (Conflict): {bool(conflict)}")
    except Exception as e:
        results.append(f"❌ Test 2 (Conflict): {str(e)}")
    
    # Test 3: Ambiguity Cooldown
    try:
        cooldown = advanced_rules.should_apply_ambiguity_cooldown(2, ["idk", "whatever"])
        results.append(f"✅ Test 3 (Cooldown): {cooldown}")
    except Exception as e:
        results.append(f"❌ Test 3 (Cooldown): {str(e)}")
    
    # Test 4: Skill Bridge
    try:
        bridge = advanced_rules.detect_skill_bridge_opportunity("I'm good at Python but new to React")
        results.append(f"✅ Test 4 (Bridge): {bool(bridge)}")
    except Exception as e:
        results.append(f"❌ Test 4 (Bridge): {str(e)}")
    
    # Test 5: Inspiration
    try:
        inspire = advanced_rules.detect_inspiration_need("I'm bored")
        results.append(f"✅ Test 5 (Inspiration): {inspire}")
    except Exception as e:
        results.append(f"❌ Test 5 (Inspiration): {str(e)}")
    
    # Test 6: Trending
    try:
        trending = advanced_rules.detect_trending_request("What's hot in AI?")
        results.append(f"✅ Test 6 (Trending): {trending}")
    except Exception as e:
        results.append(f"❌ Test 6 (Trending): {str(e)}")
    
    # Test 7: Upgrade
    try:
        upgrade = advanced_rules.detect_upgrade_intent("I have a Flask app")
        results.append(f"✅ Test 7 (Upgrade): {bool(upgrade)}")
    except Exception as e:
        results.append(f"❌ Test 7 (Upgrade): {str(e)}")
    
    # Test 8: Locale
    try:
        locale = advanced_rules.detect_locale_or_market("Building for Indian market")
        results.append(f"✅ Test 8 (Locale): {bool(locale)}")
    except Exception as e:
        results.append(f"❌ Test 8 (Locale): {str(e)}")
    
    # Test 9: Privacy
    try:
        privacy = advanced_rules.detect_privacy_concerns("No cloud APIs please")
        results.append(f"✅ Test 9 (Privacy): {privacy}")
    except Exception as e:
        results.append(f"❌ Test 9 (Privacy): {str(e)}")
    
    # Test 10: Quality
    try:
        quality = advanced_rules.analyze_quality_emphasis("Need production-ready with tests")
        results.append(f"✅ Test 10 (Quality): {quality['quality_focus']}")
    except Exception as e:
        results.append(f"❌ Test 10 (Quality): {str(e)}")
    
    # Test 11: Portfolio
    try:
        narrative = advanced_rules.generate_portfolio_narrative("Test Project", "AI", "For FAANG job")
        results.append(f"✅ Test 11 (Portfolio): {len(narrative) > 0}")
    except Exception as e:
        results.append(f"❌ Test 11 (Portfolio): {str(e)}")
    
    return results

if __name__ == "__main__":
    print("Running simplified advanced rules tests...")
    results = test_all_rules()
    
    # Write to file
    with open("test_results.txt", "w") as f:
        f.write("ADVANCED RULES TEST RESULTS\n")
        f.write("="*50 + "\n\n")
        for result in results:
            f.write(result + "\n")
            print(result)
        
        passed = sum(1 for r in results if r.startswith("✅"))
        failed = sum(1 for r in results if r.startswith("❌"))
        
        f.write(f"\n{'='*50}\n")
        f.write(f"SUMMARY: {passed}/{len(results)} passed\n")
        print(f"\nSUMMARY: {passed}/{len(results)} passed")
        
    print("\nResults written to test_results.txt")
    sys.exit(0 if failed == 0 else 1)
