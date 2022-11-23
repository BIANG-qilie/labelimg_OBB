import math

class Vector():
    def __init__(self, qpoint1, qpoint2):
        self.x = qpoint2.x() - qpoint1.x()
        self.y = qpoint2.y() - qpoint1.y()

    def dot_product(self, vector):
        return self.x * vector.x + self.y * vector.y
    
    def magnitude(self):
        return math.sqrt(self.x**2 + self.y**2)

    def projection(self, vector):
        dot = self.dot_product(vector)
        magnitude = vector.magnitude()

        return dot / (magnitude**2)
        