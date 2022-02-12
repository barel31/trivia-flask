from flask import Blueprint, redirect, url_for, render_template, request, session, flash
from flask_login import login_user, login_required, logout_user, current_user
from .models import User
from . import db
import random
import json
import requests
import html
import time

questions = {}
answered_dict = {}
finish_list = []
database_refreshed_by = 'Server'
ADMIN_PASSWORD = "banana"
questions_update_time = ''

app_main = Blueprint("main", __name__)


@app_main.route("/login", methods=["POST", "GET"])
def login():
    if request.method == "POST":
        username = request.form["un"]

        # TODO implement password

        if user := User.query.filter_by(name=username).first():
            session["score"] = user.score
            print("User:", username, "logged in")
            write_log(f"[User] {username}", "logged in")
        else: # Setting a new user
            user = User(username)
            db.session.add(user)
            db.session.commit()
            session["score"] = 0
            print("New user:", username, "logged in")
            write_log(f"[User] New user {username}", "logged in")

        login_user(user, remember=True)
        session["nickname"] = username
        flash("Login successful!", category='success')


        return redirect(request.args.get("next") or url_for("main.play"))

    else:
        if current_user.is_authenticated and "nickname" in session:
            flash("You already logged in!")
            return redirect(url_for("main.play"))

        return render_template("login.html")


@app_main.route("/")
@app_main.route("/play")
@login_required
def play():
    if "nickname" and "score" in session:
        global database_refreshed_by
        return render_template("play.html", 
                               username=session["nickname"], 
                               score=session["score"], 
                               database_time=questions_update_time, 
                               total_questions=len(questions.keys()),
                               database_refreshed_by=database_refreshed_by)
    else:
        flash("Please login")
        return redirect(url_for("main.login"))


# TODO implement effect when question database reload
@app_main.route("/questions", methods=["POST", "GET"])
@login_required
def _questions():
    if request.method == "POST":  # answer
        if "answer" in request.form:
            question_id, answer = request.form['answer'].split('#')

            correct_answer = check_for_answer(question_id)
            user_id = current_user.get_id()

            if is_right := correct_answer == int(answer):
                flash('Correct, you got 5 points!', category="success")

                rank = check_for_user_rank(user_id)
                points(user_id, 5)
                rank2 = check_for_user_rank(user_id)
                if rank2 < rank:
                    flash(f'You went up in the Scoreboard! Your position is now #{rank2}!', category="success")

                if user_id in answered_dict.keys():
                    answered_dict[user_id] += [int(question_id)]
                else:
                    answered_dict[user_id] = [int(question_id)]
            else: # wrong answer
                flash(f'Wrong!, you lost 3 points, the answer is ({correct_answer}) {questions[int(question_id)]["answers"][correct_answer-1]}', category='error')
                points(user_id, -3)

            print("User", session["nickname"], "answered", "right" if is_right else "wrong", "to question #" + question_id)

            return redirect(url_for("main._questions"))

        elif "refresh_questions_database" in request.form:
            finish, _,_ = create_random_question(current_user.get_id())
            if finish is not None:
                flash("You have to answer all questions before you can refreshing the questions database", category="error")
                return redirect(url_for("main._questions"))

            try:
                reload_questions()

                flash("Questions database have been refreshed!", category='success')
                print(f"User {session['nickname']} Refresh questions database")
                write_log(f"[User] {session['nickname']}", "refreshed questions database")

            except Exception as e:
                flash(e, category='error')
                flash(request.form["refresh_questions_database"], category='error')
                print('[ERROR]', e)
                write_log('[ERROR]', e)
                print(request.form["refresh_questions_database"])

            return redirect(url_for("main._questions"))

    else:  # render question
        question_id, question, answers = create_random_question(current_user.get_id())

        if question_id is None: # render no_questions.html
            global finish_list
            place = len(finish_list)
            
            if not place:
                global database_refreshed_by
                database_refreshed_by = session['nickname']

            if session["nickname"] not in finish_list:
                write_log(f"[User] {session['nickname']}", f"finish all the questions. (#{place})")

                finish_list += [session["nickname"]]
                place += 1

            flash(f"You are the {'first' if place==1 else '#'+str(place)} to complete all of the questions since last database was refresh! ({questions_update_time})", category="success")

            return render_template("no_questions.html", number=place, database_time=questions_update_time, finish_list=finish_list)

        user_id = current_user.get_id()
        if user_id not in answered_dict.keys():
            answered_dict[user_id] = []

        return render_template("questions.html", question_id=question_id, question=question, answers=answers,
                               answered=len(answered_dict[user_id]), total_questions=len(questions))


@app_main.route("/scoreboard")
def scoreboard():
    value = User.query.order_by(User.score.desc())#.limit(10)
    return render_template("scoreboard.html", values=value, user_id=-1 if not current_user.is_authenticated else int(current_user.get_id()))


@app_main.route("/logout")
def logout():
    if current_user and "nickname" in session:
        username = session["nickname"]
        flash(f"You have been logged out! {username}")
        print("User:", username, "logged out")
        write_log(f"[User] {username}", "logged out")
    else:
        flash("You are not logged in")

    # session.pop("user_id", None)
    session.pop("nickname", None)
    session.pop("score", None)
    session.pop("admin", None)
    # session.pop("return", None)

    logout_user()

    return redirect(url_for("main.login"))


def create_random_question(user_id):
    global answered_dict
    if user_id in answered_dict.keys():
        questions_asked = answered_dict[user_id]
    else:
        questions_asked = []
    questions_not_asked = [x for x in questions.keys() if x not in questions_asked]
    # questions_not_asked = map(lambda x: x, questions.keys())


    if len(questions_not_asked) == 0:  # No question remain
        return None, None, None
    question = random.choice(questions_not_asked)

    # in_question[username] = question # TODO implement anti exploit

    # proto_question = f'{question}#{questions[question]["question"]}#{"#".join(questions[question]["answers"])}'
    return question, questions[question]["question"], questions[question]["answers"]


def load_questions_from_web():
    r = requests.get("https://opentdb.com/api.php?amount=20&difficulty=easy&type=multiple")
    # r.text.replace("&#039;", "'").replace("&quot;", "'").replace("&amp;", "&")
    j = json.loads(r.text)
    for count, question in enumerate(j['results'], 1):
        answers = question['incorrect_answers'] + [question['correct_answer']]
        random.shuffle(answers)
        fixed_replaced_question = question["question"].replace("&#039;", "'").replace("&quot;", "'").replace("&amp;", "&")
        fixed_replaced_answers = [answer.replace("&#039;", "'").replace("&quot;", "'").replace("&amp;", "&") for answer in answers]

        if fixed_replaced_question.find('#') != -1 or fixed_replaced_question.find('|' or answers.find("#") != -1 or answers.find("|" != -1)) != -1:
            print('passing question occurred when loading questions from web\nloop #', count)
        else:
            questions[count] = {
                "question": html.unescape(fixed_replaced_question),
                "answers": html.unescape(fixed_replaced_answers),
                "correct": answers.index(question['correct_answer']) + 1}

    global questions_update_time
    questions_update_time = time.strftime('%d/%m/%y %H:%M')


def check_for_answer(question_id):
    try:
        correct_answer = questions[int(question_id)]['correct']
    except Exception as e:
        correct_answer = 0
        print(e)
        write_log("[EXCEPTION]", e)
        print('[EXCEPTION] correct_answer = 0')

    return correct_answer


def points(user_id, points):
    found_user = User.query.filter_by(id=user_id).first()
    found_user.score += points
    db.session.commit()

    if "score" in session:
        session["score"] = found_user.score


def check_for_user_rank(user_id):
    values = User.query.order_by(User.score.desc())

    for count, value in enumerate(values, 1):
        if value.id == int(user_id):
            return count

    # query = User.query.func.rank().over(order_by=User.score.desc()).label('rank')
    # print(query)

    return -1


def reload_questions():
    load_questions_from_web()

    global database_refreshed_by
    database_refreshed_by = 'Admin'

    answered_dict.clear()
    finish_list.clear()


def write_log(prefix, bfr):
    with open('logs.log', 'a') as log:
        log.write(f'{time.strftime("%d/%m/%y %H:%M")} {prefix} {bfr}\n')


# TODO implement request method
# @app_main.route('/request-test', method=['POST'])
# def request_test():
#     test = json.loads(request.data)
#     testArg = test['arg']
#
#     return jsonify({})
