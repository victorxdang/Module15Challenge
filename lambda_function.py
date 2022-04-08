### Required Libraries ###
from datetime import datetime
from dateutil.relativedelta import relativedelta

### Functionality Helper Functions ###
def parse_int(n):
    """
    Securely converts a non-integer value to integer.
    """
    print(f"Calling parse_int(n = {n})")
    
    try:
        return int(n)
    except ValueError:
        return float("nan")


def build_validation_result(is_valid, violated_slot, message_content):
    """
    Define a result message structured as Lex response.
    """
    print(f"Calling build_validation_result(is_valid = {is_valid}, violated_slot = {violated_slot}, message_content = {message_content})")
    
    if message_content is None:
        return {"isValid": is_valid, "violatedSlot": violated_slot}

    return {
        "isValid": is_valid,
        "violatedSlot": violated_slot,
        "message": {"contentType": "PlainText", "content": message_content},
    }


### Dialog Actions Helper Functions ###
def get_slots(intent_request):
    """
    Fetch all the slots and their values from the current intent.
    """
    print(f"Calling get_slots(intent_request = {intent_request})")
    
    return intent_request["currentIntent"]["slots"]


def elicit_slot(session_attributes, intent_name, slots, slot_to_elicit, message):
    """
    Defines an elicit slot type response.
    """
    print(f"Calling elicit_slot((session_attributes = {session_attributes}, intent_name = {intent_name}, slots = {slots}, slot_to_elicit, message = {slot_to_elicit})")

    return {
        "sessionAttributes": session_attributes,
        "dialogAction": {
            "type": "ElicitSlot",
            "intentName": intent_name,
            "slots": slots,
            "slotToElicit": slot_to_elicit,
            "message": message,
        },
    }


def delegate(session_attributes, slots):
    """
    Defines a delegate slot type response.
    """
    print(f"Calling delegate(session_attributes = {session_attributes}, slots = {slots}")

    return {
        "sessionAttributes": session_attributes,
        "dialogAction": {"type": "Delegate", "slots": slots},
    }


def close(session_attributes, fulfillment_state, message):
    """
    Defines a close slot type response.
    """
    print(f"Calling close(session_attributes = {session_attributes}, fulfillment_state = {fulfillment_state}, message = {message})")

    response = {
        "sessionAttributes": session_attributes,
        "dialogAction": {
            "type": "Close",
            "fulfillmentState": fulfillment_state,
            "message": message,
        },
    }

    return response


"""
Step 3: Enhance the Robo Advisor with an Amazon Lambda Function

In this section, you will create an Amazon Lambda function that will validate the data provided by the user on the Robo Advisor.

1. Start by creating a new Lambda function from scratch and name it `recommendPortfolio`. Select Python 3.7 as runtime.

2. In the Lambda function code editor, continue by deleting the AWS generated default lines of code, then paste in the starter code provided in `lambda_function.py`.

3. Complete the `recommend_portfolio()` function by adding these validation rules:

    * The `age` should be greater than zero and less than 65.
    * The `investment_amount` should be equal to or greater than 5000.

4. Once the intent is fulfilled, the bot should respond with an investment recommendation based on the selected risk level as follows:

    * **none:** "100% bonds (AGG), 0% equities (SPY)"
    * **low:** "60% bonds (AGG), 40% equities (SPY)"
    * **medium:** "40% bonds (AGG), 60% equities (SPY)"
    * **high:** "20% bonds (AGG), 80% equities (SPY)"

> **Hint:** Be creative while coding your solution, you can have all the code on the `recommend_portfolio()` function, or you can split the functionality across different functions, put your Python coding skills in action!

5. Once you finish coding your Lambda function, test it using the sample test events provided for this Challenge.

6. After successfully testing your code, open the Amazon Lex Console and navigate to the `recommendPortfolio` bot configuration, integrate your new Lambda function by selecting it in the “Lambda initialization and validation” and “Fulfillment” sections.

7. Build your bot, and test it with valid and invalid data for the slots.

"""


### Intents Handlers ###
def recommend_portfolio(intent_request):
    """
    Performs dialog management and fulfillment for recommending a portfolio.
    """

    print(f"Calling recommend_portfolio(intent_request = {intent_request})")

    first_name = get_slots(intent_request)["firstName"]
    age = get_slots(intent_request)["age"]
    investment_amount = get_slots(intent_request)["investmentAmount"]
    risk_level = get_slots(intent_request)["riskLevel"]
    source = intent_request["invocationSource"]

    if source == "DialogCodeHook":
        # This code performs basic validation on the supplied input slots.

        # Gets all the slots
        slots = get_slots(intent_request)

        # Validates user's input using the validate_data function
        validation_result = validate_data(first_name, age, investment_amount, risk_level)

        # If the data provided by the user is not valid,
        # the elicitSlot dialog action is used to re-prompt for the first violation detected.
        if not validation_result["isValid"]:
            slots[validation_result["violatedSlot"]] = None  # Cleans invalid slot

            # Returns an elicitSlot dialog to request new data for the invalid slot
            return elicit_slot(
                intent_request["sessionAttributes"],
                intent_request["currentIntent"]["name"],
                slots,
                validation_result["violatedSlot"],
                validation_result["message"],
            )

        # Fetch current session attributes
        output_session_attributes = intent_request["sessionAttributes"]

        # Once all slots are valid, a delegate dialog is returned to Lex to choose the next course of action.
        return delegate(output_session_attributes, get_slots(intent_request))

    # Return a message with conversion's result.
    return close(
        intent_request["sessionAttributes"],
        "Fulfilled",
        {
            "contentType": "PlainText",
            "content": f"Thank you for your information. Your recommended portfolio allocation is: {recommendation(risk_level)}"
        },
    )

### Data Validation ###
def validate_data(first_name, age, investment_amount, risk_level):
    """
    Validates the data provided by the user.
    """
    
    print(f"First Name: {first_name}, Age: {age}, Investment Amount: {investment_amount}, Risk Level: {risk_level}")
    
    if age is not None:
        if parse_int(age) <= 0 or parse_int(age) >= 65:
            return build_validation_result(
                False,
                "age",
                "Your age should be a positive value and less than 65 years old!"
            )
        
    if investment_amount is not None:
        if parse_int(investment_amount) < 5000:
            return build_validation_result(
                False,
                "investmentAmount",
                "You must have at least $5000 to use this robo advisor."
            )

    if risk_level is not None:
        risk_level = risk_level.lower()
        
        if risk_level not in [ "none", "low", "medium", "high" ]:
            return build_validation_result(
                False,
                "riskLevel",
                "You must select either None, Low, Medium or High."
            )

    return build_validation_result(True, None, None)


### Equities Allocation Recommendation ###
def recommendation(risk_level):
    """
    Function to return the recommended asset allocations.
    """
    
    risk_level = risk_level.lower()
    
    if risk_level == "none": 
        return "100% bonds (AGG), 0% equities (SPY)"
    elif risk_level == "low": 
        return "60% bonds (AGG), 40% equities (SPY)"
    elif risk_level == "medium":
        return "40% bonds (AGG), 60% equities (SPY)"
    elif risk_level == "high": 
        return "20% bonds (AGG), 80% equities (SPY)"
    else:
        return "Invalid Input! Please enter either None, Low, Medium or High."


### Intents Dispatcher ###
def dispatch(intent_request):
    """
    Called when the user specifies an intent for this bot.
    """

    print(f"Calling dispatch(intent_request = {intent_request})")
    intent_name = intent_request["currentIntent"]["name"]

    # Dispatch to bot's intent handlers
    if intent_name == "recommendPortfolio":
        return recommend_portfolio(intent_request)

    raise Exception("Intent with name " + intent_name + " not supported")


### Main Handler ###
def lambda_handler(event, context):
    """
    Route the incoming request based on intent.
    The JSON body of the request is provided in the event slot.
    """
    print(f"Calling lambda_handler(event = {event}, context = {context})")

    return dispatch(event)