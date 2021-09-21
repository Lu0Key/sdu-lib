from bs4 import BeautifulSoup
import requests
import execjs
import json
import time
import os
import datetime

# 10 六层走廊
# 58 D616室
#  8 D603室
#  9 D604室（安静区）
# 11 D610室
area = 10
area = str(area)
segment = 2835944
segment = str(segment)

basepath = os.path.dirname(os.path.realpath(__file__))+"\\"

# 读取账号密码
info = {}
with open(basepath+"info.json") as f:
    info = json.loads(f.read())
    f.close()

# 等到第二天一开始才抢座位
while True:
    time.sleep(10)
    if time.strftime("%H:%M", time.localtime()) == "00:02":
        break

# 获取第二天
def getTomorrow(): 
    today=datetime.date.today() 
    oneday=datetime.timedelta(days=1) 
    yesterday=today+oneday  
    return yesterday

day = str(getTomorrow())


# 登录所需数据
data = {
    "ul":str(len(info["username"])),
    "pl":str(len(info["password"])),
    "lt":"",
    "execution":"",
    "_eventId":"",
    "rsa":""
}

def get_rsa():
    js = ""
    with open(basepath+"des.js",encoding="utf-8") as f:
        js = f.read()
        f.close()
    rsa = execjs.compile(js).call('strEnc', info["username"]+info["password"]+data["lt"],"1","2","3")
    return rsa

def book(id,send_cookies):
    request_data = {
        "access_token":send_cookies["access_token"],
        "userid":send_cookies["userid"],
        "segment":segment,
        "type":"1",
        "operateChannel":"2"
    }
    base_headers = {
        "Origin":"http://seat.lib.sdu.edu.cn",
        "Host":"seat.lib.sdu.edu.cn",
        "User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:92.0) Gecko/20100101 Firefox/92.0",
        "Referer":"http://seat.lib.sdu.edu.cn/web/seat3?area="+area+"&segment=2835944&day="+day+"&startTime=08:00&endTime=17:30"
    }
    send_cookies["redirect_url"]="/home/web/seat2/area/3/day/"+day
    resp = requests.post("http://seat.lib.sdu.edu.cn/api.php/spaces/"+str(id)+"/book",cookies=send_cookies,data=request_data,headers=base_headers)
    # print("---------------------------")
    # print(id,send_cookies,request_data)
    return resp

def auto_check(url,send_cookies):
    base_headers = {
        "Origin":"http://seat.lib.sdu.edu.cn",
        "Host":"seat.lib.sdu.edu.cn",
        "User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:92.0) Gecko/20100101 Firefox/92.0"
    }
    url = "http://seat.lib.sdu.edu.cn/cas/index.php?callback=http://seat.lib.sdu.edu.cn/web/seat3?area="+area+"&segment="+segment+"&day="+day+"&startTime=08:00&endTime=22:30"
    send_cookies["uservisit"] = "1"
    resp = requests.get(url=url,headers=headers,cookies=send_cookies)
    print("\nsend_cookies",send_cookies)
    print("==============================")
    for cookie in resp.cookies:
        send_cookies[cookie.name]=cookie.value
    send_cookies["redirect_url"] = "/user/index/book"
    # send_cookies.pop("uservisit")
    # print("new send_cookies",send_cookies)
    # print("status_code",resp.status_code)
    return send_cookies


# 登录
headers = {
    "User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:92.0) Gecko/20100101 Firefox/92.0"
}

url = "http://pass.sdu.edu.cn/cas/login?service=http%3A%2F%2Fseat.lib.sdu.edu.cn%2Fcas%2Findex.php%3Fcallback%3Dhttp%3A%2F%2Fseat.lib.sdu.edu.cn%2Fweb%2Fseat3%3Farea%3D10%26segment%3D2601158%26day%3D"+day+"%26startTime%3D08%3A00%26endTime%3D22%3A30"

resp = requests.get(url,headers=headers)
cookies = {
    "JSESSIONID":resp.cookies.get("JSESSIONID"),
    "Language":"zh_CN"
}
soup = BeautifulSoup(resp.text,"lxml")
lt = soup.select_one("#lt")
data["lt"] = lt.get("value")
execution = soup.select_one("[name=execution]")
data["execution"] = execution.get("value")
eventId = soup.select_one("[name=_eventId]")
data["_eventId"] = eventId.get("value")
data["rsa"] = get_rsa()

# 进行第一次跳转
url = "http://pass.sdu.edu.cn/cas/login?service=http://seat.lib.sdu.edu.cn/cas/index.php?callback=http://seat.lib.sdu.edu.cn/web/seat3?area=10&segment=2601158&day="+day+"&startTime=08:00&endTime=22:30"
resp = requests.post(url,data=data,headers=headers,cookies=cookies)
print(resp.cookies)
# print(resp.status_code)
list = resp.history
list.append(resp)
cookies = {}
for item in list:
    item_cookies = item.cookies
    for cookie in item_cookies:
        cookies[cookie.name]=cookie.value
cookies["redirect_url"]="/web/seat2/area/3"
# cookies.pop("CASTGC")
cookies.pop("Language")
print(cookies)

# 登录结束

headers["Host"]="seat.lib.sdu.edu.cn"
headers["Referer"] = "http://seat.lib.sdu.edu.cn/home/web/seat2/area/3/day/"+day

# 获取segment
resp = requests.get("http://seat.lib.sdu.edu.cn/api.php/v3areas/3/date/"+day,headers=headers,cookies=cookies)
segment_data = json.loads(resp.text.encode('utf-8').decode('unicode_escape'))
if segment_data["status"] == 1:
    areas = segment_data["data"]["list"]["childArea"]
    for A in areas:
        if A["id"] == int(area):
            segment = str(A["area_times"]["data"]["list"][0]["bookTimeId"])
            print("GET segment",A["area_times"]["data"]["list"][0]["bookTimeId"])
            break
else:
    print(segment_data)

headers["Referer"]="http://seat.lib.sdu.edu.cn/web/seat3?area="+area+"&segment="+segment+"&day="+day+"&startTime=08:00&endTime=22:30"
resp = requests.get("http://seat.lib.sdu.edu.cn/api.php/spaces_old?area="+area+"&segment="+segment+"&day="+day+"&startTime=08:00&endTime=22:30",headers=headers,cookies=cookies)

print(resp.text.encode('utf-8').decode('unicode_escape'))



count = 0
jsonObj = json.loads(resp.text.encode('utf-8').decode('unicode_escape'))
if jsonObj["status"] == 1:
    seatslist = jsonObj["data"]["list"]
    for seat in seatslist:
        if seat["status_name"] == "空闲":
            count = count + 1
            print(seat["id"])
            resp = book(seat["id"],cookies)
            # print(resp.text)
            # new_cookies = auto_check("",cookies)
            # time.sleep(2)
            # resp = book(seat["id"],new_cookies)
            print(resp.text.encode('utf-8').decode('unicode_escape'))
            respjson = json.loads(resp.text.encode('utf-8').decode('unicode_escape'))
            print(respjson["msg"])
            if respjson["status"] == 1:
                break
            else:
                continue
else:
    print("获取信息失败")

if count == 0:
    print("座位已满")
