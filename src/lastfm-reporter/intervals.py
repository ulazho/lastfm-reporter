
from dataclasses import dataclass
from typing import List, Tuple

@dataclass
class Intervals():
    """
    A simple class for working with intervals. Finding intersections and adding new ones. 
    It can be changed to an "Interval Tree" structure to increase performance 
    """
    intervals_list: List[Tuple]

    def __init__(self, intervals: List[Tuple] = [(0, 0)] ) -> None:
        self.intervals_list = intervals
        self.intervals_list.sort()
        self.__union()

    def __str__(self) -> str:
        return str(self.intervals_list)
    
    def __iter__(self):
        return iter(self.intervals_list)

    def __union(self) -> None:
        i = 0
        while i + 1 < len(self.intervals_list):
            if self.intervals_list[i][1] + 1 >= self.intervals_list[i + 1][0] :
                start = min(self.intervals_list[i][0], self.intervals_list[i + 1][0])
                end = max(self.intervals_list[i][1], self.intervals_list[i + 1][1])
                self.intervals_list.pop(i)
                self.intervals_list.pop(i)
                self.intervals_list.insert(i, (start, end))
                i -= 1
            i += 1

    def intersection(self, in_interval: Tuple) -> List[Tuple]:
        """
        Returns the intersection of intervals
        """
        intersection_intervals = []
        for interval in self.intervals_list:
            if interval[1] >= in_interval[0]: 

                start = max(interval[0], in_interval[0])
                end = min(interval[1], in_interval[1])

                if start > end: continue
                intersection_intervals.append((start, end))
        return intersection_intervals

    def complement(self, in_interval: Tuple[int, int]) -> List[Tuple]:
        """
        Returns the complement of the intervals
        """
        intersection_intervals = self.intersection(in_interval)
        complement = []
        for i in range(len(intersection_intervals) - 1):

            if intersection_intervals[i][1] <= intersection_intervals[i + 1][0]:
                complement.append((
                    intersection_intervals[i][1],
                    intersection_intervals[i + 1][0]
                )
                )

        #If intersection is empthy
        if intersection_intervals == []: return [in_interval]

        #Completes missing intervals on the left and right sides, if necessary
        if intersection_intervals[0][0] > in_interval[0]: 
            complement.insert(0, (in_interval[0], intersection_intervals[0][0] - 1))
        if intersection_intervals[-1][1] < in_interval[1]:
            complement.append((intersection_intervals[-1][1] + 1, in_interval[1]))
        return complement

    def add(self, intervals:List[Tuple]) -> None:
        """
        Add a new interval
        """
        for interval in intervals:
            self.intervals_list.append(interval)
        self.intervals_list.sort()
        self.__union()

    def total_length(self) -> int:
        """
        Returns the total length of all intervals
        """
        intervals_sum = 0
        for interval in self.intervals_list:
            intervals_sum += interval[1] - interval[0] + 1
        return intervals_sum
    
