﻿# import
import os
import tweepy
import datetime
import json
import dropbox
import urllib
import requests
import pickle

# グローバル変数
CFID = []
TwitterID = []
lastSubID = {}

# Dropbox からダウンロード
def downloadFromDropbox():
    
    # グローバル変数
    global CFID
    global TwitterID
    global lastSubID

    # Dropbox オブジェクトの生成
    dbx = dropbox.Dropbox(os.environ["DROPBOX_KEY"])
    dbx.users_get_current_account()

    # CFID をダウンロード
    dbx.files_download_to_file("cper_bot/CF/CFID.txt", "/cper_bot/CF/CFID.txt")
    with open("cper_bot/CF/CFID.txt", "r") as f:
        CFID.clear()
        for id in f:
            CFID.append(id.rstrip("\n"))
    print("cper_bot-CF-detection: Downloaded CFID (size : ", str(len(CFID)), ")")
    
    # TwitterID をダウンロード
    dbx.files_download_to_file("cper_bot/CF/TwitterID.txt", "/cper_bot/CF/TwitterID.txt")
    with open("cper_bot/CF/TwitterID.txt", "r") as f:
        TwitterID.clear()
        for id in f:
            TwitterID.append(id.rstrip("\n"))
    print("cper_bot-CF-detection: Downloaded TwitterID (size : ", str(len(TwitterID)), ")")
    
    # lastSubID をダウンロード
    dbx.files_download_to_file("cper_bot/CF/lastSubID.txt", "/cper_bot/CF/lastSubID.txt")
    with open("cper_bot/CF/lastSubID.txt", "rb") as f:
        lastSubID = pickle.load(f)
    print("cper_bot-CF-detection: Downloaded lastSubID (size : ", str(len(lastSubID)), ")")

# Dropbox にアップロード
def uploadToDropbox():
    
    # グローバル変数
    global lastSubID

    # Dropbox オブジェクトの生成
    dbx = dropbox.Dropbox(os.environ["DROPBOX_KEY"])
    dbx.users_get_current_account()
    
    # lastSubID をアップロード
    with open("cper_bot/CF/lastSubID.txt", "wb") as f:
        pickle.dump(lastSubID, f)
    with open("cper_bot/CF/lastSubID.txt", "rb") as f:
        dbx.files_delete("/cper_bot/CF/lastSubID.txt")
        dbx.files_upload(f.read(), "/cper_bot/CF/lastSubID.txt")
    print("cper_bot-CF-detection: Uploaded lastSubID (size : ", str(len(lastSubID)), ")")

def detection():
    
    # グローバル変数
    global CFID
    global TwitterID
    global lastSubID
    
    # 各種キー設定
    CK = os.environ["CONSUMER_KEY"]
    CS = os.environ["CONSUMER_SECRET"]
    AT = os.environ["ACCESS_TOKEN_KEY"]
    AS = os.environ["ACCESS_TOKEN_SECRET"]
    
    # Twitter オブジェクトの生成
    auth = tweepy.OAuthHandler(CK, CS)
    auth.set_access_token(AT, AS)
    api = tweepy.API(auth)
    
    # 時刻表示を作成
    timeStamp = datetime.datetime.today()
    timeStamp = str(timeStamp.strftime("%Y/%m/%d %H:%M"))
    
    # データをダウンロード
    downloadFromDropbox()

    # 提出を解析
    idx = 0
    for user in CFID:
        subsJsonRes = urllib.request.urlopen("https://codeforces.com/api/user.status?handle=" + str(user))
        subsJsonData = json.loads(subsJsonRes.read().decode("utf-8"))
        if user in lastSubID:
            for sub in subsJsonData["result"]:
                if int(sub["id"]) <= lastSubID[user]:
                    break
                if "verdict" in sub:
                    if str(sub["verdict"]) == "OK":
                        try:
                            api.update_status(user + " ( @" + TwitterID[idx] + " ) さんが <Codeforces> " + str(sub["problem"]["name"]) + " を AC しました！\n" + "https://codeforces.com/contest/" + str(sub["contestId"]) + "/submission/" + str(sub["id"]) + "\n" + timeStamp)
                            print("cper_bot-CF-detection: " + user + " ( @" + TwitterID[idx] + " ) 's new AC submission (problem : " + str(sub["problem"]["name"]) + ")")
                        except:
                            print("cper_bot-CF-detection: Tweet Error")
        lastSubID[user] = int(subsJsonData["result"][0]["id"])
        idx = idx + 1

    # データをアップロード
    uploadToDropbox()

if __name__ == '__main__':
    print("cper_bot-CF-detection: Running as debug...")
    detection()
    print("cper_bot-CF-detection: Debug finished")