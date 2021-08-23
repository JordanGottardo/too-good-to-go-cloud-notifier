
class ProductsQueueCache():

    def __init__(self):
        self.productsQueueDictionary = {}
     
    def Add(self, id, productsQueue):
        self.productsQueueDictionary[id] = productsQueue

    def Get(self, id):
        return self.productsQueueDictionary[id]

    def Contains(self, id):
        return id in self.productsQueueDictionary

    def RestartMonitoring(self, id):
        self.productsQueueDictionary[id].RestartMonitoring()

    def SoftStopMonitoring(self, id):
        self.productsQueueDictionary[id].SoftStopMonitoring()

    def HardStopMonitoring(self, id):
        self.productsQueueDictionary[id].HardStopMonitoring()
        self.productsQueueDictionary.pop(id)

