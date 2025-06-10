from twilio.twiml.messaging_response import MessagingResponse
#from twilio.twiml.messaging_response import Message
from twilio.rest import Client
from flask import Flask, request
import os 
import dotenv
app = Flask(__name__)

@app.route('/', methods=['GET','POST'])
def info_reply():

    inc_msg = request.form.get("Body", None).lower()

    resp = MessagingResponse()
    msg = resp.message()
    account_sid = os.environ["TWILIO_ACCOUNT_SID"]
    auth_token = os.environ["TWILIO_AUTH_TOKEN"]
    #client = Client(account_sid, auth_token


    
    if inc_msg in ["menu", "hi", "hello"]:
        msg.body(
            "📋 *Main Menu*\n"
            "1. View District\n"
            "2. View Municipality\n"
            "3. View Map\n"
            "4. Lodge Complaint\n"
            "5. Emergency Services\n\n"
            "Please type the number of your choice."
        )
            
       
           

    elif inc_msg == "1":
        msg.body("You are in Amathole District")
    elif inc_msg == "2":
        msg.body("Your local municipality is Mnquma Local Municipality.")
    elif inc_msg == "3":
        msg.body("Here is the map of your district: \n https://goo.gl/maps/example")
    elif inc_msg == "4":
        msg.body("Please reply with your complaints details.")
    elif inc_msg == "5":
        msg.body("Emergency Services: \n Police: 10111 \n Ambulance: 10177 ")
    else:
        msg.body("Welcome! Please select the option you would like.")
        inc_msg = "menu"
        msg.body(
            "\n📋 *Main Menu*\n"
            "1. View District\n"
            "2. View Municipality\n"
            "3. View Map\n"
            "4. Lodge Complaint\n"
            "5. Emergency Services\n\n"
            "Please type the number of your choice."
        )
      #  msg.body("Welcome! Please type "'"*menu*"'" to see options.")

   # resp.append(msg)
    return str(resp)

if __name__ == "__main__":
    app.run(debug=True, port=5000)
        