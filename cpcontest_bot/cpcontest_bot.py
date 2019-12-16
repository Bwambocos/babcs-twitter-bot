﻿# import
import subprocess
import datetime
from apscheduler.schedulers.blocking import BlockingScheduler
import followBack
import getLiveContestID
import FA
import updateHighestScore
import ranking

# インスタンス化
sched = BlockingScheduler(job_defaults = {'max_instances' : 10})
    
# フォロバ（毎時 0, 20, 40 分）
@sched.scheduled_job('cron', minute = '0, 20, 40', hour = '*/1')
def scheduled_job():

    print("cpcontest_bot: ----- followBack Start -----")
    followBack.followBack()
    print("cpcontest_bot: ----- followBack End -----")

liveContestIDs = []

# 開催中のコンテストを取得
@sched.scheduled_job('interval', seconds = 30)
def scheduled_job():
    
    print("cpcontest_bot: ----- getLiveContestID Start -----")

    global liveContestIDs
    liveContestIDs = getLiveContestID.get()

    print("cpcontest_bot: ----- getLiveContestID End -----")

@sched.scheduled_job('interval', seconds = 60)
def scheduled_job():
    
    global liveContestIDs
    if len(liveContestIDs) > 0:
        
        # FA を見つける
        print("cpcontest_bot: ----- FA Start -----")
        FA.FA(liveContestIDs)
        print("cpcontest_bot: ----- FA End -----")

        # 問題ごとの最高得点更新を検知
        print("cpcontest_bot: ----- updateHighestScore Start -----")
        updateHighestScore.updateHighestScore(liveContestIDs)
        print("cpcontest_bot: ----- updateHighestScore End -----")

        # 20 位以内に浮上したユーザーを検知
        print("cpcontest_bot: ----- ranking Start -----")
        ranking.ranking(liveContestIDs)
        print("cpcontest_bot: ----- ranking End -----")

# おまじない
sched.start()
