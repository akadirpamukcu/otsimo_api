from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import urllib.request
import json
import time
import html
import random 


class RequestHandler(BaseHTTPRequestHandler):
    def newGame(self,query):
        global session_count
        global data
        #default variables
        difficulty="easy"
        category=9
        question_count=10
        if "amount" in query:
            question_count = (query["amount"])[0]
        if "difficulty" in query:
            difficulty = "".join(query["difficulty"])
        if "category" in query:
            category = "".join(query["category"])
        self.send_response(200)
        self.end_headers()
        self.wfile.write(str.encode("New Trivia Game started"+"\n" + "Session ID = " + str(session_count) + "\n"))

        url = "https://opentdb.com/api.php?amount=" + str(question_count) +  "&category=" + str(category) + "&difficulty=" + str(difficulty) 

        webURL = urllib.request.urlopen(url)
        data = webURL.read()
        encoding = webURL.info().get_content_charset('utf-8')
        data = json.loads(data.decode(encoding))
        count = 0
        for i in data["results"]:
            count+=1
        if count < int(question_count):
            question_count=count;
        session = { "id": session_count,  "question_number": 0,  "remain": int(question_count) , "correct_count": 0, "state": "open"}
        sessions.append(session)
        session_count+=1
        return session_count-1

    def next(self,query):
        global sent_time
        sent_time = time.time()
        session = int((query["id"])[0])
        if "id" not in query:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b'Session id needed.\n')
            return
        if int((query["id"])[0]) <= len(sessions):
            if str(sessions[session-1]["state"]) == "done":
                self.send_response(404)
                self.end_headers()
                self.wfile.write(b'This session is already played.\n')
                return
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b'invalid session id\n')
            return
        if( int(sessions[session-1]["remain"]) == 0):
            sessions[session-1]["state"] = "done"
            self.send_response(200)
            self.end_headers()
            self.wfile.write(str.encode("Game is Over" + "\n"+ str(sessions[session-1]["correct_count"]) + " correct out of " + str(sessions[session-1]["question_number"]+1)+"\n"))
            return

        a = "Question Number: " +  str(sessions[session-1]["question_number"]+1) + "\n" + "Category: "
        a+= data["results"][sessions[session-1]["question_number"]]["category"] +"\n" 
        a+= "Question: " +  data["results"][sessions[session-1]["question_number"]]["question"] + "\n" 
        a+=  "\n" + "Answers:" + "\n" 
        if(data["results"][sessions[session-1]["question_number"]]["type"] == "multiple"):
            answers = [data["results"][sessions[session-1]["question_number"]]["correct_answer"],data["results"][sessions[session-1]["question_number"]]["incorrect_answers"][1],data["results"][sessions[session-1]["question_number"]]["incorrect_answers"][0],data["results"][sessions[session-1]["question_number"]]["incorrect_answers"][2]]
            random.shuffle(answers)
            a+= "- " + answers[3] + "\n"  + "- " + answers[0] + "\n" + "- " + answers[1] + "\n" + "- " + answers[2] + "\n" + "\n" + "You have 15 seconds to answer!" + "\n"
        if(data["results"][sessions[session-1]["question_number"]]["type"] == "boolean"):
            a+= "-" + "True" + "\n" + "-" + "False" + "\n" + "You have 15 seconds to answer!" + "\n"
        self.send_response(200)
        self.end_headers()
        self.wfile.write(bytes(html.unescape(a),"utf-8"))
        return


    def answer(self,query):
        session = int((query["id"])[0])
        global sent_time
        if(time.time() - sent_time  > 15):
            self.send_response(200)
            self.end_headers()
            self.wfile.write(str.encode("Time is Over!!" + "\n"+"\n"+ str(sessions[session-1]["correct_count"]) + " correct out of " + str(sessions[session-1]["question_number"]+1)+"\n"+"\n"+ "There are " + str(sessions[session-1]["remain"]-1) + " more questions left" + "\n" ))
            sessions[session-1]["question_number"]+=1
            sessions[session-1]["remain"]-=1
            return
        
        if "id" not in query:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b'Session id needed.\n')
            return
        if int((query["id"])[0]) <= len(sessions):
            if sessions[session-1]["state"] == "done":
                self.send_response(404)
                self.end_headers()
                self.wfile.write(b'This session is already played.\n')
                return
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b'invalid session id\n')
            return
        sessions[session-1]["remain"]-=1
        if "answer" in query:
            answer = "".join(query["answer"])
            if(answer == data["results"][sessions[session-1]["question_number"]]["correct_answer"]):
                sessions[session-1]["correct_count"]+=1
                self.send_response(200)
                self.end_headers()
                self.wfile.write(str.encode("CORRECT ANSWER!!" + "\n"+"\n"+ str(sessions[session-1]["correct_count"]) + " correct out of " + str(sessions[session-1]["question_number"]+1)+"\n"+"\n"+ "There are " + str(sessions[session-1]["remain"]) + " more questions left" + "\n" ))
            else:
                self.send_response(200)
                self.end_headers()
                self.wfile.write(str.encode("WRONG ANSWER!!" + "\n"+"\n"+ str(sessions[session-1]["correct_count"]) + " correct out of " + str(sessions[session-1]["question_number"]+1)+"\n"+"\n"+ "There are " + str(sessions[session-1]["remain"]) + " more questions left" + "\n" ))
        sessions[session-1]["question_number"]+=1
        if int(sessions[session-1]["remain"]) < 0:
            sessions[session-1]["state"] = "done"
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b'Not Found!\n')
            return


    def say_hello(self, query):
        """
        Send Hello Message with optional query
        """
        mes = "Hello"
        if "name" in query:
            # query is params are given as array to us
            mes += " " + "".join(query["name"])
        self.send_response(200)
        self.end_headers()
        self.wfile.write(str.encode(mes+"\n"))

    def do_GET(self):
        url = urlparse(self.path)
        if url.path == "/hello":
            return self.say_hello(parse_qs(url.query))
        if url.path == "/newGame":
            return  self.newGame(parse_qs(url.query))
        if url.path == "/next":
            self.next(parse_qs(url.query))
            return
        # return 404 code if path not found
        self.send_response(404)
        self.end_headers()
        self.wfile.write(b'Not Found!\n')

    def do_POST(self):
        url = urlparse(self.path)
        if url.path == "/answer":
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            self.answer(parse_qs(post_data.decode("utf-8")))
            return
        self.send_response(404)
        self.end_headers()
        self.wfile.write(b'Not Found!\n')

if __name__ == "__main__":
    data = {}
    session_count=1
    sessions = []
    sent_time = time.time()
    port = 8080
    print(f'Listening on localhost:{port}')
    server = HTTPServer(('', port), RequestHandler)
    server.serve_forever()

