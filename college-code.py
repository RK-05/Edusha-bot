from flask import Flask, render_template, flash, request,session,jsonify
from chatterbot import ChatBot 
from chatterbot.trainers import ChatterBotCorpusTrainer 

import mysql.connector
import sys
import boto3
import os

ENDPOINT="edushachat.cpyclmfbbpkm.ap-south-1.rds.amazonaws.com"
PORT="3306"
USR="edushacc"
REGION="ap-south-1"
DBNAME="edusha"
os.environ['LIBMYSQL_ENABLE_CLEARTEXT_PLUGIN'] = '1'

#gets the credentials from .aws/credentials
session = boto3.Session(profile_name='default')
client = boto3.client('rds')

token = client.generate_db_auth_token(DBHostname=ENDPOINT, Port=PORT, DBUsername=USR, Region=REGION)

try:
    mydb =  mysql.connector.connect(host=ENDPOINT, user=USR, passwd="edusha_cc", port=PORT, database=DBNAME)
    mycursor = mydb.cursor()
except Exception as e:
    print("Database connection failed due to {}".format(e))          

chatbot1 = ChatBot(
    "My ChatterBot",
    logic_adapters=["chatterbot.logic.BestMatch",])
  
  
# Create a new trainer for the chatbot 
trainer = ChatterBotCorpusTrainer(chatbot1) 
   
# Now let us train our bot with multipple corpus 
trainer.train("chatterbot.corpus.english.botprofile","chatterbot.corpus.english.greetings", 
              "chatterbot.corpus.english.conversations" ,"chatterbot.corpus.english.humor") 
     
# App config.
DEBUG = False
app = Flask(__name__)
app.config.from_object(__name__)
app.config['SECRET_KEY'] = '7d441f27d441f2756'

course_type=[]
sql = "SELECT name FROM course_typo"
mycursor.execute(sql)
myresult = mycursor.fetchall()
for x in myresult:
    course_type.append(x[0])
cat_type=[]
sql = "SELECT name FROM `course_category`"
mycursor.execute(sql)
myresult = mycursor.fetchall()
for x in myresult:
    cat_type.append(x[0])
course_mn=[]
sql = "SELECT name FROM `course_master`"
mycursor.execute(sql)
myresult = mycursor.fetchall()
for x in myresult:
    course_mn.append(x[0].strip())
course_mn.append('All')
tot_state=[]
sql = "SELECT name FROM `states`"
mycursor.execute(sql)
state = mycursor.fetchall()
for i in state:
    tot_state.append(i[0])
tot_state.append('ALL')
@app.route('/', methods=['GET', 'POST'])
def Attendence_upload():
    global response,req
    if request.method=='POST':
        req=request.json
        try:
            if req['type'] == '0':
                return jsonify([{"text":"Hello there!<br> I am your personal assistant EBO.<br> Let me help you.<br> Please select from suggested actions to proceed" , "actions": ["Contact our team"]}])
        except:    
            try:
                if req['msg'] in ['FIND COLLEGES','SEARCH COLLEGES']:
                    return jsonify([{"text":"Welcome to college finder powered by edusha."},{"text":"select from the following category","actions":course_type}])
                elif req['msg'] in course_type:
                    return jsonify([{"text":"select from the following category","actions":cat_type}])
                elif req['msg'] in cat_type:
                    col=[]
                    mycursor = mydb.cursor()
                    sql = """SELECT `name`,ct.`city` FROM `college_list` cl JOIN `basic_college` bc ON cl.`id` = bc.`cId` JOIN `cities` ct ON cl.`cityId` = ct.`id` WHERE cid IN (SELECT cc.collegeId FROM `college_has_course` cc JOIN `course_master` cm ON cc.`courseid`= cm.id JOIN `course_category` ca ON cc.`courseCat` = ca.id JOIN `course_typo` ct ON cm.`courseType`= ct.`id` WHERE ca.`name` = '{}' ) AND ranking>0 ORDER BY ranking LIMIT 10""".format(req['msg'])
                    mycursor.execute(sql)
                    myresult = mycursor.fetchall()
                    for x in myresult:
                        col.append("{},{}".format(x[0],x[1]))
                    return jsonify([{"text":"Top {} college's".format(req['msg']),"actions":col}])
                else:
                    response = chatbot1.get_response(req['msg']) 
                    return jsonify([{"text":response}])
            except:
                if (req['msg1'] in course_mn and req['msg2'].upper() in tot_state) and (req['msg3'] in course_type and req['msg4'] in cat_type):
                    if req['msg1'] != 'All' and req['msg2'] != "All":
                        mycursor = mydb.cursor()
                        sql = "SELECT DISTINCT cl.`name`,cty.`city` FROM `college_has_course` cc JOIN `course_master` cm ON cc.`courseid`= cm.id JOIN `course_category` ca ON cc.`courseCat` = ca.id JOIN `course_typo` ct ON cm.`courseType`= ct.`id` JOIN `college_list` cl on cc.`collegeId`=cl.`id` JOIN `cities` cty ON cl.`cityId` = cty.`id` JOIN `states` st ON cl.`stateId` = st.`id` WHERE ca.`name` = '{}' AND ct.`name`='{}' AND CM.`name` = '{}' AND st.`name` = '{}'".format(req['msg4'],req['msg3'],req['msg1'],req['msg2'])
                        mycursor.execute(sql)
                        college_result = mycursor.fetchall()
                        return jsonify([{"text":"select from the following college's","actions":['{},{}'.format(i[0],i[1]) for i in college_result]}])
                    elif req['msg1'] != 'All' and req['msg2'] == "All":
                        mycursor = mydb.cursor()
                        sql = "SELECT `college_list`.`name`,ct.`city` FROM `college_has_course` JOIN `college_list`  ON `college_has_course`.`collegeId`=`college_list`.`id` JOIN `cities` ct ON `college_list`.`cityId` = ct.`id` WHERE `college_has_course`.`courseid` IN (SELECT id from `course_master` WHERE name='{} ')".format(req['msg1'])
                        mycursor.execute(sql)
                        college_result = mycursor.fetchall()
                        return jsonify([{"text":"select from the following college's","actions":['{},{}'.format(i[0],i[1]) for i in college_result]}])
                    elif req['msg1'] == 'All' and req['msg2'] != "All":
                        mycursor = mydb.cursor()
                        sql="SELECT  DISTINCT cl.`name`,cty.`city` FROM `college_has_course` cc JOIN `course_master` cm ON cc.`courseid`= cm.id JOIN `course_category` ca ON cc.`courseCat` = ca.id JOIN `course_typo` ct ON cm.`courseType`= ct.`id` JOIN `college_list` cl on cc.`collegeId`=cl.`id` JOIN `cities` cty ON cl.`cityId` = cty.`id` JOIN `states` st ON cl.`stateId` = st.`id` WHERE ca.`name` = '{}' AND ct.`name`='{}' AND st.`name` = '{}'".format(req['msg4'],req['msg3'],req['msg2'])
                        mycursor.execute(sql)
                        college_result = mycursor.fetchall()
                        return jsonify([{"text":"select from the following college's","actions":['{},{}'.format(i[0],i[1]) for i in college_result]}])
                    else:
                        mycursor = mydb.cursor()
                        sql="SELECT  DISTINCT cl.`name`,cty.`city` FROM `college_has_course` cc JOIN `course_master` cm ON cc.`courseid`= cm.id JOIN `course_category` ca ON cc.`courseCat` = ca.id JOIN `course_typo` ct ON cm.`courseType`= ct.`id` JOIN `college_list` cl on cc.`collegeId`=cl.`id` JOIN `cities` cty ON cl.`cityId` = cty.`id` JOIN `states` st ON cl.`stateId` = st.`id` WHERE ca.`name` = '{}' AND ct.`name`='{}'".format(req['msg4'],req['msg3'])
                        mycursor.execute(sql)
                        college_result = mycursor.fetchall()
                        return jsonify([{"text":"select from the following college's","actions":['{},{}'.format(i[0],i[1]) for i in college_result]}])
                elif req['msg1'] in course_type and req['msg2'].upper() in cat_type :
                    course=[]
                    mycursor = mydb.cursor()
                    sql = "SELECT name FROM `course_master` WHERE categoryId = (SELECT id FROM `course_category` WHERE name = '{}') and `courseType` = (SELECT id from `course_typo` WHERE name = '{}')".format(req['msg2'],req['msg1'])
                    mycursor.execute(sql)
                    myresult = mycursor.fetchall()
                    for x in myresult:
                        course.append(x[0])
                    return jsonify([{"text":"select from following courses","actions":course},{"text":"select the state","actions":tot_state}])
                elif req['msg2'] in ['Facilities','Sports','Top_recruiters']:
                    col_dets=[]
                    if req['msg2'] == 'Top_recruiters':
                        query = "SELECT `top_recruiters`.`name` FROM `college_has_recruiters` JOIN `top_recruiters` ON `college_has_recruiters`.`recruiterid`=`top_recruiters`.`id` WHERE `college_has_recruiters`.`collegeId` IN (SELECT id FROM `college_list` WHERE name = '{} ')".format(req['msg1'])
                    elif req['msg2'] == 'Sports':
                        query = "SELECT `sportslist`.`name` FROM `college_has_sports` JOIN `sportslist` ON `college_has_sports`.`sportsid`=`sportslist`.`id` WHERE `college_has_sports`.`collegeId` IN (SELECT id FROM `college_list` WHERE name = '{} ')".format(req['msg1'])
                    else:
                        query = "SELECT `activitylist`.`name` FROM `college_has_activities` JOIN `activitylist` ON `college_has_activities`.`activityid`=`activitylist`.`id` WHERE `college_has_activities`.`collegeId` IN (SELECT id FROM `college_list` WHERE name = '{} ')".format(req['msg1'])
                    mycursor = mydb.cursor()
                    sql = query
                    mycursor.execute(sql)
                    mycollegedets = mycursor.fetchall()
                    for x in mycollegedets:

                        col_dets.append(x[0])
                    return jsonify([{"text":"{} in the {} are".format(req['msg2'],req['msg1']),"actions":col_dets}]) 
                else:
                    return jsonify([{"text":"No data avalible"}])
    else: return jsonify([{"text":"Invalid request"}])
