from flask import Blueprint, redirect, url_for, render_template, request, session, flash
from website.models import User
from . import db
from .main import reload_questions, finish_list#, write_log
from flask_login import current_user, login_required

ADMIN_PASSWORD = "banana"

app_admin = Blueprint("admin", __name__)


@app_admin.route("/admin", methods=["POST", "GET"])
@login_required
def admin():
    if request.method == "POST":
        if "password" in request.form:
            password = request.form["password"]
            if password == ADMIN_PASSWORD:
                if "nickname" not in session:
                    flash("You have to login first", category='error')
                    return redirect(url_for("admin.admin"))

                session["admin"] = str(current_user)
                print("[ADMIN]", "User", session["nickname"], "have been logged to Admin")

                return load_admin_page()

            else:
                flash("Wrong password", category='error')
                return redirect(url_for("admin.admin"))

        elif "admin" not in session:
            flash("You are not logged in to Admin.", category='error')
            return redirect(url_for("admin.admin"))

        elif "delete" in request.form:
            try:
                user_id = User.query.filter_by(id=request.form["delete"]).first()
                db.session.delete(user_id)
                db.session.commit()
                flash(f"User {user_id.name!r} have been deleted by {session['nickname']}", category='success')
                print(f"[ADMIN] {session['nickname']} deleted user {user_id.name!r}")
            except Exception as e:
                flash(e, category='error')
                flash(request.form["delete"], category='error')
                print('[ERROR]', e)
                print(request.form["delete"])

            return load_admin_page()

        elif "edit_score" in request.form:
            try:
                given_id, score = request.form["edit_score"].split("#")
                if not score.isdigit():
                    raise Exception('The score have to be a number')

                user_id = User.query.filter_by(id=given_id).first()
                user_id.score = score
                db.session.commit()

                flash(f"User {user_id.name!r} score have been set to {score}", category='success')
                print(f"[ADMIN] {session['nickname']!r} edited {user_id.name!r} score to {score}")

            except Exception as e:
                flash(e, category='error')
                flash(request.form["edit_score"], category='error')
                print('[ERROR]', e)
                print(request.form["edit_score"])

            return load_admin_page()

        elif "edit_name" in request.form:
            try:
                given_id, name = request.form["edit_name"].split("#")

                duplicate_user = User.query.filter_by(name=name).first()
                if duplicate_user:
                    flash("This Nickname have already taken by another user.", category='error')

                else:
                    user_id = User.query.filter_by(id=given_id).first()
                    old_name = user_id.name
                    user_id.name = name
                    db.session.commit()

                    flash(f"Username {old_name!r} have been changed to {name!r}", category='success')
                    print(f"[ADMIN] {session['nickname']} edit User {old_name} name to {name}")

            except Exception as e:
                flash(e, category='error')
                flash(request.form["edit_name"], category='error')
                print('[ERROR]', e)
                print(request.form["edit_name"])

            return load_admin_page()

        elif "refresh_questions_database" in request.form:
            try:
                reload_questions(f"Admin: {session['nickname']}")

                flash("Questions database have been refreshed!", category='success')
                print(f"[ADMIN] {session['nickname']} Refresh questions database")

            except Exception as e:
                flash(e, category='error')
                flash(request.form["refresh_questions_database"], category='error')
                print('[ERROR]', e)
                print(request.form["refresh_questions_database"])

            return load_admin_page()

        elif "query" in request.form:
            query = request.form["query"]
            try:
                result = db.engine.execute(query)
            except Exception as e:
                result = e

            flash(result)
            return load_admin_page()

    else: # GET method
        if "admin" in session:
            return load_admin_page()

        else:
            flash("The password is absolutely not a " + ADMIN_PASSWORD)
            return render_template("admin.html")



def load_admin_page():
    # global finish_list
    values = User.query.all()
    return render_template("admin_users.html", values=values, finish_list=finish_list)


@app_admin.route("/admin_logout")
@login_required
def admin_logout():
    flash(f'You have been logged out from Admin! {session["nickname"]}')
    session.pop("admin", None)
    return redirect(url_for("main.play"))
