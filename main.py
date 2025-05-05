from flask import Flask, render_template, redirect, url_for, request, send_file
from flask_bootstrap import Bootstrap5
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String
from flask_wtf import FlaskForm
from wtforms import StringField
from wtforms.validators import DataRequired
import sqlite3
import os

# create 'add' form
class AddToDo(FlaskForm):
    todo =StringField("Write your To-Do:", validators=[DataRequired()])


# implement flask app
app = Flask(__name__, instance_relative_config=True)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
Bootstrap5(app)

# create database
class Base(DeclarativeBase):
    pass

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///todos.db"
db = SQLAlchemy(model_class=Base)
db.init_app(app)

# create table
class Todos(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    todo: Mapped[str] = mapped_column(String(250), nullable=False)

with app.app_context():
    db.create_all()

@app.route("/", methods=['GET','POST'])
def home():
    # add new task
    add_form = AddToDo()
    if add_form.validate_on_submit():
        new_todo = Todos(
            todo = add_form.todo.data
        )
        db.session.add(new_todo)
        db.session.commit()
        return redirect(url_for('home'))

    #show all todos in descending order by ids
    result = db.session.execute(db.select(Todos).order_by(Todos.id.desc()))
    all_todos = result.scalars().all()

    #delete post
    if request.method == 'POST':
        # returns list of ids
        selected_options = request.form.getlist('options')
        print(f"Selected options: {selected_options}")
        for id in selected_options:
            delete_todo = db.get_or_404(Todos, int(id))
            db.session.delete(delete_todo)
            db.session.commit()
        return redirect(url_for('home'))
        
    return render_template("index.html", add_form=add_form, todos=all_todos)

#saves data in a txt file
@app.route('/save')
def save_data():
    db_path = os.path.join(app.instance_path, 'todos.db')
    txt_path = os.path.join(app.instance_path, 'todoList.txt')

    if not os.path.exists(db_path):
        return "Database file not found.", 404

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()

        with open(txt_path, 'w') as file:
            for table_name in tables:
                table = table_name[0]
                file.write(f"--- Table: {table} ---\n")

                cursor.execute(f"SELECT * FROM {table}")
                rows = cursor.fetchall()
                for row in rows:
                    file.write(f"{row}\n")

        conn.close()

        # Send the file as a download
        return send_file(txt_path, as_attachment=True)

    except Exception as e:
        return f"Error: {e}", 500



if __name__ == '__main__':
    app.run(debug=True)