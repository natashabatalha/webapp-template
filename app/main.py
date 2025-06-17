import tornado.ioloop
import tornado.web
import os

def make_app():
    return tornado.web.Application([
        (r"/", MainHandler),
        (r"/submit", FormHandler),
        (r"/dashboard", DashboardHandler),
        (r"/result", ResultHandler),
    ], debug=True, autoreload=True)

class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.render("templates/index.html")

class FormHandler(tornado.web.RequestHandler):
    def post(self):
        num1 = self.get_argument("number1")
        num2 = self.get_argument("number2")
        self.redirect(f"/dashboard?number1={num1}&number2={num2}")

class DashboardHandler(tornado.web.RequestHandler):
    def get(self):
        # This handler doesn't need to pass any data,
        # it just renders the dashboard page.
        self.render("templates/dashboard.html")

class ResultHandler(tornado.web.RequestHandler):
    def get(self):
        try:
            num1 = float(self.get_argument("number1"))
            num2 = float(self.get_argument("number2"))
            total = num1 + num2
            self.render("templates/result.html", total=total)
        except (ValueError, TypeError):
            self.write("Invalid input. Please enter valid numbers.")



if __name__ == "__main__":
    app = make_app()
    port = 9999
    app.listen(port)
    print(f"Server started on http://localhost:{port}")
    tornado.ioloop.IOLoop.current().start()
