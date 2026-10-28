"""
test_e2e_sanad_hafidz.py — End-to-end test for Sprint A+B

Test OMNYX Direction dengan Sanad Orchestra + Hafidz Injection.
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from brain_qa.omnyx_direction import omnyx_process


async def main():
    print("=== E2E Test: Sanad Orchestra + Hafidz Injection ===\n")
    
    # Test 1: Simple factual query
    print("Test 1: Simple factual query")
    result = await omnyx_process("siapa presiden indonesia?", persona="AYMAN")
    print(f"  Answer: {result.get('answer', '')[:150]}...")
    print(f"  Complexity: {result.get('complexity', '')}")
    print(f"  Sanad score: {result.get('sanad_score', 0):.3f}")
    print(f"  Sanad verdict: {result.get('sanad_verdict', '')}")
    print(f"  Hafidz injected: {result.get('hafidz_injected', False)}")
    print(f"  Hafidz stored: {result.get('hafidz_stored', False)}")
    print(f"  Duration: {result.get('duration_ms', 0)}ms")
    print()
    
    # Test 2: Creative query
    print("Test 2: Creative query")
    result2 = await omnyx_process("buat puisi tentang cinta", persona="UTZ")
    print(f"  Answer: {result2.get('answer', '')[:150]}...")
    print(f"  Complexity: {result2.get('complexity', '')}")
    print(f"  Sanad score: {result2.get('sanad_score', 0):.3f}")
    print(f"  Sanad verdict: {result2.get('sanad_verdict', '')}")
    print(f"  Hafidz stored: {result2.get('hafidz_stored', False)}")
    print(f"  Duration: {result2.get('duration_ms', 0)}ms")
    print()
    
    # Test 3: Check Sanad stats endpoint
    print("Test 3: Sanad stats")
    from brain_qa.sanad_orchestra import SanadOrchestra
    orchestra = SanadOrchestra()
    stats = orchestra.get_stats()
    print(f"  Stats: {stats}")
    print()
    
    # Test 4: Check Hafidz stats
    print("Test 4: Hafidz stats")
    from brain_qa.hafidz_injector import HafidzInjector
    injector = HafidzInjector()
    stats = injector.get_stats()
    print(f"  Stats: {stats}")
    print()
    
    print("=== E2E Test Complete ===")


if __name__ == "__main__":
    asyncio.run(main())
