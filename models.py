#  models on Capstone

from datetime import datetime

from flask_bcrypt import Bcrypt
from flask_sqlalchemy import SQLAlchemy

bcrypt = Bcrypt()
db = SQLAlchemy()


class User(db.Model):
  

    __tablename__ = 'users'

    id = db.Column(
        db.Integer,
        primary_key=True,
    )

    email = db.Column(
        db.Text,
        nullable=False,
        unique=True,
    )

    username = db.Column(
        db.Text,
        nullable=False,
        unique=True,
    )

    image_url = db.Column(
        db.Text,
        default="https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQUDAr2Zy9ZAs8KhMkc91DlHzoqFuLfXaZ1wFL9Iqr2k7iEfL0U6r8mG3i48HBecICyiDE&usqp=CAU",
    )

    header_image_url = db.Column(
        db.Text,
        default="https://new.mospolytech.ru/upload/iblock/f7d/student-privacy4.jpg"
    )

    password = db.Column(
        db.Text,
        nullable=False,
    )


    def __repr__(self):
        return f"<User #{self.id}: {self.username}, {self.email}>"


    @classmethod
    def signup(cls, username, email, password, image_url):


        hashed_pwd = bcrypt.generate_password_hash(password).decode('UTF-8')

        user = User(
            username=username,
            email=email,
            password=hashed_pwd,
            image_url=image_url,
        )

        db.session.add(user)
        return user

    @classmethod
    def authenticate(cls, username, password):


        user = cls.query.filter_by(username=username).first()

        if user:
            is_auth = bcrypt.check_password_hash(user.password, password)
            if is_auth:
                return user

        return False


class Progress(db.Model):

    __tablename__ = 'progress'

    id = db.Column(
        db.Integer,
        primary_key=True,
    )
    user_id = db.Column(
        db.Integer,
        db.ForeignKey('users.id', ondelete='CASCADE'),
        nullable=False,
    )

    quiz_score = db.Column(
        db.Integer,
        nullable=True,
        
    )

    is_grammar_book_completed = db.Column(
        db.Boolean,
        nullable=True,
    )

    is_story_book_completed = db.Column(
        db.Boolean,
        nullable=True,
    )

    is_video_completed = db.Column(
        db.Boolean,
        nullable=True,
    )


    

def connect_db(app):

    db.app = app
    db.init_app(app)
