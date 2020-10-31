from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from rasa_core.actions.action import Action
from rasa_core.events import SlotSet
import zomatopy
import json
import pandas as pd
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import re
import warnings
warnings.simplefilter('ignore')

# zomato api key
config = {"user_key": "b23c8351909babab08ea98b2bdbea289"}
zomato = zomatopy.initialize_app(config)

# gmail id and app password
email = 'vasanth260m12@@gmail.com'
password = 'eijnbexyzkeqvnfy'


def get_soundex(token):
    """Get the soundex code for the string"""
    token = token.upper()

    soundex = ""

    # first letter of input is always the first letter of soundex
    soundex += token[0]

    # create a dictionary which maps letters to respective soundex codes. Vowels and 'H', 'W' and 'Y' will be represented by '.'
    dictionary = {"BFPV": "1", "CGJKQSXZ": "2", "DT": "3",
                  "L": "4", "MN": "5", "R": "6", "AEIOUHWY": "."}

    for char in token[1:]:
        for key in dictionary.keys():
            if char in key:
                code = dictionary[key]
                if code != soundex[-1]:
                    soundex += code

    # remove vowels and 'H', 'W' and 'Y' from soundex
    soundex = soundex.replace(".", "")

    # trim or pad to make soundex a 4-character code
    soundex = soundex[:4].ljust(4, "0")

    return soundex


def zomato_helper(loc, cuisine, budget, top=5):
    """
    Get zomato api results as a pandas data frame

    @param string $loc
    @param string $cuisine
    @param string $budget

    @return (pandas.DataFrame, string): a tuple with the results in a df
    and a string that contains the error if any
    """
    # initializing a dataframe to store the results
    df = pd.DataFrame(columns=['name', 'address', 'budget', 'rating'])

    # try: getlocationinfo from zomato
    # except: return the empty df and error as string
    # else: if loc detail is succesfull accessed proceed further
    try:
        location_detail = zomato.get_location(loc, 1)

        # parse the json as python dict
        d1 = json.loads(location_detail)
        lat = d1["location_suggestions"][0]["latitude"]
        lon = d1["location_suggestions"][0]["longitude"]
    except:
        # return empty df if error
        return (df, "location error")
    else:
        cuisines_dict = {'american': 1, 'chinese': 25, 'mexican': 73,
                         'italian': 55, 'north indian': 50, 'south indian': 85}

        # here we are using regex to make sure the limits are set properly for the budget
        # this is more of a fail safe, effort has been put into creating regex, synonymns
        # and examples in data.json file
        if re.search("(<|less)\\s*(than)*\\s*(rs|RS|Rs|INR|MRP|inr|mrp)*.*[0-9]{3}", budget):
            filer_min = 0
            filer_max = 300
        elif re.search("(rs|RS|Rs|INR|MRP|inr|mrp)*.*[0-9]{3}\\s*(-|to)\\s*(rs|RS|Rs|INR|MRP|inr|mrp)*.*[0-9]{3}", budget):
            filer_min = 301
            filer_max = 700
        elif re.search("(>|greater)\\s*(than)*\\s*(rs|RS|Rs|INR|MRP|inr|mrp)*.*[0-9]{3}", budget):
            filer_min = 701
            filer_max = 9999
        else:
            filer_min = 0
            filer_max = 9999

        # results has the list of all restaurants
        results = zomato.restaurant_search(
            "", lat, lon, str(cuisines_dict.get(cuisine)), 20)

        # json to dict
        d = json.loads(results)

        # store in a pandas dataframe
        for row, restaurant in enumerate(d['restaurants']):
            df.loc[row] = [restaurant['restaurant']['name']] + \
                [restaurant['restaurant']['location']['address']] + \
                [restaurant['restaurant']['average_cost_for_two']] + \
                [restaurant['restaurant']['user_rating']['aggregate_rating']]

        # filter for budget
        df = df[(df['budget'] > filer_min) & (df['budget'] < filer_max)]

        # if no results send empty dataframe with error in a string
        if df.empty:
            return (df, "no results")

        # return df with None for string to denote no error if we get this far
        return (df.sort_values('rating', ascending=False).head(top), None)


class ActionCheckLocation(Action):
    """A class to check if the given location is valid"""

    def name(self):
        return 'action_check_location'

    def run(self, dispatcher, tracker, domain):

        # list of all tier 1 and 2 cities
        cities = ['bangalore', 'chennai', 'delhi', 'hyderabad', 'kolkata', 'mumbai', 'visakhapatnam', 'ahmedabad', 'pune', 'surat',
                  'coimbatore', 'agra', 'ajmer', 'aligarh', 'amravati', 'amritsar', 'asansol', 'aurangabad', 'bareilly', 'belgaum',
                  'bhavnagar', 'bhiwandi', 'bhopal', 'bhubaneswar', 'bikaner', 'bokarosteelcity', 'chandigarh', 'coimbatore', 'nagpur',
                  'cuttack', 'dehradun', 'dhanbad', 'bhilai', 'durgapur', 'erode', 'faridabad', 'firozabad', 'ghaziabad', 'gorakhpur',
                  'gulbarga', 'guntur', 'gwalior', 'gurgaon', 'guwahati', 'hubli–dharwad', 'indore', 'jabalpur', 'jaipur', 'jalandhar',
                  'jammu', 'jamnagar', 'jamshedpur', 'jhansi', 'jodhpur', 'kakinada', 'kannur', 'kanpur', 'kochi', 'kottayam', 'kolhapur',
                  'kollam', 'kota', 'kozhikode', 'kurnool', 'ludhiana', 'lucknow', 'madurai', 'malappuram', 'mathura', 'goa', 'mangalore',
                  'meerut', 'moradabad', 'mysore', 'nanded', 'nashik', 'nellore', 'noida', 'palakkad', 'patna', 'pondicherry', 'allahabad',
                  'raipur', 'rajkot', 'rajahmundry', 'ranchi', 'rourkela', 'salem', 'sangli', 'siliguri', 'solapur', 'srinagar', 'thiruvananthapuram',
                  'thrissur', 'tiruchirappalli', 'tirupati', 'tirunelveli', 'tiruppur', 'tiruvannamalai', 'ujjain', 'bijapur', 'vadodara', 'varanasi',
                  'vasai-virar city', 'vijayawada', 'vellore', 'warangal']

        # tier 1 and 2 cities with their soundexes
        soundex_dict = {'B524': 'bangalore', 'C500': 'chennai', 'D400': 'delhi', 'H361': 'hyderabad', 'K423': 'kolkata', 'M510': 'mumbai', 'V221': 'visakhapatnam',
                        'A531': 'ahmedabad', 'P500': 'pune', 'S630': 'surat', 'C513': 'coimbatore', 'A260': 'agra', 'A256': 'ajmer', 'A426': 'aligarh', 'A561': 'amravati', 'A563': 'amritsar',
                        'A252': 'asansol', 'A652': 'aurangabad', 'B640': 'bareilly', 'B425': 'belgaum', 'B152': 'bhubaneswar', 'B530': 'bhiwandi', 'B140': 'bhopal', 'B256': 'bikaner',
                        'B262': 'bokarosteelcity', 'C532': 'chandigarh', 'N216': 'nagpur', 'C320': 'cuttack', 'D635': 'dehradun', 'D513': 'dhanbad', 'B400': 'bhilai', 'D621': 'durgapur',
                        'E630': 'erode', 'F631': 'faridabad', 'F621': 'firozabad', 'G213': 'ghaziabad', 'G621': 'gorakhpur', 'G416': 'gulbarga', 'G536': 'guntur', 'G460': 'gwalior', 'G625': 'gurgaon',
                        'G300': 'guwahati', 'H143': 'hubli–dharwad', 'I536': 'indore', 'J141': 'jabalpur', 'J160': 'jaipur', 'J453': 'jalandhar', 'J500': 'jammu', 'J526': 'jamnagar',
                        'J523': 'jamshedpur', 'J520': 'jhansi', 'J316': 'jodhpur', 'K253': 'kakinada', 'K560': 'kannur', 'K516': 'kanpur', 'K200': 'kochi', 'K350': 'kottayam', 'K416': 'kolhapur',
                        'K450': 'kollam', 'K300': 'kota', 'K223': 'kozhikode', 'K654': 'kurnool', 'L350': 'ludhiana', 'L250': 'lucknow', 'M360': 'mathura', 'M416': 'malappuram', 'G000': 'goa',
                        'M524': 'mangalore', 'M630': 'meerut', 'M631': 'moradabad', 'M260': 'mysore', 'N533': 'nanded', 'N220': 'nashik', 'N460': 'nellore', 'N300': 'noida', 'P423': 'palakkad',
                        'P350': 'patna', 'P532': 'pondicherry', 'A413': 'allahabad', 'R160': 'raipur', 'R230': 'rajkot', 'R255': 'rajahmundry', 'R520': 'ranchi', 'R624': 'rourkela', 'S450': 'salem',
                        'S524': 'sangli', 'S426': 'siliguri', 'S416': 'solapur', 'S652': 'srinagar', 'T615': 'tiruvannamalai', 'T626': 'tiruchirappalli', 'T613': 'tirupati', 'T654': 'tirunelveli',
                        'T616': 'tiruppur', 'U250': 'ujjain', 'B216': 'bijapur', 'V336': 'vadodara', 'V652': 'varanasi', 'V216': 'vasai-virar city', 'V230': 'vijayawada', 'V460': 'vellore', 'W652': 'warangal'}

        # access location given by user
        loc = tracker.get_slot('location')

        # if none is set for loc, notify and exit
        if loc is None:
            dispatcher.utter_message(
                "Sorry, didn’t find any such location. Can you please type again?")
            return [SlotSet('location', None)]

        # check if loc is in the list of cities
        if loc in cities:
            return [SlotSet('location', loc)]
        # if not present check again with soundexes to account for spelling errors
        elif soundex_dict.get(get_soundex(loc)):
            dispatcher.utter_message(
                loc + " has been spell corrected as " + soundex_dict.get(get_soundex(loc)))
            return [SlotSet('location', soundex_dict.get(get_soundex(loc)))]

        # not present in the list of cities maintained so notify appropriately and reset the location
        dispatcher.utter_message(
            "Sorry the location is either non serviceable or misspelled, try again")
        return [SlotSet('location', None)]


class ActionSendMail(Action):
    """Uses smtplib to send the list of restaurants in mail"""

    def name(self):
        return 'action_send_mail'

    def run(self, dispatcher, tracker, domain):

        # subject for the email
        subject = 'Restaurant search results'

        # create the server
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(email, password)

        # html template
        html = """\
        <html>
            <head></head>
            <body>
                {0}
            </body>
        </html>
        """

        # all variables to get the list of restaurants
        loc = tracker.get_slot('location')
        cuisine = tracker.get_slot('cuisine')
        budget = tracker.get_slot('budget')
        send_to_email = tracker.get_slot('email_id')

        dispatcher.utter_message("Constructing your list from Zomato")
        result = zomato_helper(loc, cuisine, budget)

        # zomato helper returns a tuple, with the error captured in the second
        # entry of tule
        if result[1] is not None:
            html = html.format(result[1])
        else:
            html = html.format(result[0].sort_values(
                'rating', ascending=False).head(10).to_html(index=False))

        # construct the message and attach the table
        msg = MIMEMultipart()
        msg['From'] = email
        msg['To'] = send_to_email
        msg['Subject'] = subject
        msg.attach(MIMEText(html, 'html'))

        dispatcher.utter_message("Sending mail")

        try:
            # send the mail
            server.sendmail(email, send_to_email, msg.as_string())
        except:
            dispatcher.utter_message("Sending failed")

        # close the server
        server.quit()
        return [SlotSet('email_id', send_to_email)]


class ActionSearchRestaurants(Action):
    """A class to search for restaurants"""

    def name(self):
        return 'action_search_restaurant'

    def run(self, dispatcher, tracker, domain):

        # access all required variables from tracker
        loc = tracker.get_slot('location')
        cuisine = tracker.get_slot('cuisine')
        budget = tracker.get_slot('budget')

        # use the helper function to access the results
        dispatcher.utter_message("Talking with Zomato servers")
        result = zomato_helper(loc, cuisine, budget)

        # the results is a tuple , with the second element having string
        # with stores errors if any
        if result[1] is not None:
            dispatcher.utter_message(
                result[1]+", restarting conversation (Go for a higher budget and a tier 1 city, it increases the chance of finding more restaurants)")
            return [SlotSet('location', None), SlotSet('budget', None), SlotSet('cuisine', None)]

        # printing the table as string and passing it to the dispatcher
        dispatcher.utter_message(result[0].to_string(index=False))
        dispatcher.utter_message(
            "Should I send you details of all the restaurants on email?")
        return [SlotSet('location', loc)]
