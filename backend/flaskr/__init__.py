import os
from pickle import GET
from unicodedata import category
from flask import Flask, request, abort, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import random
from flask_sqlalchemy  import func

from models import setup_db, Question, Category

QUESTIONS_PER_PAGE = 10


def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__)
    setup_db(app)
    CORS(app)

    cors = CORS(app, resources={r"/*": {"origins": "*"}})

    @app.after_request
    def after_request(response):
        response.headers.add('Access-Control-Allow-Headers',
                             'Content-Type, Authorization')
        response.headers.add('Access-Control-Allow-Headers',
                             'GET, POST, PATCH, DELETE, OPTIONS')
        return response

    def paginate_questions(request, selection):
        page = request.args.get("page", 1, type=int)
        start = (page - 1) * QUESTIONS_PER_PAGE
        end = start + QUESTIONS_PER_PAGE

        questions = [question.format() for question in selection]
        current_questions = questions[start:end]

        return current_questions
    
    def get_next_page(page, request, paginate):
        if paginate < page:
            nextpage = request.args.get('page', 1, type=int) + 1
            return str(request.url_root + 'questions?page=') + str(nextpage)
        else:
            return str(request.url_root + 'questions?page=1')

    @app.route('/categories', methods=['GET'])
    def get_categories():
        categories = Category.query.order_by(Category.id).all()
        if categories is None:
            abort(404)
        return jsonify({
            "success": True,
            "categories": {category.id:category.type for category in categories},
            "total_categories": len(categories)
        })

    @app.route('/questions', methods=['GET'])
    def get_question():
        try:
            myQuestion = Question.query.all()
            current_questions = paginate_questions(request, myQuestion)
            
            paginate = len(current_questions) % QUESTIONS_PER_PAGE
            next_page = get_next_page(len(current_questions), request, paginate)
            if not current_questions:
                abort(404)
                
            return jsonify({
                'success': True,
                'question': current_questions,
                'totalQuestions': len(Question.query.all()),
                'next_page': next_page
            })
        except:
            abort(422)

    @app.route('/questions/<int:question_id>',  methods=['DELETE'])
    def delete_question(question_id):
        try:
            questionToDelete = Question.query.get(question_id)
            if not questionToDelete:
                abort(404)
            questionToDelete.delete()
            return jsonify({
                "success": True,
                "deleted": question_id
            })
        except:
            abort(422)

    @app.route('/categories/<int:category_id>/questions',  methods=['GET'])
    def get_questionsByCategory(category_id):
        try:
            selection = Question.query.filter(Question.category == category_id).all()
            current_questions = paginate_questions(request, selection)
            if selection is None:
                abort(404)
            else:
                return jsonify({
                    'success': True,
                    'questions': current_questions,
                    'total_questions': len(selection)
                })
        except:
            abort(422)

    @app.route('/questions/search', methods=['POST'])
    def search_questions():
        search_term = request.args.get("search", None)
        if search_term:
                results = Question.query.order_by(Question.id).filter(
                Question.question.ilike("%{}%".format(search_term))
                )
                searched_items = [search.format() for search in results]
                return jsonify(
                    {
                        "success": True,
                        "questions": searched_items,
                        "total_searched_items" : len(searched_items),
                        "searched_term" : search_term,
                    }
                )
        else:
            abort(422)

    @app.route('/questions', methods=['POST'])
    def create_question():
        body = request.get_json(Question)
        try:
            new_question = body.get('question', None)
            new_answer = body.get('answer', None)
            new_difficulty = body.get('difficulty', None)
            new_category = body.get('category', None)

            addQuestion = Question(question=new_question, answer=new_answer,
                                difficulty=new_difficulty, category=new_category)
            addQuestion.insert()
            selection = Question.query.order_by(Question.id).all()
            current_question = paginate_questions(request, selection)

            return jsonify({
                'success': True,
                'questions': current_question,
                'total_questions': len(Question.query.all())
            })
        except:
            abort(422)


    @app.route('/quizzes', methods=['POST'])
    def create_quiz():
     body = request.get_json()

     if body is None or body['previous_questions'] is None or body['category'] is None:
      abort(400)

    try:
      previous_questions = Question.get('previous_questions')
      category = Question.get('category')

      if category == 0:
        questions = Question.query.order_by(func.random())
      else:
        questions = Question.query.filter(Question.category==category).order_by(func.random())

        question = questions.filter(Question.id.notin_(previous_questions)).first()

      if question is None:
        return jsonify({
          'success': True
        })

      return jsonify({
        'success': True,
        'question': question.format()
      })
    except:
      abort(422)




    @app.errorhandler(422)
    def unprocessable(error):
        return jsonify({
            "success": False,
            "error": 422,
            "message": "unprocessable"
        }), 422

    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({
            "success": False,
            "error": 400,
            "message": "bad Request"
        }), 400

    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({
            "success": False,
            "error": 500,
            "message": "Internal Server error"
        }), 500

    return app
