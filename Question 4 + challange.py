a1 = [3, 5, 0, 0, 5, 89]
b1 = [5, 6, 1, 4]
a2 = 0
b2 = 0
smallestLength = 0

if len(a1) < len(b1):
    smallestLength = len(a1)
else:
    smallestLength = len(b1)

for i in range(smallestLength):
    if a1[i] > b1[i]:
        a2 += 1
    else:
        b2 += 1

if a2 > b2:
    print(a1)
else:
    print(b1)