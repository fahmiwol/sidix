import sys
from pathlib import Path

# Setup path
_BRAIN_QA = Path(__file__).resolve().parents[1]
if str(_BRAIN_QA) not in sys.path:
    sys.path.insert(0, str(_BRAIN_QA))

from brain_qa.social_radar import analyze_social_context

def test_radar_logic():
    print("Testing Social Radar Logic...")
    
    # Case 1: High engagement, Micro tier
    meta1 = {
        "likes": 500,
        "comments": 50,
        "followers": 5000,
        "recent_comments": ["Bagus", "Mantap", "Keren"]
    }
    res1 = analyze_social_context("http://ig.com/p1", meta1)
    assert res1["metrics"]["engagement_rate"] == 11.0
    assert res1["metrics"]["tier"] == "micro"
    print("[PASS] Case 1: High engagement/Micro")
    
    # Case 2: Negative sentiment
    meta2 = {
        "likes": 100,
        "comments": 10,
        "followers": 1000,
        "recent_comments": ["Kecewa", "Mahal", "Lambat"]
    }
    res2 = analyze_social_context("http://ig.com/p2", meta2)
    assert res2["metrics"]["sentiment"] < 0
    assert "krisis kepercayaan" in res2["advice"]
    print("[PASS] Case 2: Negative sentiment advice")
    
    # Case 3: Leader tier
    meta3 = {
        "likes": 10000,
        "comments": 200,
        "followers": 150000,
        "recent_comments": ["Beli dimana?"]
    }
    res3 = analyze_social_context("http://ig.com/p3", meta3)
    assert res3["metrics"]["tier"] == "leader"
    print("[PASS] Case 3: Leader tier")
    
    print("\nALL RADAR LOGIC TESTS PASSED!")

if __name__ == "__main__":
    test_radar_logic()
