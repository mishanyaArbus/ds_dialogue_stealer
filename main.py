import requests as r
from tqdm import tqdm
import pickle
from analizer import analyze

s = r.Session()

s.headers["authorization"] = "ODgzODg5OTcxNjI5NTM5MzU5.YaeIkQ.xMblva0qbNE5rtAOx2kmGC3QcZc"

#getting the messages
num_of_msgs = int(input("Num of messages to parse --> "))
chat_id = input("Chat id --> ")
lim = 100

msg_list = []

resp = s.get(f"https://discord.com/api/v9/channels/{chat_id}/messages?limit={lim}").json()
#print("resp",[a['id'] for a in resp])

last_msg_id = resp[len(resp)-1]["id"]

msg_list.extend(resp)

for i in tqdm(range(round(num_of_msgs/100)), desc="collection"):
    temp_after_msg_list = s.get(f"https://discord.com/api/v9/channels/{chat_id}/messages?before={last_msg_id}&limit={lim}").json()
    try:
        last_msg_id = temp_after_msg_list[-1]["id"]
    except:
        break
    msg_list.extend(last_msg_id)

#end getting the messages

#saving the messages
pickle.dump(msg_list, open("saved_msgs",'wb'))

analyze(msg_list)