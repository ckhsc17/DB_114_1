from ..Action import Action
from .OnlineUsers import OnlineUsers
from .UsersLog import UsersLog
from utils import list_option, get_selection

class Online(Action):
    def __init__(self, action_name):
        super().__init__(action_name)
        self.options = [
                        OnlineUsers("Online Users"),
                        UsersLog("Users Log")
                        ]

    def exec(self, conn, user):
        print("Manage Online Users")

        
        msg = '[INPUT]What do you want to do?\n' + list_option(self.options) + '---> '
        conn.send(msg.encode('utf-8'))
        
    

        action = get_selection(conn, self.options)
        action.exec(conn)

        
        # conn.send(f'\nUpdate successfully! New {item}: {new_value}\n'.encode('utf-8'))
        