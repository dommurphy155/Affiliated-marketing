link_clicks = {}

def record_click(link_id):
    link_clicks[link_id] = link_clicks.get(link_id, 0) + 1

def get_clicks(link_id):
    return link_clicks.get(link_id, 0)
