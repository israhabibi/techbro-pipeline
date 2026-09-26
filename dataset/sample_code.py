# Techbro Twitter Indonesia Dataset - Sample Code

# Dataset: https://www.kaggle.com/datasets/israhabibi/techbro-twitter-indonesia

# Tiga file CSV:
# - techbro_tweets.csv  : 1 baris per tweet (granular)
# - techbro_activity.csv: 1 baris per (hari x user) - gampang di-groupby
# - techbro_topics.csv  : 1 baris per topik hangat (ada kolom days)

import pandas as pd

# ---------- Load ----------
tweets = pd.read_csv("techbro_tweets.csv")
activity = pd.read_csv("techbro_activity.csv")
topics = pd.read_csv("techbro_topics.csv")

print("tweets  :", tweets.shape)
print("activity:", activity.shape)
print("topics  :", topics.shape)

# ---------- 1. Tweet per hari ----------
tweets_per_day = activity.groupby("day")["tweet_count"].sum().sort_index()
print("\nTotal tweet per hari (head):")
print(tweets_per_day.head())

# ---------- 2. User paling aktif (akumulasi) ----------
top_users = (activity.groupby("user_handle")["tweet_count"]
             .sum().sort_values(ascending=False).head(10))
print("\nTop 10 user paling aktif:")
print(top_users)

# ---------- 3. User paling aktif di hari tertentu ----------
hari = tweets["day"].max()
print("User paling aktif di " + str(hari) + ":")
print(activity[activity["day"] == hari]
      .sort_values("tweet_count", ascending=False).head(5))

# ---------- 4. Topik hangat + hari muncul ----------
print("\nTopik hangat:")
for _, r in topics.iterrows():
    print("  - " + str(r["topic"]) + " (" + str(r["tweet_count"]) + " tweet, hari: " + str(r["days"]) + ")")
    print("    " + str(r["summary"])[:100])

# ---------- 5. Filter tweet per user ----------
user = "ainunnajib"
print("\nSample tweet @" + user + ":")
print(tweets[tweets["user_handle"] == user]["text"].head(3).to_list())

# ---------- 6. Cari tweet yang mengandung keyword ----------
for kw in ["AI", "rust", "startup"]:
    n = tweets["text"].str.contains(kw, case=False, na=False).sum()
    print("Tweet mengandung '" + kw + "': " + str(n))
