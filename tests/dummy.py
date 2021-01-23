class DummyCallable:
    
    def __init__(self, *args, **kwargs):
        self.args, self.kwargs = args, kwargs
    
    
    def __call__(self):
        return self.args, self.kwargs
