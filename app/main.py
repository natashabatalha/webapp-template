import tornado.ioloop
import tornado.web
import os

def make_app():
    """
    Here we have a one Handler for every action you want in your webapp. 
    Sometimes you can think of these as each individual webpage you are building (e.g. Dashboard), 
    other times these are "actions" of your website like the FormHandler. 
    """
    return tornado.web.Application([
        (r"/", MainHandler), #main website always called "index.html" 
        (r"/submit", FormHandler), #this is going to handle bundling our user's form input and trigger something on submit
        (r"/dashboard", DashboardHandler), #this is going to be our dumping ground for a users calculation
        (r"/result", ResultHandler),#this will be our results page 
    ], debug=True, autoreload=True)#as you edit this page your website will update automatically if this is set to True and True

class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.render("templates/index.html") # when we end with a "render" function it will display the website you want

class FormHandler(tornado.web.RequestHandler):
    # there are two types of functions "get" and "post" -- as you might guess "get" is getting or displaying info. 
    # "post" is passing information
    def post(self): 
        #number1 and number2 are defined by the "id" in the html form you have created
        num1 = self.get_argument("number1")
        num2 = self.get_argument("number2")
        # opposed to render, this is now redirecting info to your dashboard with the information
        self.redirect(f"/dashboard?number1={num1}&number2={num2}") 

class DashboardHandler(tornado.web.RequestHandler):
    def get(self):
        # This handler doesn't need to pass any data,
        # it just renders the dashboard page (formhandler has given us the info we need for the dashboard)
        self.render("templates/dashboard.html")

class ResultHandler(tornado.web.RequestHandler):
    def get(self):
        try:
            num1 = float(self.get_argument("number1"))
            num2 = float(self.get_argument("number2"))
            # here is our calculation being done 
            total = num1 + num2
            # result will render with the information 
            # 
            self.render("templates/result.html", total=total)
        except (ValueError, TypeError):
            self.write("Invalid input. Please enter valid numbers.")



if __name__ == "__main__":
    app = make_app()
    port = 9999
    app.listen(port)
    print(f"Server started on http://localhost:{port}")
    tornado.ioloop.IOLoop.current().start()
