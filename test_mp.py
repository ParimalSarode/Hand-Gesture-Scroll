import mediapipe as mp
try:
    print(mp.solutions)
    print("Success")
except AttributeError:
    print("Failure")
