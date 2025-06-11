from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
import requests 

run = Flask(__name__)

MAPIT_BASE_URL = "https://mapit.openup.org.za"
#tracking userstates
user_state = {} 

@run.route("/whatsapp", methods= ['POST', 'GET'])
def whatsapp_webhook():


    incoming_msg = request.values.get("Body","").lower()
    lat = request.values.get("Latitude")
    lon = request.values.get("Longitude")
    sender = request.form.get("From")

    resp = MessagingResponse()
    msg = resp.message()

    state = user_state.get(sender, "start")
    complaints = {}

    

    if lat and lon and state == "started":
        map_it = f"{MAPIT_BASE_URL}/point/4326/{lon},{lat}"
        print(map_it)
        res = requests.get(map_it)
        data = res.json()

        district = municipality = province = None
    
        for area in data.values():
            if area['type_name'] == "District":
                district = area['name']
            if area["type_name"] == "Municipality":
                municipality = area["name"]
            if area["type_name"] == "Province":
                province = area["name"]
                

        if province:
            response_text = (
                f"📍 You are in: \n"
                f"Province: *{province}*\n"
                f"District: *{district or 'N/A'}*\n"
                f"Municipality: *{municipality or 'N/A'}*\n\n"
                f"What would you like to do? \n"
                f"1️⃣ Lodge a complaint\n"
                f"2️⃣ View emergency contact\n"
                f"3️⃣ View map of your municipality\n\n"
                f"_Reply with the number option above_."
            )
            msg.body(response_text)
        else:
            response_text = "*Sorry, we couldn't locate your position. Please try again*"
   
    elif incoming_msg == "1" and state == "started":
            user_state[sender] = "in_complaints"
            msg.body(
                "Please select the type of complaint you would like to lodge.\n\n"
                "#️⃣1️⃣ Water\n"
                "#️⃣2️⃣ Electricity\n"
                "#️⃣3️⃣ Sanitation\n"
                "#️⃣4️⃣ Roads\n"
                "#️⃣5️⃣ Other\n\n"                                                                                     
                "_*Please enter the \"#\" key followed by number of the complaint type you would like to lodge.*_"
                )
            
    if incoming_msg == "#1" and state == "in_complaints":
            complaint_type = "water_complaint"
            msg.body("Please type the description of the issue. \nOptionally, you can include an image along with your description.📸")
            complaints = {"sender": sender, "complaint_type" :complaint_type, "complaint_description": incoming_msg}
    elif incoming_msg == "#2" and state == "in_complaints":
            complaint_type = "power_complaint"
            msg.body("Please type the description of the issue. \nOptionally, you can include an image along with your description.📸")
            complaints = {"sender": sender, "complaint_type" :complaint_type, "complaint_description": incoming_msg}
    elif incoming_msg == "#3" and state == "in_complaints":
            complaint_type = "sanitation_complaint"
            msg.body("Please type the description of the issue. \nOptionally, you can include an image along with your description.📸")
            complaints = {"sender": sender, "complaint_type" :complaint_type, "complaint_description": incoming_msg}
    elif incoming_msg == "#4" and state == "in_complaints":
            complaint_type = "road_complaint"
            msg.body("Please type the description of the issue. \nOptionally, you can include an image along with your description.📸")
            complaints = {"sender": sender, "complaint_type" :complaint_type, "complaint_description": incoming_msg}
    elif incoming_msg == "#5" and state == "in_complaints":
            complaint_type = "other_complaint"
            msg.body("Please type the description of the issue. \nOptionally, you can include an image along with your description.📸")
            complaints = {"sender": sender, "complaint_type" :complaint_type, "complaint_description": incoming_msg}


    elif incoming_msg == "2" and state == "started":
            user_state[sender] = "in_EMS"
            #View EMS 
    elif incoming_msg == "3" and state == "started":
            #Display map of muni location
            user_state[sender] = "in_map"
       

    elif state == "started" and not lon and not lat:
          msg.body("Sorry 😅, I could not understand that, plz follow my send your location so I can look up your current Muni_Info!")   
        #  print(state)
    else:
        msg.body("📍 Please send your *location* to look up Muni_Info.")
        user_state[sender] = "started"
        #print(state)

    return str(resp)

if __name__ == "__main__":
    run.run(debug = True)