from .User import User

from action.classroom_management.ManageClassroom import ManageClassroom
from action.course_management.ManageCourse import ManageCourse
from action.behavior_analysis.ListUserInfo import ListUserInfo
from action.event.SearchEvent import SearchEvent

from action.behavior_analysis.LoginTime import LoginTime
from action.behavior_analysis.PopularDate import PopularDate
from action.behavior_analysis.UsageRate import UsageRate
from action.behavior_analysis.PopularEvent import PopularEvent
from action.behavior_analysis.PopularClassroom import PopularClassroom
from action.behavior_analysis.Online import Online



class Admin(User):
    def __init__(self, userid, username, pwd, email):
        super().__init__(userid, username, pwd, email)
        self.user_action =  super().get_available_action() + [
                                ManageClassroom("Add/Remove/Modify/Search Classroom"),
                                ManageCourse("Add/Upload/Remove/Modify/Search Course"),
                                ListUserInfo("List User Information"),
                                SearchEvent("Search Study Event"),
                                LoginTime("Login Time Analysis"),
                                PopularDate("Popular Date Analysis"),
                                UsageRate("Usage Rate Analysis"),
                                PopularEvent("Popular Event Analysis"),
                                PopularClassroom("Popular Classroom Analysis"),
                                Online("Users Analysis")
                            ]
        

    def isAdmin(self):
        return True