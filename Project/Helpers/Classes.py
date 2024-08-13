class User:
    def __init__(self, user_data):
        self.id = user_data['id']
        self.username = user_data['username']
        self.email = user_data['email']
        self.password = user_data['password']
        self.interests = user_data['interests']
        self.reactions = [Reaction(reaction) for reaction in user_data['reactions']]


class Reaction:
    def __init__(self, reaction_data):
        self.reaction = reaction_data['reaction']
        self.probability = reaction_data['probability']