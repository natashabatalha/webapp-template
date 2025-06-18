import tornado.ioloop
import tornado.web
import os
import tornado.escape
import tornado.httpserver
import tornado.options
import tornado.web
from tornado.options import define, options
from collections import namedtuple, OrderedDict
from concurrent.futures import ProcessPoolExecutor
import uuid

import viz 
import cds

define("port", default=9999, help="run on the given port", type=int)
define("debug", default=True, help="automatically detect code changes in development")
define("workers", default=4, help="maximum number of simultaneous async tasks")

# Define a simple named tuple to keep track for submitted calculations
CalculationTask = namedtuple('CalculationTask', ['id', 'name', 'task',
                                                 'cookie', 'count', 'form_data'])


class Application(tornado.web.Application):
    """Gobal settings of the server
    This defines the global settings of the server. This parses out the
    handlers, and includes settings for if ever we want to tie this to a
    database.
    """
    def __init__(self):
        handlers = [
        (r"/", MainHandler), #main website always called "index.html" 
        #(r"/submit", FormHandler), #this is going to handle bundling our user's form input and trigger something on submit
        (r"/dashboard", DashboardHandler), #this is going to be our dumping ground for a users calculation
        #(r"/result", ResultHandler),
        (r"/calculation/new", CalculationNewHandler),
        (r"/calculation/new/([^/]+)", CalculationNewHandler),
        (r"/calculation/status/([^/]+)", CalculationStatusHandler),
        (r"/calculation/view/([^/]+)", CalculationViewHandler),


        ]
        settings = dict(
            blog_title="cds",
            template_path=os.path.join(os.path.dirname(__file__), "templates"),
            static_path=os.path.join(os.path.dirname(__file__), "static"),
            xsrf_cookies=True,
            cookie_secret="__TODO:_GENERATE_YOUR_OWN_RANDOM_VALUE_HERE__",
        )
        super(Application, self).__init__(handlers, **settings)

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

        print('in _get_task_response',response)

        response['html'] = tornado.escape.to_basestring(
            self.render_string("calc_row.html", response=response))
        return response
        
    def write_error(self, status_code, **kwargs):
        """
        This renders a customized error page
        """
        reason = self._reason
        error_info = ''
        trace_print = ''
        if 'exc_info' in kwargs:
            error_info = kwargs['exc_info']
            try:
                trace_print = traceback.format_exception(*error_info)
                trace_print = "\n".join(map(str,trace_print))
            except:
                pass
        self.render('errors.html',page=None, status_code=status_code, reason=reason, error_log=trace_print)


    def _get_task_result(self, id):
        """
        This method grabs only the result returned from the python `Future`
        object. This contains the stuff that Pandeia returns.
        """
        calc_task = self.buffer.get(id)
        task = calc_task.task
        return task.result()

    def _add_task(self, id, name, task, form_data=None):
        """
        This creates the task and adds it to the buffer.
        """
        self.buffer[id] = CalculationTask(id=id, name=name, task=task,
                                          count=len(self.buffer)+1,
                                          cookie=self.get_cookie("user"),
                                          form_data=form_data)

        # Only allow 100 tasks **globally**. This will delete old tasks first.
        if len(self.buffer) > 100:
            self.buffer.popitem(last=False)

class MainHandler(BaseHandler):
    def get(self):
        if not self.get_cookie("user"):
            self.set_cookie("user", str(uuid.uuid4()))
        self.render("index.html") # when we end with a "render" function it will display the website you want

class FormHandler(BaseHandler):
    # there are two types of functions "get" and "post" -- as you might guess "get" is getting or displaying info. 
    # "post" is passing information
    def post(self): 
        #number1 and number2 are defined by the "id" in the html form you have created
        num1 = self.get_argument("number1")
        num2 = self.get_argument("number2")
        # opposed to render, this is now redirecting info to your dashboard with the information
        self.redirect(f"/dashboard?number1={num1}&number2={num2}") 

class DashboardHandler(BaseHandler):
    """
    Request handler for the dashboard page. This will retrieve and render
    the html template, along with the list of current task objects.
    """
    def get(self):
        task_responses = [self._get_task_response(id) for id, nt in
                          list(self.buffer.items())
                          if ((nt.cookie == self.get_cookie("user"))
                          & (id[len(id)-1]=='e'))]
        
        self.render("dashboard.html", calculations=task_responses[::-1])


class CalculationNewHandler(BaseHandler):
    """
    This request handler deals with processing the form data and submitting
    a new calculation task to the parallelized workers.
    """
    def get(self, id=None):
        design_options=['a','b','c']
        self.render("new.html", id=id,design_options=design_options)

    
    def post(self):
        """
        The post method contains the returned data from the form data (
        accessed by using `self.get_argument(...)` for specific arguments,
        or `self.request.body` to grab the entire returned object.
        """        
        form_data = {}
        for key in self.request.arguments:
            form_data[key] = self.get_argument(key)

        id = str(uuid.uuid4())+'e'
       
        finaldata = {'a':float(form_data['number1']),'b':
                     float(form_data['number2'])}
        
        task = self.executor.submit(cds.run, finaldata)


        self._add_task(id, self.get_argument("calc_name"), task, form_data)

        response = self._get_task_response(id)
        response['info'] = {}
        response['location'] = '/calculation/status/{}'.format(id)


        self.write(dict(response))
        self.redirect("../dashboard")

class CalculationStatusHandler(BaseHandler):
    """
    Handlers returning the status of a particular JWST calculation task.
    """
    def get(self, id):
        response = self._get_task_response(id)

        if self.request.connection.stream.closed():
            return

        self.write(dict(response))

class CalculationViewHandler(BaseHandler):
    """
    Get viz data 
    """
    def get(self, id):
        
        result = self._get_task_result(id)
        
        graph_div = viz.plot()
        #div['timing_div'] = result['timing_div']
        #div['input_div'] = result['input_div'] 
        #div['warnings_div'] = result['warnings_div']

        #delete files
        #allfiles = os.listdir(__TEMP__)
        #for i in allfiles:
        #    if i.find(id) != -1:
        #        os.remove(os.path.join(__TEMP__,i))

        self.render("view.html", graph_div=graph_div)


"""
class ResultHandler(BaseHandler):
    def get(self):
        try:
            num1 = float(self.get_argument("number1"))
            num2 = float(self.get_argument("number2"))
            # here is our calculation being done 
            total = num1 + num2
            # add cds calculation 

            # result will render with the information 
            # 
            self.render("result.html", total=total)
        except (ValueError, TypeError):
            self.write("Invalid input. Please enter valid numbers.")
        """

def main():
    tornado.options.parse_command_line()
    BaseHandler.executor = ProcessPoolExecutor(max_workers=options.workers)
    http_server = tornado.httpserver.HTTPServer(Application())
    http_server.listen(options.port)
    tornado.ioloop.IOLoop.current().start()

if __name__ == "__main__":
    main()

