from models.models import db, Question, StudentAnswer, QuestionKeyword
from flask import Flask
from config.config import Config

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = Config.SQLALCHEMY_DATABASE_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

with app.app_context():
    print("清空 student_answers ...")
    db.session.query(StudentAnswer).delete()
    print("清空 question_keywords ...")
    db.session.query(QuestionKeyword).delete()
    print("清空 questions ...")
    db.session.query(Question).delete()
    db.session.commit()
    print("题目及相关依赖表已清空！") 