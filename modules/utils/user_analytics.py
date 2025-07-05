import logging

user_stats = {}

def record_command(user_id, command):
    user_stats.setdefault(user_id, {})
    user_stats[user_id][command] = user_stats[user_id].get(command, 0) + 1
    logging.info(f"User {user_id} used command {command}")

def get_stats(user_id):
    return user_stats.get(user_id, {})
