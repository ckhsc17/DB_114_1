from ..Action import Action
from DB_utils import get_hot_search_dates

class PopularClassroom(Action):
    def exec(self, conn, user):
        print("Popular Classroom Analysis")