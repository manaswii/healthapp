# Health Info
https://infohealth.herokuapp.com/ \
(for screenshots go to the end of the README)

### Idea behind it ###
The inspiration behind it was to make a single station to healthy living for people,\
**A web app which displays useful health information to users and also helps them track them.**

## It displays the following: ##
- Amount of water you should drink everyday.
- Hours of sleep you must get everyday.
- Calories you should consume to maintain your current weight for a sedentary lifestyle.

## It has a Tracker built in, which helps you keep track of the following information: ##
- Hours you slept today
- Glasses of water you drank today
- Calories you consumed today

## Technologies used ##
1. Flask for backend
2. Jinja2 for HTML templating
3. POSTGRES database
4. Bootstrap to make it responsive and for a lot of the styling

## The decisions and choices ##
- The website uses javascript to get the user's timezone so that everything especially in the History is displayed properly in the user's current timezone.
- The decision to use POSTGRES after making the whole website with sqlite3 once because heroku isn't compatible with sqlite, POSTGRES was one of the hardest things to work with at first because of the timezone queries.
- Using the API to search food items and it's calories.
- Working on the aesthetics and the color scheme was extremely fun.

## Files: ##
1. `application.py` - It is the main guts of the website, it holds the flask backend of the website.
2. `helpers.py` - It is a file with helper functions used in the main file, it was made to keep the main file less crowded.
3. `health.db` - It was the database when the website was using sqlite3, now it's been replaced by POSTGRES.
#### Template HTML files ####
4. `layout.html` - All the other HTML files extend from this, it's the HTML layout files which includes bootstrap library and the navbar and other barebones. 
5. `login.html` - It's the login page of the website.
6. `register.html` - It's the register page of the website.
7. `index.html` - It's the home page of the website, it contains the **Tracker** and all the **Health information**.
8. `accountSettings.html` - It's the page from where user's can add their details such as their height, weight, age and gender.
9. `history.html` - It display the stored information for all the previous dates.
10. `moreinfo.html` - It displays the information for a particular day in more details when a date is clicked from history.html.
11. `about.html` - It's the about page of the website.
12. `changepassword.html` It's the form which is used to change the password, it's accessible from the accouunt settings.
#### CSS ####
13. `styles.css` - It's the CSS file used for styling throughout.\
#### Image files ####
`favicon.ico, food.png, pensive.png, pensive2.png, sleep.png, water.png, welldone.png, welldone.gif`\
## Some screenshots ##
### index.html (it has the **information** on the left side and the **Tracker** on the right side) ###
![image](https://user-images.githubusercontent.com/85053597/131918599-f4a53422-89a1-4770-95c3-2c63a890a560.png)
### History section,The older section is grouped by dates. You can click on one of the dates to expand it even further and see when exactly you added what entry. ###
![image](https://user-images.githubusercontent.com/85053597/131920712-881945a8-6d3a-4125-b5fe-1b4a13a67b84.png)
### History section on a phone ###
![image](https://user-images.githubusercontent.com/85053597/131921523-6c49881b-3632-4c91-abab-bd9c0cca5de3.png)

