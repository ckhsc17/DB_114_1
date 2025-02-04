#Old
from ..Action import Action
from DB_utils import get_behavior

class ListBehavior(Action):
     def exec(self, conn, user):
        print("Behavior Analysis")


        behavior = self.read_input(conn, "behavior that you want to analyze")
        '''
        if behavior not in ["click", "search", "view"]:
            conn.send(f"Invalid behavior type: {behavior}\n".encode('utf-8'))
            return -1
        '''
        period = self.read_input(conn, "period that you want to analyze")
        user_id = self.read_input(conn, "user id that you want to analyze")
        
        table = get_behavior(behavior, period, user_id)
        self.send_table(conn, table)
    
        return 