import os
from pickle import GET
from unicodedata import category
from flask import Flask, request, abort, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import random

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

    @app.route('/categories', methods=['GET'])
    def get_categories():
        categories = Category.query.order_by(Category.id).all()
        if categories is None:
            abort(404)
        return jsonify({
            "success": True,
            "categories": [category.format() for category in categories],
            "total_categories": len(categories)
        })

    @app.route('/questions', methods=['GET'])
    def get_question():
        myQuestion = Question.query.all()
        current_questions = paginate_questions(request, myQuestion)
        if not current_questions:
            abort(404)
        return jsonify({
            'success': True,
            'question': current_questions,
            'totalQuestions': len(Question.query.all())
        })

    @app.route('/questions/<int:question_id>',  methods=['DELETE'])
    def delete_question(question_id):
        questionToDelete = Question.query.get(question_id)
        if not questionToDelete:
            abort(404)
        questionToDelete.delete()
        return jsonify({
            "success": True,
            "deleted": question_id
        })

    @app.route('/categories/<int:category_id>/questions',  methods=['GET'])
    def get_questionsByCategory(category_id):
        selection = Question.query.filter(
            Question.category == category_id).all()
        current_questions = paginate_questions(request, selection)
        if selection is None:
            abort(404)
        else:
            return jsonify({
                'success': True,
                'questions': current_questions,
                'total_questions': len(selection)
            })

    @app.route('/questions/search', methods=['POST'])
    def search_questions():
        searchQuestion = request.get_json()
        if searchQuestion is None or searchQuestion['search_term'] is None:
            abort(400)
        search_term = searchQuestion.get('search_term')
        results = Question.query.filter(
            Question.question.ilike(f'%{search_term}%')).all()
        if len(results) == 0:
            abort(404)
        search_questions = get_question(request, results)
        return jsonify({
            'success': True,
            'questions': search_questions,
            'data': len(results)
        })

    @app.route('/question', methods=['POST'])
    def create_question():
        body = request.get_json()

        if not('question' in body and 'answer' in body and 'difficulty' in body):
            abort(422)
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

    @app.route('/quizzes', methods=['POST'])
    def create_quiz():
        try:
            body = request.get_json()

            if not ('quiz_category' in body and 'previous_questions' in body):
                abort(422)

            category = body.get('quiz_category')
            previous_questions = body.get('previous_questions')

            if category['type'] == 'click':
                available_questions = Question.query.filter(
                    Question.id.notin_((previous_questions))).all()
            else:
                available_questions = Question.query.filter_by(
                    category=category['id']).filter(Question.id.notin_((previous_questions))).all()

                quiz_question = available_questions[random.randrange(
                    0, len(available_questions))].format() if len(available_questions) > 0 else None

            return jsonify({
                'success': True,
                'question': quiz_question
            })
        except:
            abort(422)

        @app.errorhandler(422)
        def unprocessable(error):
            return jsonify({
                "success": False,
                "error": 422,
                "message": "unable to Process"
            }), 422

        @app.errorhandler(400)
        def bad_request(error):
            return jsonify({
                "success": False,
                "error": 400,
                "message": "try again!!! bad Request"
            }), 400

        @app.errorhandler(500)
        def internal_error(error):
            return jsonify({
                "success": False,
                "error": 500,
                "message": "Internal Server error"
            }), 500

    return app
