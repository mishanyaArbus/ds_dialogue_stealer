import requests as r
from tqdm import tqdm
from threading import Thread
import queue
import random
from time import sleep

import os

s = r.Session()

s.headers["authorization"] = input("Discord token --> ")

threads = int(input("Threads --> "))
chat_id = input("Chat id --> ")

chat_name = s.get(f"https://discord.com/api/v9/channels/{chat_id}").json()['name']

if not os.path.exists(chat_name):
    os.mkdir(chat_name)

print(f"Dialogues will be saved to {chat_name}")

num_of_root = int(input("Num of end messages to find --> "))
lim = 100

msg_list = []

resp = s.get(f"https://discord.com/api/v9/channels/{chat_id}/messages?limit={lim}").json()
#print("resp",[a['id'] for a in resp])

last_msg_id = resp[len(resp)-1]["id"]

msg_list.extend(resp)

def getmsg(ses: r.Session, l_chat_id, l_last_id):
    l_resp = ses.get(f"https://discord.com/api/v9/channels/{l_chat_id}/messages?limit=1&around={l_last_id}")

    if l_resp.status_code == 200:
        l_last_msg = l_resp.json()[0]

        return l_last_msg

    elif l_resp.status_code == 429:
        sleep(int(l_resp.json()['retry_after']))
        return getmsg(ses, l_chat_id, l_last_id)
    else:
        raise Exception(f"Got error {l_resp.status_code} {l_resp.text} while investigating {l_last_id}")

def investigate(ses: r.Session, end_msg):
    dialogue = []
    l_last_id = end_msg["message_reference"]["message_id"]
    l_chat_id = end_msg["message_reference"]["channel_id"]
    dialogue.append(end_msg['content'])
    while True:

        l_last_msg = getmsg(ses, l_chat_id, l_last_id)

        dialogue.append(l_last_msg['content'])

        if "message_reference" in l_last_msg:
            l_last_id = l_last_msg["message_reference"]["message_id"]
            l_chat_id = l_last_msg["message_reference"]["channel_id"]
        else:
            break

    #saving
    print(f"{q.qsize()} messages left to analyze")

    with open(os.path.join(chat_name, f"size {len(dialogue)}-{random.randint(100000, 999999)}.txt"),"a", encoding='utf-8') as file:
        for msg in dialogue[::-1]:
            file.write(msg+"\n")

def perform():
    while True:
        data = q.get()
        investigate(data["ses"], data["end_msg"])
        q.task_done()


for i in tqdm(range(round(num_of_root/100)), desc="collecting end messages"):
    temp_after_msg_list = s.get(f"https://discord.com/api/v9/channels/{chat_id}/messages?before={last_msg_id}&limit={lim}").json()
    try:
        last_msg_id = temp_after_msg_list[-1]["id"]
    except:
        break
    msg_list.extend(temp_after_msg_list)

#end getting the messages

#clean
seen_ids = {}
clean_msgs = []
# print(msg_list)
for msg in msg_list:
    # print(msg)

    if msg['id'] in seen_ids or ("message_reference" in msg and msg["message_reference"]["message_id"] in seen_ids):
        pass
    else:
        clean_msgs.append(msg)

    seen_ids[msg['id']] = 1
    if "message_reference" in msg:
        seen_ids[msg['message_reference']['message_id']] = 1

print(f"{len(msg_list)-len(clean_msgs)} cleaned messages")
#analize
q = queue.Queue()
print(f"Started analyzing")
for _ in range(threads):
    Thread(target=perform, daemon=True).start()

for last_msg in clean_msgs:
    if "message_reference" in last_msg:
        q.put({"ses":s, "end_msg":last_msg})

q.join()
print("done")