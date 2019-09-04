import json
import operator
import time
import datetime
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.db.models import Q

# Create your views here.
from attend.models import Events, Attendees, User, Room, Group


def calendar(request,pIndex):
    # 将新会议添加到数据库中
    meetings=Events.objects.all().order_by("-Id")
    if pIndex == '':
        pIndex = '8'
    people=Attendees.objects.filter(Eventid=pIndex).all()
    return render(request, 'meeting/calendar.html', {"meetings": meetings,"people": people,'pIndex':pIndex})

def isnewUser(request):#判断是否为新用户
    if request.method == "POST":
        print("openid: "+request.POST["openid"])
        #print("email: " + request.POST["email"])
        openid = request.POST["openid"]
        lists1 = User.objects.filter(Openid=openid).all()
        if (len(lists1) != 0):
              print('已存在该用户！')
              return HttpResponse(lists1[0].Address)
        else:
              print('这是一个新用户！')
              return HttpResponse("0")
    else:
        return HttpResponse("2")

def newUser(request):#新用户注册
    if request.method == "POST":
        openid=request.POST["openid"]
        email=request.POST["email"]
        group = request.POST["group"]
        user=User.objects.filter(Address=email).all()
        if(len(user)!=0):
            User.objects.filter(Address=email).update(Openid=openid,Group=group)
        else:
            User.objects.create(Openid=openid,Address=email,Group=group)
    return HttpResponse("2")

def attend2(request):#会议签到
    if request.method == "GET":
        email = request.GET["email"]
        loca = request.GET["location"]
        local=Room.objects.filter(Id=loca).all()#获取会议室真实name
        if len(local):
            for lo in local:
                location = lo.Meetingroom
        else:
            location="nolocation"
        localtime = time.strftime("%Y-%m-%d", time.localtime())
        now = datetime.datetime.now()
        start = now - datetime.timedelta( minutes=30)
        stop = now + datetime.timedelta(minutes=10)
        lists = Attendees.objects.filter(Meetingtime__gt=start,Meetingtime__lt=stop,Address=email).all().order_by("-Id")#获取近40分钟所有签到记录
        print(location)
        print(start)
        print(lists)
        json_list = []
        for a in lists:
            event = Events.objects.filter(Start__gte=start,Start__lte=stop,End__gte=now,Location__icontains=location).all()#获取近40分钟所有会议记录
            print(event)
            for i in event:
                if((str(i.Start.strftime("%Y-%m-%d"))==localtime)and(a.Eventid==i.Id)):
                    events_dict = {}
                    if(int(a.Isattend)==0):
                        events_dict["Istrue"] = 0
                        print(a.Isattend,type(a.Isattend))
                        localtime = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
                        if(localtime>str(a.Meetingtime)):
                            Attendees.objects.filter(Id=a.Id).update(Isattend=2, Attendtime=localtime)#迟到
                            a.Isattend=2
                        else:
                            Attendees.objects.filter(Id=a.Id).update(Isattend=1, Attendtime=localtime)#正常签到
                            a.Isattend = 1
                    elif((int(a.Isattend)==1)or(int(a.Isattend)==2)or(int(a.Isattend)==3)):
                        events_dict["Istrue"] = 1
                    events_dict["Attendid"] = a.Id
                    events_dict["Eventid"] = a.Eventid
                    events_dict["Subject"] = i.Subject
                    events_dict["Start"] =  str(i.Start.strftime("%H:%M:%S"))
                    events_dict["Location"] = i.Location
                    events_dict["Isattend"] = a.Isattend
                    if(str(a.Attendtime)!="None"):
                        events_dict["Attendtime"] = str(a.Attendtime.strftime("%H:%M:%S"))
                    else:
                        events_dict["Attendtime"] = ""
                    json_list.append(events_dict)
        print (len(json_list))
        ret1 = json.loads(json.dumps(json_list, ensure_ascii=False))
        return JsonResponse({"events": ret1}, json_dumps_params={'ensure_ascii': False})
        #return HttpResponse(json_list)
def attend(request):#未用到的会议签到
    if request.method == "POST":
        Attendid=request.POST["Attendid"]
        localtime = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        Attendees.objects.filter(Id=Attendid).update(Isattend="1",Attendtime=localtime)
    return HttpResponse("2")
def events(request):#用户个人当天会议列表
    if request.method == "GET":
        email = request.GET["email"]
        localtime = time.strftime("%Y-%m-%d", time.localtime())
        # lists = Events.objects.filter(Start=localtime).all().order_by("-Id")
        lists = Attendees.objects.filter(Address=email).all().order_by("Meetingtime")
        json_list = []
        for a in lists:
            if(int(a.Isattend)!=4):#如果a.isattend=4证明用户拒绝了该会议
                event = Events.objects.filter(Id=a.Eventid).all()
                if(str(event[0].Start.strftime("%Y-%m-%d"))==localtime):
                    local = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
                    if (int(a.Isattend) == 0):#如果用户没有签到且会议已经结束将用户签到属性改为3
                        if (local > str(event[0].End)):
                            Attendees.objects.filter(Id=a.Id).update(Isattend=3)
                            a.Isattend=3
                    events_dict={}
                    events_dict["Attendid"] = a.Id
                    events_dict["Eventid"] = a.Eventid
                    events_dict["Subject"] = event[0].Subject
                    events_dict["Start"] =  str(event[0].Start.strftime("%H:%M:%S"))
                    events_dict["End"] = str(event[0].End.strftime("%H:%M:%S"))
                    events_dict["Location"] = event[0].Location
                    events_dict["Isattend"] = a.Isattend
                    if(str(a.Attendtime)!="None"):
                        events_dict["Attendtime"] = str(a.Attendtime.strftime("%H:%M:%S"))
                    else:
                        events_dict["Attendtime"] = ""
                    json_list.append(events_dict)
        ret1 = json.loads(json.dumps(json_list, ensure_ascii=False))
        return JsonResponse({"events": ret1}, json_dumps_params={'ensure_ascii': False})
def detail(request):#返回会议详情
    if request.method == "GET":
        eventid = request.GET["Eventid"]
        #print("email: " + email)
        localtime = time.strftime("%Y-%m-%d", time.localtime())
        # lists = Events.objects.filter(Start=localtime).all().order_by("-Id")
        lists = Attendees.objects.filter(Eventid=eventid).all().order_by("-Id")
        Attendees_list = []#签到列表
        Truenum=0#正确签到的人数
        Falsenum=0
        Latenum=0

        for a in lists:
            if (int(a.Isattend) != 4):
                Attendees_dict={}
                Attendees_dict["Id"] = a.Id
                Attendees_dict["Name"] = a.Name
                Attendees_dict["Address"] = a.Address
                Attendees_dict["Isattend"] = a.Isattend
                if ((a.Isattend == 0)or(a.Isattend==3)):
                    Falsenum=Falsenum+1
                elif(a.Isattend == 1):
                    Truenum=Truenum+1
                else:
                    Latenum=Latenum+1
                if(str(a.Attendtime)!="None"):
                    Attendees_dict["Attendtime"] = str(a.Attendtime.strftime("%H:%M:%S"))
                else:
                    Attendees_dict["Attendtime"] = ""
                Attendees_list.append(Attendees_dict)
        event=Events.objects.filter(Id=eventid).all()
        Events_dict={}
        Events_dict["Subject"] = event[0].Subject
        Events_dict["Location"] = event[0].Location
        Events_dict["Start"] = str(event[0].Start.strftime("%H:%M:%S"))
        Events_dict["Organizer"] = event[0].Organizer
        Events_dict["Organizeraddress"] = event[0].Organizeraddress
        Events_dict["Truenum"] = Truenum
        Events_dict["Falsenum"] = Falsenum
        Events_dict["Latenum"] = Latenum
        Events_dict["Total"] = Truenum+Falsenum+Latenum
        Events_dict["Proportion"] = round(((Truenum*100+Latenum*100)/(Truenum+Falsenum+Latenum)),1)
        Attendees_list = sorted(Attendees_list, key=operator.itemgetter('Isattend'))
        Attendees_json = json.loads(json.dumps(Attendees_list, ensure_ascii=False))
        return JsonResponse({"Attendees": Attendees_json,"Events":Events_dict}, json_dumps_params={'ensure_ascii': False})#返回会议信息EVENTS以及参与者信息Attendees
def refuse(request):#用户拒绝会议时将Isattend更新为4
    if request.method == "GET":
        attendid = request.GET["Attendid"]
        Attendees.objects.filter(Id=attendid).update(Isattend="4")
        return HttpResponse("refuse")
def insert(request):#管理员添加会议人员
    if request.method == "GET":
        eventid = request.GET["Eventid"]
        userid = request.GET["Userid"]
        event = Events.objects.filter(Id=eventid).all()
        user = User.objects.filter(Id=userid).all()
        list=Attendees.objects.filter(Eventid=eventid,Address=user[0].Address).all()
        if(len(list)!=0):
            for a in list:
                if(int(a.Isattend)==4):
                    Attendees.objects.filter(Eventid=eventid,Address=user[0].Address).update(Isattend="0")
                    return HttpResponse("insert")
                else:
                    return HttpResponse("existed")
        else:
            Attendees.objects.create(Eventid=event[0].Id, Name=user[0].Name,
                                     Address=user[0].Address, Isattend='0',
                                     Meetingtime=event[0].Start)
            return HttpResponse("insert")
def users(request):#用户列表
    if request.method == "POST":
        lists = User.objects.all().order_by("Name")
        groups = Group.objects.all().order_by("Groupname")
        json_list = []
        i=0
        group1=[]
        for group in groups:
            groups_dict = {}
            users=User.objects.filter(Group=group.Groupname).all().order_by("Name")
            user_list=[]
            if(len(users)!=0):
                for a in users:
                    users_dict = {}
                    users_dict["Userid"] = a.Id
                    users_dict["name"] = a.Name
                    user_list.append(users_dict)
            if(i==0):
                group1=user_list
            i+=1
            userlist = json.loads(json.dumps(user_list, ensure_ascii=False))
            groups_dict["Groupid"]=group.Id
            groups_dict["name"] = group.Groupname
            groups_dict["Userlist"] = userlist
            json_list.append(groups_dict)
        ret1 = json.loads(json.dumps(json_list, ensure_ascii=False))
        objectgroups=[]
        objectgroups.append(json_list)
        objectgroups.append(group1)
        ret2 = json.loads(json.dumps(objectgroups, ensure_ascii=False))
        return JsonResponse({"groups": ret1,"objectgroups":ret2}, json_dumps_params={'ensure_ascii': False})

def groups(request):  # 部门列表
    if request.method == "POST":
        groups = Group.objects.all().order_by("Groupname")
        json_list = []
        print(groups)
        for a in groups:
            groups_dict = {}
            groups_dict["id"] = a.Id
            groups_dict["group"] = a.Groupname
            json_list.append(groups_dict)
        ret1 = json.loads(json.dumps(json_list, ensure_ascii=False))
        return JsonResponse({"groups": ret1}, json_dumps_params={'ensure_ascii': False})
#以下为sugar API
def sugartodayevents(request):#当天会议列表sugar中Apirate用到
    if request.method == "POST":
        conditions = json.loads(request.body)
        conditions = conditions["conditions"]
        for id in conditions:
            if(id['k']=="date"):
                localtime = id['v']
        #localtime = time.strftime("%Y-%m-%d", time.localtime())
        lists = Events.objects.all().order_by("Start")
        json_list = []
        for a in lists:
            if (str(a.Start.strftime("%Y-%m-%d")) == localtime):
                events_dict={}
                events_dict["label"] = a.Subject
                events_dict["value"] = a.Id
                json_list.append(events_dict)
        ret1 = json.loads(json.dumps(json_list, ensure_ascii=False))
        return JsonResponse({"data": ret1,"status": 0,
	"msg": 'Error' }, json_dumps_params={'ensure_ascii': False})
def apiusers(request):#用户列表（暂时不用）
    if request.method == "POST":
        lists = User.objects.all().order_by("Name")
        json_list = []
        for a in lists:
            if (len(a.Openid) != 0):  # 如果openid!=null
                users_dict = {}
                users_dict["label"] = a.Name
                users_dict["value"] = a.Id
                json_list.append(users_dict)
        ret1 = json.loads(json.dumps(json_list, ensure_ascii=False))
        return JsonResponse({"data": ret1,"status": 0,
	"msg": 'Error' }, json_dumps_params={'ensure_ascii': False})
def apidetail(request):#返回会议签到详情Apirate饼图所需数据
    if request.method == "POST":
        conditions = json.loads(request.body)
        conditions=conditions["conditions"]
        for id in conditions:
            eventid=id['v']
        lists = Attendees.objects.filter(Eventid=eventid).all().order_by("Meetingtime")
        Truenum=0#正确签到的人数
        Falsenum=0
        Latenum=0
        for a in lists:
            if (int(a.Isattend) != 4):
                if ((a.Isattend == 0)or(a.Isattend==3)):
                    Falsenum=Falsenum+1
                elif(a.Isattend == 1):
                    Truenum=Truenum+1
                elif(a.Isattend == 2):
                    Latenum=Latenum+1
        json_list = []
        for a in range(0,3):
            if (a == 0):
                events_dict={}
                events_dict["name"] = "准时"
                events_dict["value"] = Truenum
                json_list.append(events_dict)
            if (a == 1):
                events_dict={}
                events_dict["name"] = "迟到"
                events_dict["value"] = Latenum
                json_list.append(events_dict)
            if (a == 2):
                events_dict = {}
                events_dict["name"] = "未签到"
                events_dict["value"] = Falsenum
                json_list.append(events_dict)
        ret1 = json.loads(json.dumps(json_list, ensure_ascii=False))
        return JsonResponse({"data": ret1, "status": 0,
                         "msg": 'Error'}, json_dumps_params={'ensure_ascii': False})
def apitable(request):#返回会议签到详情Apitable表格所需数据
    if request.method == "POST":
        body = json.loads(request.body)
        conditions=body["conditions"]
        eventid=0
        try:
            drillDowns=body["drillDowns"]
        except:
            print("nodrillDowns")
        for id in conditions:
            if(id['k']=="select"):
                eventid=id['v']
        if(eventid==0):
            for i in drillDowns:
                subject=i['item']['subject']
                start=i['item']['start']
                start=datetime.datetime.strptime(start,"%Y-%m-%d %H:%M:%S")
            events=Events.objects.filter(Subject=subject,Start=start).all()
            eventid=events[0].Id
        lists = Attendees.objects.filter(Eventid=eventid).all()
        columns = []
        for i in range(0, 5):
            if (i == 0):
                events_dict = {}
                events_dict["name"] = "部门"
                events_dict["id"] = "group"
                columns.append(events_dict)
            elif (i == 1):
                events_dict = {}
                events_dict["name"] = "姓名"
                events_dict["id"] = "name"
                columns.append(events_dict)
            elif (i == 2):
                events_dict = {}
                events_dict["name"] = "会议名称"
                events_dict["id"] = "subject"
                columns.append(events_dict)
            elif (i == 3):
                events_dict = {}
                events_dict["name"] = "会议时间"
                events_dict["id"] = "start"
                columns.append(events_dict)
            elif (i == 4):
                events_dict = {}
                events_dict["name"] = "签到时间"
                events_dict["id"] = "time"
                columns.append(events_dict)
        rows = []
        for a in lists:
            user=User.objects.filter(Address=a.Address).all()
            if (int(a.Isattend) != 4):
                item = Events.objects.filter(Id=a.Eventid).all()
                if ((a.Isattend == 0) or (a.Isattend == 3)):
                    events_dict = {}
                    events_dict["group"] = user[0].Group
                    events_dict["name"] = user[0].Name
                    events_dict["subject"] = item[0].Subject
                    events_dict["start"] = str(item[0].Start.strftime("%Y-%m-%d %H:%M:%S"))
                    if (str(a.Attendtime) != "None"):
                        events_dict["time"] = str(a.Attendtime.strftime("%H:%M:%S"))
                    else:
                        events_dict["time"] = ""
                    #events_dict["__showx_row_level"] = "red"
                    rows.append(events_dict)
                elif (a.Isattend == 1):
                    events_dict = {}
                    events_dict["group"] = user[0].Group
                    events_dict["name"] = user[0].Name
                    events_dict["subject"] = item[0].Subject
                    events_dict["start"] = str(item[0].Start.strftime("%Y-%m-%d %H:%M:%S"))
                    if (str(a.Attendtime) != "None"):
                        events_dict["time"] = str(a.Attendtime.strftime("%H:%M:%S"))
                    else:
                        events_dict["time"] = ""
                    events_dict["__showx_row_level"] = "green"
                    rows.append(events_dict)
                elif (a.Isattend == 2):
                    events_dict = {}
                    events_dict["group"] = user[0].Group
                    events_dict["name"] = user[0].Name
                    events_dict["subject"] = item[0].Subject
                    events_dict["start"] = str(item[0].Start.strftime("%Y-%m-%d %H:%M:%S"))
                    if (str(a.Attendtime) != "None"):
                        events_dict["time"] = str(a.Attendtime.strftime("%H:%M:%S"))
                    else:
                        events_dict["time"] = ""
                    #events_dict["__showx_row_level"] = "red"
                    rows.append(events_dict)
        data = {"columns": columns, "rows": rows}
        return JsonResponse({"data": data, "status": 0,
                             "msg": 'Error'}, json_dumps_params={'ensure_ascii': False})
def userrate(request):#返回user rate中具体个人的饼图信息
    if request.method == "POST":
        body = json.loads(request.body)
        conditions=body["conditions"]
        try:
            dependence = body["dependence"]
            username=dependence["item"]["category"]
        except:
            username = "Qi, Yuan"
        for id in conditions:
            if (id['k'] == "dateRange"):
                s1 = id['v']
                s1 = s1.split(',')
                start = datetime.datetime.strptime(s1[0], "%Y-%m-%d")
                end = datetime.datetime.strptime(s1[1], "%Y-%m-%d")
        user = User.objects.filter(Name=username).all()
        lists = Attendees.objects.filter(Meetingtime__gte=start,Meetingtime__lte=end,Address=user[0].Address).all()
        Truenum=0#正确签到的人数
        Falsenum=0
        Latenum=0
        for a in lists:
            if (int(a.Isattend) != 4):
                if ((a.Isattend == 0)or(a.Isattend==3)):
                    Falsenum=Falsenum+1
                elif(a.Isattend == 1):
                    Truenum=Truenum+1
                elif(a.Isattend == 2):
                    Latenum=Latenum+1
        json_list = []
        for a in range(0,3):
            if (a == 0):
                events_dict={}
                events_dict["name"] = "准时"
                events_dict["value"] = Truenum
                json_list.append(events_dict)
            if (a == 1):
                events_dict={}
                events_dict["name"] = "迟到"
                events_dict["value"] = Latenum
                json_list.append(events_dict)
            if (a == 2):
                events_dict = {}
                events_dict["name"] = "未签到"
                events_dict["value"] = Falsenum
                json_list.append(events_dict)
        ret1 = json.loads(json.dumps(json_list, ensure_ascii=False))
        return JsonResponse({"data": ret1, "status": 0,
                         "msg": 'Error'}, json_dumps_params={'ensure_ascii': False})
def onemouthdetail(request):#返回单个用户在日期范围内签到详情表格
    if request.method == "POST":
        body = json.loads(request.body)
        conditions=body["conditions"]
        try:
            dependence = body["dependence"]
            username=dependence["item"]["category"]
        except:
            username = "Qi, Yuan"
        for id in conditions:
            if (id['k'] == "dateRange"):
                s1 = id['v']
                s1 = s1.split(',')
                start = datetime.datetime.strptime(s1[0], "%Y-%m-%d")
                end = datetime.datetime.strptime(s1[1], "%Y-%m-%d")
        user = User.objects.filter(Name=username).all()
        lists = Attendees.objects.filter(Meetingtime__gte=start,Meetingtime__lte=end,Address=user[0].Address).all()
        columns=[]
        for i in range(0,5):
            if(i==0):
                events_dict = {}
                events_dict["name"] = "部门"
                events_dict["id"] = "group"
                columns.append(events_dict)
            elif(i==1):
                events_dict = {}
                events_dict["name"] = "姓名"
                events_dict["id"] = "name"
                columns.append(events_dict)
            elif (i == 2):
                events_dict = {}
                events_dict["name"] = "会议名称"
                events_dict["id"] = "subject"
                columns.append(events_dict)
            elif (i == 3):
                events_dict = {}
                events_dict["name"] = "会议时间"
                events_dict["id"] = "start"
                columns.append(events_dict)
            elif (i == 4):
                events_dict = {}
                events_dict["name"] = "签到时间"
                events_dict["id"] = "time"
                columns.append(events_dict)
        rows=[]
        for a in lists:
            if (int(a.Isattend) != 4):
                item=Events.objects.filter(Id=a.Eventid).all()
                if ((a.Isattend == 0)or(a.Isattend==3)):
                    events_dict = {}
                    events_dict["group"] = user[0].Group
                    events_dict["name"] = user[0].Name
                    events_dict["subject"] = item[0].Subject
                    events_dict["start"] = str(item[0].Start.strftime("%Y-%m-%d %H:%M:%S"))
                    if (str(a.Attendtime) != "None"):
                        events_dict["time"] = str(a.Attendtime.strftime("%H:%M:%S"))
                    else:
                        events_dict["time"] = ""
                    #events_dict["__showx_row_level"] = "red"
                    rows.append(events_dict)
                elif(a.Isattend == 1):
                    events_dict = {}
                    events_dict["group"] = user[0].Group
                    events_dict["name"] = user[0].Name
                    events_dict["subject"] = item[0].Subject
                    events_dict["start"] = str(item[0].Start.strftime("%Y-%m-%d %H:%M:%S"))
                    if (str(a.Attendtime) != "None"):
                        events_dict["time"] = str(a.Attendtime.strftime("%H:%M:%S"))
                    else:
                        events_dict["time"] = ""
                    events_dict["__showx_row_level"] = "green"
                    rows.append(events_dict)
                elif(a.Isattend == 2):
                    events_dict = {}
                    events_dict["group"] = user[0].Group
                    events_dict["name"] = user[0].Name
                    events_dict["subject"] = item[0].Subject
                    events_dict["start"] = str(item[0].Start.strftime("%Y-%m-%d %H:%M:%S"))
                    if (str(a.Attendtime) != "None"):
                        events_dict["time"] = str(a.Attendtime.strftime("%H:%M:%S"))
                    else:
                        events_dict["time"] = ""
                    #events_dict["__showx_row_level"] = "red"
                    rows.append(events_dict)
        data = {"columns": columns, "rows": rows}
        return JsonResponse({"data": data, "status": 0,
                         "msg": 'Error'}, json_dumps_params={'ensure_ascii': False})
def usersrate(request):#返回整体当月签到详情user rate 饼图
    if request.method == "POST":
        conditions = json.loads(request.body)
        conditions=conditions["conditions"]
        for id in conditions:
            if (id['k'] == "dateRange"):
                s1 = id['v']
                s1 = s1.split(',')
                start = datetime.datetime.strptime(s1[0], "%Y-%m-%d")
                end = datetime.datetime.strptime(s1[1], "%Y-%m-%d")
        lists = Attendees.objects.filter(Meetingtime__gte=start,Meetingtime__lte=end).all()
        Truenum=0#正确签到的人数
        Falsenum=0
        Latenum=0
        for a in lists:
            user=User.objects.filter(Address=a.Address).all()
            if(len(user) != 0):
                if (len(user[0].Openid) != 0):
                    if (int(a.Isattend) != 4):
                        if ((a.Isattend == 0)or(a.Isattend==3)):
                            Falsenum=Falsenum+1
                        elif(a.Isattend == 1):
                            Truenum=Truenum+1
                        elif(a.Isattend == 2):
                            Latenum=Latenum+1
        json_list = []
        for a in range(0,3):
            if (a == 0):
                events_dict = {}
                events_dict["name"] = "准时"
                events_dict["value"] = Truenum
                json_list.append(events_dict)
            if (a == 1):
                events_dict={}
                events_dict["name"] = "迟到"
                events_dict["value"] = Latenum
                json_list.append(events_dict)
            if (a == 2):
                events_dict = {}
                events_dict["name"] = "未签到"
                events_dict["value"] = Falsenum
                json_list.append(events_dict)
        ret1 = json.loads(json.dumps(json_list, ensure_ascii=False))
        return JsonResponse({"data": ret1, "status": 0,
                         "msg": 'Error'}, json_dumps_params={'ensure_ascii': False})
def apilist(request):#user rate 条形图
    if request.method == "POST":
        conditions = json.loads(request.body)
        conditions = conditions["conditions"]
        for id in conditions:
            if (id['k'] == "dateRange"):
                s1 = id['v']
                s1 = s1.split(',')
                start = datetime.datetime.strptime(s1[0], "%Y-%m-%d")
                end = datetime.datetime.strptime(s1[1], "%Y-%m-%d")
        lists = User.objects.all().order_by("Name")
        json_list = []
        for a in lists:
            if (len(a.Openid) != 0):  # 如果openid!=null
                lists = Attendees.objects.filter(Meetingtime__gte=start, Meetingtime__lte=end,Address=a.Address).all()
                Truenum = 0
                Falsenum = 0
                Latenum = 0
                for attend in lists:
                    if (int(attend.Isattend) != 4):
                        if ((attend.Isattend == 0) or (attend.Isattend == 3)):
                            Falsenum = Falsenum + 1
                        elif (attend.Isattend == 1):
                            Truenum = Truenum + 1
                        elif (attend.Isattend == 2) :
                            Latenum = Latenum + 1
                Total = Truenum + Falsenum + Latenum
                if(Total==0):
                    Total=1
                Truenum = round(((Truenum) / Total), 3)
                Latenum = round(((Latenum) / Total), 3)
                Falsenum = round(((Falsenum) / Total), 3)
                users_dict = {}
                users_dict["id"] = a.Id
                users_dict["name"] = a.Name
                users_dict["Truenum"] = Truenum
                users_dict["Latenum"] = Latenum
                users_dict["Falsenum"] = Falsenum
                json_list.append(users_dict)
        json_list = sorted(json_list, key=operator.itemgetter('Truenum'))#根据用户为签到比例从大到小排序
        categories=[]
        series=[]
        data0 = []
        data1 = []
        data2 = []
        for user in json_list:
            categories.append(user['name'])
            for i in range(0,3):
                if(i==0):
                    data0.append(user['Falsenum'])
                elif(i==1):
                    data1.append(user['Truenum'])
                elif(i==2):
                    data2.append(user['Latenum'])
        for a in range(0,3):
            if (a == 0):
                events_dict = {}
                events_dict["name"] = "准时"
                events_dict["data"] = data1
                series.append(events_dict)
            if (a == 1):
                events_dict = {}
                events_dict["name"] = "迟到"
                events_dict["data"] = data2
                series.append(events_dict)
            if (a == 2):
                events_dict = {}
                events_dict["name"] = "未签到"
                events_dict["data"] = data0
                series.append(events_dict)
        series = json.loads(json.dumps(series, ensure_ascii=False))
        data={"categories":categories,"series":series}
        return JsonResponse({"status": 0,
	"msg": 'Error',"data": data }, json_dumps_params={'ensure_ascii': False})
def groupslist(request):#group rate big条形图
    if request.method == "POST":
        conditions = json.loads(request.body)
        conditions = conditions["conditions"]
        for id in conditions:
            if (id['k'] == "dateRange"):
                s1 = id['v']
                s1 = s1.split(',')
                start = datetime.datetime.strptime(s1[0], "%Y-%m-%d")
                end = datetime.datetime.strptime(s1[1], "%Y-%m-%d")
        groups = Group.objects.all().order_by("Groupname")
        #groups = User.objects.values('Group').distinct().all().order_by("Group")
        json_list = []
        for i in groups:
            lists=User.objects.filter(Group=i.Groupname).all()
            Truenum = 0
            Falsenum = 0
            Latenum = 0
            Total = 0
            for a in lists:
                if (len(a.Openid) != 0):  # 如果openid!=null
                    lists = Attendees.objects.filter(Meetingtime__gte=start, Meetingtime__lte=end,Address=a.Address).all()
                    for attend in lists:
                        if (int(attend.Isattend) != 4):
                            if ((attend.Isattend == 0) or (attend.Isattend == 3)):
                                Falsenum = Falsenum + 1
                            elif (attend.Isattend == 1):
                                Truenum = Truenum + 1
                            elif (attend.Isattend == 2) :
                                Latenum = Latenum + 1
            Total = Total+Truenum + Falsenum + Latenum
            if(Total==0):
                Total=1
            Truenum = round(((Truenum) / Total), 3)
            Latenum = round(((Latenum) / Total), 3)
            Falsenum = round(((Falsenum) / Total), 3)
            users_dict = {}
            users_dict["id"] = i.Id
            users_dict["name"] = str(i.Groupname)
            users_dict["Truenum"] = Truenum
            users_dict["Latenum"] = Latenum
            users_dict["Falsenum"] = Falsenum
            json_list.append(users_dict)
        json_list = sorted(json_list, key=operator.itemgetter('Truenum'))#根据用户为签到比例从大到小排序
        categories=[]
        series=[]
        data0 = []
        data1 = []
        data2 = []
        for user in json_list:
            categories.append(user['name'])
            for i in range(0,3):
                if(i==0):
                    data0.append(user['Falsenum'])
                elif(i==1):
                    data1.append(user['Truenum'])
                elif(i==2):
                    data2.append(user['Latenum'])
        for a in range(0,3):
            if (a == 0):
                events_dict = {}
                events_dict["name"] = "准时"
                events_dict["data"] = data1
                series.append(events_dict)
            if (a == 1):
                events_dict = {}
                events_dict["name"] = "迟到"
                events_dict["data"] = data2
                series.append(events_dict)
            if (a == 2):
                events_dict = {}
                events_dict["name"] = "未签到"
                events_dict["data"] = data0
                series.append(events_dict)
        series = json.loads(json.dumps(series, ensure_ascii=False))
        data={"categories":categories,"series":series}
        return JsonResponse({"status": 0,
	"msg": 'Error',"data": data }, json_dumps_params={'ensure_ascii': False})
def grouplist(request):#group rate small条形图
    if request.method == "POST":
        body = json.loads(request.body)
        conditions = body["conditions"]
        try:
            dependence = body["dependence"]
            group=dependence["item"]["category"]
        except:
            group = "3"
        for id in conditions:
            if (id['k'] == "dateRange"):
                s1 = id['v']
                s1 = s1.split(',')
                start = datetime.datetime.strptime(s1[0], "%Y-%m-%d")
                end = datetime.datetime.strptime(s1[1], "%Y-%m-%d")
        userlists = User.objects.filter(Group=group).all().order_by("Name")
        json_list = []
        for a in userlists:
            if (len(a.Openid) != 0):  # 如果openid!=null
                lists = Attendees.objects.filter(Meetingtime__gte=start, Meetingtime__lte=end,Address=a.Address).all()
                Truenum = 0
                Falsenum = 0
                Latenum = 0
                for attend in lists:
                    if (int(attend.Isattend) != 4):
                        if ((attend.Isattend == 0) or (attend.Isattend == 3)):
                            Falsenum = Falsenum + 1
                        elif (attend.Isattend == 1):
                            Truenum = Truenum + 1
                        elif (attend.Isattend == 2) :
                            Latenum = Latenum + 1
                Total = Truenum + Falsenum + Latenum
                if(Total==0):
                    Total=1
                Truenum= round(((Truenum ) / Total), 3)
                Latenum = round(((Latenum) / Total), 3)
                Falsenum = round(((Falsenum ) / Total), 3)
                users_dict = {}
                users_dict["id"] = a.Id
                users_dict["name"] = a.Name
                users_dict["Truenum"] = Truenum
                users_dict["Latenum"] = Latenum
                users_dict["Falsenum"] = Falsenum
                json_list.append(users_dict)
        json_list = sorted(json_list, key=operator.itemgetter('Truenum'))#根据用户为签到比例从大到小排序
        categories=[]
        series=[]
        data0 = []
        data1 = []
        data2 = []
        for user in json_list:
            categories.append(user['name'])
            for i in range(0,3):
                if(i==0):
                    data0.append(user['Falsenum'])
                elif(i==1):
                    data1.append(user['Truenum'])
                elif(i==2):
                    data2.append(user['Latenum'])
        for a in range(0,3):
            if (a == 0):
                events_dict = {}
                events_dict["name"] = "准时"
                events_dict["data"] = data1
                series.append(events_dict)
            if (a == 1):
                events_dict = {}
                events_dict["name"] = "迟到"
                events_dict["data"] = data2
                series.append(events_dict)
            if (a == 2):
                events_dict = {}
                events_dict["name"] = "未签到"
                events_dict["data"] = data0
                series.append(events_dict)
        series = json.loads(json.dumps(series, ensure_ascii=False))
        data={"categories":categories,"series":series}
        return JsonResponse({"status": 0,
	"msg": 'Error',"data": data }, json_dumps_params={'ensure_ascii': False})
def grouprate(request):#返回group rate 饼图
    if request.method == "POST":
        body = json.loads(request.body)
        conditions = body["conditions"]
        try:
            dependence = body["dependence"]
            group = dependence["item"]["category"]
        except:
            group = "3"
        for id in conditions:
            if (id['k'] == "dateRange"):
                s1 = id['v']
                s1 = s1.split(',')
                start = datetime.datetime.strptime(s1[0], "%Y-%m-%d")
                end = datetime.datetime.strptime(s1[1], "%Y-%m-%d")
        userlists = User.objects.filter(Group=group).all().order_by("Name")
        Truenum = 0  # 正确签到的人数
        Falsenum = 0
        Latenum = 0
        for user in userlists:
            if (len(user.Openid) != 0):  # 如果openid!=null
                lists = Attendees.objects.filter(Meetingtime__gte=start, Meetingtime__lte=end,Address=user.Address).all()
                for a in lists:
                    user=User.objects.filter(Address=a.Address).all()
                    if(len(user) != 0):
                        if (len(user[0].Openid) != 0):
                            if (int(a.Isattend) != 4):
                                if ((a.Isattend == 0)or(a.Isattend==3)):
                                    Falsenum=Falsenum+1
                                elif(a.Isattend == 1):
                                    Truenum=Truenum+1
                                elif(a.Isattend == 2):
                                    Latenum=Latenum+1
        json_list = []
        for a in range(0,3):
            if (a == 0):
                events_dict = {}
                events_dict["name"] = "准时"
                events_dict["value"] = Truenum
                json_list.append(events_dict)
            if (a == 1):
                events_dict={}
                events_dict["name"] = "迟到"
                events_dict["value"] = Latenum
                json_list.append(events_dict)
            if (a == 2):
                events_dict = {}
                events_dict["name"] = "未签到"
                events_dict["value"] = Falsenum
                json_list.append(events_dict)
        ret1 = json.loads(json.dumps(json_list, ensure_ascii=False))
        return JsonResponse({"data": ret1, "status": 0,
                         "msg": 'Error'}, json_dumps_params={'ensure_ascii': False})