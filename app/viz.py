import plotly.express as px 
import plotly.graph_objects as go
import plotly.io as pio

def plot():
    #insert figure making 
    fig = px.scatter(x=[0, 1, 2, 3, 4], y=[0, 1, 4, 9, 16])    
    #graph_json = pio.to_json(fig)
    graph_div = pio.to_html(fig, full_html=False, include_plotlyjs='cdn')
    return graph_div