import os
import json
import re
from collections import OrderedDict
from flask import Flask, render_template, request, redirect, flash, url_for, session, abort


app = Flask(__name__)
app.secret_key = "ab5t5gdfnmk34322bum"

def count_highest(username):
    highest = 0
    if session[username]:
        for v in session[username].values():
            highest += int(v)
    else:
        pass
    return highest

@app.route('/', methods=["GET", "POST"])
def index():
    """
    Welcome page with a form to send username and start game.
    Function also checks for username in users.txt, just to avoid overwriting data in the leaderboard
    """
    if request.method == "POST":
        if len(request.form["username"]) >= 4:
             return redirect(url_for('user', username=request.form["username"]))
    return render_template('index.html')
    
@app.route('/<username>', methods=["GET","POST"])
def user(username):
    """
    user starting page, with an encouraging image and a simple form with start button
    """
    if request.method == "POST":
        level="1"
        score="0"
        session[username] = {}
        session.modified = True
        return redirect(url_for('game', username=username, level=level, score=score))
        
    return render_template('user.html', username = username)
    

@app.route("/game/<username>/<level>/<score>", methods=["GET","POST"])
def game(username, level, score=0):
    """ This function creates instance game page, where riddles are displayed.
    After clicking submit, the json file is being checked for riddle with specific number stored as level, then
    the data are copied to a 3-elements list.
    """
    
    if int(score) > count_highest(username):
        return redirect(url_for('ban', username=username))
    
    rlist = []
    # loading riddle
    riddle_file = open("data/riddles.json", "r")
    riddle_data = json.load(riddle_file)
    riddle_file.close()
    
    for obj in riddle_data:
        if obj["level"] == level:
            # Finds proper riddle
            rlist.append(obj["riddle"])
            rlist.append(obj["answer"])
            rlist.append(obj["img_source"])
            
    if request.method == "POST":
        if request.form["answer"].lower() == rlist[1].lower():
            points = request.form['score_getter']
            #convert all to integer, just in case
            new_score = int(score) + int(points)
            session[username].setdefault(level, points)
            session.modified = True
            if int(level) < len(riddle_data):
                """If the level value is still smaller or same as the number of riddle objects - if there are still 
                any riddles to answer - then we get another view with the next riddle. Otherwise, gets back to user view with leaderboard"""
                    
                new_level = str(int(level) + 1)
                return redirect(url_for('game', username=username, level=new_level, score=new_score)) # score = new_score
            else:
                # redirect to the game_over view with leaderboard
                return redirect(url_for('game_over', username=username, score=score)) # score = score
        else:
            if request.form["answer"] == "":
                return redirect(url_for('game', username=username, level=level, score=score)) #score = score
            else:
                # if answer is incor refresh with 
                flash("Oops! Wrong! The answer is not {}".format(request.form["answer"]))
                return redirect(url_for('game', username=username, level=level, score=score)) #score = score
                
    return render_template('game.html',
    riddle_text = rlist[0],
    riddle_image= rlist[2],
    username=username,
    level=level,
    score=score)       


@app.route('/game_over/<username>/<score>', methods=["GET"])
def game_over(username, score):
    """
    This function takes score as parameter, then reads the records file and checks if the score's been higher then the higest so far.
    If positive, re-writes file with dictionary containing new record.
    If there's more then 6, pops out random of the lowest.
    Also passes overall score stored in session to the template.
  
    """
    # puts data into dictionary
    data = {}
    data.setdefault(username, int(score))
    lb_file = open("data/leaderboard.json", "r")
    lb_data = json.load(lb_file)
    lb_file.close()
    # if there's less than 10 records, write into the file, whatever the score 
    if(len(lb_data)<6):
        for name, points in lb_data.items():
            data[name] = points
        outfile = open("data/leaderboard.json", "w")
        json.dump(data, outfile)
        outfile.close()
    else:
        popout = int(min(lb_data.values()))
        #check if score isn't higher than any of the highest scores so far
        # if it is pop the lowest out
        if int(score) >= popout:
            pop = ""
            for name, points in lb_data.items():
                # just in case if there's many users with the same score
                # make sure only one, random record will be deleted
                if points == popout:
                    pop = name
                data[name] = int(points)
            del data[pop]
               
            with open('data/leaderboard.json', 'w') as outfile:
                json.dump(data, outfile)
    scoring = OrderedDict(sorted(session[username].items()))
    return render_template('game_over.html', username=username, score=score, scoring=scoring)
    
@app.route('/leaderboard', methods=["GET"])  
def leaderboard():
    """
    Displays leaderboard read from leaderboard.json.
    """
    lb_file = open("data/leaderboard.json", "r")
    lb_data = json.load(lb_file)
    lb_file.close()
    leaderboard = OrderedDict(sorted(lb_data.items(), key=lambda x: x[1], reverse=True))
    
    return render_template('show_leaderboard.html', leaderboard=leaderboard)
    
@app.route('/cheating_ban/<username>')
def ban(username):
    
    int_level = max([int(s) for s in session[username].keys()])
    level = str(int_level)
    print(level)
    score = count_highest(username)
    print(score)
    return render_template('ban.html', username=username, level=level, score=score)
    
@app.route('/restart/<username>')
def restart(username):
    try:
        session.pop(username)
    except(KeyError):
        abort(410)
    return redirect(url_for('index'))
    
    
@app.errorhandler(410)
def page_gone():
    message = "You can see this page, because you probably choose to reset user data."
    return render_template('error.html', message=message)
if __name__ == '__main__':
    app.run(host=os.getenv('IP'), port=(int(os.getenv('PORT'))), debug=True)