import json
import urllib.request
import os

with open("skins_map.json", "r", encoding="utf-8") as f:
    skins_map = json.load(f)

targets = {
    "skin_nomad.png": "Nomad Knife | Doppler",
    "skin_hyperbeast.png": "M4A1-S | Hyper Beast",
    "skin_mac10.png": "MAC-10 | Light Box",
    "skin_butterfly.png": "Butterfly Knife | Fade",
    "skin_dragonlore.png": "AWP | Dragon Lore",
    "skin_printstream.png": "Desert Eagle | Printstream",
    "skin_asiimov.png": "AWP | Asiimov",
    "skin_vulcan.png": "AK-47 | Vulcan",
    "skin_redline.png": "AK-47 | Redline",
    "skin_neonoair.png": "USP-S | Neo-Noir"
}

out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "webapp", "images")

for fname, sname in targets.items():
    found_url = None
    for k, u in skins_map.items():
        if sname.lower() in k.lower():
            found_url = u
            break
    if found_url:
        try:
            req = urllib.request.Request(found_url, headers={'User-Agent': 'Mozilla/5.0'})
            data = urllib.request.urlopen(req, timeout=10).read()
            with open(os.path.join(out_dir, fname), "wb") as f:
                f.write(data)
            print(f"Yuklandi: {fname} ({sname})")
        except Exception as e:
            print(f"Xato ({fname}): {e}")

print("Tugadi!")
