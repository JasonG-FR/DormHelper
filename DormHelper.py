#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  DormHelper.py
#
#  Copyright 2018 JasonG-FR <jason.gombert@protonmail.com>
#
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#  MA 02110-1301, USA.
#


import threading

from random import sample, randint, choice, shuffle, seed
from time import time
from datetime import datetime
from csv import DictReader


class Student(object):
    def __init__(self, id, friends):
        self.id = id
        self.friends = friends
        self.happiness = 0

    def update_happiness(self, room):
        self.happiness = 0
        for friend in self.friends:
            if friend in room:
                self.happiness += 1


class Room(object):
    def __init__(self, beds):
        self.nb_beds = beds
        self.students = []

    def add_student(self, student):
        if len(self.students) < self.nb_beds:
            self.students.append(student)
        else:
            raise Exception("The room is full!")


class bcolors(object):
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'


class Thread(threading.Thread):
    def __init__(self, max_beds, room_names, students, start):
        threading.Thread.__init__(self, target=find_bed_buddies, args=(max_beds, room_names, students, start))
        self.start()


def random_friends(nb_friends, exclude, size):
    # Generate a list of all students
    other_students = [f"S{i}" for i in range(size)]

    # Remove the current student from the list
    other_students.pop(exclude)

    return sample(other_students, nb_friends)


def bed_usage_possiblilities(max_bed):
    # A room could be empty, or have more than 1 bed used but no more than 'max_bed'

    # Generate all the possibilities (including 1 bed used)
    possibilities = list(range(max_bed + 1))

    # Remove the '1 bed used' bed_usage_possibility
    possibilities.pop(1)

    return possibilities


def random_rooms(max_beds, nb_students):
    if nb_students > sum(max_beds):
        raise Exception(f"Not enough beds : {sum(max_beds)} beds for {nb_students} students!")

    # If number of beds = number of students
    if nb_students == sum(max_beds):
        # Every bed is taken in each rooms
        return max_beds

    # Else, we have to randomly choose how to use the rooms
    result = []
    while sum(result) != nb_students:
        result = [choice(bed_usage_possiblilities(max_beds[i])) for i in range(len(max_beds))]

    return result


def calc_global_happiness(students):
    # add everyone's happiness (is someone is not with a friend, happiness = 0, and so is the global happiness)
    happiness = [student.happiness for student in students]
    if 0 in happiness:
        return 0
    else:
        return sum(happiness)


def calc_happiness_score(global_happiness, students):
    # Give a score in % : 0% means everyone have 1 friend, 100% means everyone have all their friends
    score_min = len(students)
    score_max = sum([len(student.friends) for student in students])
    score = (global_happiness - score_min) / (score_max - score_min) * 100

    return score


def print_solution(set_rooms, room_names):
    # Set the color to BOLD BLUE and add spaces for indentation
    result = bcolors.BOLD + bcolors.OKBLUE + "                        "
    for room_name, set_room in zip(room_names, set_rooms):
        result += f"{room_name} : ({', '.join(student_id for student_id in set_room)}), "
    # Remove the last ', ' and stop the bold and blue color
    result = result[:-2] + bcolors.ENDC

    print(result)


def find_bed_buddies(max_beds, room_names, students, start):
    # Load the global variables
    global solutions
    global uniques
    global best
    global iters

    thread_iters = 0

    while True:
        # While not everyone is at least with one friend
        while True:
            # Generate a random room filling
            beds = random_rooms(max_beds, len(students))
            # Try to fill randomly the rooms until everyone is with at least one friend
            i = 0
            while True:
                # Storing the students in a Dict in order to find their Data only using their ID
                students_temp = {student.id: student for student in students}
                # Generate new empty rooms
                rooms = [Room(beds) for beds in max_beds]
                # Shuffle the students IDs then add them to each bed
                # (Suffled Student 1 - Bed 1, Suffled Student 2 - Bed 2)
                students_ids = list(students_temp.keys())
                shuffle(students_ids)
                j = 0
                for room, bed in zip(rooms, beds):
                    for _ in range(bed):
                        room.add_student(students_ids[j])
                        j += 1

                # Calculate the happiness of every student
                for room in rooms:
                    for student_id in room.students:
                        students_temp[student_id].update_happiness(room.students)

                # Calculate the global happiness and the global happiness score
                happiness = calc_global_happiness(students_temp.values())
                happiness_score = calc_happiness_score(happiness, students_temp.values())
                # Check if eveyone is with at least one friends (happiness > 0)
                if happiness > 0:
                    # Using frozensets to delete the possibility of doubles : R1 : (S1, S2) == R1: (S2, S1)
                    set_rooms = frozenset([frozenset(room.students) for room in rooms])
                    # Check if this solution is unique and if its score is higher (don't stop on worse solutions)
                    if set_rooms not in uniques and happiness_score >= best:
                        break

                # Check if we reached the maximun number of tries for this room configuration
                if i >= 100000:
                    break
                i += 1
                thread_iters += 1

            # Update the global variable storing the total iterations done
            # (using lock to be sure only one thread is updating it)
            with lock:
                iters += thread_iters
                thread_iters = 0

            # Check if eveyone is with at least one friend (and not because the max number of tries for the room config)
            if happiness > 0:
                if set_rooms not in uniques and happiness_score >= best:
                    break

            # Show some stats so the user know the program is still working and how fast
            now = time()
            print(f"[{datetime.fromtimestamp(int(now)).strftime('%Y-%m-%d %H:%M:%S')}]"
                  f" : {iters} tries -> {iters//(now - start):.0f} tries/s")

        if set_rooms not in uniques:
            # We update the global variables with this better solution
            with lock:
                uniques.add(set_rooms)
                solutions.append(tuple([rooms, happiness, happiness_score]))
                best = max([solution[-1] for solution in solutions])

                # Warn the user that it found a better solution
                stop = time()
                print(f"[{datetime.fromtimestamp(int(stop)).strftime('%Y-%m-%d %H:%M:%S')}] : " +
                      bcolors.BOLD + bcolors.OKGREEN + "New solution found!" + bcolors.ENDC + bcolors.BOLD +
                      f" Happiness score = {happiness_score:.0f} %, best = {best:.0f} %"
                      f", {iters} tries -> {iters//(stop - start):.0f} tries/s" + bcolors.ENDC)

                # Print the solution
                print_solution(set_rooms, room_names)


lock = threading.Lock()

# Global variables used to communicate between threads
solutions = []
uniques = set()
best = 0
iters = 0


def main(nb_threads, seed_value, room_path, student_path):
    # Create a list for each thread (to isolate them)
    students_th = [[] for _ in range(nb_threads)]

    # If both files are provided, read the data from them
    if room_path and student_path:
        with open(room_path, "r") as room_file:
            max_beds = []
            room_names = []
            reader = DictReader(room_file)
            for row in reader:
                room_names.append(row["ROOM NAME"])
                max_beds.append(int(row["BEDS"]))

        with open(student_path, "r") as student_file:
            reader = DictReader(student_file)
            for row in reader:
                friends = [row["ID FRIEND 1"], row["ID FRIEND 2"], row["ID FRIEND 3"]]
                # Put the student in each thread list
                for student_th in students_th:
                    student_th.append(Student(row["STUDENT ID"], friends))

    # Generate random data if no files are provided
    else:
        room_names = ["R1", "R2", "R3", "R4"]
        max_beds = [5, 3, 4, 5]
        nb_students = 10

        # Generate random students
        for i in range(nb_students):
            r_friends = random_friends(randint(1, 3), i, nb_students)
            for student_th in students_th:
                student_th.append(Student(f"S{i}", r_friends))

    start = time()
    # Lambda function to print "1 Thread" and "2 Threads"
    print_th = lambda nb: f"{nb} Thread" if nb == 1 else f"{nb} Threads"

    # Print the parameters (usefull to see if everything started correctly and to recover the seed if needed)
    if room_path and student_path:
        print(bcolors.BOLD + f"[{datetime.fromtimestamp(int(time())).strftime('%Y-%m-%d %H:%M:%S')}] : "
              f"DormHelper Started, {print_th(nb_threads)}, Seed {seed_value}, Using {room_path} and {student_path}"
              f" : {len(students_th[0])} students for {sum(max_beds)} beds" + bcolors.ENDC)
    else:
        print(bcolors.BOLD + f"[{datetime.fromtimestamp(int(time())).strftime('%Y-%m-%d %H:%M:%S')}] : "
              f"DormHelper Started, {print_th(nb_threads)}, Seed {seed_value}, Random Data"
              f" : {len(students_th[0])} students for {sum(max_beds)} beds" + bcolors.ENDC)

    # Start all the threads
    for student_th in students_th:
        Thread(max_beds, room_names, student_th, start)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Randomly affects students to rooms and select'
                                                 'the best solution found')
    # Set the default seed to the current timestamp in order for it to change a each launch
    parser.add_argument('--seed', default=int(time()),
                        help='use a user defined seed in order to get reproductible events', type=int)
    parser.add_argument('--threads', default=2, help='number of threads to use (default=2)', type=int)
    parser.add_argument('rooms', nargs='?', default=None,
                        help='the path to the file that contains the list of the rooms')
    parser.add_argument('students', nargs='?', default=None,
                        help='the path to the file that contains the list of students')

    args = parser.parse_args()
    seed(args.seed)

    main(args.threads, args.seed, args.rooms, args.students)
