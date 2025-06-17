import tornado.ioloop
import tornado.web
import os
import tornado.escape
import tornado.httpserver
import tornado.options
import tornado.web
from tornado.options import define, options


define("port", default=9999, help="run on the given port", type=int)
define("debug", default=True, help="automatically detect code changes in development")
define("workers", default=4, help="maximum number of simultaneous async tasks")

class Application(tornado.web.Application):
    """Gobal settings of the server
    This defines the global settings of the server. This parses out the
    handlers, and includes settings for if ever we want to tie this to a
    database.
    """
    def __init__(self):
        handlers = [
        (r"/", MainHandler), #main website always called "index.html" 
        (r"/submit", FormHandler), #this is going to handle bundling our user's form input and trigger something on submit
        (r"/dashboard", DashboardHandler), #this is going to be our dumping ground for a users calculation
        (r"/result", ResultHandler)
        ]
        settings = dict(
            blog_title="cds",
            template_path=os.path.join(os.path.dirname(__file__), "templates"),
            static_path=os.path.join(os.path.dirname(__file__), "static"),
            xsrf_cookies=True,
            cookie_secret="__TODO:_GENERATE_YOUR_OWN_RANDOM_VALUE_HERE__",
        )
        super(Application, self).__init__(handlers, **settings)


class MainHandler(tornado.web.RequestHandler):
    def get(self):
        design_options = ['a','b','c']#cds.list_all_designs()
        self.render("templates/index.html",design_options=design_options) # when we end with a "render" function it will display the website you want

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
            # add cds calculation 

            # result will render with the information 
            # 
            self.render("templates/result.html", total=total)
        except (ValueError, TypeError):
            self.write("Invalid input. Please enter valid numbers.")

def main():
    tornado.options.parse_command_line()
    BaseHandler.executor = ProcessPoolExecutor(max_workers=options.workers)
    http_server = tornado.httpserver.HTTPServer(Application())
    http_server.listen(options.port)
    tornado.ioloop.IOLoop.current().start()


if __name__ == "__main__":
    main()



class BaseHandler(tornado.web.RequestHandler):
    """
    Logic to handle user information and database access might go here.
    """
    executor = ProcessPoolExecutor(max_workers=16)
    buffer = OrderedDict()

    def _get_task_response(self, id):
        """
        Simple function to grab a calculation that's stored in the buffer,
        and return a dictionary/json-like response to the front-end.
        """
        calc_task = self.buffer.get(id)
        task = calc_task.task

        response = {'id': id,
                    'name': calc_task.name,
                    'count': calc_task.count}

        if task.running():
            response['state'] = 'running'
            response['code'] = 202
        elif task.done():
            response['state'] = 'finished'
        elif task.cancelled():
            response['state'] = 'cancelled'
        else:
            response['state'] = 'pending'

        response['html'] = tornado.escape.to_basestring(
            self.render_string("calc_row.html", response=response))
        return response