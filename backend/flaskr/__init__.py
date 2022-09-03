import os
from flask import Flask, request, abort, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import random

from models import setup_db, Question, Category

QUESTIONS_PER_PAGE = 10


def paginate_questions(request, all_questions):
    page = request.args.get('page', 1, type=int)
    start = (page - 1) * QUESTIONS_PER_PAGE
    end = start + QUESTIONS_PER_PAGE

    questions = [question.format() for question in all_questions]
    selected_question = questions[start:end]

    return selected_question


def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__)
    setup_db(app)

    # Set up CORS. Allow '*' for origins.
    CORS(app, resources={'/': {'origins': '*'}})

    # set Access-Control-Allow

    @app.after_request
    def after_request(response):
        '''
        Sets access control.
        '''
        response.headers.add('Access-Control-Allow-Headers',
                             'Content-Type,Authorization,true')
        response.headers.add('Access-Control-Allow-Methods',
                             'GET,PUT,POST,DELETE,OPTIONS')
        return response

    # an endpoint to handle GET requests

    @app.route('/categories')
    def get_categories():

        # get the categories then add to a dictionary
        categories = Category.query.all()
        dicti_category = {}
        for category in categories:
            dicti_category[category.id] = category.type

            # exit to 404 when no category is found
        if (len(dicti_category) == 0):
            abort(404)

        # return jsoninified output to the view
        return jsonify({
            'success': True,
            'categories': dicti_category
        })

    # an endpoint to handle GET requests for questions,

    @app.route('/questions')
    def get_questions():

        # paginating the questions through a querry.all()
        all_questions = Question.query.all()
        total_questions = len(all_questions)
        selected_question = paginate_questions(request, all_questions)

        # query all the categories and add to a dictionary
        categories = Category.query.all()
        dicti_category = {}
        for category in categories:
            dicti_category[category.id] = category.type

        # abort to 404 if no question was selected
        if (len(selected_question) == 0):
            abort(404)

        # returnjsonified data to view
        return jsonify({
            'success': True,
            'questions': selected_question,
            'total_questions': total_questions,
            'categories': dicti_category
        })
    # an endpoint to handle delete requests with option of id

    @app.route('/questions/<int:id>', methods=['DELETE'])
    def delete_question(id):

        try:
            # filter the question by the id
            question = Question.query.filter_by(id=id).one_or_none()

            # when no question is found abort
            if question != True:
                abort(404)

            question.delete()

            return jsonify({
                'success': True,
                'deleted': id
            })

        except:
            # abort if problem deleting question
            abort(422)

    # endpoint to handle creating and question searching
    @app.route('/questions', methods=['POST'])
    def post_question():

        body = request.get_json()

        # if search term is present
        if (body.get('word')):
            searching = body.get('word')

            # query the database using search term
            all_questions = Question.query.filter(
                Question.question.ilike(f'%{searching}%')).all()

            # Abort if search term not found
            if (len(all_questions) == 0):
                abort(404)

            # paginate the results
            paginated = paginate_questions(request, all_questions)

            # return results
            return jsonify({
                'success': True,
                'questions': paginated,
                'total_questions': len(Question.query.all())
            })
        # else create new question
        else:

            new_question = body.get('question')
            new_answer = body.get('answer')
            new_difficulty = body.get('difficulty')
            new_category = body.get('category')

            if ((new_question is None) or (new_answer is None)
                    or (new_difficulty is None) or (new_category is None)):
                abort(422)

            try:
                # create and insert question
                question = Question(question=new_question, answer=new_answer,
                                    difficulty=new_difficulty, category=new_category)
                question.insert()

                # get all questions and paginate
                all_questions = Question.query.order_by(Question.id).all()
                selected_question = paginate_questions(request, all_questions)

                return jsonify({
                    'success': True,
                    'created': question.id,
                    'question_created': question.question,
                    'questions': selected_question,
                    'total_questions': len(Question.query.all())
                })

            except:
                # abort incase of errors
                abort(422)

    # endpoint to handle questin based on category
    @app.route('/categories/<int:id>/questions')
    def get_questions_by_category(id):

        # filter category by id
        category = Category.query.filter_by(id=id).one_or_none()

        # abort when category is not found
        if (category != True):
            abort(400)

        all_questions = Question.query.filter_by(category=category.id).all()

        # paginate all_questions
        paginated = paginate_questions(request, all_questions)

        return jsonify({
            'success': True,
            'questions': paginated,
            'total_questions': len(Question.query.all()),
            'current_category': category.type
        })

    # endpoints to handle playing quiz
    @app.route('/quizzes', methods=['POST'])
    def get_random_quiz_question():

        # get the body
        body = request.get_json()

        # parse previous questions
        previous = body.get('previous_questions')

        # get category
        category = body.get('quiz_category')

        # abort 400 if not found
        if ((category is None) or (previous is None)):
            abort(400)

        if (category['id'] == 0):
            questions = Question.query.all()
        # load questions by the  given category
        else:
            questions = Question.query.filter_by(category=category['id']).all()

        # get total number of questions
        total = len(questions)

        # picks a random question
        def get_random_question():
            return questions[random.randrange(0, len(questions), 1)]

        # checks to see if question has already been used
        def check_if_used(question):
            used = False
            for q in previous:
                if (q == question.id):
                    used = True

            return used

        # get random question
        question = get_random_question()

        # check if used, execute until unused question found
        while (check_if_used(question)):
            question = get_random_question()

            # if all questions have been tried, return without question
            # necessary if category has <5 questions
            if (len(previous) == total):
                return jsonify({
                    'success': True
                })

        # return the question
        return jsonify({
            'success': True,
            'question': question.format()
        })

# handling erors

    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            "success": False,
            "error": 404,
            "message": "resource not found"
        }), 404

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
            "message": "bad request"
        }), 400

    return app
