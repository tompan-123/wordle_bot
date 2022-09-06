import numpy as np
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
from selenium.webdriver.common.action_chains import ActionChains

# Open list of valid words
def get_word_list(word_list_path):
    result = []
    with open(word_list_path) as fp:
        result.extend([word.strip() for word in fp.readlines()])
    return result


# Returns incorrect letters
def badLetters(result, guess):
    bad_letters = []
    for i in range(0, 5):
        if result[i] == 0:
            bad_letters.append(guess[i])
    return bad_letters


# Returns correct letters that are wrong location
def partialLetters(result, guess):
    partial_letters = []
    for i in range(0, 5):
        if result[i] == 1:
            partial_letters.append([guess[i], i])
    return partial_letters


# Finds fully correct letters in word
def correctLetters(result, guess):
    correct_letters = []
    for i in range(0, 5):
        if result[i] == 2:
            correct_letters.append([guess[i], i])
    return correct_letters


# Returns possible choices (subset of all possible words)
def word_remover(result, guess, possible_words):
    bad_letters = badLetters(result, guess)
    correct_letters = correctLetters(result, guess)
    partial_letters = partialLetters(result, guess)
    good_letters = []
    for g in correct_letters:
        good_letters.append(g[0])
    for p in partial_letters:
        good_letters.append(p[0])

    acceptable_words1 = []
    for w in possible_words:
        check = 0
        for b in bad_letters:
            if b in w:
                # a letter might be bad and good if you guess twice but word only has one occurance
                if b in good_letters:
                    pass
                else:
                    check = 1
                    break
        if check == 0:
            acceptable_words1.append(w)

    acceptable_words2 = []
    for w in acceptable_words1:
        check = 0
        for g in correct_letters:
            if w[g[1]] != g[0]:
                check = 1
                break
        if check == 0:
            acceptable_words2.append(w)

    acceptable_words3 = []
    for w in acceptable_words2:
        check = 0
        for p in partial_letters:
            if w[p[1]] == p[0]:
                check = 1
                break
        if check == 0:
            acceptable_words3.append(w)

    acceptable_words4 = []
    for w in acceptable_words3:
        check = 0
        for g in good_letters:
            if g not in w:
                check = 1
                break
        if check == 0:
            acceptable_words4.append(w)

    acceptable_words5 = []
    for w in acceptable_words4:
        check = 0
        for b in bad_letters:
            if b in good_letters:
                if w.count(b) != good_letters.count(b):
                    check = 1
                    break
        if check == 0:
            acceptable_words5.append(w)
    return acceptable_words5


# Finds frequencies of letters in each position of each possible word
def letterFreq(possible_words):
    alphabet = "abcdefghijklmnopqrstuvwxyz"
    arr = {}
    for char in alphabet:
        freq = [0, 0, 0, 0, 0]
        for w in possible_words:
            for i in range(0, 5):
                if w[i] == char:
                    freq[i] += 1
        arr[char] = freq
    return arr


# Calculates score based on letter frequencies
def wordScore(possible_words, frequencies):
    word_scores = {}
    max_freq = [0, 0, 0, 0, 0]
    for char in frequencies:
        for i in range(0, 5):
            if max_freq[i] < frequencies[char][i]:
                max_freq[i] = frequencies[char][i]
    for w in possible_words:
        score = 1
        for i in range(0, 5):
            char = w[i]
            score *= 1 + (frequencies[char][i] - max_freq[i]) ** 2
        word_scores.update({w: score})
    return word_scores


# Finds best word
def bestWord(possible_words, frequencies):
    max_score = np.inf
    best_word = ""
    scores = wordScore(possible_words, frequencies)
    for w in possible_words:
        if scores[w] < max_score:
            max_score = scores[w]
            best_word = w
    return best_word


# Wrapper function to solve wordle
def solve(word_list_path, driver_path):
    print("Hello, Wordle Solver Bot is going to work its magic!")
    possible_words = get_word_list(word_list_path)

    driver = webdriver.Chrome(driver_path)

    driver.get("https://www.nytimes.com/games/wordle/index.html")

    try:
        cookies = WebDriverWait(driver, 3).until(
            EC.presence_of_element_located((By.ID, "pz-gdpr-btn-accept"))
        )
        cookies.click()
    except:
        print("No cookies popup")

    try:
        close = WebDriverWait(driver, 3).until(
            EC.presence_of_element_located(
                (By.CLASS_NAME, "Modal-module_closeIcon__b4z74")
            )
        )
        close.click()
    except:
        print("No tutorial popup")

    best_word = bestWord(possible_words, letterFreq(possible_words))

    actions = ActionChains(driver)
    actions.send_keys(best_word)
    actions.send_keys(Keys.RETURN)
    actions.perform()

    time.sleep(5)

    result = []
    for i in range(1, 6):
        block = driver.find_element_by_xpath(
            '//*[@id="wordle-app-game"]/div[1]/div/div[1]/div[' + str(i) + "]/div"
        )
        state = block.get_attribute("data-state")
        if state == "absent":
            result.append(0)
        elif state == "present":
            result.append(1)
        else:
            result.append(2)

    try:
        stats_screen = WebDriverWait(driver, 3).until(
            EC.presence_of_element_located(
                (By.XPATH, '//*[@id="wordle-app-game"]/div[3]/div/div[1]/div[1]')
            )
        )
        print("Wordle solved! The answer is: " + best_word + "!")
        return

    except:
        print("Guessing again")

    possible_words = word_remover(result, best_word, possible_words)

    for i in range(2, 7):
        possible_words = word_remover(result, best_word, possible_words)
        if len(possible_words) == 0:
            break
        best_word = bestWord(possible_words, letterFreq(possible_words))

        actions = ActionChains(driver)
        actions.send_keys(best_word)
        actions.send_keys(Keys.RETURN)
        actions.perform()

        time.sleep(5)

        try:
            stats_screen = WebDriverWait(driver, 3).until(
                EC.presence_of_element_located(
                    (By.XPATH, '//*[@id="wordle-app-game"]/div[3]/div/div[1]/div[1]')
                )
            )
            print("Wordle solved! The answer is: " + best_word + "!")
            return

        except:
            print("Guessing again")

        result = []
        for j in range(1, 6):
            block = driver.find_element_by_xpath(
                '//*[@id="wordle-app-game"]/div[1]/div/div['
                + str(i)
                + "]/div["
                + str(j)
                + "]/div"
            )
            state = block.get_attribute("data-state")
            if state == "absent":
                result.append(0)
            elif state == "present":
                result.append(1)
            else:
                result.append(2)

    print(
        "Oh no, looks like we weren't able to solve the Worldle in less than 6 tries today. Sorry :("
    )


if __name__ == "__main__":
    webdriver_path = input("Please input the location of your Chrome webdriver path: ")
    solve("possible_words.txt", webdriver_path)
    input("Press Return to exit program ")
    exit()
