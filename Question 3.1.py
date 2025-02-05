wordlist = []

while True:
    word = input('Please enter a word: ')

    if word in wordlist:
        print(f'{word} already found')
        break

    else:
        wordlist.append(word)