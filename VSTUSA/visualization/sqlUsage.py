from visualization.models import ApiEventholding

def getDates():
    dates = []
    objects = ApiEventholding.objects.values_list("date").distinct()

    for obj in objects:
        dates.append(str(obj[0]))

    return ["2024-10-21", "2024-10-22", "2024-10-23"]

def getEntries(forDate):
    entries = []
    objects = ApiEventholding.objects.filter(date = forDate)

    for obj in objects:
        entry = {}
        
        entry["start_time"] = obj.time_slot.start_time
        entry["end_time"] = obj.time_slot.end_time
        entry["subject"] = obj.event.subject.name
        entry["place_building"] = obj.place.building
        entry["place_room"] = obj.place.room

        entries.append(entry)

    return entries