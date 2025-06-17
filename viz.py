import plotly.express as px 
import plotly.graph_objects as go
import plotly.io as pio

def make_plot1():
    df = px.data.iris()
    #insert figure making 
    fig= px.scatter(df)
    
    graph_json = pio.to_json(fig)
    return graph_json