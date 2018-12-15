﻿# import
import os
import tweepy
import datetime
import json
import dropbox
import urllib
from bs4 import BeautifulSoup
import requests
import pickle

# グローバル変数
AtCoderID = []
TwitterID = []
lastSubID = {}

# Dropbox からダウンロード
def downloadFromDropbox():
    
    # グローバル変数
    global AtCoderID
    global TwitterID
    global lastSubID

    # Dropbox オブジェクトの生成
    dbx = dropbox.Dropbox(os.environ["DROPBOX_KEY"])
    dbx.users_get_current_account()

    # AtCoderID をダウンロード
    dbx.files_download_to_file("AtCoderID.txt", "/AtCoderID.txt")
    with open("AtCoderID.txt", "r") as f:
        AtCoderID.clear()
        for id in f:
            AtCoderID.append(id.rstrip("\n"))
    print("detection: Downloaded AtCoderID (size : ", str(len(AtCoderID)), ")")
    
    # TwitterID をダウンロード
    dbx.files_download_to_file("TwitterID.txt", "/TwitterID.txt")
    with open("TwitterID.txt", "r") as f:
        TwitterID.clear()
        for id in f:
            TwitterID.append(id.rstrip("\n"))
    print("detection: Downloaded TwitterID (size : ", str(len(TwitterID)), ")")
    
    #lastSubID をダウンロード
    dbx.files_download_to_file("lastSubID.txt", "/lastSubID.txt")
    with open("lastSubID.txt", "rb") as f:
        lastSubID = pickle.load(f)
    print("detection: Downloaded lastSubID (size : ", str(len(lastSubID)), ")")

# Dropbox にアップロード
def uploadToDropbox():
    
    # グローバル変数
    global lastSubID

    # Dropbox オブジェクトの生成
    dbx = dropbox.Dropbox(os.environ["DROPBOX_KEY"])
    dbx.users_get_current_account()
    
    # lastSubID をアップロード
    with open("lastSubID.txt", "wb") as f:
        pickle.dump(lastSubID, f)
    with open("lastSubID.txt", "rb") as f:
        dbx.files_delete("/lastSubID.txt")
        dbx.files_upload(f.read(), "/lastSubID.txt")
    print("detection: Uploaded lastSubID (size : ", str(len(lastSubID)), ")")

def detection():
    
    # グローバル変数
    global AtCoderID
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

    # コンテストごとに提出を解析
    contestsJsonRes = urllib.request.urlopen("https://atcoder-api.appspot.com/contests")
    contestsJsonData = json.loads(contestsJsonRes.read().decode("utf-8"))
    for contest in contestsJsonData:

        # ページ送り
        sublistPageNum = 1
        subCount = 0

        while True:
            sublistURL = "https://beta.atcoder.jp/contests/" + str(contest["id"]) + "/submissions?page=" + str(sublistPageNum)
            sublistHTML = requests.get(sublistURL)
            try:
                sublistHTML.raise_for_status()
                sublistData = BeautifulSoup(sublistHTML.text, "html.parser")
            except:
                print("detection: sublistHTML Error")
                break
            sublistTable = sublistData.find_all("table", class_ = "table table-bordered table-striped small th-center")
            if len(sublistTable) == 0:
                break

            # １行ずつ解析
            sublistRows = sublistTable[0].find_all("tr")
            del sublistRows[0]
            skipFlag = False
            newLastSubID = lastSubID[str(contest["id"])]
            for row in sublistRows:
                links = row.find_all("a")
                subID = int(str(links[3].get("href")).split("/")[4])
                userID = str(links[1].get("href")).split("/")[2]
                if subID <= int(lastSubID[str(contest["id"])]):
                    skipFlag = True
                    break
                newLastSubID = max(newLastSubID, subID)
                subCount = subCount + 1

                # ユーザーの AC 提出かどうか判定
                subData = [cell.get_text() for cell in row.select("td")]
                idx = 0
                for ids in AtCoderID:
                    if userID == ids and subData[6] == "AC":
                        try:
                            api.update_status(userID + " ( @" + TwitterID[idx] + " ) さんが " + str(contest["title"]) + "：" + str(subData[1]) + " を AC しました！\n提出コード：" + "https://beta.atcoder.jp" + str(links[3].get("href")) + "\n" + timeStamp)
                            print("detection: " + userID + " ( @" + TwitterID[idx] + " ) 's new AC submission (contest : " + str(contest["title"]) + ", problem : " + str(subData[1]) + ")")
                        except:
                            print("detection: Tweet Error")
                    idx = idx + 1
            if skipFlag:
                break
            sublistPageNum = sublistPageNum + 1

        print("detection: Checked " + contest["title"] + " submissions (subCount : " + str(subCount) + ", newlastSubID : " + str(newLastSubID) + ")")
        lastSubID[str(contest["id"])] = newLastSubID

    # データをアップロード
    uploadToDropbox()