import json
import operator
import time
import datetime
import pyecharts
from random import randrange
from django.http import HttpResponse, JsonResponse, HttpResponseRedirect
from django.shortcuts import render
from pyecharts.commons import utils
from django.db.models import Q
from pyecharts.commons.utils import JsCode
from pyecharts.components import Table
from pyecharts.globals import ThemeType
from pyecharts.options import ComponentTitleOpts
from rest_framework.views import APIView
from pyecharts.faker import Faker
from pyecharts.charts import Bar, Pie, Grid, Line
from pyecharts import options as opts
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
            User.objects.create(Openid=openid,Address=email,Group=group,Passwd="ames@12345")
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
        start = now - datetime.timedelta(minutes=30)
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
                        #print(a.Isattend,type(a.Isattend))
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
        #print(groups)
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
        thisevent=Events.objects.filter(Id=eventid).all()
        for this in thisevent:
            subject=this.Subject
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
        data = {"subject": subject, "ret1": ret1}
        return data
        return JsonResponse({"data": ret1, "status": 0,
                         "msg": 'Error'}, json_dumps_params={'ensure_ascii': False})
def apitable(request):#返回会议签到详情Apitable表格所需数据
    if request.method == "POST":
        body = json.loads(request.body)
        try:
            conditions=body["conditions"]
        except:
            conditions = [1]
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
        events = Events.objects.filter(Id=eventid).all()
        subject = events[0].Subject
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
        data = {"columns": columns, "rows": rows,"subject":subject}
        return data
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
        data = {"user": username, "ret1": ret1}
        return data
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
        data = {"ret1": ret1}
        return data
        return JsonResponse({"data": ret1, "status": 0,
                         "msg": 'Error'}, json_dumps_params={'ensure_ascii': False})
def apilist(request):#user rate 条形图
    if request.method == "POST":
        body = json.loads(request.body)
        conditions = body["conditions"]
        select=body["group"]
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
        if(select=="出勤排名"):
            json_list = sorted(json_list, key=operator.itemgetter('Truenum'))#根据用户为签到比例从大到小排序
        elif(select=="缺勤排名"):
            json_list = sorted(json_list, key=operator.itemgetter('Falsenum'))  # 根据用户为缺勤比例从大到小排序
        elif(select=="迟到排名"):
            json_list = sorted(json_list, key=operator.itemgetter('Latenum'))  # 根据用户为迟到比例从大到小排序
        else:
            json_list = sorted(json_list, key=operator.itemgetter('Truenum'))  # 根据用户为签到比例从大到小排序
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
        data = {"categories": categories, "series": series,"select":select}
        return data
        return JsonResponse({"status": 0,
	"msg": 'Error',"data": data }, json_dumps_params={'ensure_ascii': False})
def groupslist(request):#group rate big条形图
    if request.method == "POST":
        print(request.body)
        #conditions = json.loads(request.headers)
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
        return data
        return JsonResponse({"status": 0,"msg": 'Error',"data": data }, json_dumps_params={'ensure_ascii': False})
def grouplist(request):#group rate small条形图
    if request.method == "POST":
        body = json.loads(request.body)
        conditions = body["conditions"]
        try:
            dependence = body["dependence"]
            group=dependence["item"]["category"]
        except:
            group = "Engineering"
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
        data = {"categories": categories, "series": series,"group":group}
        return data
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
            group = "Engineering"
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
        data = {"group": group, "ret1": ret1}
        return data
        return JsonResponse({"data": ret1, "status": 0,
                         "msg": 'Error'}, json_dumps_params={'ensure_ascii': False})

#可视化图表界面

def response_as_json(data):
    json_str = json.dumps(data)
    response = HttpResponse(
        json_str,
        content_type="application/json",
    )
    response["Access-Control-Allow-Origin"] = "*"
    return response


def json_response(data, code=200):
    data = {
        "code": code,
        "msg": "success",
        "data": data,
    }
    return response_as_json(data)


def json_error(error_string="error", code=500, **kwargs):
    data = {
        "code": code,
        "msg": error_string,
        "data": {}
    }
    data.update(kwargs)
    return response_as_json(data)


barJsonResponse = json_response
JsonError = json_error


def bar_base() -> Bar:
    c = (
         Bar(init_opts=opts.InitOpts(theme=ThemeType.MACARONS))
        .add_xaxis(["衬衫", "羊毛衫", "雪纺衫", "裤子", "高跟鞋", "袜子"])
        .add_yaxis("商家A", [randrange(0, 100) for _ in range(6)])
        .add_yaxis("商家B", [randrange(0, 100) for _ in range(6)])
        .set_global_opts(title_opts=opts.TitleOpts(title="Bar", subtitle="Error"))
        .add_js_funcs("""console.log('hello world')""")
        .dump_options_with_quotes()
    )

    return c

def grid_vertical() -> Grid:
    bar = (
        Bar()
        .add_xaxis(Faker.choose())
        .add_yaxis("商家A", Faker.values())
        .add_yaxis("商家B", Faker.values())
        .set_global_opts(title_opts=opts.TitleOpts(title="Grid-Bar"))
    )
    line = (
        Line()
        .add_xaxis(Faker.choose())
        .add_yaxis("商家A", Faker.values())
        .add_yaxis("商家B", Faker.values())
        .set_global_opts(
            title_opts=opts.TitleOpts(title="Grid-Line", pos_top="48%"),
            legend_opts=opts.LegendOpts(pos_top="48%"),
        )
    )

    grid = (
        Grid()
        .add(bar, grid_opts=opts.GridOpts(pos_bottom="60%",pos_left="60%"))
        .add(line, grid_opts=opts.GridOpts(pos_top="60%"))
        .dump_options_with_quotes()
    )
    return grid

def bar(list,bartitle) -> Grid:
    try:
        selected=list["selected"]
    except:
        selected=["True","True","True"]
    c = (
        Bar({"theme": ThemeType.MACARONS})
        .add_xaxis(list["categories"])
        .add_yaxis(list["series"][0]["name"], list["series"][0]["data"], stack="stack1",is_selected=selected[0],)
        .add_yaxis(list["series"][1]["name"], list["series"][1]["data"], stack="stack1",is_selected=selected[1],)
        .add_yaxis(list["series"][2]["name"], list["series"][2]["data"], stack="stack1",is_selected=selected[2],)
        .reversal_axis()
        .set_series_opts(itemstyle_opts={
            "normal": {
                "barBorderRadius": [30, 30, 30, 30],
            }},
            )

        .set_series_opts(label_opts=opts.LabelOpts(position="right"))
        .set_global_opts(
            yaxis_opts=opts.AxisOpts(axislabel_opts=opts.LabelOpts(rotate=+0),boundary_gap=['10%','10%'],name_gap=300),
            title_opts=opts.TitleOpts(title=bartitle),
            legend_opts=opts.LegendOpts(pos_top="95%"),
        )
        #.dump_options_with_quotes()
    )
    grid = (
        Grid()
            .add(c, grid_opts=opts.GridOpts(pos_left="20%"))
            .dump_options_with_quotes()
    )
    return grid


def pie(list1,bartitle) -> Pie:
    c = (
        Pie({"theme": ThemeType.MACARONS})
        .add("", list1)
        .set_global_opts(
            legend_opts=opts.LegendOpts(pos_top="95%"),
            title_opts=opts.TitleOpts(title=bartitle))
        .set_series_opts(label_opts=opts.LabelOpts(formatter="{b}: {c}"))
        .dump_options_with_quotes()
    )
    return c

def table(list1,bartitle) -> Table:
    c = Table()
    headers=list1["headers"]
    rows=list1["rows"]
    c.add(headers,rows).set_global_opts(
            title_opts=ComponentTitleOpts(title=bartitle))
    return c

def viewtype(request):
    if request.method == "POST":
        try:
            body = json.loads(request.body)
            type = body["type"]
            if (type == "getevents"):
                events=sugartodayevents(request)
                return events
            if (type == "eventpie"):
                x = apidetail(request)
                name = []
                value = []
                for a in x["ret1"]:
                    name.append(a["name"])
                    value.append(a["value"])
                a = [list(z) for z in zip(name, value)]
                text = "会议签到率--"+x["subject"]
                return barJsonResponse(json.loads(pie(a, text)))
            if (type == "eventtable"):
                x = apitable(request)
                headers=[]
                for i in range(0,5):
                    if i!=2:
                        headers.append(x["columns"][i]["name"])
                rows=[]
                for a in range(0,len(x["rows"])):
                    row=[]
                    row.append(x["rows"][a]["group"])
                    row.append(x["rows"][a]["name"])
                    row.append(x["rows"][a]["start"])
                    row.append(x["rows"][a]["time"])
                    rows.append(row)
                text = "会议签到详情--" + x["subject"]
                list1={"headers":headers,"rows":rows}
                return JsonResponse(list1, json_dumps_params={'ensure_ascii': False})
                #return barJsonResponse(table(list1, text))
            if (type == "groupslist"):
                x = groupslist(request)
                return barJsonResponse(json.loads(bar(x, "GroupsList")))
            if (type == "grouplist"):
                x = grouplist(request)
                text = "部门签到排名--" + x["group"]
                return barJsonResponse(json.loads(bar(x, text)))
            if (type == "groupsrate"):
                x = usersrate(request)
                name = []
                value = []
                for a in x["ret1"]:
                    name.append(a["name"])
                    value.append(a["value"])
                a = [list(z) for z in zip(name, value)]
                text = "本月整体签到率"
                return barJsonResponse(json.loads(pie(a, text)))
            if (type == "grouprate"):
                x = grouprate(request)
                name = []
                value = []
                for a in x["ret1"]:
                    name.append(a["name"])
                    value.append(a["value"])
                a = [list(z) for z in zip(name, value)]
                text = "部门签到次数--" + x["group"]
                return barJsonResponse(json.loads(pie(a, text)))
            if (type == "userslist"):
                x = apilist(request)
                if(len(x["categories"])>10):
                    series = []
                    for i in range(0,3):
                        events_dict = {}
                        events_dict["name"] = x["series"][i]["name"]
                        events_dict["data"] = x["series"][i]["data"][len(x["categories"])-10:len(x["categories"])]
                        series.append(events_dict)
                    if (x["select"] == "出勤排名"):
                        selected = ["True","False","False"]
                    elif (x["select"] == "缺勤排名"):
                        selected = ["False","False","True"]
                    elif (x["select"] == "迟到排名"):
                        selected = ["False","True","False"]
                    data = {"categories": x["categories"][len(x["categories"])-10:len(x["categories"])], "series": series,"selected":selected}
                    x=data
                #return barJsonResponse(json.loads(grid_vertical()))
                return barJsonResponse(json.loads(bar(x, "UsersList")))
            if (type == "userrate"):
                x = userrate(request)
                name = []
                value = []
                for a in x["ret1"]:
                    name.append(a["name"])
                    value.append(a["value"])
                a = [list(z) for z in zip(name, value)]
                text = "个人签到次数--" + x["user"]
                return barJsonResponse(json.loads(pie(a, text)))
        except Exception as e:
            print(e)
        return barJsonResponse(json.loads(grid_vertical()))
class ChartView(APIView):
    def get(self, request, *args, **kwargs):
        return barJsonResponse(json.loads(bar_base()))

class EventView(APIView):
    def get(self, request, *args, **kwargs):
        #return HttpResponse(content=open("./templates/index.html").read())
        return render(request, "eventview.html")
        if request.session.has_key("user"):
            return render(request, "eventview.html",{"user":request.session["user"]})
        else:
            return HttpResponseRedirect( "/meeting/login")

class GroupView(APIView):
    def get(self, request, *args, **kwargs):
        #return HttpResponse(content=open("./templates/index.html").read())
        return render(request, "groupview.html")
        if request.session.has_key("user"):
            return render(request, "groupview.html",{"user":request.session["user"]})
        else:
            return HttpResponseRedirect( "/meeting/login")

class index(APIView):
    def get(self, request, *args, **kwargs):
        return render(request, "index.html")

class UserView(APIView):
    def get(self, request, *args, **kwargs):
        #return HttpResponse(content=open("./templates/index.html").read())
        return render(request, "userview.html")
        if request.session.has_key("user"):
            return render(request, "userview.html",{"user":request.session["user"]})
        else:
            return HttpResponseRedirect("/meeting/login")

def login(request):
    if request.session.has_key("user"):
        return HttpResponseRedirect( "/meeting/eventview")
    if request.method=="POST":
        address=request.POST['address']
        passwd=request.POST['passwd']
        islogin=User.objects.filter(Address__exact=address,Passwd__exact=passwd)
        if islogin:
            request.session["user"]=User.objects.filter(Address=address).last().Name
            return HttpResponseRedirect("/meeting/eventview")
        else:
            #return HttpResponseRedirect("/meeting/login")
            return HttpResponseRedirect("/meeting/eventview")
    return render(request, "login.html")

def logout(request):
    del request.session["user"]
    return HttpResponseRedirect("/meeting/login")

def changepwd(request):
    if request.method=="POST":
        passwd=request.POST["passwd"]
        if(passwd!=""):
            name=request.session["user"]
            User.objects.filter(Name=name).update(Passwd=passwd)
            del request.session["user"]
            return HttpResponse("success")
    else:
        return HttpResponse("error")