"""Utility file to seed database with data from api and through webscraping"""

from model import User, Recipe, Website, Serving, Ingredient, USMeasurement, MetricMeasurement, USAmount, MetricAmount, Instruction, Course, RecipeIngredient, IngredientType, RecipeServing, USIngredientMeasure, MetricIngredientMeasure, RecipeCourse

from model import connect_to_db, db
from server import app
from webscrape_details import get_all_recipe_info
import unirest
import os
import re


def load_users(username, password):
    """Load sample users."""

    print "Users"

    user = User(username=username,
                password=password)

    db.session.add(user)
    db.session.commit()


def load_website(site_name):
    """Load website name."""

    print "Websites"

    # if the website does not already exist in database, add to database
    if not Website.query.filter_by(site_name=site_name).all():
        website = Website(site_name=site_name)

        db.session.add(website)

    db.session.commit()


def load_courses(courses):
    """Load course(s) for the recipe."""

    print "Course(s)"

    for course_name in courses:
        # if the course does not already exist in database, add to database
        if not Course.query.filter_by(course_name=course_name).all():
            course = Course(course_name=course_name)

            db.session.add(course)

    db.session.commit()


def load_servings(servings):
    """Load serving size(s) for the recipe."""

    print "Serving(s)"

    if not Serving.query.filter_by(serving_size=servings).all():
        serving = Serving(serving_size=servings)

        db.session.add(serving)

    db.session.commit()


def load_ingredienttypes(all_ingredients):
    """Load ingredient types for the recipe."""

    print "Ingredient Type(s)"

    for ingredient in all_ingredients:
        type_name = ingredient['aisle']

        if not IngredientType.query.filter_by(type_name=type_name).all():
            ingredienttype = IngredientType(type_name=type_name)

            db.session.add(ingredienttype)

    db.session.commit()


def load_ingredients(all_ingredients):
    """Load ingredients for the recipe."""

    print "Ingredient(s)"

    for ingredient in all_ingredients:
        ingredient_name = ingredient['name']
        type_name = ingredient['aisle']

        if not Ingredient.query.filter_by(ingredient_name=ingredient_name).all():
            type_id = IngredientType.query.filter_by(type_name=type_name).first().type_id
            ingredient = Ingredient(ingredient_name=ingredient_name, type_id=type_id)

            db.session.add(ingredient)

    db.session.commit()


def load_measurements(scrape_ingredients):
    """Load measurement units and amounts for the recipe."""

    print "Measurements and Amounts"

    for i in range(len(scrape_ingredients)):
        ingredient = scrape_ingredients[i]
        if ingredient.get('metrics_measures'):
            metric_unit = ingredient['metrics_measures']['metric_unit']
            # check if the metric unit already exists in database
            if not MetricMeasurement.query.filter_by(metric_unit=metric_unit).all():
                metricmeasure = MetricMeasurement(metric_unit=metric_unit)
                db.session.add(metricmeasure)
            for num in ingredient['metrics_measures']['metric_amount']:
                # check if the metric amount already exists in database
                if not MetricAmount.query.filter_by(metric_amount=num).all():
                    metricamount = MetricAmount(metric_amount=num)
                    db.session.add(metricamount)

        if ingredient.get('us_measures'):
            measure = ingredient['us_measures']
            if measure.get('us_unit'):
                us_unit = measure['us_unit']
                # check if us unit already exists in database
                if not USMeasurement.query.filter_by(us_unit=us_unit).all():
                    usmeasure = USMeasurement(us_unit=us_unit)
                    db.session.add(usmeasure)
            if measure.get('us_amount'):
                for num in measure['us_amount']:
                    # to check if the us amount already exists in databse
                    if not USAmount.query.filter_by(us_amount=num).all():
                       # to check if the amount is a fraction
                        if '/' in num:
                            # to check if it is a mixed fraction
                            if len(num.split()) > 1:
                                whole_number = int(num.split()[0])
                                fraction_numbers = num.split()[1].split('/')
                                us_decimal = float(whole_number) + (float(int(fraction_numbers[0])) / float(int(fraction_numbers[1])))
                            else:
                                fraction_numbers = num.split('/')
                                us_decimal = float(int(fraction_numbers[0])) / float(int(fraction_numbers[1]))
                        # amount is a whole number
                        else:
                            us_decimal = float(int(num))

                        usamount = USAmount(us_amount=num, us_decimal=us_decimal)
                        db.session.add(usamount)

    db.session.commit()


def load_recipes(recipe_name, recipe_api_id, time_in_min, site_name, src_url, img_url):
    """Load recipes into database."""

    print "Recipe"

    if not Recipe.query.filter_by(recipe_name=recipe_name).all():
        site_id = Website.query.filter_by(site_name=site_name).first().site_id

        recipe = Recipe(recipe_name=recipe_name,
                        time_in_min=time_in_min,
                        recipe_api_id=recipe_api_id,
                        src_url=src_url,
                        img_url=img_url,
                        site_id=site_id)

        db.session.add(recipe)

    db.session.commit()


def load_recipe_ingredients(recipe_name, all_ingredients, scrape_ingredients):
    """Load recipeingredients into database."""

    print "Recipe Ingredients"

    recipe_id = Recipe.query.filter_by(recipe_name=recipe_name).first().recipe_id

    for i in range(len(scrape_ingredients)):
        original_string = scrape_ingredients[i]['stripped_ingredient']
        ingredient_id = None
        ingredient_ids = []
        for ingredient in all_ingredients:
            name = ingredient['name']
            name_words = name.split()

            # to make sure the original string from webscrape
            # matches the correct ingredient name received from the api
            if len(name_words) > 1:
                if name_words[-1] in original_string and name_words[-2] in original_string:
                    ingredient_id = Ingredient.query.filter_by(ingredient_name=name).first().ingredient_id
                    ingredient_ids.append(ingredient_id)
            elif len(name_words) == 1:
                if name in original_string:
                    ingredient_id = Ingredient.query.filter_by(ingredient_name=name).first().ingredient_id
                    ingredient_ids.append(ingredient_id)

        new_ingredient = None
        if not ingredient_ids:
            new_string = original_string
            if re.search(r'\(.*\)', new_string):
                new_string = ''.join(filter(None, re.split(r'\(.*\)', new_string)))
            if re.search(r'[A-Za-z]+ed', new_string):
                new_string = ''.join(filter(None, re.split(r'[A-Za-z]+ed', new_string)))
            if re.search(r'\,.*', new_string):
                new_string = ''.join(filter(None, re.split(r'\,.*', new_string)))
            new_string = new_string.split()
            for i in range(len(new_string)):
                new_string[i] = new_string[i].strip()
            new_string = ' '.join(new_string)
            if not Ingredient.query.filter_by(ingredient_name=new_string).all():
                new_ingredient = Ingredient(ingredient_name=new_string)
                db.session.add(new_ingredient)

        if not ingredient_id:
            ingredient_id = Ingredient.query.filter_by(ingredient_name=new_string).first().ingredient_id
        # to make sure the same ingredient is not added to the same
        # recipe multiple times
        if not RecipeIngredient.query.filter_by(original_string=original_string).all():
            if scrape_ingredients[i].get('link'):
                link = scrape_ingredients[i]['link']
                recipeingredient = RecipeIngredient(original_string=original_string,
                                                    recipe_id=recipe_id,
                                                    ingredient_id=ingredient_id,
                                                    link=link)
            else:
                recipeingredient = RecipeIngredient(original_string=original_string, recipe_id=recipe_id, ingredient_id=ingredient_id)
            db.session.add(recipeingredient)

    db.session.commit()


def load_instructions(recipe_name, instruction_info):
    """Load instructions for the recipe."""

    print "Instruction(s)"

    for instruction in instruction_info:
        step_instruction = instruction['step']
        step_order = instruction['number']
        recipe_id = Recipe.query.filter_by(recipe_name=recipe_name).first().recipe_id

        step = Instruction(step_order=step_order,
                           step_instruction=step_instruction,
                           recipe_id=recipe_id)

        db.session.add(step)

    db.session.commit()


def load_ingredient_measures(scrape_ingredients, all_ingredients, recipe_name):
    """Load ingredientmeasures for recipe."""

    print "Ingredients Measurements"

    for i in range(len(scrape_ingredients)):
        original_string = scrape_ingredients[i]['stripped_ingredient']
        recipeingredient_id = RecipeIngredient.query.filter_by(original_string=original_string).first().recipeingredient_id

        # to make sure string and ingredient matches
        for ingredient in all_ingredients:
            if ingredient['name'] in original_string:
                ingredient_name = ingredient['name']

        if scrape_ingredients[i].get('metrics_measures'):
            metric_measure_id = MetricMeasurement.query.filter_by(metric_unit=scrape_ingredients[i]['metrics_measures']['metric_unit']).first().metric_measure_id
            # for when only 1 value in metric amount list
            metric_amount_id = MetricAmount.query.filter_by(metric_amount=scrape_ingredients[i]['metrics_measures']['metric_amount'][0]).first().metric_amount_id
            # add to database
            metric = MetricIngredientMeasure(recipeingredient_id=recipeingredient_id,
                                             metric_measure_id=metric_measure_id,
                                             metric_amount_id=metric_amount_id)
            db.session.add(metric)

            if len(scrape_ingredients[i]['metrics_measures']['metric_amount']) > 1:
                metric_amount_id2 = MetricAmount.query.filter_by(metric_amount=scrape_ingredients[i]['metrics_measures']['metric_amount'][1]).first().metric_amount_id
                # add to database
                metric2 = MetricIngredientMeasure(recipeingredient_id=recipeingredient_id,
                                          metric_measure_id=metric_measure_id,
                                          metric_amount_id=metric_amount_id2)
                db.session.add(metric2)

        if scrape_ingredients[i].get('us_measures'):
            # starting values for variables
            us_measure_id = None
            us_amount_id = None
            us_amount_id2 = None

            # find real values for variables
            if scrape_ingredients[i]['us_measures'].get('us_unit'):
                us_measure_id = USMeasurement.query.filter_by(us_unit=scrape_ingredients[i]['us_measures']['us_unit']).first().us_measure_id

            if scrape_ingredients[i]['us_measures'].get('us_amount'):
                us_amount_id = USAmount.query.filter_by(us_amount=scrape_ingredients[i]['us_measures']['us_amount'][0]).first().us_amount_id
                if len(scrape_ingredients[i]['us_measures']['us_amount']) > 1:
                    us_amount_id2 = USAmount.query.filter_by(us_amount=scrape_ingredients[i]['us_measures']['us_amount'][1]).first().us_amount_id

            # add data to usingredientmeasures table
            # if us_measure_id available
            if us_measure_id:
                # both us_measure_id and us_amount_id available
                if us_amount_id:
                    usmeasure = USIngredientMeasure(recipeingredient_id=recipeingredient_id,
                                                    us_measure_id=us_measure_id,
                                                    us_amount_id=us_amount_id)
                    db.session.add(usmeasure)
                    # both us_measure_id and us_amount_id2 available
                    if us_amount_id2:
                        usmeasure2 = USIngredientMeasure(recipeingredient_id=recipeingredient_id,
                                                         us_measure_id=us_measure_id,
                                                         us_amount_id=us_amount_id2)
                        db.session.add(usmeasure2)
                # only us_measure_id available
                else:
                    usmeasure = USIngredientMeasure(recipeingredient_id=recipeingredient_id,
                                                    us_measure_id=us_measure_id)
                    db.session.add(usmeasure)
            # only us_amount_id available
            elif us_amount_id and not us_measure_id:
                usmeasure = USIngredientMeasure(recipeingredient_id=recipeingredient_id,
                                                us_amount_id=us_amount_id)
                db.session.add(usmeasure)
                # only us_amount_id and us_amount_id2 available
                if us_amount_id2:
                    usmeasure2 = USIngredientMeasure(recipeingredient_id=recipeingredient_id,
                                                     us_amount_id=us_amount_id2)
                    db.session.add(usmeasure2)
        # no us_measures
        else:
            usmeasure = USIngredientMeasure(recipeingredient_id=recipeingredient_id)
            db.session.add(usmeasure)

    db.session.commit()


def load_recipe_servings(servings, recipe_name):
    """Load recipeservings for recipe."""

    print "Recipe Servings"

    serving_id = Serving.query.filter_by(serving_size=servings).first().serving_id
    recipe_id = Recipe.query.filter_by(recipe_name=recipe_name).first().recipe_id

    recipeserving = RecipeServing(serving_id=serving_id,
                                  recipe_id=recipe_id)

    db.session.add(recipeserving)

    db.session.commit()


def load_recipe_courses(recipe_name, courses):
    """Load recipecourses for recipe."""

    print "Recipe Courses"

    recipe_id = Recipe.query.filter_by(recipe_name=recipe_name).first().recipe_id
    for course_name in courses:
        course_id = Course.query.filter_by(course_name=course_name).first().course_id
        recipecourse = RecipeCourse(course_id=course_id,
                                    recipe_id=recipe_id)

        db.session.add(recipecourse)

    db.session.commit()


###############################################################################

if __name__ == "__main__":
    connect_to_db(app)

    # In case tables haven't been created, create them
    db.create_all()

    # test-case urls
    urls = ["http://minimalistbaker.com/sun-dried-tomato-chickpea-burgers/",
            "http://minimalistbaker.com/cauliflower-rice-stuffed-peppers/",
            "http://minimalistbaker.com/banana-split-smoothie/",
            "http://minimalistbaker.com/strawberry-rhubarb-crumble-bars-gf/",
            "http://minimalistbaker.com/no-bake-almond-butter-cup-bars/",
            "http://minimalistbaker.com/asian-quinoa-salad/"]

    for url in urls:

        #info from webscraping
        scrape_info = get_all_recipe_info(url)

        courses = scrape_info['courses']
        scrape_ingredients = scrape_info['ingredients']
        site_name = scrape_info['site_name']
        src_url = scrape_info['src_url']
        img_url = scrape_info['img_url']

        #general recipe info through api request
        url_recipe_name = filter(None, re.split(r'.*com\/', url))[0]

        response1 = unirest.get("https://spoonacular-recipe-food-nutrition-v1.p.mashape.com/recipes/extract?forceExtraction=false&url=http://minimalistbaker.com/%s" % url_recipe_name,
            headers={
                "X-Mashape-Key": os.environ['MASHAPE_KEY']
            }
        )

        api_info = response1.body

        recipe_api_id = api_info['id']
        servings = int(api_info['servings'])
        recipe_name = api_info['title']
        all_ingredients = api_info['extendedIngredients']  # list all ingredients
        time_in_min = int(api_info['readyInMinutes'])

        #instructions for recipe through api request
        response2 = unirest.get("https://spoonacular-recipe-food-nutrition-v1.p.mashape.com/recipes/%s/analyzedInstructions?stepBreakdown=true" % recipe_api_id,
            headers={
                "X-Mashape-Key": os.environ['MASHAPE_KEY'],
                "Accept": "application/json"
            }
        )

        instruction_info = response2.body[0]['steps']

        load_website(site_name)
        load_servings(servings)
        load_courses(courses)
        load_ingredienttypes(all_ingredients)
        load_ingredients(all_ingredients)
        load_measurements(scrape_ingredients)
        load_recipes(recipe_name, recipe_api_id, time_in_min, site_name, src_url, img_url)
        load_recipe_ingredients(recipe_name, all_ingredients, scrape_ingredients)
        load_instructions(recipe_name, instruction_info)
        load_ingredient_measures(scrape_ingredients, all_ingredients, recipe_name)
        load_recipe_servings(servings, recipe_name)
        load_recipe_courses(recipe_name, courses)

    # test-case users
    #load_users(username, password)
    load_users('Ada', '12345')
    load_users('Grace', 'hbacad')