
class ProductsQueueCache():

    def __init__(self):
        self.productsQueueDictionary = {}
     
    def Add(self, id, productsQueue):
        self.productsQueueDictionary[id] = productsQueue

    def Get(self, id):
        return self.productsQueueDictionary[id]

    def StopMonitoring(self, id):
        self.productsQueueDictionary[id].StopMonitoring()

