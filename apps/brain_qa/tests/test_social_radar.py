import requests
import json

def test_social_radar():
    url = "http://localhost:8765/social/radar/scan"
    payload = {
        "url": "https://www.instagram.com/p/C_abc123/",
        "metadata": {
            "likes": 1200,
            "comments": 45,
            "followers": 50000,
            "recent_comments": ["Bagus banget!", "Keren gan", "Beli dimana?", "Pelayanan lambat kecewa"]
        }
    }
    try:
        r = requests.post(url, json=payload)
        print(f"Status: {r.status_code}")
        print(json.dumps(r.json(), indent=2))
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_social_radar()
