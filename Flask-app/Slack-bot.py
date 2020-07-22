import os
from flask import Flask, url_for, render_template, request, redirect, make_response
from slack import WebClient
from slackeventsapi import SlackEventAdapter
import plotly.graph_objects as go
import datetime
import plotly.io as pio
import threading
import json

app = Flask(__name__)
client = WebClient(os.environ['SLACK_ACCESS'])
events = SlackEventAdapter(os.environ['SLACK_SECRET'], "/slack/events", app)
userScores = {}
tickets = {}

'''
modalFile and welcomeFile contain the block-kit data that the bot will use
to serve the modal when prompting a ticket service and format the welcome message respectively
'''
modalFile = open('static/ticket_form')
jsonModal = json.load(modalFile)
modalFile.close()
welcomeFile = open('static/welcome_msg')
welcomeBlock = welcomeFile.read()
welcomeFile.close()

#This event fires every time someone joins the server.
#It sends the aformentioned welcome message to the new user.
@events.on('team_join')
def welcome(event_data):
    print(event_data)
    uid = event_data['event']['user']['id']
    client.chat_postMessage(channel=uid, blocks=welcomeBlock)

#The landing page, where users can view and resolve tickets
@app.route('/', methods = ['GET'])
def LandingPage():
    return render_template('ticket.html')

#This method is called by both the shortcut which prompts this method to serve the modal and the actual submission of the modal.
#When called during submission, it creates and stores the ticket from user input
@app.route('/ticket', methods=['POST'])
def LoadForm():
    payload = json.loads(request.form['payload'])
    if payload['type'] == 'view_submission':
        vals =payload['view']['state']['values']
        vals = [vals[x] for x in vals.keys()]
        vals = [x['text']['value'] for x in vals]
        tickets.update({datetime.datetime.now().strftime('%y_%m_%d_%H_%M_%S'):{'poster':vals[0], 'query':vals[1]}})
    client.views_open(trigger_id=payload['trigger_id'], view=jsonModal)
    return '', 200

#simply deletes the ticket
@app.route('/resolve/<key>', methods=['POST'])
def Resolveticket(key):
    del tickets[key]
    redirect(url_for('LandingPage'))

#returns all tickets, in json format
@app.route('/queries', methods=['GET'])
def GetTickets():
    print(json.dumps(tickets))
    return str(json.dumps(tickets))

'''
The Praise function is called by the /praise slash command in the workspace
Although it can effectively work with 2 arguments (name and amount)
It is important to note that all arguments passed in by the 'text' field in the form
Splitting required
'''
@app.route('/praise', methods=['POST'])
def Praise():
    print(request.form)
    uid = request.form['user_id']
    if request.form['text'] != '':
        words = request.form['text'].split(' ')
        #The function doesn't run if the arguments supplied are invalid but the user who called the function will be notified that it didn't go through
        if len(words) > 2:
            client.chat_postMessage(channel=uid, text='looks like you messed up. /praise cannot handle more than 2 arguments')
            return '', 200
        username = words[0]
        praiseAmount = 1
        try:
            if len(words)==2:
                praiseAmount = int(words[1])
        except:
            client.chat_postMessage(channel=uid, text='looks like you messed up. /praise needs argument 2 to be a number')
        if username in userScores:
            userScores[username] += praiseAmount
        else:
            userScores[username] = praiseAmount
        trailingS = 's' if praiseAmount != 1 else ''
        client.chat_postMessage(channel='praising-room', text=words[0] + ' has been praised ' + str(praiseAmount) + ' time'+ trailingS)
    else:
        client.chat_postMessage(channel=uid, text='looks like you messed up. /praise needs atleast one argument to work')
    return '', 200

#Generates a plotly bar graph showing the userscores 
@app.route('/report', methods=['POST'])
def GenerateReport():
    if len(userScores) > 0:
        thread = threading.Thread(target=GeneratePraiseGraph, args=(request.url_root,))
        thread.start()
        #Cannot generate in time before timeout,
        #so it is done in a new thread
        return 'Working on it!'
    else:
        return 'No data exists yet. use \'/praise\' to contribute'
    return '' , 200


def GeneratePraiseGraph(base_url):
    try:
        descending = sorted(userScores.items(), key=lambda x:x[1], reverse=True)
        labels, values = map(list, zip(*descending))
        fname = 'images/' + str(datetime.datetime.now().strftime('%y_%m_%d_%H_%M_%S')) + '.png'
        fig = go.Figure([go.Bar(x=labels, y=values)])
        print('got this far')
        fig.write_image('static/' + fname, engine='kaleido')
        im_url =  base_url + 'static/' +fname
        print(im_url)
        client.chat_postMessage(channel='praising-room', attachments = [{'text':'So far, ' + labels[0] + ' recieving the most praise at ' + str(values[0]),'image_url':im_url}])
    except:
        client.chat_postMessage(channel='praising-room', text='Something went wrong... So sorry')


if __name__ == '__main__':
    app.run(host='0.0.0.0',port=int(os.environ.get('PORT', 8080)))