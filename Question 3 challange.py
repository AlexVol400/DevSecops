wordlist = []

while True:
    word = input('Please enter a word: ').lower()
    wordlist.append(word)
    word_to_check = word

    if wordlist.count(word_to_check) == 3:
        print(f'{word} already found')
        break