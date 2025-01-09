from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap5
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String, Float
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, FloatField
from wtforms.validators import DataRequired
import requests



app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///movies_table.db"
Bootstrap5(app)
# token has been changed
token_bearer = "eyJhbGciOiJIUzI1NiJ9.eyJhdWQiOiI2OTNkZWI0YTEzYmUwYWQwYjdjODBmNzZmODAwNjdmNiIsIm5iZiI6MTczNjMyMTk3Ni4zMDksInN1YiI6IjY3N2UyYmI4ZjJjNjIxODA3ZGJiMDRkOCIsInNjb3BlcyI6WyJhcGlfcmVhZCJdLCJ2ZXJzaW9uIjoxfQ.cHNq0jVqqqLIHHWvbVROilmj6p7Fw4uBI3CqsjWLpvw"

# CREATE DB


class Base(DeclarativeBase):
    pass


db = SQLAlchemy(model_class=Base)
db.init_app(app)


class Movie(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(100), unique=True)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    description: Mapped[str] = mapped_column(String(250), nullable=False)
    rating: Mapped[int] = mapped_column(Float, nullable=True)
    ranking: Mapped[int] = mapped_column(Integer, nullable=True)
    review: Mapped[str] = mapped_column(String(250), nullable=True)
    img_url: Mapped[str] = mapped_column(String(250), nullable=False)


class AddMovieForm(FlaskForm):
    title = StringField("Title", validators=[DataRequired()])
    submit = SubmitField("Add Movie")


class EditForm(FlaskForm):
    rating = FloatField("Your rating out of 10 e.g 7.5", validators=[DataRequired()])
    review = StringField("Review", validators=[DataRequired()])
    submit = SubmitField("Ok")


# CREATE TABLE
with app.app_context():
    db.create_all()


@app.route("/")
def home():
    data = db.session.execute(db.select(Movie).order_by(Movie.rating)).scalars().all()
    for i in range(len(data)):
        data[i].ranking = len(data) - i
    db.session.commit()

    return render_template("index.html", movies=data)


@app.route("/add", methods=["GET", "POST"])
def add_movie():
    form = AddMovieForm()
    movie_url = 'https://image.tmdb.org/t/p/w500/'
    movie_name = request.form.get('title')
    url = f"https://api.themoviedb.org/3/search/movie?query={movie_name}&include_adult=false&language=en-US&page=1"
    headers = {
        "accept": "application/json",
        "Authorization": f"Bearer {token_bearer}"
    }
    if request.method == "POST":
        response = requests.get(url, headers=headers)
        data = response.json()
        return render_template("select.html", data=data)
    movie_id = request.args.get('api_id')
    if movie_id:
        print(f'movie id: {movie_id}')
        url_2 = f'https://api.themoviedb.org/3/movie/{movie_id}'
        response = requests.get(url_2, headers=headers)
        data_final = response.json()
        new_movie = Movie(
            title=data_final['original_title'],
            year=data_final['release_date'][:4],
            description=data_final['overview'],
            img_url=f"{movie_url}/{data_final['poster_path']}"
        )
        db.session.add(new_movie)
        db.session.commit()
        return redirect(url_for('home'))
    return render_template("add.html", form=form)


@app.route("/edit/<int:movie_id>", methods=["GET", "POST"])
def edit_movie(movie_id):
    edit = EditForm()
    if request.method == "POST":
        movie = db.get_or_404(Movie, movie_id)
        movie.rating = request.form.get('rating')
        movie.review = request.form.get('review')
        db.session.commit()
        return redirect(url_for('home'))

    return render_template("edit.html", form=edit)


@app.route("/delete/<int:movie_id>", methods=['GET', 'POST'])
def delete_movie(movie_id):
    movie = db.get_or_404(Movie, movie_id)
    db.session.delete(movie)
    db.session.commit()
    return redirect(url_for('home'))


if __name__ == '__main__':
    app.run(debug=True)
