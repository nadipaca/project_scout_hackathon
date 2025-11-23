"""Quick test to verify advanced rules work"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from agi_agents.project_scout import advanced_rules

# Test 1: Motivation Detection
print("Test 1: Motivation Detection")
result = advanced_rules.detect_motivation_state("I'm overwhelmed and stuck")
print(f"  Result: {result}")
print(f"  Expected: overwhelmed")
print(f"  ✅ PASS" if result == "overwhelmed" else f"  ❌ FAIL")
print()

# Test 2: Constraint Conflict
print("Test 2: Constraint Conflict Detection")
result = advanced_rules.detect_constraint_conflicts("advanced", "weekend", "distributed systems")
print(f"  Result: {result}")
print(f"  Expected: Some conflict message")
print(f"  ✅ PASS" if result else f"  ❌ FAIL")
print()

# Test 3: Ambiguity Cooldown
print("Test 3: Ambiguity Cooldown")
result = advanced_rules.should_apply_ambiguity_cooldown(2, ["I don't know", "whatever"])
print(f"  Result: {result}")
print(f"  Expected: True")
print(f"  ✅ PASS" if result else f"  ❌ FAIL")
print()

# Test 4: Skill Bridge
print("Test 4: Skill Bridge Detection")
result = advanced_rules.detect_skill_bridge_opportunity("I'm good at Python but new to React")
print(f"  Result: {result}")
print(f"  Expected: Dict with bridge_needed=True")
print(f"  ✅ PASS" if result and result.get('bridge_needed') else f"  ❌ FAIL")
print()

# Test 5: Privacy Detection
print("Test 5: Privacy Detection")
result = advanced_rules.detect_privacy_concerns("I don't want to use cloud APIs")
print(f"  Result: {result}")
print(f"  Expected: True")
print(f"  ✅ PASS" if result else f"  ❌ FAIL")
print()

print("\n✅ Quick test complete!")
