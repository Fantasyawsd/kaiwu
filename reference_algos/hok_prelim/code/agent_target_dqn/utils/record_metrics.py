import numpy as np
from collections import deque

class RecordMetrics:
    def __init__(self, max_len=None):
        self.values = deque(maxlen=max_len)
    
    def reset(self):
        self.values.clear()

    def record(self, data):
        self.values.append(data)
    
    def get_average(self):
        if not self.values:
            return 0
        return np.average(np.array(self.values), axis=0).tolist()

if __name__ == '__main__':
    # Example usage
    metrics = RecordMetrics(max_len=2)
    # metrics.record([1, 2, 3])
    # metrics.record([4, 5, 6])
    # metrics.record([7, 8, 9])
    # metrics.record([7, 8, 9])
    metrics.record(True)
    metrics.record(False)
    metrics.record(False)

    print("Average of recorded metrics:", metrics.get_average())
    print("Recorded values:", list(metrics.values))  # Display the current values in the deque
