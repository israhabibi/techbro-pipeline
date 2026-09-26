import os
os.environ["DATA_DIR"] = "/home/isra_habibi/techbro/data"
import main
days = main._load_all_topics()
print("days loaded:", len(days))
for d in days[:3]:
    print(" ", d["date"], "topics:", len(d["topics"]), "| first:", d["topics"][0]["topic"] if d["topics"] else "-")
print("last:", days[-1]["date"] if days else "-")
