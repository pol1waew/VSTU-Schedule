from django.shortcuts import render
import sqlite3

def index(request):
    connection = sqlite3.connect("db.sqlite3")
    cursor = connection.cursor()

    cursor.execute("select \
                   api_timeslot.start_time, api_timeslot.end_time \
                   from api_eventholding \
                   inner join api_timeslot on api_eventholding.time_slot_id = api_timeslot.id")
    data = cursor.fetchall()
    time = '{} - {}'.format(str(data[0][0])[:-3], str(data[0][1])[:-3])
    
    cursor.execute("select \
                   api_subject.name \
                   from api_eventholding \
                   join api_event on api_eventholding.event_id = api_event.id \
                   join api_subject on api_event.subject_id = api_subject.id")
    subject = cursor.fetchall()[0][0]
    
    cursor.execute("select \
                   api_eventplace.building, api_eventplace.room \
                   from api_eventholding \
                   inner join api_eventplace on api_eventholding.place_id = api_eventplace.id")
    data = cursor.fetchall()
    place = '{}-{}'.format(data[0][0], str(data[0][1])[5:])

    teacher = "" 

    connection.close()

    return render(request, "index.html", {
        "time" : time,
        "subject" : subject,
        "teacher" : teacher,
        "place" : place
        })