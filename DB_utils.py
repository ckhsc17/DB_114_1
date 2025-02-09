import sys
import psycopg2
from tabulate import tabulate
from threading import Lock

from pymongo import MongoClient
from datetime import datetime, timedelta
from collections import defaultdict

DB_NAME = "I'M_IN"
DB_USER = "postgres"
# DB_NAME = "db_114_1"
# DB_USER = "bowen"
DB_HOST = "127.0.0.1"
DB_PORT = 5432
MONGO_URI = "mongodb://localhost:27017"

cur = None
db = None
create_event_lock = Lock()


# MongoDB 連線
def get_mongo_client(uri=MONGO_URI, db_name=DB_NAME):
    client = MongoClient(uri)
    return client[db_name]


# 記錄行為的函式
def log_action(event_type, details=None, user_id=None):
    mongo = get_mongo_client()
    action = {
        "event_type": event_type,
        "details": details,
        "user_id": user_id,
        "timestamp": datetime.now(),
    }
    mongo.activities.insert_one(action)
    print(f"Logged action: {action}")


def log_login(user_id, port):
    log_action(event_type="login", user_id=user_id)

    mongo = get_mongo_client()

    mongo.online_users.update_one(
        {"user_id": user_id},
        {
            "$set": {
                "status": "online",
                "port": port,
                "login_time": datetime.utcnow(),
                "last_active_time": datetime.utcnow(),
            }
        },
        upsert=True,  # 若無則插入
    )

    print(f"User {user_id} login at {datetime.now()}, from {port}")


def log_logout(addr):
    mongo = get_mongo_client()
    user = mongo.online_users.find_one({"port": addr[1]})
    if user:
        user_id = user["user_id"]
        mongo.online_users.update_one(
            {"user_id": user_id},
            {"$set": {"status": "offline", "logout_time": datetime.utcnow()}},
        )
        print(f"User {user_id} logout at {datetime.now()}")
    else:
        print(f"User {addr} not found in online users.")
        return

    log_action(event_type="logout", user_id=user_id)


def log_signup(user_id):
    log_action(event_type="signup", user_id=user_id)


def log_modify_user_info(user_id, item, new_value):
    log_action(
        event_type="modify_user_info",
        details={"item": item, "new_value": new_value},
        user_id=user_id,
    )


def log_join_event(user_id, event_id):
    log_action(event_type="join_event", details={"event_id": event_id}, user_id=user_id)


def db_connect():
    exit_code = 0
    try:
        global db
        db = psycopg2.connect(
            database=DB_NAME, user=DB_USER, password="", host=DB_HOST, port=DB_PORT
        )
        print("Successfully connect to DBMS.")
        global cur
        cur = db.cursor()
        return db

    except psycopg2.Error as err:
        print("DB error: ", err)
        exit_code = 1
    except Exception as err:
        print("Internal Error: ", err)
        raise err
    # finally:
    #     if db is not None:
    #         db.close()
    sys.exit(exit_code)


def print_table(cur):
    rows = cur.fetchall()
    columns = [desc[0] for desc in cur.description]

    return tabulate(rows, headers=columns, tablefmt="github")


# ============================= System function =============================
def db_register_user(username, pwd, email):
    cmd = """
            insert into "USER" (User_name, Password, Email) values (%s, %s, %s)
            RETURNING User_id;
            """
    cur.execute(cmd, [username, pwd, email])
    userid = cur.fetchone()[0]

    cmd = """
            insert into "USER_ROLE" (User_id, Role) VALUES (%s, 'User');
            """
    cur.execute(cmd, [userid])
    db.commit()

    return userid


def fetch_user(userid):
    cmd = """
            select * 
            from "USER" u
            join "USER_ROLE" r on u.User_id = r.User_id
            where u.User_id = %s;
            """
    cur.execute(cmd, [userid])

    rows = cur.fetchall()
    if not rows:
        return None, None, None, None, None
    else:
        isUser = False
        isAdmin = False
        for row in rows:
            userid, username, pwd, email, userid, role = row

            if role == "User":
                isUser = True
            elif role == "Admin":
                isAdmin = True

    return username, pwd, email, isUser, isAdmin


def username_exist(username):

    cmd = """
            select count(*) from "USER"
            where User_name = %s;
            """
    # print(cur.mogrify(cmd, [username]))
    cur.execute(cmd, [username])

    count = cur.fetchone()[0]
    return count > 0


def userid_exist(userid):
    cmd = """
            select count(*) 
            from "USER"
            where User_id = %s;
            """
    cur.execute(cmd, [userid])
    count = cur.fetchone()[0]
    return count > 0


# ============================= function for User =============================
def update_user_info(userid, item, new_value):
    cmd = f"""
            update "USER"
            set {item} = %s
            where User_id = %s;
            """
    print(f"Update User Info | {userid}: {item}->{new_value}")
    cur.execute(cmd, [new_value, userid])
    print(f"After update")
    db.commit()
    return


def isReserved(event_date, event_period_start, event_duration, classroom_id):
    query = f"""
            Select
            Case
                When Exists
                (
                    Select *
                    From "STUDY_EVENT_PERIOD" As sep
                    Where sep.Classroom_id = %s
                    And sep.Event_date = %s
                    And sep.Event_period >= %s
                    And sep.Event_period <= %s
                )
                Then 1
                Else 0
            End
            """

    # print(cur.mogrify(query, [classroom_id, event_date, event_period_start, int(event_period_start)+int(event_duration)]))
    cur.execute(
        query,
        [
            classroom_id,
            event_date,
            event_period_start,
            int(event_period_start) + int(event_duration),
        ],
    )
    return cur.fetchone()[0] > 0


def create_study_group(
    content,
    user_max,
    course_id,
    user_id,
    event_date,
    event_period_start,
    event_duration,
    classroom_id,
):

    create_event_lock.acquire()

    if isReserved(event_date, event_period_start, event_duration, classroom_id):
        return -1

    print("Is Available!!!")

    query = "select Create_Study_Group(%s, %s, %s, %s, %s, %s, %s, %s);"
    # print(cur.mogrify(query, [content, user_max, course_id, user_id,
    #                    event_date, event_period_start, event_duration, classroom_id]))
    cur.execute(
        query,
        [
            content,
            user_max,
            course_id,
            user_id,
            event_date,
            event_period_start,
            event_duration,
            classroom_id,
        ],
    )

    event_id = cur.fetchone()[0]
    db.commit()

    create_event_lock.release()

    return event_id


def list_available_study_group() -> str:
    query = """
            Select se.*
            From "STUDY_EVENT" As se
            Left Join "PARTICIPATION" As p On se.Event_id = p.Event_id
            Where se.Status = 'Ongoing'
            Group By se.Event_id
            Having Count(p.User_id) < (
                Select User_max
                From "STUDY_EVENT" AS se2
                Where se.Event_id = se2.Event_id
            );
            """

    cur.execute(query)

    return print_table(cur)


def join_study_group(user_id, event_id, join_time):
    query = """
            Insert Into "PARTICIPATION" (User_id, Event_id, Join_Time)
            Values (%s, %s, %s);
            """
    cur.execute(query, [user_id, event_id, join_time])
    db.commit()

    log_join_event(user_id, event_id)
    return


def isInEvent(user_id, event_id):
    query = """
            Select count(*)
            From "PARTICIPATION"
            Where Event_id = %s And User_id = %s;
            """
    cur.execute(query, [event_id, user_id])
    return cur.fetchone()[0] > 0


def leave_study_group(user_id, event_id):
    query = """
            Delete From "PARTICIPATION"
            Where Event_id = %s And User_id = %s;
            """
    cur.execute(query, [event_id, user_id])
    db.commit()


def list_history(user_id):
    query = """
            Select *
            From "PARTICIPATION" As p
            Join "STUDY_EVENT" As se On p.Event_id = se.Event_id
            Where p.User_id = %s;
            """
    cur.execute(query, [user_id])

    return print_table(cur)


def find_course(instructor_name, course_name):

    query = f"""
            Select *
            From "COURSE"
            Where 
            """
    count = 0
    if instructor_name != "None":
        count += 1
        query += f"Instructor_name Like '%{instructor_name}%'"
    if course_name != "None":
        if count > 0:
            query += " And "
        count += 1
        query += f"Course_name Like '%{course_name}%'"
    query += ";"

    if count == 0:  # All argument is "None" (No keyword for search)
        return "Instructor_name and Course_name cannot be both empty."

    # print(cur.mogrify(query))
    cur.execute(query)

    return print_table(cur)


def find_reserved_room_on_date(event_date):
    query = """
            Select c.Room_name, sep.Event_period
            From "STUDY_EVENT_PERIOD" As sep
            Join "CLASSROOM" As c On sep.Classroom_id = c.Classroom_id
            Where sep.Event_date = %s;
            """
    # print(cur.mogrify(query, [event_date]))
    cur.execute(query, [event_date])

    # # 記錄行為到 MongoDB
    log_action(
        event_type="query_reserved_room",
        details={
            "event_date": event_date,
            "query_date": datetime.utcnow().strftime("%Y-%m-%d"),
        },
    )

    print("Recent searched room on date: ")
    print(recent_searched_room())
    return print_table(cur)


# ============================= function for Admin =============================
def append_classroom(building_name, capacity_size, floor_number, room_name):
    query = """
            Insert Into "CLASSROOM" (Building_name, Capacity_size, Floor_number, Room_name)
            Values (%s, %s, %s, %s)
            RETURNING Classroom_id;
            """

    # print(cur.mogrify(query, [building_name, capacity_size, floor_number, room_name]))
    cur.execute(query, [building_name, capacity_size, floor_number, room_name])
    classroom_id = cur.fetchone()[0]
    db.commit()
    return classroom_id


def classroom_exist(classroom_id):
    query = """
            Select count(*)
            From "CLASSROOM"
            Where Classroom_id = %s;
            """
    cur.execute(query, [classroom_id])
    return cur.fetchone()[0] > 0


def remove_classroom(classroom_id):
    query = """
            Delete From "CLASSROOM"
            Where Classroom_id = %s;
            """

    cur.execute(query, [classroom_id])
    db.commit()


def update_classroom(classroom_id, item, new_value):
    query = f"""
            Update "CLASSROOM"
            Set {item} = %s
            Where Classroom_id = %s;
            """

    cur.execute(query, [new_value, classroom_id])
    db.commit()


def search_classroom(building_name, capacity_size, floor_number, room_name):
    query = """
            Select *
            From "CLASSROOM"
            Where 
            """
    count = 0
    if building_name != "None":
        count += 1
        query += f"Building_name Like '%{building_name}%'"
    if capacity_size != "None":
        if count > 0:
            query += " And "
        count += 1
        query += f"Capacity_size = {capacity_size}"
    if floor_number != "None":
        if count > 0:
            query += " And "
        count += 1
        query += f"Floor_number = {floor_number}"
    if room_name != "None":
        if count > 0:
            query += " And "
        count += 1
        query += f"Room_name Like '%{room_name}%'"
    query += ";"

    if count == 0:  # All argument is "None" (No keyword for search)
        return "Search column cannot be all empty."

    # print(cur.mogrify(query))
    cur.execute(query)

    return print_table(cur)


def append_course(
    course_name, instructor_name, department_name, lecture_time, commit=True
):
    query = """
            Insert Into "COURSE" (Course_name, Instructor_name, Department_name, Lecture_time)
            Values (%s, %s, %s, %s)
            RETURNING Course_id;
            """

    # print(cur.mogrify(query, [course_name, instructor_name, department_name, lecture_time]))
    cur.execute(query, [course_name, instructor_name, department_name, lecture_time])
    print(f"After exec")
    course_id = cur.fetchone()[0]
    if commit:
        db.commit()
    return course_id


def upload_courses(df):
    print(tabulate(df, headers="keys", tablefmt="psql"))
    try:
        for idx, row in df.iterrows():
            append_course(
                row["課程名稱"],
                row["授課教師"],
                row["授課對象"],
                row["時間"],
                commit=False,
            )
        db.commit()
        return "Successfully append courses."

    except psycopg2.DatabaseError as error:
        print(f"psycopg2 db error")
        if db:
            db.rollback()
        return f"Database upload error. Rollback. Error: {error}"

    except Exception as error:
        print(f"Error: {error}. Rollback.")
        if db:
            db.rollback()
        return f"Rollback. Error: {error}"


def course_exist(course_id):
    query = """
            Select count(*)
            From "COURSE"
            Where Course_id = %s;
            """
    cur.execute(query, [course_id])
    return cur.fetchone()[0] > 0


def remove_course(course_id):
    query = """
            Delete From "COURSE"
            Where Course_id = %s;
            """

    cur.execute(query, [course_id])
    db.commit()


def update_course(course_id, item, new_value):
    query = f"""
            Update "COURSE"
            Set {item} = %s
            Where Course_id = %s;
            """

    cur.execute(query, [new_value, course_id])
    db.commit()


def list_user_info(user_id):
    cmd = """
            Select *
            From "USER"
            Where User_id = %s;
            """
    cur.execute(cmd, [user_id])
    return print_table(cur)


def search_study_event(course_name):
    query = f"""
            Select *
            From "STUDY_EVENT" As se
            Join "COURSE" As c On se.Course_id = c.Course_id
            Where c.Course_name Like '%{course_name}%';
            """

    cur.execute(query)

    return print_table(cur)


def recent_searched_room():
    mongo = get_mongo_client()
    query = mongo.activities.find({"event_type": "query_reserved_room"})
    result = []
    for q in query:
        room_name = q["details"]["event_date"]
        result.append(room_name)

    room_count = {room: result.count(room) for room in set(result)}
    return room_count


# 行為分析
def get_behavior(behavior, period, user_id):
    mongo = get_mongo_client()
    query = mongo.activities.find()
    result = []
    for q in query:
        result.append(q)
    return result


def get_online_users():
    print("Get Online Users")
    db = get_mongo_client()
    users = db.online_users.find({"status": "online"}, {"user_id": 1, "_id": 0})

    online_users = [(u["user_id"], fetch_user(u["user_id"])[0]) for u in users] # 取得使用者名稱
    return tabulate(online_users, headers=["User ID", "Username"], tablefmt="github")


def get_user_log(user_id):
    db = get_mongo_client()
    logs = db.activities.find({"user_id": user_id})

    return tabulate(logs, headers="keys", tablefmt="github")

def get_hot_search_dates(days=30):
    db = get_mongo_client()
    start_time = datetime.utcnow() - timedelta(days=days)

    query = db.activities.aggregate([
        {
            "$match": {
                "event_type": "query_reserved_room",  # 只統計查詢教室的行為
                "timestamp": {"$gte": start_time}  # 限制只統計最近 days 天內的數據
            }
        },
        {
            "$group": {
                "_id": "$details.event_date",  # 按「被查詢的日期」分組
                "count": {"$sum": 1}  # 統計該日期被查詢的次數
            }
        },
        {"$sort": {"count": -1}}  # 按查詢次數降序排序
    ])

    result = list(query)  # 轉換 MongoDB Cursor 為列表
    
    result_list = [(r["_id"], r["count"]) for r in result]
    
    return tabulate(result_list, headers=["Event Date", "Count"], tablefmt="github")

def get_period_users(start_date = None, end_date = None, interval = "day"):
    """
    統計某個時間區間內，每天/每小時的登入人次
    :param start_date: 開始日期 (格式: YYYY-MM-DD)，可為 None（預設為今天）
    :param end_date: 結束日期 (格式: YYYY-MM-DD)，可為 None（預設為今天）
    :param interval: "day" 表示按天統計, "hour" 表示按小時統計（預設為 "day"）
    :return: 統計結果 (字典)
    """
    
    # 若 `start_date` 和 `end_date` 為 None，則預設為今天
    today = datetime.today().strftime("%Y-%m-%d")
    start_date = start_date or today
    end_date = end_date or today  # 預設結束日期也是今天
    
    print(f"Get Period Users from {start_date} to {end_date}")

    db = get_mongo_client()
    
    # 轉換時間格式
    start_dt = datetime.strptime(start_date, "%Y-%m-%d")
    end_dt = datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1)  # 包含整天

    # 查詢條件：篩選 event_type = "login" 且在指定時間範圍內
    query = {
        "event_type": "login",
        "timestamp": {"$gte": start_dt, "$lt": end_dt}
    }
    
    users = db.activities.find(query, {"user_id": 1, "timestamp": 1, "_id": 0})
    
    # 使用 defaultdict 統計登入人次
    login_stats = defaultdict(int)

    for user in users:
        login_time = user["timestamp"]
        
        if interval == "day":
            time_key = login_time.strftime("%Y-%m-%d")  # 按天統計
        elif interval == "hour":
            time_key = login_time.strftime("%Y-%m-%d %H:00")  # 按小時統計
        else:
            raise ValueError("interval 只能是 'day' 或 'hour'")
        
        login_stats[time_key] += 1

    # 輸出統計結果（在server console上）
    print("\n📊 登入人次統計結果：")
    for time_key, count in sorted(login_stats.items()):
        print(f"{time_key}: {count} 人登入")

    '''
    # 格式化結果為字符串，這樣可以發送給客戶端
    result_str = "\n📊 登入人次統計結果：\n"
    for time_key, count in sorted(login_stats.items()):
        result_str += f"{time_key}: {count} 人登入\n"
    '''

    # 格式化結果為簡單的 key,value 格式，方便前端繪圖
    result_str = ""
    for time_key, count in sorted(login_stats.items()):
        result_str += f"{time_key},{count}\n"

    return result_str

def calculate_usage():
    query = f"""
        SELECT 
            sep.classroom_id,
            COUNT(p.event_id) / c.capacity_size AS usage_rate,  -- 計算使用率
            se.status
        FROM 
            "STUDY_EVENT_PERIOD" sep
        JOIN 
            "STUDY_EVENT" se ON sep.event_id = se.event_id
        JOIN 
            "PARTICIPATION" p ON se.event_id = p.event_id
        JOIN 
            "CLASSROOM" c ON sep.classroom_id = c.classroom_id
        GROUP BY 
            sep.classroom_id, se.status, c.capacity_size
        ORDER BY 
            usage_rate DESC  -- 根據使用率排序，假設需要按使用率排序
        LIMIT 10;  -- 只列出前10筆資料，沒有篩選條件時使用
    """

    cur.execute(query)

    return print_table(cur)
