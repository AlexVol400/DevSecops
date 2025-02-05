counter = 0
sum = 0

while True:
    counter += 1
    avg = sum / counter

    num = float(input(f" Please enter a number {counter} (avg: {avg}, sum: {sum}): "))

    if num < 0:
        print(f"Thank you. Goodbye")
        break

    sum += num